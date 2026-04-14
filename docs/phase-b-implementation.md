# Phase B: 논문 평가 및 요약 파이프라인 구현 상세 (paper-service)

본 문서는 `paper-service`에서 구현된 논문 자동 평가, 요약 및 하이브리드 데이터 저장 파이프라인에 대한 상세 내용을 정리합니다.

---

## 1. 아키텍처 개요

`paper-service`는 `monitoring-service`(Phase A)가 Kafka를 통해 발행한 신규 논문 이벤트를 수신하여, AI 전문가 수준의 평가와 요약을 수행하고 결과를 RDB(MariaDB)와 VectorDB(ChromaDB)에 분산 저장합니다.

### 전체 데이터 흐름

```
monitoring-service
  ├── arXiv API 수집 → categories 태그 포함
  └── Kafka (new_papers_topic) 발행
         │
         ▼
paper-service (Kafka Consumer Thread)
  ├── 1. PDF 다운로드 & 파싱 (pdf_parser.py)
  ├── 2. AI Scientist 앙상블 평가 (evaluator.py)
  │       ├── score ≥ 6.0 → Accept
  │       └── score < 6.0 → Reject (처리 종료)
  ├── 3. 카테고리 분류 (classify_category)
  ├── 4. 마크다운 요약 생성 (summarizer.py)
  ├── 5. MariaDB 저장 → paper_summary 테이블
  ├── 6. ChromaDB 저장 → papers 컬렉션
  ├── 7. internal_docs 유사도 쿼리
  └── 8. MariaDB 저장 → paper_relate 테이블
```

---

## 2. 주요 구현 모듈

### 2.1. AI Scientist 방식의 고도화된 자동 리뷰어 (`evaluator.py`)

Sakana AI의 AI Scientist 논문(`ai-scientist.md` 참조)에서 제안한 자동 리뷰 아키텍처를 구현합니다.

| 구성 요소 | 구현 방식 | 세부 내용 |
|---|---|---|
| **앙상블 리뷰** | 3명의 독립 GPT-4o 리뷰어 | 각 리뷰어가 서로 다른 temperature로 초안 생성 |
| **자기 반성 루프** | 리뷰어당 2회 반복 | 초안을 스스로 재검토하여 낙관주의 편향 억제 |
| **Area Chair 합의** | 총 6단계(3×2) 후 메타 리뷰 | 최종 점수 및 Accept/Reject 결정 |
| **풀텍스트 분석** | PDF 원문 최대 15,000자 | 초록만으로 판단하지 않음 |
| **비판적 페르소나** | `reviewer_system_prompt_neg` | 결함 발견에 집중, 낙관 편향 배제 |

**평가 점수 기준 (NeurIPS 스타일)**

| 점수 | 의미 | is_relevant |
|---|---|---|
| 8~10 | Top 50% 이상의 우수 논문 | `True` |
| 6~7 | Borderline~Weak Accept | `True` |
| 4~5 | Weak Reject | `False` |
| 1~3 | Reject (심각한 결함) | `False` |

임계값: `final_score >= 6.0` → `is_relevant = True`

### 2.2. PDF 파싱 (`pdf_parser.py`)

- `requests`로 PDF URL 다운로드 → 임시 파일 저장 → `PyPDF2`로 페이지별 텍스트 추출
- `sanitize_text()`: null 바이트, 제어 문자 제거 및 연속 공백 정리
- 다운로드 실패 시 빈 문자열 반환 → abstract만으로 평가 fallback

### 2.3. Markdown 기반 요약 시스템 (`summarizer.py`)

프론트엔드 대시보드에서 즉시 렌더링 가능하도록 Markdown 포맷의 요약본을 생성합니다.

**출력 JSON 스키마:**
```json
{
  "paper_id": "string",
  "title": "string",
  "summary": "## Markdown 형식의 요약 본문",
  "keywords": ["keyword1", "keyword2"],
  "citations": [{"text": "논문 내 핵심 인용구"}]
}
```

