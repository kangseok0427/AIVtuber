# brain/agent.py
import os
from dotenv import load_dotenv
from typing import TypedDict, Literal
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from typing import Annotated

from brain.tools import SearchTool, GuidebookTool, MemoryTool
from avatar.vtube_bridge import VTubeBridge
from tts.tts import text_to_speech
import re
import re as _re

load_dotenv()

THINK_MODEL  = os.getenv("OLLAMA_THINK_MODEL")
ANSWER_MODEL = os.getenv("OLLAMA_ANSWER_MODEL")
BASE_URL = os.getenv("OLLAMA_BASE_URL")
NAME     = os.getenv("VTUBER_NAME")
T_THINK  = float(os.getenv("VTUBER_THINK_TEMP"))
T_ANSWER = float(os.getenv("VTUBER_ANSWER_TEMP"))

# 툴 인스턴스 생성
search_tool    = SearchTool().build()
guidebook_tool = GuidebookTool().build()
memory_tool    = MemoryTool()
memory_search  = memory_tool.build()

tools = [search_tool, guidebook_tool, memory_search]

# 두 가지 온도 LLM
llm_think  = ChatOllama(model=THINK_MODEL,  base_url=BASE_URL, temperature=T_THINK)
llm_answer = ChatOllama(model=ANSWER_MODEL, base_url=BASE_URL, temperature=T_ANSWER)
# 툴 바인딩은 think LLM에만 (툴 호출 판단은 냉정하게)
llm_think_with_tools = llm_think.bind_tools(tools)

# brain/agent.py - 상단에 추가

def load_prompt(filename: str, **kwargs) -> str:
    with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
        return f.read().format(**kwargs)

# 상태 정의
# brain/agent.py - VTuberState에 필드 추가

class VTuberState(TypedDict):
    user_input:       str
    messages:         Annotated[list, add_messages]
    emotion:          str
    vtube_expression: str | None  # ✅ 추가
    answer:           str

# 노드 1 — think (툴 호출 판단 + 사고)
def think_node(state: VTuberState) -> VTuberState:
    # 최근 3개 대화 시간순으로 무조건 불러오기
    all_results = memory_tool.db.get()
    memory_context = ""

    if all_results and all_results['documents']:
        paired = list(zip(all_results['documents'], all_results['metadatas']))
        paired.sort(key=lambda x: x[1].get('timestamp', ''), reverse=True)
        recent = paired[:3]
        recent.reverse()
        memory_context = "\n\n[최근 대화 기록]\n" + "\n".join(
            f"- {doc}" for doc, _ in recent
        )

    system = SystemMessage(content=load_prompt("think.txt", NAME=NAME))

    user_content = state["user_input"]
    if memory_context:
        user_content += memory_context

    human = HumanMessage(content=user_content)
    messages = [system, human]
    response = llm_think_with_tools.invoke(messages)
    return {**state, "messages": [system, human, response]}
# 노드 2 — answer (캐릭터 말투로 최종 답변)
# brain/agent.py - answer_node 함수 전체 교체

# brain/agent.py - answer_node 안 감정 분류 부분 교체

EMOTION_MAP = {
    "happy":     "Exp7 Laugh",
    "love":      "Exp2 Heart",
    "excited":   "Exp1 Sparkling",
    "surprised": "Exp6 Surprise",
    "confused":  "Exp3 Confused",
    "nervous":   "Exp10 Nervous",
    "sad":       "Exp5 FaceShadow",
    "angry":     "Exp8 Angry",
    "thinking":  "Exp9 Loading",
    "neutral":   None
}
# 노드와 엣지! 학습 시작하기
def detect_emotion(answer: str) -> tuple[str, str]:
    """[EMOTION:태그] 추출 후 답변에서 제거"""
    match = re.search(r'\[EMOTION:(\w+)\]', answer)
    emotion = match.group(1) if match else "neutral"
    clean_answer = re.sub(r'\[EMOTION:\w+\]', '', answer).strip()
    return emotion, clean_answer

def answer_node(state: VTuberState) -> VTuberState:
    system = SystemMessage(content=load_prompt("answer.txt", NAME=NAME))

    # 툴 결과 추출
    tool_results = ""
    for msg in state["messages"]:
        if hasattr(msg, "type") and msg.type == "tool":
            tool_results += f"\n{msg.content}"

    # ✅ messages에서 memory_context 추출 (HumanMessage에 포함돼 있음)
    user_content = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            user_content = msg.content
            break

    if tool_results:
        user_content += f"\n\n[검색 결과]{tool_results}"

    human = HumanMessage(content=user_content)
    response = llm_answer.invoke([system, human])
    answer = response.content
    ...

    import re as _re
    clarification = _re.search(r'\[NEED_CLARIFICATION:(.*?)\]', answer)
    if clarification:
        question = clarification.group(1).strip()
        clean_answer = question + " [EMOTION:confused]"
        emotion, clean_answer = detect_emotion(clean_answer)
        vtube_expression = EMOTION_MAP.get(emotion, None)
        memory_tool.save(state["user_input"], clean_answer)
        return {**state, "answer": clean_answer, "emotion": emotion, "vtube_expression": vtube_expression}

    emotion, clean_answer = detect_emotion(answer)
    vtube_expression = EMOTION_MAP.get(emotion, None)
    
    with open("obs/overlay.html", "r", encoding="utf-8") as f:
        overlay = f.read()

    overlay_updated = re.sub(
        r'<div id="message">.*?</div>',
        f'<div id="message">{clean_answer}</div>',
        overlay,
        flags=re.DOTALL
    )

    with open("obs/overlay.html", "w", encoding="utf-8") as f:
        f.write(overlay_updated)

    memory_tool.save(state["user_input"], answer)
    return {**state, "answer": clean_answer, "emotion": emotion, "vtube_expression": vtube_expression}
# 그래프 조립
graph = StateGraph(VTuberState)

graph.add_node("think",  think_node)
graph.add_node("tools",  ToolNode(tools))
graph.add_node("answer", answer_node)

graph.set_entry_point("think")

# think 후 툴 호출 여부 판단 (조건부 엣지)
def should_use_tools(state: VTuberState) -> Literal["tools", "answer"]:
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "answer"

graph.add_conditional_edges(
    "think",
    should_use_tools,
    {
        "tools": "tools",
        "answer": "answer"
    }
)

# 툴 실행 후 → answer
graph.add_edge("tools", "answer")
graph.add_edge("answer", END)

agent = graph.compile()

# 테스트
# brain/agent.py - __main__ 블록 전체 교체

if __name__ == "__main__":
    import asyncio
    from avatar.vtube_bridge import VTubeBridge
    from chat.reader import ChzzkReader

    async def main():
        bridge = VTubeBridge()
        await bridge.connect()
        print(f"{NAME} 에이전트 시작!\n")

        async def handle_chat(nickname: str, content: str):
            result = agent.invoke({
                "user_input":       f"{nickname}: {content}",
                "messages":         [],
                "emotion":          "",
                "vtube_expression": None,
                "answer":           ""
            })
            print(f"😊 감정: {result['emotion']} → {result['vtube_expression']}")
            print(f"🎤 {NAME}: {result['answer']}\n")

            await asyncio.gather(
                bridge.trigger_and_reset(result["vtube_expression"], duration=5.0),
                text_to_speech(result["answer"])
            )

        reader = ChzzkReader(on_chat_callback=handle_chat)
        await reader.start()

    asyncio.run(main())