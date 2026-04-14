1. 크롤링 로직 (Filter-Logic): "1차 거름망"

이 단계는 에이전트 없이 빠르고 저렴한 코드로 구현합니다. 1시간마다 수백 건의 논문을 빠르게 쳐내는 역할.

역할: 정량적 메타데이터 기반 필터링

판단 기준:

- 소속: Author 소속에 특정 키워드(Google, Meta, OpenAI, Stanford 등) 포함 여부.
- 컨퍼런스: comments 필드에 주요 학회(NeurIPS, ICLR 등) 언급 여부.
- 화제성: Hugging Face Upvotes 수치가 기준값(예: 5개) 이상인 것.

| **정보 항목** | **arXiv API** | **Hugging Face API** | **비고** |
| --- | --- | --- | --- |
| **제목/초록** | ✅ 제공 (Full Text 아님) | ✅ 제공 | 기본 데이터 |
| **컨퍼런스** | ⚠️ `comments` 필드에 텍스트로 존재 | ❌ 거의 없음 | 사용자가 직접 입력한 거라 형식이 제각각 |
| **소속 (Affiliation)** | ❌ **기본 제공 안 함** | ⚠️ 일부 유저 프로필 연결 시 가능 | 가장 큰 병목 구간 |
| **화제성 (Upvotes)** | ❌ (인용 수도 실시간 아님) | ✅ `likes` 필드로 실시간 제공 | HF는 화제성 파악에 유리 |

**→ arXiv ID를 통해 Semantic Scholar API 호출로 저자의 소속, 인용수, 영향력 지표를 받아서 검토 필수**

1. 조사 에이전트: "2차 정밀 분석"

1차를 통과한 20~30건의 논문에 대해서만 LLM(에이전트)이 투입됩니다.

역할: 초록(Abstract)을 읽고 이론적 가치와 잠재적 파급력 점수화.

판단 기준:

- **독창성**: 기존 방법론의 단순 개선인가, 아니면 새로운 패러다임(Zero-shot, Scaling Law 등)을 제시하는가?
- **일반성**: 특정 좁은 도메인이 아니라 AI 전반에 영향을 미칠 이론인가?
- **관심도 예측**: 에이전트가 "이 논문은 1주일 내로 리서치 커뮤니티에서 크게 회자될 것인가?"를 판단.
- **기업 관련도**: SK AX 기준으로 영향도가 큰 논문인가?

결과: 최종 3~5건의 'High-Impact' 논문 선정 및  Kafka 각 이벤트 발행.

추천 아키텍처 흐름

Collector (Python Scheduler): 3시간마다 arXiv/HF 호출 (Max 1000개).

Metadata Filter (Logic): 상윤님이 정한 'Top-tier Lab' 리스트와 'Upvote' 기준으로 1차 필터링.

Semantic Filter: 저자, 인용수, 영향력 지표 받아서.

Impact Agent: 1차 통과된 논문들의 제목+초록을 읽고 Impact Score(0~100) 부여.

Kafka Producer: Score가 80점 이상인 논문들만 high_impact_paper_detected 토픽으로 발행.

상윤님을 위한 팁:

에이전트를 쓸 때 'Serper'나 'Google Search API'를 에이전트에게 쥐여주면 더 좋습니다. 논문 제목으로 구글링을 해서 벌써 블로그 포스팅이 올라왔는지, X(트위터)에서 언급이 되는지를 에이전트가 직접 확인하게 하면 '사람들의 관심'을 더 정확히 측정할 수 있거든요.