### 2.4. 카테고리 분류 시스템 (`consumer.py` - `classify_category`)

arXiv 논문 태그를 프로젝트 대분류 체계로 자동 변환합니다.

**대분류 체계 및 arXiv 태그 매핑:**

| 대분류 | arXiv 태그 |
|---|---|
| **Language & Text** | `cs.CL` |
| **Vision & Graphics** | `cs.CV`, `cs.GR` |
| **Robotics & Control** | `cs.RO`, `cs.SY`, `eess.SY` |
| **ML Foundation** | `cs.LG`, `cs.AI`, `cs.NE`, `stat.ML` |
| **Multi-Agent & RL** | `cs.MA`, `cs.GT` |
| **Ethics & Society** | `cs.CY`, `cs.HC` |

**우선순위 규칙:** 논문이 복수 태그를 가질 경우 (예: `cs.CL` + `cs.LG`) 더 구체적인 대분류를 선택합니다.

```
Language & Text > Vision & Graphics > Robotics & Control
> Multi-Agent & RL > Ethics & Society > ML Foundation
```

태그가 없거나 매핑되지 않는 경우 `"ML Foundation"`을 기본값으로 사용합니다.

**데이터 흐름:**
```
monitoring-service: result.categories → Kafka 메시지 arxiv_categories 필드
paper-service: classify_category(arxiv_categories) → category 문자열
             → MariaDB paper_summary.category 저장
             → ChromaDB metadata.category + metadata.arxiv_categories 저장
```

### 2.5. 사내 문서 유사도 분석 및 순위 누적 (`consumer.py`)

ChromaDB의 `internal_docs` 컬렉션에서 논문 요약과 유사한 사내 문서 청크를 검색하여 관계를 도출합니다.

- 쿼리: `md_summary` 텍스트 기준, n_results=50
- **중복 병합 로직**: 같은 `doc_id`의 청크가 여러 개 검색될 경우 rank를 중복 부여하지 않고 `reason` 필드에 청크 내용을 누적(Append)
- 최대 rank 10까지만 `paper_relate` 저장

---

## 3. 하이브리드 데이터베이스 전략

### 3.1. MariaDB (RDB) - 프론트엔드 및 관계 저장소

**`paper_summary` 테이블:**

| 컬럼 | 타입 | 내용 |
|---|---|---|
| `paper_id` | VARCHAR(255) PK | arXiv ID 등 논문 고유 식별자 |
| `md_summary` | TEXT | Markdown 형식의 요약 본문 |
| `paper_url` | VARCHAR(1024) | 원본 논문 URL |
| `authors` | TEXT | JSON 배열 문자열 |
| `category` | VARCHAR(255) | 대분류 (예: "Language & Text") |

**`paper_relate` 테이블:**

| 컬럼 | 타입 | 내용 |
|---|---|---|
| `paper_id` | VARCHAR(255) PK/FK | paper_summary 참조 |
| `internal_doc_id` | VARCHAR(255) PK | 사내 문서 ID |
| `rank` | INTEGER | 유사도 순위 (1~10) |
| `reason` | TEXT | 매칭 사유 (Markdown, 청크 누적) |

### 3.2. ChromaDB (`papers` 컬렉션) - 시맨틱 검색 엔진

**저장 데이터:**
- `documents`: `summarize_paper()` 결과 전체를 JSON 문자열로 직렬화
- `metadatas`: 아래 필드 포함

| 메타데이터 키 | 내용 |
|---|---|
| `source_type` | `"paper"` |
| `document_type` | `"paper"` |
| `access_level` | `"public"` |
| `title` | 논문 제목 |
| `keyword` | 수집에 사용한 키워드 |
| `category` | 대분류 (예: `"ML Foundation"`) |
| `arxiv_categories` | 원본 태그 콤마 구분 (예: `"cs.LG,cs.AI"`) |
| `evaluation_score` | AI 평가 점수 (float) |
| `evaluation_review` | Area Chair 메타 리뷰 텍스트 |

