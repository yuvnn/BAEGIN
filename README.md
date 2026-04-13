# Paper Monitoring Platform Template

논문 모니터링, 논문 요약서 생성, 사내 문서 비교 보고서 생성을 위한 멀티서비스 템플릿입니다.

## Services

- `vue-project`: 사용자 UI (모니터링 결과 조회, 요약/비교 요청)
- `auth-server`: 인증 토큰 발급/검증
- `user-service`: 사용자/조직 프로필 관리
- `enroll-service`: 모니터링 대상 키워드/저널/사내 문서 등록 관리
- `pdf-service`: PDF/사내 문서를 파싱하고 Chroma(VectorDB)에 적재
- `monitoring-service`: 논문 수집, 요약 생성, 사내 문서와 비교 보고서 생성

## Core Data Flow

1. `enroll-service`에서 감시 키워드/관심 분야/비교 대상 사내 문서를 등록합니다.
2. `monitoring-service`가 스케줄 기반으로 신규 논문을 수집합니다.
3. `pdf-service`가 논문 PDF/사내기술 문서를 임베딩하여 Chroma에 저장합니다.
4. `monitoring-service`가 Chroma에서 유사 문서를 검색해 요약/비교 보고서를 생성합니다.
5. 생성 결과를 UI에서 조회하고 `data/reports`에 저장합니다.

## Quick Start

```bash
docker compose up --build -d
```

## Ports

- Vue: `15173`
- Auth: `18081`
- User: `18082`
- Enroll: `18083`
- PDF: `18084`
- Monitoring: `18085`
- Chroma: `18090`

## Next Implementation Priorities

1. 인증/인가 통합 (JWT + RBAC)
2. 실제 논문 수집 커넥터 (arXiv, Crossref, PubMed, Semantic Scholar)
3. 사내 문서 보안 정책 반영 (암호화, 접근권한, 감사로그)
4. 비교 품질 개선 (RAG prompt, scoring, citation)
5. 운영 관측성 추가 (Prometheus + Grafana + alerting)
