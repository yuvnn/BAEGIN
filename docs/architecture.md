# Architecture Overview

## Pattern

- Frontend + Domain Microservices + Shared VectorDB(Chroma)
- API 중심 통신(REST), 추후 이벤트 기반으로 확장 가능

## Domain Responsibilities

- Auth: 사용자 인증, 토큰 발급
- User: 사용자 및 조직 정보
- paper-service: 논문 평가 및 요약, 등록 관리, 벡터DB 적재, 사내 문서 유사도 평가
- internal-service: 사내 문서와 논문 비교 보고서 생성, Chroma(VectorDB) 적재
- Monitoring-service: 키워드/저널 기준 논문 수집

## VectorDB Strategy

- Collection 분리
  - `papers`
  - `internal_docs`
- metadata 예시
  - source_type: paper/internal
  - title, authors, published_at, topic, department
  - document_type: paper/internal/docx/planning
  - access_level: public/internal/restricted

## Processing Flow

1. `monitoring-service`가 외부 논문 API를 폴링하여 신규 논문을 수집
2. `paper-service`가 수집 논문 평가/요약, 등록 관리, 벡터DB 적재, 사내 문서 유사도 평가 수행
3. `internal-service`가 사내 문서와 논문을 비교하고 비교 보고서를 생성
4. 생성 결과를 Chroma 및 결과 저장소(JSON/TXT)로 적재하고 UI에 제공
