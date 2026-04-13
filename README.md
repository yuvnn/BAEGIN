# Paper Monitoring Platform Template

논문 모니터링, 논문 요약서 생성, 사내 문서 비교 보고서 생성을 위한 멀티서비스 템플릿입니다.

## Services

- `vue-project`: 사용자 UI (모니터링 결과 조회, 요약/비교 요청)
- `auth-server`(Spring Boot): 인증 토큰 발급/검증
- `user-service`: 사용자/조직 프로필 관리
- `paper-service`: 논문 평가 및 요약, 등록 관리, 벡터DB 적재, 사내 문서 유사도 평가
- `comparepdf-service`: 사내 문서와 논문 비교 보고서 생성, Chroma(VectorDB) 적재
- `monitoring-service`: 키워드/저널 기준 논문 수집

## Core Data Flow

1. `monitoring-service`가 키워드/저널 기준으로 신규 논문을 수집합니다.
2. `paper-service`가 논문 평가/요약, 등록 관리, 벡터DB 적재, 사내 문서 유사도 평가를 수행합니다.
3. `comparepdf-service`가 사내 문서와 논문을 비교하여 비교 보고서를 생성하고 Chroma에 적재합니다.
4. 생성 결과를 서비스 API를 통해 조회할 수 있습니다.
5. 생성 결과를 UI에서 조회하고 `data/reports`에 저장합니다.

## Quick Start

```bash
docker compose up --build -d
```

프론트엔드는 Nginx가 정적 파일을 서빙하며, `/api/*` 요청은 내부적으로 `monitoring-service`로 프록시됩니다.

## Ports

- Vue: `15173`
- Auth: `18081`
- User: `18082`
- Paper: `18083`
- PDF: `18084`
- Monitoring: `18085`
- Chroma: `18090`

## Service Check Links

### Frontend

- Vue UI: http://localhost:15173

### Backend API Docs (Swagger)

- Auth Docs: http://localhost:18081/docs
- User Docs: http://localhost:18082/docs
- Paper Docs: http://localhost:18083/docs
- PDF Docs: http://localhost:18084/docs
- Monitoring Docs: http://localhost:18085/docs

### Health Check

- Auth Health: http://localhost:18081/health
- User Health: http://localhost:18082/health
- Paper Health: http://localhost:18083/health
- PDF Health: http://localhost:18084/health
- Monitoring Health: http://localhost:18085/health

### Chroma

- Chroma Endpoint: http://localhost:18090

## Runtime Verification Commands

```bash
docker compose ps
docker compose logs -f monitoring-service
curl http://localhost:18085/health
```

## Next Implementation Priorities

1. 인증/인가 통합 (JWT + RBAC)
2. 실제 논문 수집 커넥터 (arXiv, Crossref, PubMed, Semantic Scholar)
3. 사내 문서 보안 정책 반영 (암호화, 접근권한, 감사로그)
4. 비교 품질 개선 (RAG prompt, scoring, citation)
5. 운영 관측성 추가 (Prometheus + Grafana + alerting)
