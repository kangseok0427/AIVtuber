# 🛠️ brain/tools 코드 문서

> AI VTuber 프로젝트 — `brain/tools` 폴더 전체 코드 분석  
> 작성 기준: Python 3.11 / LangChain / LangGraph / Ollama (nomic-embed-text)

---

## 📁 폴더 구조

```
brain/
└── tools/
    ├── __init__.py       # 툴 모아서 export
    ├── search.py         # 인터넷 서치 툴
    ├── guidebook.py      # 가이드북 탐색 툴
    └── memory.py         # 대화 맥락 툴
```

---

## 📖 용어 정리

| 용어 | 설명 |
|------|------|
| **데코레이터** | 함수 위에 `@tool` 붙이면 일반 함수를 LangChain 툴 객체로 자동 변환 |
| **클로저** | 내부 함수가 외부 함수의 변수를 기억하는 것. `internet_search`가 `max_results`를 기억하는 방식 |
| **독스트링(docstring)** | `"""설명"""` 형태의 문자열. 에이전트가 읽고 언제 이 툴을 쓸지 판단하는 툴 설명서 |
| **임베딩** | 텍스트를 숫자 벡터로 변환하는 것. `"하루"` → `[0.12, 0.84, ...]` |
| **청크(chunk)** | 긴 문서를 일정 크기로 잘라낸 조각 |
| **코사인 유사도** | 두 벡터 간 각도로 유사도를 측정. 각도가 작을수록 유사 |
| **컬렉션** | ChromaDB 안에서 데이터를 구분하는 그룹 이름 |
| **타입힌트** | `query: str`, `-> str` 처럼 변수/반환값의 타입을 명시하는 것 |
| **`self`** | 클래스 메서드에서 객체 자신을 가리키는 참조값 |
| **`__init__`** | 클래스로 객체 만들 때 자동으로 실행되는 초기화 함수 |
| **`_메서드`** | 앞에 `_` 붙이면 내부에서만 쓰는 메서드라는 관례적 표시 |
| **제너레이터** | 값을 한 번에 다 만들지 않고 필요할 때마다 하나씩 만드는 객체. `list()`로 변환 필요 |

---

## 📄 search.py

### 역할
DuckDuckGo로 인터넷을 실시간 검색해서 결과를 에이전트에게 반환

### import 설명

```python
from langchain.tools import tool
```
- `tool` 데코레이터를 가져옴
- `@tool` 붙이면 일반 함수 → LangChain 툴 객체로 자동 변환

```python
from duckduckgo_search import DDGS
```
- DuckDuckGo 검색 라이브러리의 핵심 클래스
- `DDGS` = DuckDuckGo Search. 검색 요청을 보내는 객체

---

### 클래스 구조

```python
class SearchTool:
```
데이터(변수)와 기능(함수)을 하나로 묶은 틀

---

### `__init__` 메서드

```python
def __init__(self, max_results: int = 3):
```

| 인자 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `self` | — | — | 객체 자신을 가리키는 참조값. 항상 첫 번째 인자 |
| `max_results` | `int` | `3` | 검색 결과 최대 개수 |

```python
self.max_results = max_results
```
- 인자로 받은 값을 객체 변수로 저장
- `self.max_results`로 저장해야 다른 메서드에서도 꺼내 쓸 수 있음

---

### `build` 메서드

```python
def build(self):
```
- 툴 객체를 만들어서 반환하는 메서드
- `__init__`에서 바로 안 만드는 이유 → 툴은 에이전트에 등록할 때만 필요하므로 필요한 시점에 생성

```python
max_results = self.max_results
```
- `self.max_results`를 지역변수로 복사
- 이유: `@tool` 함수 안에서 `self` 직접 참조 시 클로저 문제 방지

```python
@tool
def internet_search(query: str) -> str:
    """인터넷에서 최신 정보를 검색할 때 사용. 시청자가 모르는 정보를 물어볼 때 호출."""
```

| 인자 | 타입 | 설명 |
|------|------|------|
| `query` | `str` | 에이전트가 넘겨주는 검색어 |

> ⚠️ 독스트링이 에이전트의 툴 선택 기준. 설명이 명확할수록 에이전트가 올바르게 호출

```python
with DDGS() as ddgs:
    results = list(ddgs.text(query, max_results=max_results))
```

