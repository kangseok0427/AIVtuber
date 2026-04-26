# 🤖 brain/agent.py 코드 분석 문서

> AI VTuber 프로젝트 — LangGraph 에이전트 전체 코드 한 줄씩 분석  
> 작성 기준: Python 3.11 / LangGraph / LangChain / Ollama

---

## 📁 파일 위치

```
ai-vtuber/
└── brain/
    └── agent.py   ← 이 파일
```

---

## 📖 용어 정리

| 용어 | 설명 |
|------|------|
| **State** | 모든 노드가 공유하는 데이터 저장소. 노드는 state를 읽고 수정해서 다음 노드에 전달 |
| **Node** | 그래프 안의 실행 단위. 하나의 파이썬 함수가 하나의 노드 |
| **Edge** | 노드 간의 연결. 어떤 노드 다음에 어떤 노드로 갈지 결정 |
| **조건부 엣지** | 함수 반환값에 따라 다른 노드로 분기하는 엣지 |
| **TypedDict** | 딕셔너리인데 키와 값의 타입이 고정된 것. State 정의에 사용 |
| **Literal** | 특정 문자열 값만 허용하는 타입힌트. 예: `Literal["tools", "answer"]` |
| **SystemMessage** | LLM에게 역할/지시를 내리는 시스템 프롬프트. 대화 맥락의 최상단에 위치 |
| **HumanMessage** | 사용자(시청자)가 입력한 메시지 |
| **AIMessage** | LLM이 반환하는 응답 메시지. `.content`로 텍스트 꺼냄 |
| **tool_calls** | AIMessage 안에 담긴 툴 호출 요청 정보. 어떤 툴을 어떤 인자로 부를지 포함 |
| **ToolNode** | 툴 목록을 받아서 LLM이 요청한 툴을 자동으로 실행해주는 prebuilt 노드 |
| **tools_condition** | think 노드 출력의 tool_calls를 확인해서 라우팅 경로를 반환하는 prebuilt 함수 |
| **bind_tools** | LLM에게 "이런 툴들을 사용할 수 있어"라고 알려주는 메서드 |
| **invoke** | LLM 또는 그래프를 실행하는 메서드 |
| **compile** | 선언한 노드+엣지를 실행 가능한 객체로 변환 |
| **언패킹** | `{**state, "key": value}` = state 전체 복사하면서 특정 키만 수정 |
| **prebuilt** | LangGraph가 미리 구현해서 제공하는 컴포넌트 |
| **temperature** | LLM 답변의 창의성/다양성 조절값. 낮을수록 일관적, 높을수록 창의적 |

---

## 📦 import 블록

```python
import os
```
- 파이썬 내장 모듈
- `.env` 환경변수를 `os.getenv()`로 읽을 때 사용

```python
from dotenv import load_dotenv
```
- `.env` 파일을 읽어서 환경변수로 등록해주는 함수
- 이걸 호출해야 `os.getenv()`가 `.env` 값을 인식함

```python
from typing import TypedDict, Literal
```
- `TypedDict` = 딕셔너리의 키와 값의 타입을 명시할 수 있게 해주는 클래스. State 정의에 사용
- `Literal` = 특정 문자열 값만 허용하는 타입힌트
- 둘 다 타입힌트 전용이라 런타임엔 영향 없고, 코드 가독성과 IDE 자동완성에 도움

```python
from langchain_ollama import ChatOllama
```
- Ollama 서버와 통신하는 LangChain LLM 클래스
- `ChatOllama(model="gemma3:4b")`처럼 모델 이름 넘기면 해당 모델로 요청 전송

```python
from langchain_core.messages import HumanMessage, SystemMessage
```
- LangChain의 메시지 타입 클래스들
- `SystemMessage` = LLM에게 역할/지시를 내리는 시스템 프롬프트
- `HumanMessage` = 사용자(시청자)가 입력한 메시지
- 이 두 클래스로 메시지를 구조화해서 LLM에 전달

