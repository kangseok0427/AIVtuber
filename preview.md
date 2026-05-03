# 🎭 가온 AI VTuber - 최종 기술 스택 정리

## 📌 프로젝트 개요
치지직 방송 플랫폼에서 실시간으로 시청자와 소통하는 AI VTuber 시스템.
시청자 채팅을 읽고, AI가 캐릭터 말투로 답변하며, 음성과 표정까지 자동으로 제어.

---

## 🏗 전체 아키텍처
```
치지직 채팅
    ↓
버퍼 + 주제 필터링 (LLM 선택)
    ↓
LangGraph 에이전트
    ├── think_node (툴 호출 판단 + 메모리 조회)
    ├── tools (검색 / 메모리 / 가이드북)
    └── answer_node (캐릭터 답변 생성)
    ↓
감정 분류 → VTube Studio 표정 제어
    ↓
Edge TTS → Applio RVC → VB-Cable
    ↓
VTube Studio 립싱크 + OBS 자막 오버레이
    ↓
치지직 방송 송출
```

---

## 🧠 AI / LLM
| 기술 | 버전/모델 | 용도 |
|------|-----------|------|
| LangChain | 최신 | 에이전트 프레임워크 |
| LangGraph | 최신 | 에이전트 워크플로우 |
| Ollama | 학교 GPU 서버 | LLM 서버 |
| gemma4:26b | 26B | 메인 대화 모델 (think + answer) |
| nomic-embed-text | 최신 | 텍스트 임베딩 |
| ChromaDB | 최신 | 벡터 DB |

## 🛠 툴 시스템
| 툴 | 용도 |
|----|------|
| ddgs (DuckDuckGo) | 인터넷 실시간 검색 |
| memory_search | 과거 대화 맥락 조회 (ChromaDB) |
| guidebook_search | 캐릭터 설정 / 방송 규칙 조회 |

## 🎙 음성
| 기술 | 용도 |
|------|------|
| Edge TTS | 텍스트 → 음성 변환 |
| Applio (RVC) | 음성 → 가온 목소리 변환 (파일 변환 방식) |
| Gradio Client | Applio API 호출 |
| PyAudio | 오디오 출력 |
| SoundDevice | 오디오 재생 |
| SoundFile | 오디오 파일 처리 |
| VB-Cable | 가상 오디오 케이블 |
| BlackHole | Mac 오디오 라우팅 |

## 🎭 아바타
| 기술 | 용도 |
|------|------|
| VTube Studio | Live2D 아바타 제어 |
| WebSocket | VTube Studio API 연결 |
| uLipSync | 립싱크 |
| Syphon | VTube Studio → OBS 연결 |

## 💬 채팅
| 기술 | 용도 |
|------|------|
| chzzkpy | 치지직 채팅 비공식 라이브러리 |
| asyncio | 비동기 채팅 처리 |
| 버퍼 시스템 | 채팅 임시 저장 + 만료 처리 |
| LLM 주제 선택 | 방송 주제 기반 채팅 선택 |

## 📺 방송
| 기술 | 용도 |
|------|------|
| OBS | 방송 송출 (Apple VT H.264 Hardware) |
| HTML 오버레이 | 실시간 자막 표시 (meta refresh) |

---

## 📁 프로젝트 구조
```
ai-vtuber/
├── main.py                  # 진입점
├── start.sh                 # 자동 시작 스크립트
├── .env                     # 환경변수 (gitignore)
├── brain/
│   ├── agent.py             # LangGraph 에이전트
│   └── tools/
│       ├── __init__.py
│       ├── search.py        # 인터넷 검색 툴 (ddgs)
│       ├── memory.py        # 대화 메모리 툴 (ChromaDB)
│       └── guidebook.py     # 캐릭터 가이드북 툴
├── avatar/
│   └── vtube_bridge.py      # VTube Studio WebSocket 연결
├── chat/
│   └── reader.py            # 치지직 채팅 읽기 + 필터링
├── tts/
│   └── tts.py               # Edge TTS + Applio RVC 변환
├── obs/
│   └── overlay.html         # OBS 자막 오버레이
├── prompts/                 # 시스템 프롬프트 (gitignore)
│   ├── think.txt            # think 노드 프롬프트
│   └── answer.txt           # answer 노드 프롬프트
├── docs/                    # 가이드북 문서 (gitignore)
│   └── character.txt        # 캐릭터 설정
└── assets/
    ├── models/              # RVC 모델 파일 (gitignore)
    │   ├── Gaon_200e_2200s.pth
    │   └── Gaon.index
    └── output/              # TTS 출력 파일
```

---

## 🐍 주요 파이썬 라이브러리
```
langchain
langgraph
langchain-ollama
langchain-chroma
langchain-community
chromadb
edge-tts
gradio-client
chzzkpy
websockets
pyaudio
sounddevice
soundfile
numpy
scipy
python-dotenv
```

---

## 🔑 환경변수 목록 (.env)
```
OLLAMA_THINK_MODEL=qwen2.5:3b
OLLAMA_ANSWER_MODEL=gemma4:26b
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://ollama.aikopo.net
VTUBER_NAME=가온
VTUBER_THINK_TEMP=0.1
VTUBER_ANSWER_TEMP=0.8
VTUBE_TOKEN=
TTS_VOICE=ko-KR-SunHiNeural
TTS_MODEL_NAME=Gaon_200e_2200s.pth
TTS_INDEX_NAME=Gaon.index
APPLIO_URL=http://127.0.0.1:6969
CHZZK_NID_AUT=
CHZZK_NID_SES=
CHZZK_CHANNEL_ID=
```

---

## 🎭 캐릭터 설정 (가온)
- **나이**: 22살
- **성격**: 친절한 츤데레
- **외모**: 보라색 포니테일, 보라색 눈동자, 하얀 피부, 보라색 후드티, 상어이빨
- **현재 아바타**: 픽셀 스타일 (추후 까칠한 눈매의 Live2D로 업그레이드 예정)
- **말투**: 반말, 츤데레 표현, 이모지 1~2개

---

## 🚀 실행 방법
**터미널 1 (Applio):**
```bash
cd ~/Applio
conda activate applio
python app.py
```

**터미널 2 (에이전트):**
```bash
cd ~/ai-vtuber
conda activate vtuber
python main.py
```

---

## 📝 gitignore 목록
```
.env
__pycache__/
.DS_Store
assets/models/
prompts/
docs/
```