# BAEGIN — Paper Monitoring Platform

논문 자동 수집·요약, 사내 문서 비교 보고서 생성을 위한 마이크로서비스 플랫폼입니다.

---

## 실행 방법

### 1. 환경 변수 준비

프로젝트 루트의 `.env` 파일에 아래 값을 설정합니다.

```env
# JWT 서명 키 (32자 이상)
JWT_SECRET=your-secret-key-at-least-32-characters

# LLM API
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Slack 알림 (선택)
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C...

# Semantic Scholar API (선택 — 없으면 rate limit 적용)
SEMANTIC_SCHOLAR_API_KEY=...
```

### 2. 실행

```bash
# 전체 서비스 빌드 및 기동
docker compose up --build -d

# 로그 확인
docker compose logs -f

# 종료
docker compose down
```

### 3. 기동 확인

서비스가 모두 뜨는 데 약 90초가 소요됩니다 (Eureka 헬스체크 대기).

| 확인 항목 | URL |
|-----------|-----|
| **프론트엔드** | http://localhost:15173 |
| **Eureka 대시보드** (서비스 등록 현황) | http://localhost:18761 |
| **API Gateway** | http://localhost:18080 |
| Auth Swagger | http://localhost:18081/swagger-ui/index.html |
| User Swagger | http://localhost:18082/docs |
| Paper Swagger | http://localhost:18083/docs |
| Internal Swagger | http://localhost:18084/docs |
| Monitoring Swagger | http://localhost:18085/docs |
| Chatbot Swagger | http://localhost:18086/docs |
| ChromaDB | http://localhost:18090 |

```bash
# 헬스체크 빠른 확인
docker compose ps
curl http://localhost:18082/health
curl http://localhost:18083/health
curl http://localhost:18085/health
```

### 4. 사내 문서 등록

비교 보고서 기능을 사용하려면 PDF 파일을 `data/internal_docs/` 디렉터리에 넣고 서비스를 기동합니다.

```bash
mkdir -p data/internal_docs
cp your-document.pdf data/internal_docs/
docker compose up --build -d
```

---

## 전체 아키텍처

```
Browser
  │
  └─ Nginx (vue-project:80)
       ├─ /api/*        → api-gateway:8080  (Spring Cloud Gateway)
       │                      │
       │          ┌───────────┼───────────────┐
       │          ▼           ▼               ▼
       │     auth-server  user-service   paper-service  monitoring-service
       │     (Spring Boot) (FastAPI)     (FastAPI)      (FastAPI)
       │
       └─ /internal-api/* → internal-service:8000 (FastAPI, direct)
```

### 서비스 디스커버리 (Spring Cloud Eureka)

```
eureka-server (8761)
  ├── api-gateway       등록 O
  ├── auth-server       등록 O
  ├── user-service      등록 O
  ├── paper-service     등록 O
  ├── monitoring-service 등록 O
  ├── internal-service  등록 X (직접 호출)
  └── chatbot-service   등록 X (직접 호출)
```

Gateway는 `lb://서비스명` 방식으로 Eureka를 통해 부하분산합니다.

### 메시지 흐름 (Kafka)

```
monitoring-service
  └─ [Kafka] new_papers_topic ──→ paper-service (consumer)
```

monitoring-service가 수집한 논문을 Kafka로 발행하면, paper-service가 소비해 MariaDB + ChromaDB에 저장합니다.

### 서비스간 HTTP 호출

```
monitoring-service ──→ internal-service  /ingest/paper   (논문 텍스트 적재)
monitoring-service ──→ paper-service     /papers/{id}    (논문 상세 조회, 간접)
```

---

## 서비스 구조

```
BAEGIN/
├── docker-compose.yml
├── .env                        # 환경 변수 (gitignore)
├── data/
│   ├── internal_docs/          # 사내 문서 PDF 마운트 경로
│   ├── reports/                # 생성된 보고서 저장
│   ├── chroma/                 # ChromaDB 영속 데이터
│   └── kafka/                  # Kafka 로그 데이터
│
├── eureka-server/              # [Spring Boot] 서비스 레지스트리 (port 8761)
├── api-gateway/                # [Spring Boot] 라우팅 + JWT 검증 (port 8080)
├── auth-server/                # [Spring Boot] 로그인/회원가입/OTP (port 8080→18081)
│
├── user-service/               # [FastAPI] 사용자 프로필·키워드 관리 (port 8000→18082)
├── paper-service/              # [FastAPI] 논문 평가·요약·벡터DB 적재 (port 8000→18083)
├── internal-service/           # [FastAPI] 사내 문서 비교 보고서 생성 (port 8000→18084)
├── monitoring-service/         # [FastAPI] 논문 수집·필터링·스코어링 (port 8000→18085)
├── chatbot-service/            # [FastAPI] 논문 추천 챗봇 (port 8000→18086)
│
└── vue-project/                # [Vue 3 + Nginx] 프론트엔드 (port 80→15173)
```

### 포트 정리

| 서비스 | 컨테이너 포트 | 호스트 포트 |
|--------|:---:|:---:|
| eureka-server | 8761 | 18761 |
| api-gateway | 8080 | 18080 |
| auth-server | 8080 | 18081 |
| user-service | 8000 | 18082 |
| paper-service | 8000 | 18083 |
| internal-service | 8000 | 18084 |
| monitoring-service | 8000 | 18085 |
| chatbot-service | 8000 | 18086 |
| chromadb | 8000 | 18090 |
| mariadb | 3306 | 3306 |
| kafka | 9092 | 19092 |
| vue-project (nginx) | 80 | 15173 |

---

## 핵심 데이터 흐름

1. `monitoring-service`가 arXiv 등에서 논문을 수집하고 임팩트 스코어 기반으로 필터링합니다.
2. 통과한 논문을 Kafka(`new_papers_topic`)로 발행하고, `internal-service`에 텍스트 적재를 요청합니다.
3. `paper-service`가 Kafka 메시지를 소비해 논문을 MariaDB·ChromaDB에 저장합니다.
4. 사용자가 프론트엔드에서 논문 요약 또는 사내 문서 비교 보고서를 요청합니다.
5. `internal-service`가 ChromaDB RAG 기반으로 비교 보고서를 스트리밍으로 응답합니다.

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| 서비스 디스커버리 | Spring Cloud Netflix Eureka |
| API Gateway | Spring Cloud Gateway (WebFlux) |
| 인증 | JWT (JJWT), Spring Security OAuth2 Resource Server |
| 백엔드 (Java) | Spring Boot 3.4.5, Spring Cloud 2024.0.0 |
| 백엔드 (Python) | FastAPI, SQLAlchemy, py-eureka-client |
| 프론트엔드 | Vue 3, Nginx |
| 벡터DB | ChromaDB |
| 관계형DB | MariaDB 10.11 |
| 메시지 큐 | Apache Kafka (KRaft mode) |
| LLM | OpenAI / Anthropic Claude |