```python
from langgraph.graph import StateGraph, END
```
- `StateGraph` = 노드와 엣지로 구성된 에이전트 그래프를 만드는 클래스. 에이전트의 뼈대
- `END` = 그래프 실행을 종료하는 특수 노드. `add_edge("answer", END)`처럼 마지막 노드에 연결

```python
from langgraph.prebuilt import ToolNode, tools_condition
```
- `ToolNode` = 툴 목록을 받아서 LLM이 요청한 툴을 자동으로 실행해주는 prebuilt 노드
- `tools_condition` = think 노드의 출력을 보고 툴 호출이 있으면 `"tools"`, 없으면 `END`를 반환하는 라우팅 함수
- 둘 다 LangGraph가 제공하는 prebuilt 컴포넌트라 직접 구현 불필요

```python
from brain.tools import SearchTool, GuidebookTool, MemoryTool
```
- 우리가 직접 만든 툴 클래스 3개를 `brain/tools/__init__.py`를 통해 import
- `brain.tools` = `brain/tools/` 폴더를 파이썬 패키지로 인식

---

## ⚙️ 환경변수 + 설정

```python
load_dotenv()
```
- `.env` 파일을 읽어서 `os.environ`에 등록
- 이 줄이 없으면 `os.getenv()`가 `.env` 값을 못 읽음
- 반드시 import 직후에 호출해야 이후 코드에서 환경변수 사용 가능

```python
MODEL    = os.getenv("OLLAMA_MODEL", "gemma3:4b")
BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
NAME     = os.getenv("VTUBER_NAME", "하루")
T_THINK  = float(os.getenv("VTUBER_THINK_TEMP", "0.1"))
T_ANSWER = float(os.getenv("VTUBER_ANSWER_TEMP", "0.8"))
```

| 변수 | .env 키 | 기본값 | 설명 |
|------|---------|--------|------|
| `MODEL` | `OLLAMA_MODEL` | `gemma3:4b` | 사용할 Ollama 모델 이름 |
| `BASE_URL` | `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 서버 주소 |
| `NAME` | `VTUBER_NAME` | `하루` | VTuber 캐릭터 이름 |
| `T_THINK` | `VTUBER_THINK_TEMP` | `0.1` | think LLM temperature |
| `T_ANSWER` | `VTUBER_ANSWER_TEMP` | `0.8` | answer LLM temperature |

> `float(...)` 로 감싸는 이유: `os.getenv()`는 항상 **문자열**로 반환하기 때문에 숫자로 변환 필요. `ChatOllama`의 `temperature`는 `float` 타입을 요구함  
> 대문자 변수명은 **모듈 상수**라는 관례적 표시 (변경하지 않을 값)

---

## 🛠️ 툴 인스턴스 생성

```python
search_tool    = SearchTool().build()
guidebook_tool = GuidebookTool().build()
memory_tool    = MemoryTool()
memory_search  = memory_tool.build()
```

| 변수 | 설명 |
|------|------|
| `SearchTool().build()` | 클래스 인스턴스 생성 후 즉시 툴 반환 |
| `GuidebookTool().build()` | 동일. ChromaDB 로드까지 `__init__`에서 처리 |
| `memory_tool` | 인스턴스를 따로 저장. `answer_node`에서 `.save()` 호출 필요하기 때문 |
| `memory_search` | `memory_tool.build()`로 얻은 툴 객체. 검색용 |

> `MemoryTool()`만 따로 저장하는 이유: 다른 둘과 달리 **저장 기능(`.save()`)도 같이 써야 함**

```python
tools = [search_tool, guidebook_tool, memory_search]
```
- 세 툴을 리스트로 묶음
- `ToolNode`와 `bind_tools()` 두 곳에 모두 전달됨
- `ToolNode`는 실행용, `bind_tools`는 LLM에게 툴 존재를 알려주는 용도

---

## 🤖 LLM 두 개 선언

```python
llm_think  = ChatOllama(model=MODEL, base_url=BASE_URL, temperature=T_THINK)
llm_answer = ChatOllama(model=MODEL, base_url=BASE_URL, temperature=T_ANSWER)
```

| LLM | temperature | 역할 |
|-----|-------------|------|
| `llm_think` | 0.1 (낮음) | 냉정하게 상황 분석 + 툴 호출 판단 |
| `llm_answer` | 0.8 (높음) | 자연스럽고 창의적인 캐릭터 답변 생성 |

```python
llm_think_with_tools = llm_think.bind_tools(tools)
```
- `bind_tools()` = LLM에게 "이런 툴들을 사용할 수 있어"라고 알려주는 메서드
- 내부적으로 툴의 이름, 설명(독스트링), 인자 스키마를 LLM 프롬프트에 주입
- `llm_think`에만 바인딩하는 이유: 툴 호출 결정은 냉정한 분석 단계에서만, 답변 생성은 툴 결과를 참고만 하면 됨

---

## 📋 State 정의

```python
class VTuberState(TypedDict):
    user_input: str
    messages:   list
    emotion:    str
    answer:     str
