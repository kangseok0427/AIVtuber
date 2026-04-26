# 📚 AI VTuber 프로젝트 참고문헌

> LangGraph 에이전트 + RAG + 메모리 + VTuber 관련 논문 및 GitHub 레퍼런스

---

## 🧠 핵심 논문

### 1. ReAct: Synergizing Reasoning and Acting in Language Models
- **저자**: Yao et al.
- **연도**: 2022
- **링크**: https://arxiv.org/abs/2210.03629
- **핵심 내용**: 추론(Reasoning) + 행동(Acting)을 결합한 에이전트 패턴의 원조 논문. LLM이 생각하고 툴을 호출하고 관찰하는 루프를 반복하는 ReAct 프레임워크 제안.
- **우리 프로젝트 관련성**: `think 노드 (temp=0.1)` → 툴 호출 → `answer 노드 (temp=0.8)` 구조의 이론적 기반

---

### 2. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- **저자**: Lewis et al.
- **연도**: 2020
- **링크**: https://arxiv.org/abs/2005.11401
- **핵심 내용**: 외부 문서를 벡터 검색으로 가져와서 LLM의 답변을 보강하는 RAG 프레임워크 원조 논문. 파라메트릭 메모리(LLM 가중치)와 비파라메트릭 메모리(검색 인덱스)의 결합.
- **우리 프로젝트 관련성**: `GuidebookTool`, `MemoryTool`의 이론적 기반. hot-swap 가능한 검색 인덱스 구조.

---

### 3. Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG
- **연도**: 2025
- **링크**: https://arxiv.org/abs/2501.09136
- **핵심 내용**: 기존 정적 RAG를 넘어 동적 의사결정, 반복 추론, 협업 워크플로우를 결합한 Agentic RAG 시스템 전반을 정리한 서베이. LangGraph, LlamaIndex, AutoGen 등 주요 프레임워크 비교 포함.
- **우리 프로젝트 관련성**: 전체 에이전트 아키텍처 설계의 이론적 근거. think→tool→answer 루프 설계 참고.

---

### 4. Memory in the Age of AI Agents: A Survey
- **연도**: 2025
- **링크**: https://github.com/Shichun-Liu/Agent-Memory-Paper-List
- **핵심 내용**: AI 에이전트의 메모리 시스템을 단기/장기/외부 메모리로 분류하고 RAG, episodic memory, 대화 맥락 등 관련 논문 전체를 정리한 서베이.
- **우리 프로젝트 관련성**: `MemoryTool` 고도화 시 참고. episodic memory 구조 적용 가능.

---

### 5. ChatHaruhi: Reviving Anime Character in Reality via Large Language Model
- **연도**: 2024
- **링크**: https://arxiv.org/abs/2308.09597
- **핵심 내용**: 애니메이션 캐릭터의 말투, 성격, 기억을 LLM으로 재현하는 연구. 캐릭터 설정 프롬프트 + 장기 기억 구조 + 대화 스타일 유지 방법론 제안.
- **우리 프로젝트 관련성**: VTuber 캐릭터 설정 및 말투 유지에 직접 적용 가능. 시스템 프롬프트 설계 참고.

---

### 6. Buffer of Thoughts: Thought-Augmented Reasoning with Large Language Models
- **연도**: 2024
- **링크**: https://arxiv.org/abs/2406.04271
- **핵심 내용**: LLM의 추론 과정을 버퍼에 저장하고 재활용하는 방식으로 복잡한 추론 성능을 향상시키는 프레임워크.
- **우리 프로젝트 관련성**: `think 노드`의 사고 과정을 state에 저장하고 재활용하는 구조 설계 참고.

---

### 7. LLMs Working in Harmony: A Survey on Multi-Agent Systems
- **연도**: 2025
- **링크**: https://arxiv.org/abs/2504.01963
- **핵심 내용**: LLM 기반 멀티에이전트 시스템의 Planning, Memory, Tool Use, Framework를 종합적으로 정리. ReAct, Tree of Thoughts, LangGraph, CrewAI 등 비교.
- **우리 프로젝트 관련성**: 에이전트 설계 전반의 개념 정리용 서베이.

---

### 8. MemGPT: Towards LLMs as Operating Systems
- **연도**: 2023
- **링크**: https://arxiv.org/abs/2310.08560
- **핵심 내용**: LLM을 OS처럼 메모리를 계층적으로 관리하는 구조 제안. 컨텍스트 윈도우를 RAM처럼, 외부 DB를 디스크처럼 활용.
- **우리 프로젝트 관련성**: `MemoryTool`을 계층적 메모리로 고도화할 때 참고.

---