| 코드 | 설명 |
|------|------|
| `with DDGS() as ddgs` | `with`문으로 생성. 블록 끝나면 자동으로 연결 종료 |
| `ddgs.text()` | DuckDuckGo 텍스트 검색 실행 |
| `list()` | 검색 결과가 제너레이터로 오므로 리스트로 변환 |

```python
return "\n".join(
    f"- {r['title']}: {r['body']}" for r in results
)
```

| 코드 | 설명 |
|------|------|
| `r['title']` | 검색 결과의 제목 |
| `r['body']` | 검색 결과의 본문 |
| `"\n".join(...)` | 각 결과를 줄바꿈으로 연결해서 하나의 문자열로 반환 |

```python
return internet_search
```
- 완성된 툴 함수 반환
- `SearchTool().build()` 호출 시 사용 가능한 툴 객체가 나옴

---

## 📄 guidebook.py

### 역할
`docs/` 폴더의 가이드북 문서를 읽어서 ChromaDB에 저장하고, 유사도 검색으로 관련 내용을 반환

### import 설명

```python
from langchain_core.documents import Document
```
- LangChain 표준 문서 객체
- `page_content`(내용) + `metadata`(부가정보)를 담는 그릇

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
```
- 긴 문서를 청크로 잘라주는 클래스
- Recursive = 문단 → 문장 → 단어 순서로 재귀적으로 분할해서 자연스럽게 나눔

```python
from langchain_community.document_loaders import DirectoryLoader, TextLoader
```

| 클래스 | 설명 |
|--------|------|
| `DirectoryLoader` | 폴더 전체의 파일을 읽어오는 로더 |
| `TextLoader` | 개별 텍스트 파일을 읽는 로더 |

> `DirectoryLoader`가 폴더를 훑으면서 각 파일을 `TextLoader`에게 맡김

---

### `__init__` 메서드

```python
def __init__(self, docs_path: str = "docs/", collection: str = "guidebook"):
```

| 인자 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `docs_path` | `str` | `"docs/"` | 가이드북 문서가 있는 폴더 경로 |
| `collection` | `str` | `"guidebook"` | ChromaDB 안에서 데이터를 구분하는 컬렉션 이름 |

```python
self.embeddings = OllamaEmbeddings(
    model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
)
```

| 인자 | 설명 |
|------|------|
| `model` | `.env`에서 임베딩 모델 이름 읽기. 없으면 `"nomic-embed-text"` 사용 |
| `base_url` | Ollama 서버 주소. 없으면 로컬 기본값 사용 |

> 임베딩 모델이 문서와 검색어를 같은 벡터 공간에 표현해서 유사도 비교를 가능하게 함

```python
self.db = self._load_or_create()
```
- `_load_or_create()` 호출 결과를 `self.db`에 저장
- DB가 있으면 로드, 없으면 새로 생성

---

### `_load_or_create` 메서드

```python
def _load_or_create(self) -> Chroma:
```
- 반환 타입이 `Chroma` 객체
- `_` 접두사 = 내부에서만 쓰는 메서드

```python
if os.path.exists(f".chroma/{self.collection}"):
    return Chroma(
        collection_name=self.collection,
        embedding_function=self.embeddings,
        persist_directory=".chroma"
    )
```
- `.chroma/guidebook` 폴더가 이미 있으면 기존 DB 그대로 로드
- 매번 임베딩 재생성하지 않아도 되므로 속도 절약

```python
loader = DirectoryLoader(self.docs_path, loader_cls=TextLoader)
docs = loader.load()
```

| 변수 | 설명 |
|------|------|
| `loader` | 폴더 읽기 준비 객체 |
| `docs` | `Document` 객체들의 리스트. 각각 `page_content`에 파일 내용 담김 |

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50
)
chunks = splitter.split_documents(docs)
```

| 인자 | 설명 |
|------|------|
| `chunk_size=500` | 한 청크의 최대 글자 수 |
| `chunk_overlap=50` | 청크 간 겹치는 글자 수. 문맥이 잘리지 않게 앞뒤로 50자씩 겹침 |
| `chunks` | 잘린 `Document` 객체들의 리스트 |