```
- `TypedDict`를 상속 = 딕셔너리인데 키와 타입이 고정
- LangGraph의 모든 노드가 공유하는 데이터 저장소
- 노드는 이 state를 읽고 수정해서 다음 노드에 전달

| 키 | 타입 | 역할 |
|----|------|------|
| `user_input` | `str` | 시청자가 입력한 원본 채팅 텍스트 |
| `messages` | `list` | LLM에 전달되는 메시지 누적 리스트. SystemMessage, HumanMessage, AIMessage 등 |
| `emotion` | `str` | 감정 분류 결과. `answer_node`에서 추출해서 저장 |
| `answer` | `str` | VTuber의 최종 답변 텍스트 |

---

## 🧠 think_node

```python
def think_node(state: VTuberState) -> VTuberState:
```
- 인자로 `VTuberState` 타입의 `state`를 받아서 수정된 `VTuberState`를 반환
- LangGraph는 노드 함수가 반드시 state를 받고 state를 반환하는 구조

```python
    system = SystemMessage(content=f"""
당신은 AI VTuber '{NAME}'의 두뇌입니다.
시청자 채팅을 분석하고 필요한 툴을 호출하세요.
- 모르는 정보 → internet_search
- 캐릭터 설정/규칙 → guidebook_search
- 과거 대화 맥락 → memory_search
툴이 필요 없으면 바로 분석 결과만 반환하세요.
""")
```
- `SystemMessage` = LLM의 역할과 행동 지침 설정
- f-string 안에 `{NAME}`이 들어가서 `.env`의 캐릭터 이름 자동 삽입
- 이 지시가 명확할수록 에이전트의 툴 선택 정확도 상승
- `think_node`와 `answer_node`의 SystemMessage가 다른 이유: think는 "분석하는 두뇌", answer는 "말하는 캐릭터"로 역할 분리

```python
    human = HumanMessage(content=state["user_input"])
```
- `state["user_input"]` = 시청자가 입력한 채팅 텍스트를 state에서 꺼냄
- `HumanMessage`로 감싸서 LLM이 "이게 사용자 발화"임을 인식하게 함

```python
    messages = [system, human]
    response = llm_think_with_tools.invoke(messages)
```
- `messages` = 시스템 프롬프트 + 사용자 메시지를 리스트로 구성
- `llm_think_with_tools.invoke(messages)` = LLM에게 메시지 전달하고 응답 받기
- 응답(`response`)은 `AIMessage` 타입
- 툴 호출이 필요하면 `tool_calls` 필드에 어떤 툴을 부를지 정보가 담김

```python
    return {**state, "messages": messages + [response]}
