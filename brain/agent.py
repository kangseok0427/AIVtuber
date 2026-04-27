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

load_dotenv()

MODEL    = os.getenv("OLLAMA_MODEL", "gemma3:4b")
BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
NAME     = os.getenv("VTUBER_NAME", "하루")
T_THINK  = float(os.getenv("VTUBER_THINK_TEMP", "0.1"))
T_ANSWER = float(os.getenv("VTUBER_ANSWER_TEMP", "0.8"))

# 툴 인스턴스 생성
search_tool    = SearchTool().build()
guidebook_tool = GuidebookTool().build()
memory_tool    = MemoryTool()
memory_search  = memory_tool.build()

tools = [search_tool, guidebook_tool, memory_search]

# 두 가지 온도 LLM
llm_think  = ChatOllama(model=MODEL, base_url=BASE_URL, temperature=T_THINK)
llm_answer = ChatOllama(model=MODEL, base_url=BASE_URL, temperature=T_ANSWER)

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
    system = SystemMessage(content=f"""
당신은 AI VTuber '{NAME}'의 두뇌입니다.
시청자 채팅을 분석하고 필요한 툴을 호출하세요.
- 모르는 정보 → internet_search
- 캐릭터 설정/규칙 → guidebook_search
- 과거 대화 맥락 → memory_search
툴이 필요 없으면 바로 분석 결과만 반환하세요.
""")
    human = HumanMessage(content=state["user_input"])
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

def detect_emotion(answer: str) -> str:
    answer_lower = answer.lower()
    if any(w in answer_lower for w in ["사랑", "좋아"]):
        return "love"
    if any(w in answer_lower for w in ["와", "대박", "반짝", "신나"]):
        return "excited"
    if any(w in answer_lower for w in ["놀", "깜짝", "헉"]):
        return "surprised"
    if any(w in answer_lower for w in ["음", "흠", "모르", "헷갈"]):
        return "confused"
    if any(w in answer_lower for w in ["떨", "긴장", "걱정"]):
        return "nervous"
    if any(w in answer_lower for w in ["슬", "힘들", "속상"]):
        return "sad"
    if any(w in answer_lower for w in ["화", "짜증"]):
        return "angry"
    if any(w in answer_lower for w in ["생각", "찾", "검색"]):
        return "thinking"
    if any(w in answer_lower for w in ["행복", "즐", "웃"]):
        return "happy"
    return "neutral"

def answer_node(state: VTuberState) -> VTuberState:
    system = SystemMessage(content=f"""
당신은 활발하고 귀여운 AI VTuber '{NAME}'입니다.
이전 분석과 툴 결과를 참고해서 시청자에게 자연스럽게 답하세요.
- 짧고 자연스러운 한국어 (2~3문장)
- 이모지 사용 금지
- 친근하고 활기찬 말투
""")
    
    response = llm_answer.invoke([system] + state["messages"])
    answer = response.content

    emotion = detect_emotion(answer)
    vtube_expression = EMOTION_MAP.get(emotion, None)

    return {**state, "answer": answer, "emotion": emotion, "vtube_expression": vtube_expression}

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

            await bridge.trigger_and_reset(result["vtube_expression"], duration=3.0)

    asyncio.run(main())  # ← 이게 async 함수를 실행시켜주는 진입점