```python
return Chroma.from_documents(
    documents=chunks,
    embedding=self.embeddings,
    collection_name=self.collection,
    persist_directory=".chroma"
)
```
- `chunks`를 임베딩해서 ChromaDB에 저장하고 DB 객체 반환
- `from_documents()` = 문서 리스트를 받아서 임베딩 후 DB 생성하는 클래스 메서드

---

### `build` 메서드

```python
results = db.similarity_search(query, k=3)
```

| 인자 | 설명 |
|------|------|
| `query` | 에이전트가 넘겨주는 검색어. 임베딩 후 DB와 유사도 비교 |
| `k=3` | 가장 유사한 문서 3개 반환 |

> 유사도는 코사인 유사도로 계산. 벡터 간 각도가 작을수록 유사

```python
return "\n".join(
    f"- {doc.page_content}" for doc in results
)
```
- `doc.page_content` = 각 청크의 실제 텍스트 내용
- 검색된 3개 청크를 줄바꿈으로 연결해서 반환

---

## 📄 memory.py

### 역할
대화 한 턴씩 ChromaDB에 저장하고, 과거 대화에서 유사한 맥락을 검색해서 반환

> `guidebook.py`와 구조가 거의 동일. **다른 부분만** 설명

---

### `__init__` 메서드

```python
def __init__(self, collection: str = "memory"):
```
- `docs_path`가 없음
- 파일을 읽는 게 아니라 **대화를 직접 저장**하는 구조이므로 불필요

```python
self.db = Chroma(
    collection_name=self.collection,
    embedding_function=self.embeddings,
    persist_directory=".chroma"
)
```
- `from_documents()` 아닌 `Chroma()` 직접 생성
- 처음엔 **빈 DB로 시작**하고 대화하면서 데이터가 쌓임

---

### `save` 메서드

```python
def save(self, user_input: str, answer: str):
```

| 인자 | 타입 | 설명 |
|------|------|------|
| `user_input` | `str` | 시청자가 입력한 채팅 텍스트 |
| `answer` | `str` | VTuber가 생성한 답변 텍스트 |

```python
self.db.add_documents([
    Document(
        page_content=f"시청자: {user_input}\n하루: {answer}",
        metadata={"timestamp": datetime.now().isoformat()}
    )
])
```

| 코드 | 설명 |
|------|------|
| `page_content` | 대화 한 턴을 `"시청자: ...\n하루: ..."` 형태로 저장 |
| `metadata` | 언제 나눈 대화인지 시간 정보도 함께 저장 |
| `datetime.now().isoformat()` | `"2025-04-21T14:30:00"` 형식의 현재 시간 |

> 에이전트가 답변 생성 후 `memory.save(input, answer)` 호출해서 대화를 기록

---

### `build` 메서드

```python
return "\n".join(
    f"- [{r.metadata.get('timestamp', '')}] {r.page_content}"
    for r in results
)
```

| 코드 | 설명 |
|------|------|
| `r.metadata.get('timestamp', '')` | metadata에서 timestamp 꺼내고 없으면 빈 문자열 |
| `r.page_content` | 저장된 대화 내용 |

> 과거 대화를 시간 정보와 함께 에이전트에게 돌려줌

---

## 🔄 전체 데이터 흐름

```
SearchTool().build()
    └─ max_results=3 저장
    └─ build() 호출 시 internet_search 툴 반환
          └─ 에이전트가 query 넘겨줌
          └─ DDGS로 검색 → 결과 문자열 반환

GuidebookTool().build()
    └─ docs/ 폴더 읽기 → 500자씩 청크 분할
    └─ nomic으로 임베딩 → ChromaDB 저장
    └─ build() 호출 시 guidebook_search 툴 반환
          └─ 에이전트가 query 넘겨줌
          └─ 유사도 검색 → 관련 청크 반환

MemoryTool()
    └─ 빈 ChromaDB로 시작
    └─ save() → 대화 기록 저장
    └─ build() 호출 시 memory_search 툴 반환
          └─ 에이전트가 query 넘겨줌
          └─ 과거 대화에서 유사한 것 반환
```

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

---

## 📦 설치 패키지 전체

```bash
pip install \
  langchain \
  langchain-core \
  langchain-community \
  langchain-ollama \
  langchain-chroma \
  langchain-text-splitters \
  langgraph \
  chromadb \
  duckduckgo-search \
  python-dotenv \
  unstructured
```
