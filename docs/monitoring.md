**1. 프로젝트 개요**

1.1 배경 및 문제 정의

현대 연구 환경에서는 매일 수천 편의 논문이 arXiv, Semantic Scholar, PubMed 등에 업로드된다. 그러나 연구자 및 개발 조직은 다음과 같은 구조적 병목을 겪고 있다.

- 논문 인지 지연: 최신 논문이 등장해도 실무자가 인지하기까지 평균 수 주~수 개월이 소요됨
- 언어 장벽: 영문 논문이 대다수로, 국내 팀의 이해와 활용까지 추가적인 번역 비용 발생
- 연관성 파악 부재: 논문이 현재 진행 중인 사내 프로젝트·기획안과 어떻게 연결되는지 수동으로 분석해야 함
- 신뢰도 판단 어려움: 논문의 인용 수, 저널 신뢰도, 방법론 타당성 등을 개별적으로 검증해야 함

1.2 프로젝트 목표

본 프로젝트는 논문 발표 이벤트를 자동으로 감지하고, 분석·평가·요약까지 자율적으로 처리하는 AI Agent 파이프라인을 구축한다. 궁극적으로는 '논문 발표 → 사내 보고서 자동 생성'의 제로터치(Zero-Touch) 워크플로우를 실현한다.

### MVP 기능 설명
F-01 논문 모니터링 arXiv/Semantic Scholar,Hugging Face Papers 주기적 P0 Y 크롤링, 신규 논문 감지
F-02 이벤트 발행 Kafka 토픽에 new_paper_detected P0 Y 이벤트 발행

### 전체 흐름
시스템은 크게 6개 레이어로 구성된다. 각 레이어는 독립적으로 배포 및 스케일링 가능하며, Kafka를 중심으로 비동기 이벤트 기반으로 연결된다.

1. 외부 소스 (arXiv, Semantic Scholar) → 논문 모니터링 에이전트가 주기 크롤링
2. 신규 논문 감지 시 Kafka 토픽 new_paper_detected에 이벤트 발행

#### 영역 선택 기술 논의 필요

#### 인프라
- 현재 구현된 MSA 환경에서 Chroma와 mariadb 사용.
- AI Agent 특정 목표를 자율적으로 수행하는 LLM 기반 소프트웨어 컴포넌트
- Kafka 분산 이벤트 스트리밍 플랫폼. 서비스 간 비동기 메시지 전달에 사용

| **대분류** | **설명** | **해당 arXiv 태그 (예시)** |
| --- | --- | --- |
| **Language & Text** | 언어 모델, 번역, 텍스트 분석 | `cs.CL` (Computation and Language) |
| **Vision & Graphics** | 이미지, 비디오 인식, 3D 생성 | `cs.CV` (Computer Vision) |
| **Robotics & Control** | 물리적 하드웨어 제어, 자율 주행 | `cs.RO` (Robotics) |
| **ML Foundation** | 알고리즘 이론, 최적화, 통계 | `cs.LG`, `cs.AI`, `stat.ML` |
| **Multi-Agent & RL** | 에이전트 협업, 강화학습 전략 | `cs.MA`, `cs.AI` |
| **Ethics & Society** | 안전성, 편향성, 법적 문제 | `cs.CY` (Computers and Society) |

