# Architecture Overview

## Pattern

- Frontend + Domain Microservices + Shared VectorDB(Chroma)
- API 중심 통신(REST), 추후 이벤트 기반으로 확장 가능

## Domain Responsibilities

- Auth: 사용자 인증, 토큰 발급
- User: 사용자 및 조직 정보
- Enroll: 모니터링 정책/관심키워드/비교 기준 문서 등록
- PDF: 문서 파싱, 청크 분할, 임베딩, Chroma 적재
- Monitoring: 논문 수집, 요약 생성, 비교 분석 보고서 생성

## VectorDB Strategy

- Collection 분리
  - `papers`
  - `internal_docs`
- metadata 예시
  - source_type: paper/internal
  - title, authors, published_at, topic, department
  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - access  - DF, DOCX, 기획서) 업로드
2. `pdf-service`가 텍스트를 추출하고 청크로 분할
3. 임베딩 생성 후 Chroma `internal_docs`에 적재
4. `monitoring-service`가 외부 논문 API를 폴링하여 신규 논문 조회
5. 논문 초록/본문을 `papers` 컬렉션에 적재
6. 비교 요청 시:
   - 논문 벡터 검색
   - 사내 문서 벡터 검색
   - 유사도/키워드/근거문장 기반 비교 보고서 생성
7. 결과를 JSON/TXT로 저장 및 UI 제공