**활용 목적:**
1. 의미 기반 논문 간 유사도 검색 (RAG)
2. 카테고리/점수 기준 필터링 검색
3. 추후 트렌드 분석, 논문 간 차이점 분석

---

## 4. Kafka Consumer 안정성 설정

AI 평가 파이프라인은 논문 1개당 약 30~40초가 소요됩니다. 기본 Kafka 설정(`max_poll_interval_ms=300,000ms`)으로는 배치 처리 중 Heartbeat 타임아웃이 발생하여 그룹에서 탈퇴 → 메시지 재처리 루프가 발생합니다.

**현재 적용 설정 (`consumer.py`):**

| 파라미터 | 설정값 | 이유 |
|---|---|---|
| `session_timeout_ms` | 30,000 | 브로커가 소비자 장애를 감지하는 시간 |
| `heartbeat_interval_ms` | 10,000 | session_timeout의 1/3 (권장값) |
| `max_poll_interval_ms` | 1,800,000 | 30분: 대용량 배치 AI 처리 여유 확보 |
| `request_timeout_ms` | 40,000 | session_timeout보다 반드시 큰 값 |
| `connections_max_idle_ms` | 60,000 | 유휴 연결 유지 시간 |

---

## 5. 인터페이스 및 테스트

### 5.1. 프론트엔드 API

**`GET /papers?limit=N`**

ChromaDB `papers` 컬렉션에서 최근 논문 리스트를 반환합니다.

```json
[
  {
    "paper_id": "arxiv:2404.12345",
    "metadata": {
      "title": "...",
      "category": "Language & Text",
      "arxiv_categories": "cs.CL,cs.LG",
      "evaluation_score": 7.5
    },
    "summary_data": {
      "summary": "## 요약 내용 (Markdown)",
      "keywords": ["LLM", "fine-tuning"]
    }
  }
]
```

**`POST /rules`** — 모니터링 규칙 등록

```json
{
  "rule_id": "rule-001",
  "keyword": "large language model",
  "source": "arxiv",
  "internal_doc_ids": []
}
```

### 5.2. 테스트

**로컬 단위 테스트 (`paper-service/test_pipeline.py`)**

Docker 없이 로컬에서 평가~ChromaDB 저장까지 전 과정을 검증합니다.
- 대상 논문: "Attention Is All You Need" (arxiv 1706.03762)
- 로컬 ChromaDB: `PersistentClient(path="./local_chroma_test_db")`
- 실행: `OPENAI_API_KEY='sk-...' python test_pipeline.py`

**E2E 통합 테스트 (`test_integration.py`)**

Docker 환경에서 monitoring-service(A) → paper-service(B) → MariaDB/ChromaDB 전 과정을 자동 검증합니다.

- 테스트 키워드: `"large language model"` (NeurIPS 기준 통과율이 높은 핵심 ML 주제)
- max_results: `3` (처리 시간 ~90초, API 비용 최적화)
- 대기 시간: 최대 10분 (논문 3개 × 40초 + 여유)
- 확인 항목: MariaDB `paper_summary`, `paper_relate` 적재 / ChromaDB API 응답

**실행 전 준비:**
```bash
rm data/reports/seen_papers.json   # 이전 수집 기록 초기화
docker compose up --build -d       # 최신 코드로 재빌드
python test_integration.py
```

---

## 6. 향후 개선 포인트

1. **비동기 처리**: Kafka offset을 수신 직후 커밋하고 AI 평가를 별도 태스크 큐(Celery 등)로 분리하면 Consumer 재조인 위험 완전 제거
2. **HuggingFace 논문 카테고리**: 현재 HF 소스는 `arxiv_categories`가 비어 기본값 `"ML Foundation"`으로 저장됨. arxiv_id 보유 시 arXiv API 재조회로 태그 보완 가능
3. **카테고리 기반 필터링 API**: `GET /papers?category=Language+%26+Text` 형태의 필터 엔드포인트 추가
4. **평가 결과 저장**: Reject된 논문도 점수와 사유를 별도 테이블에 기록하여 수집 품질 모니터링