```
- `{**state, ...}` = state 전체를 복사하면서 특정 키만 수정하는 딕셔너리 언패킹
- `messages + [response]` = 기존 메시지 리스트에 LLM 응답을 추가
- `messages` 전체를 state에 저장하는 이유: 다음 노드가 대화 맥락 전체를 이어받아야 하기 때문

---

## 🎤 answer_node

```python
def answer_node(state: VTuberState) -> VTuberState:
```
- `think_node` 또는 `tools` 노드 이후에 실행
- state 안의 `messages`에는 이미 think 결과 + 툴 실행 결과까지 누적돼 있음

```python
    system = SystemMessage(content=f"""
당신은 활발하고 귀여운 AI VTuber '{NAME}'입니다.
이전 분석과 툴 결과를 참고해서 시청자에게 자연스럽게 답하세요.
- 짧고 자연스러운 한국어 (2~3문장)
- 이모지 1~2개
- 친근하고 활기찬 말투
""")
```
- think의 시스템 프롬프트와 역할이 다름
- think는 "분석하는 두뇌", answer는 "말하는 캐릭터"

```python
    response = llm_answer.invoke([system] + state["messages"])
```
- `llm_answer` = temp=0.8의 창의적인 LLM
- `[system] + state["messages"]` = 캐릭터 지시 프롬프트 + 지금까지의 모든 메시지(think 결과, 툴 결과 포함)
- `answer_node`는 전체 맥락을 다 보고 최종 답변 생성

```python
    answer = response.content
```
- `response`는 `AIMessage` 객체
- `.content` = 실제 텍스트 내용만 꺼냄

```python
    emotion = "neutral"
    for tag in ["happy", "sad", "angry", "surprised", "neutral"]:
        if tag in answer.lower():
            emotion = tag
            break
```

| 코드 | 설명 |
|------|------|
| `emotion = "neutral"` | 기본값을 neutral로 설정 |
| `answer.lower()` | 대소문자 구분 없이 탐색 |
| `break` | 첫 번째 매칭되는 감정 태그 하나만 뽑고 루프 종료 |

> 현재는 단순 문자열 탐색 방식. 나중에 별도 감정 분류 툴로 고도화 가능

```python
    memory_tool.save(state["user_input"], answer)
```
- 대화 한 턴(시청자 입력 + VTuber 답변)을 ChromaDB에 저장
- `memory_tool`은 위에서 따로 인스턴스로 저장해뒀기 때문에 `.save()` 호출 가능
- 다음 대화에서 `memory_search` 툴이 이 내용을 검색해서 맥락으로 활용

```python
    return {**state, "answer": answer, "emotion": emotion}
