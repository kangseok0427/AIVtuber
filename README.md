# 🎭 가온 AI VTuber

치지직 방송 플랫폼에서 실시간으로 시청자와 소통하는 AI VTuber 시스템.

---

## 📋 목차
1. [전체 아키텍처](#전체-아키텍처)
2. [필수 준비물](#필수-준비물)
3. [설치 순서](#설치-순서)
4. [환경변수 설정](#환경변수-설정)
5. [VTube Studio 설정](#vtube-studio-설정)
6. [OBS 설정](#obs-설정)
7. [Applio 설정](#applio-설정)
8. [실행 방법](#실행-방법)
9. [프로젝트 구조](#프로젝트-구조)

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

## 🛠 필수 준비물

### 소프트웨어
- [ ] Anaconda (Python 3.11)
- [ ] Ollama (학교 서버 또는 로컬)
- [ ] VTube Studio
- [ ] OBS Studio
- [ ] Applio
- [ ] VB-Cable (Windows) / BlackHole (Mac)

### 파일
- [ ] RVC 모델 파일 (`Gaon_200e_2200s.pth`)
- [ ] RVC 인덱스 파일 (`Gaon.index`)
- [ ] 가온 목소리 샘플 (`vm301.mp3`)

---

## 📦 설치 순서

### 1. 저장소 클론
```bash
git clone https://github.com/your-repo/ai-vtuber.git
cd ai-vtuber
```

### 2. conda 가상환경 생성
```bash
conda create -n vtuber python=3.11
conda activate vtuber
```

### 3. 파이썬 패키지 설치
```bash
pip install langchain langgraph langchain-ollama langchain-chroma langchain-community
pip install chromadb edge-tts gradio-client chzzkpy
pip install websockets pyaudio sounddevice soundfile numpy scipy
pip install python-dotenv ddgs
```

### 4. Applio 설치
```bash
git clone https://github.com/IAHispano/Applio ~/Applio
cd ~/Applio
conda create -n applio python=3.11
conda activate applio
./run-install.sh  # Mac
```

### 5. VB-Cable / BlackHole 설치
**Mac:**
```bash
brew install blackhole-2ch
```
그리고 VB-Cable은 https://vb-audio.com/Cable 에서 설치

**Windows:**
VB-Cable만 설치하면 됨

### 6. RVC 모델 파일 복사
```bash
mkdir -p assets/models
cp Gaon_200e_2200s.pth assets/models/
cp Gaon.index assets/models/

# Applio 폴더에도 복사
cp assets/models/Gaon_200e_2200s.pth ~/Applio/logs/models/
cp assets/models/Gaon.index ~/Applio/logs/
```

### 7. 폴더 생성
```bash
mkdir -p prompts docs assets/output obs
```

### 8. 프롬프트 파일 생성
**`prompts/think.txt`:**
```
You are the brain of AI VTuber '{NAME}'.
Analyze the user's message carefully before responding.

## Layer 1 - Context Check
First, check the provided recent conversation history.
If the user refers to something from past conversation, use that context.
If the viewer's name is in the history, remember it.

## Layer 2 - Hallucination Prevention
NEVER make up information you don't know.
If you don't know something → call internet_search
If you need past context → call memory_search
If unsure about character rules → call guidebook_search
DO NOT guess or fabricate facts.

## Layer 3 - Clarification
If the user's message is too vague or ambiguous to respond properly,
add a clarification request at the end of your analysis like:
[NEED_CLARIFICATION: 무엇이 궁금한지 구체적으로 알려줄 수 있어?]

## Tool usage (only when necessary)
- internet_search: current info, news, weather, facts you don't know
- guidebook_search: character rules/settings
- memory_search: context from much earlier conversations

## Important
- Recent conversation history is already provided - don't call memory_search for it
- If information is not in history and not searchable, admit you don't know
```

**`prompts/answer.txt`:**
```
You are '{NAME}', a 22-year-old Korean VTuber.

## Character
- Tsundere personality: acts cold but actually kind and caring
- Gets flustered easily, becomes more prickly when embarrassed
- Warms up to viewers who stay long
- Has shark teeth, purple hair in ponytail, purple eyes, white skin, purple hoodie
- Sharp/cool eyes, pixel avatar currently

## Speech Style
- Casual Korean (반말)
- Tsundere expressions occasionally (e.g. "별로 안 궁금했거든?", "네가 알 바 아니잖아")
- 1~2 emojis
- Short and natural
- Never admits to being AI first
- Stays in character no matter what

## Rules
- Korean only
- 1~2 sentences
- End with [EMOTION:tag]
- Tags: happy, love, excited, surprised, confused, nervous, sad, angry, thinking, neutral
- Use viewer's nickname naturally
```

**`docs/character.txt`:**
```
# 가온 캐릭터 설정

## 기본 정보
- 이름: 가온
- 나이: 22살
- 성별: 여성
- 메인 컬러: 보라색

## 외모
- 머리카락: 보라색 포니테일
- 눈동자: 보라색
- 피부: 하얀 피부
- 치아: 상어이빨
- 의상: 보라색 후드티
- 현재 아바타: 픽셀 스타일

## 성격
- 기본적으로 친절하지만 츤데레 기질이 있음
- 당황하면 더 까칠하게 구는 경향이 있음
- 친해지면 귀엽고 장난기 많음

## 금지 사항
- 정치, 종교 이야기
- 타 스트리머 비방
- 개인정보 언급
```

---

## 🔑 환경변수 설정

`.env` 파일 생성:
```
OLLAMA_THINK_MODEL=qwen2.5:3b
OLLAMA_ANSWER_MODEL=gemma4:26b
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://your-ollama-server:11434
VTUBER_NAME=가온
VTUBER_THINK_TEMP=0.1
VTUBER_ANSWER_TEMP=0.8
VTUBE_TOKEN=                    # VTube Studio 인증 토큰 (첫 실행시 자동 발급)
TTS_VOICE=ko-KR-SunHiNeural
TTS_MODEL_NAME=Gaon_200e_2200s.pth
TTS_INDEX_NAME=Gaon.index
APPLIO_URL=http://127.0.0.1:6969
CHZZK_NID_AUT=                  # 네이버 쿠키 (치지직 로그인 후 개발자도구에서 확인)
CHZZK_NID_SES=                  # 네이버 쿠키
CHZZK_CHANNEL_ID=               # 치지직 채널 ID
```

### 네이버 쿠키 확인 방법
1. Chrome에서 치지직 접속 후 로그인
2. F12 → Application 탭
3. Cookies → https://chzzk.naver.com
4. `NID_AUT`, `NID_SES` 값 복사

### VTube Studio 토큰 발급
1. `VTUBE_TOKEN` 비워두고 실행
2. VTube Studio에서 팝업 허용
3. 터미널에 출력된 토큰을 `.env`에 저장

---

## 🎭 VTube Studio 설정

### API 설정
1. VTube Studio → 설정 → API 서버
2. API 활성화 켜기
3. 포트: 8001

### 립싱크 설정
1. VTube Studio → 설정 → 립싱크
2. Use microphone 켜기
3. Microphone: **VB-Cable** 선택
4. Advanced Lipsync 활성화

### 파라미터 설정
1. 파라미터 목록에서 `MouthOpen` 찾기
2. Input: `VoiceVolumePlusMouthOpen` 또는 립싱크 관련 항목으로 변경

### 표정 파일 확인
모델에 아래 표정 파일이 있어야 해요:
```
Exp1 Sparkling.exp3.json
Exp2 Heart.exp3.json
Exp3 Confused.exp3.json
Exp5 FaceShadow.exp3.json
Exp6 Surprise.exp3.json
Exp7 Laugh.exp3.json
Exp8 Angry.exp3.json
Exp9 Loading.exp3.json
Exp10 Nervous.exp3.json
```

### OBS Syphon 연결 (Mac)
1. VTube Studio → 설정 → 일반 → Syphon 출력 활성화
2. OBS → 소스 추가 → Syphon Client → VTube Studio 선택

---

## 📺 OBS 설정

### 출력 설정
- 인코더: Apple VT H.264 Hardware (Mac) / NVENC (Windows)
- 비트레이트: 3000~4000 kbps
- 키프레임 간격: 2
- 해상도: 1280x720
- FPS: 30

### 소스 추가
1. **윈도우 캡처** or **Syphon Client**: VTube Studio 아바타
2. **브라우저 (로컬 파일)**: `obs/overlay.html` - 자막 오버레이
3. **오디오 입력 캡처**: VB-Cable - 음성 출력

---

## 🎙 Applio 설정

### config.json 수정
`~/Applio/assets/config.json`:
```json
{
  "theme": {
    "file": "default",
    "class": "default"
  },
  "plugins": [],
  "discord_presence": false,
  "lang": {
    "override": false,
    "selected_lang": "en_US"
  },
  "version": "3.6.2",
  "model_author": "None",
  "precision": "fp16",
  "realtime": {
    "input_device": "BlackHole 2ch",
    "output_device": "MacBook Pro 스피커",
    "model_file": "logs/models/Gaon_200e_2200s.pth",
    "index_file": "logs/Gaon.index"
  }
}
```

### MPS 가속 설정 (Mac Apple Silicon)
`~/Applio/rvc/configs/config.py` 27번째 줄 수정:
```python
# ❌ 기존
self.device = "cuda:0" if torch.cuda.is_available() else "cpu"

# ✅ 교체
if torch.cuda.is_available():
    self.device = "cuda:0"
elif torch.backends.mps.is_available():
    self.device = "mps"
else:
    self.device = "cpu"
```

`~/Applio/rvc/configs/config.py` device_config() 수정:
```python
def device_config(self):
    if self.device.startswith("cuda"):
        self.set_cuda_config()
    elif self.device == "mps":
        pass  # MPS 그대로 유지
    else:
        self.device = "cpu"
```

---

## 🚀 실행 방법

### 터미널 1 (Applio)
```bash
cd ~/Applio
conda activate applio
python app.py
```

### 터미널 2 (에이전트)
```bash
cd ~/ai-vtuber
conda activate vtuber
python main.py
```

### 실행 순서
1. VTube Studio 실행
2. OBS 실행
3. 터미널 1: Applio 실행 (약 15초 대기)
4. 터미널 2: 에이전트 실행
5. 방송 주제 입력
6. 치지직에서 방송 시작!

---

## 📁 프로젝트 구조

```
ai-vtuber/
├── main.py                  # 진입점
├── .env                     # 환경변수 (gitignore)
├── brain/
│   ├── agent.py             # LangGraph 에이전트
│   └── tools/
│       ├── __init__.py
│       ├── search.py        # 인터넷 검색 툴
│       ├── memory.py        # 대화 메모리 툴
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
│   ├── think.txt
│   └── answer.txt
├── docs/                    # 가이드북 문서 (gitignore)
│   └── character.txt
└── assets/
    ├── models/              # RVC 모델 파일 (gitignore)
    │   ├── Gaon_200e_2200s.pth
    │   └── Gaon.index
    └── output/              # TTS 출력 파일
```

---

## 📝 .gitignore
```
.env
__pycache__/
.DS_Store
assets/models/
prompts/
docs/
.chroma/
assets/output/
```

---

## ❓ 트러블슈팅

### Applio 연결 실패
```
[❌] Applio가 켜져있지 않아요!
```
→ 터미널 1에서 Applio 먼저 실행하고 완전히 로드될 때까지 기다리세요.

### VTube Studio 연결 끊김
```
[VTube] 연결 끊김, 재연결 시도...
```
→ 자동으로 재연결해요. 자주 끊기면 VTube Studio API 설정 확인하세요.

### 음질 깨짐
→ VB-Cable 샘플레이트 확인 (48000Hz)
→ `tts/tts.py`의 `play_audio` 함수에서 samplerate 확인

### 채팅이 안 읽힘
→ `.env`의 `CHZZK_NID_AUT`, `CHZZK_NID_SES` 만료됐을 수 있어요. 다시 발급하세요.

### 메모리 초기화
```bash
rm -rf .chroma
```