### 9. RoleLLM: Benchmarking, Eliciting, and Enhancing Role-Playing Abilities of LLMs
- **연도**: 2023
- **링크**: https://arxiv.org/abs/2310.00746
- **핵심 내용**: LLM의 롤플레잉 능력을 벤치마크하고 향상시키는 방법론. 캐릭터별 말투, 지식, 성격을 유지하는 프롬프트 전략 제안.
- **우리 프로젝트 관련성**: VTuber 캐릭터 일관성 유지 프롬프트 설계 참고.

---

## 💻 참고 GitHub 프로젝트

### 1. Open-LLM-VTuber ⭐ (1순위)
- **링크**: https://github.com/Open-LLM-VTuber/Open-LLM-VTuber
- **스타**: 활발히 유지보수 중
- **핵심 내용**: Ollama, OpenAI 등 다양한 LLM과 Live2D 아바타를 연동하는 오픈소스 AI VTuber 프레임워크. 에이전트 인터페이스를 상속해서 커스텀 구현 가능한 모듈러 구조. ASR/TTS/LLM 전부 교체 가능.
- **참고할 부분**: Live2D 연동 방식, TTS 파이프라인, 에이전트 인터페이스 설계
- **문서**: https://open-llm-vtuber.github.io/

---

### 2. agent-service-toolkit ⭐ (2순위)
- **링크**: https://github.com/JoshuaC215/agent-service-toolkit
- **핵심 내용**: LangGraph + FastAPI + Streamlit으로 구성된 AI 에이전트 서비스 풀스택 템플릿. LangGraph v1.0의 interrupt(), Command, Store, langgraph-supervisor 등 최신 기능 구현 포함.
- **참고할 부분**: `agent.py` 구조, 스트리밍 처리 방식, LangSmith 연동

---

### 3. awesome-LangGraph
- **링크**: https://github.com/von-development/awesome-LangGraph
- **핵심 내용**: LangGraph 생태계의 개념, 프로젝트, 툴, 템플릿을 정리한 인덱스. Agentic RAG, 멀티에이전트, 스트리밍 채팅 등 다양한 구현 예제 큐레이션.
- **참고할 부분**: 유사 프로젝트 레퍼런스, 패턴별 구현 예제 탐색용

---

### 4. AgenticRAG-Survey
- **링크**: https://github.com/asinghcsu/AgenticRAG-Survey
- **핵심 내용**: ReAct 에이전트 기반 RAG 파이프라인 구현 예제 모음. 쿼리 재구성, 셀프 쿼리, 반복 검색, Corrective RAG, Self RAG 전략까지 포함.
- **참고할 부분**: `GuidebookTool`, `MemoryTool` 고도화 시 검색 전략 참고

---

### 5. Agent Memory Paper List
- **링크**: https://github.com/Shichun-Liu/Agent-Memory-Paper-List
- **핵심 내용**: AI 에이전트 메모리 관련 논문을 단기/장기/외부/파라메트릭 메모리로 분류해서 정리한 큐레이션 리스트.
- **참고할 부분**: memory 툴 설계 고도화할 때 논문 탐색용

---

### 6. LangGraph (공식)
- **링크**: https://github.com/langchain-ai/langgraph
- **핵심 내용**: 상태 기반 멀티에이전트 프레임워크. Durable execution, Human-in-the-loop, 장단기 메모리 통합 지원. Klarna, Replit, Elastic 등 프로덕션 적용 사례 다수.
- **참고할 부분**: 공식 예제, LCEL 패턴, ToolNode 사용법

---

### 7. LangGraph Chatbot Agent
- **링크**: https://github.com/ProactiveAIAgents/LangGraph_Chatbot_Agent
- **핵심 내용**: LangGraph로 구조화된 대화 흐름과 복잡한 다이얼로그 상태를 관리하는 대화 에이전트 구현 예제.
- **참고할 부분**: 대화 상태 관리 패턴, 그래프 구성 방식

---

## 🛠️ 주요 프레임워크 공식 문서

| 프레임워크 | 문서 링크 |
|-----------|----------|
| LangGraph | https://langchain-ai.github.io/langgraph/ |
| LangChain | https://python.langchain.com/docs/ |
| LangSmith | https://docs.smith.langchain.com/ |
| Ollama | https://ollama.com/library |
| ChromaDB | https://docs.trychroma.com/ |
| DuckDuckGo Search | https://pypi.org/project/duckduckgo-search/ |

---

## 📖 읽기 추천 순서

```
입문 (지금 단계)
  1. ReAct 논문 → think/answer 구조 이해
  2. RAG 논문 → guidebook/memory 툴 이해
  3. LangGraph 공식 문서 → agent.py 구현 전 필독

중급 (툴 고도화 단계)
  4. Agentic RAG Survey → 검색 전략 고도화
  5. ChatHaruhi → 캐릭터 일관성 강화
  6. RoleLLM → 롤플레잉 프롬프트 개선

고급 (프로덕션 단계)
  7. MemGPT → 메모리 계층화
  8. Buffer of Thoughts → 추론 고도화
  9. Memory Survey → 장기 메모리 설계
```