```
- state에 최종 답변과 감정 태그를 추가해서 반환
- 이게 그래프의 최종 출력값

---

## 🕸️ 그래프 조립

```python
graph = StateGraph(VTuberState)
```
- `StateGraph` = LangGraph 핵심 클래스. 어떤 State를 쓸지 타입으로 선언
- `VTuberState`를 넘겨야 각 노드 함수의 인자/반환 타입을 자동으로 검증

```python
graph.add_node("think",  think_node)
graph.add_node("tools",  ToolNode(tools))
graph.add_node("answer", answer_node)
```

| 노드 이름 | 함수 | 설명 |
|----------|------|------|
| `"think"` | `think_node` | 사고 + 툴 호출 판단 |
| `"tools"` | `ToolNode(tools)` | LLM이 요청한 툴 자동 실행 |
| `"answer"` | `answer_node` | 캐릭터 말투로 최종 답변 생성 |

> `ToolNode(tools)` = 직접 함수 구현 불필요. tools 리스트를 넘기면 LLM이 요청한 툴을 알아서 찾아서 실행

```python
graph.set_entry_point("think")
```
- 그래프 실행의 시작점을 `"think"` 노드로 지정
- `agent.invoke()` 호출 시 무조건 `think_node`부터 실행

```python
graph.add_conditional_edges(
    "think",
    tools_condition,
    {
        "tools": "tools",
        END: "answer"
    }
)
```
- `add_conditional_edges(출발노드, 판단함수, 라우팅맵)` = 조건에 따라 다른 노드로 분기

| 인자 | 설명 |
|------|------|
| `"think"` | 출발 노드 |
| `tools_condition` | think 노드 출력의 `tool_calls` 확인해서 경로 반환하는 prebuilt 함수 |
| `{"tools": "tools", END: "answer"}` | 라우팅맵. `"tools"` 반환 시 tools 노드로, `END` 반환 시 answer 노드로 |

```python
graph.add_edge("tools", "answer")
graph.add_edge("answer", END)
```
- `add_edge(A, B)` = 항상 A 다음엔 B로 이동하는 고정 엣지
- 툴 실행 후엔 무조건 `answer_node`로
- `answer_node` 후엔 무조건 그래프 종료

```python
agent = graph.compile()
```
- 선언한 노드+엣지를 실행 가능한 객체로 컴파일
- `compile()` 이후에야 `agent.invoke()` 호출 가능
- 내부적으로 엣지 연결 유효성 검사, 타입 검사 등 수행

---

## 🔁 실행 루프

```python
if __name__ == "__main__":
```
- 이 파일을 직접 실행할 때만 아래 코드 동작
- 다른 파일에서 `from brain.agent import agent`로 import할 때는 실행 안 됨

```python
    result = agent.invoke({
        "user_input": user_input,
        "messages":   [],
        "emotion":    "",
        "answer":     ""
    })
```

| 키 | 초기값 | 이유 |
|----|--------|------|
| `user_input` | 입력된 텍스트 | 유일하게 채워진 초기값 |
| `messages` | `[]` | 노드를 거치면서 채워짐 |
| `emotion` | `""` | `answer_node`에서 채워짐 |
| `answer` | `""` | `answer_node`에서 채워짐 |

```python
    print(f"\n😊 감정: {result['emotion']}")
    print(f"🎤 {NAME}: {result['answer']}\n")
```
- `result['emotion']` = `answer_node`가 추출한 감정 태그
- `result['answer']` = VTuber의 최종 답변 텍스트

---

## 🔄 전체 실행 흐름

```
agent.invoke() 호출
    ↓
think_node
    └─ SystemMessage + HumanMessage 구성
    └─ llm_think_with_tools.invoke() 실행
    └─ AIMessage 반환 (tool_calls 포함 여부로 분기)
    ↓
tools_condition 판단
    ├─ tool_calls 있음 → tools 노드
    │       └─ ToolNode가 tool_calls 파싱
    │       └─ 해당 툴 실행 → ToolMessage로 결과 반환
    │       └─ answer 노드로 이동
    │
    └─ tool_calls 없음 → answer 노드로 바로 이동
    ↓
answer_node
    └─ [system] + state["messages"] 전체를 llm_answer에 전달
    └─ 감정 태그 추출
    └─ memory_tool.save() 호출 (대화 저장)
    └─ 최종 state 반환
    ↓
END
```

---

## 📊 노드별 LLM 비교

| 항목 | think_node | answer_node |
|------|-----------|-------------|
| LLM | `llm_think_with_tools` | `llm_answer` |
| temperature | 0.1 (냉정) | 0.8 (창의적) |
| 툴 바인딩 | ✅ 있음 | ❌ 없음 |
| 역할 | 상황 분석 + 툴 호출 판단 | 캐릭터 말투로 최종 답변 |
| 입력 | system + human | system + 전체 messages |

---

## ⚙️ .env 설정 전체

```env
OLLAMA_MODEL=gemma3:4b
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://localhost:11434
VTUBER_NAME=하루
VTUBER_THINK_TEMP=0.1
VTUBER_ANSWER_TEMP=0.8
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=ai-vtuber
```