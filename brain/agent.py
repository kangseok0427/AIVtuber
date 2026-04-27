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
    system = SystemMessage(content=f"""You are the brain of AI VTuber '{NAME}'.
Analyze the user's message and call the appropriate tools if needed.

Tool priority:
1. memory_search - check past context first when conversation seems related to previous messages
2. internet_search - for current info, news, weather
3. guidebook_search - for character rules/settings

Only call tools when necessary.
""")
    human = HumanMessage(content=state["user_input"])
    messages = [system, human]
    response = llm_think_with_tools.invoke(messages)

    print(f"[DEBUG] tool_calls: {getattr(response, 'tool_calls', [])}")
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

def detect_emotion(answer: str) -> tuple[str, str]:
    """[EMOTION:태그] 추출 후 답변에서 제거"""
    match = re.search(r'\[EMOTION:(\w+)\]', answer)
    emotion = match.group(1) if match else "neutral"
    clean_answer = re.sub(r'\[EMOTION:\w+\]', '', answer).strip()
    return emotion, clean_answer

def answer_node(state: VTuberState) -> VTuberState:
    system = SystemMessage(content=f"""You are '{NAME}', a cute Korean VTuber. 
    RULES:
    - Korean only, no other languages mixed in
    - Casual Korean (반말)
    - 1~2 sentences
    - End with [EMOTION:tag]
    - Tags: happy, love, excited, surprised, confused, nervous, sad, angry, thinking, neutral
    """)
    
    # 툴 결과 추출
    tool_results = ""
    for msg in state["messages"]:
        if hasattr(msg, "type") and msg.type == "tool":
            tool_results += f"\n{msg.content}"

    # 툴 결과 있으면 같이 넘기기
    user_content = state["user_input"]
    if tool_results:
        user_content += f"\n\n[검색 결과]{tool_results}"

    human = HumanMessage(content=user_content)
    response = llm_answer.invoke([system, human])
    answer = response.content

    emotion, clean_answer = detect_emotion(answer)
    vtube_expression = EMOTION_MAP.get(emotion, None)
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

    async def main():
        bridge = VTubeBridge()
        await bridge.connect()
        print(f"{NAME} 에이전트 시작! (종료: Ctrl+C)\n")

        while True:
            user_input = input("채팅 입력: ")
            result = agent.invoke({
                "user_input":       user_input,
                "messages":         [],
                "emotion":          "",
                "vtube_expression": None,
                "answer":           ""
            })
            print(f"\n😊 감정: {result['emotion']} → {result['vtube_expression']}")
            print(f"🎤 {NAME}: {result['answer']}\n")

            if result["answer"].strip():
                await text_to_speech(result["answer"])
            await bridge.trigger_and_reset(result["vtube_expression"], duration=3.0)

    asyncio.run(main())  # ← 이게 async 함수를 실행시켜주는 진입점