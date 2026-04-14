export const CL = [
  { name: 'Language & Text',    color: '#6ea8fe', glow: 'rgba(110,168,254,0.28)', cx: 0.08,  cy: -0.22, cz: 0.05,  r: 0.19 },
  { name: 'ML Foundation',      color: '#4dd9ac', glow: 'rgba(77,217,172,0.24)',  cx: -0.05, cy: 0.1,   cz: -0.18, r: 0.21 },
  { name: 'Robotics & Control', color: '#f87171', glow: 'rgba(248,113,113,0.26)', cx: 0.22,  cy: 0.14,  cz: 0.12,  r: 0.14 },
  { name: 'Vision & Graphics',  color: '#c084fc', glow: 'rgba(192,132,252,0.24)', cx: -0.2,  cy: -0.08, cz: 0.2,   r: 0.17 },
  { name: 'Ethics & Society',   color: '#fbbf24', glow: 'rgba(251,191,36,0.24)',  cx: 0.18,  cy: -0.05, cz: -0.2,  r: 0.15 },
  { name: 'Multi-Agent & RL',   color: '#67e8f9', glow: 'rgba(103,232,249,0.22)', cx: -0.1,  cy: 0.25,  cz: 0.1,   r: 0.12 },
]

export const PP = [
  { title: 'Scaling Laws for Neural Language Models in Multilingual Settings',  short: 'Scaling Laws for Neural LMs',      cl: 0, score: 98, cite: 312, year: 2025, venue: 'arXiv',   auth: 'Kaplan J., McCandlish S., Henighan T. et al.', abs: '다국어 환경에서 언어 모델의 스케일링 법칙을 체계적으로 분석한 연구. 파라미터 수, 데이터 크기, 컴퓨팅 예산의 관계를 정량적으로 규명하며, 최적의 모델 크기 예측 공식을 제시한다.', rel: [1,3,4] },
  { title: 'GraphRAG: Knowledge Graph-Augmented Retrieval for Complex QA',      short: 'GraphRAG: KG-Augmented Retrieval', cl: 0, score: 91, cite: 187, year: 2025, venue: 'IEEE',    auth: 'Edge D., Trinh H., Cheng N. et al.',           abs: '지식 그래프를 활용하여 RAG 시스템의 복잡한 질의응답 성능을 향상시키는 방법론. 엔티티 관계 추론을 통해 단순 벡터 검색의 한계를 극복한다.', rel: [0,4,6] },
  { title: 'Anomaly Detection in Time-Series via Diffusion Models',             short: 'Anomaly Detection via Diffusion',  cl: 2, score: 87, cite: 143, year: 2025, venue: 'NeurIPS', auth: 'Park S., Kim J., Lee H. et al.',                abs: '확산 모델을 시계열 이상 탐지에 적용한 연구. 재구성 오차 기반의 이상 점수를 정의하고, 다양한 산업 데이터셋에서 SOTA 성능을 달성한다.', rel: [3,5,6] },
  { title: 'Efficient Fine-tuning of LLMs with LoRA Variants',                  short: 'Efficient Fine-tuning: LoRA Variants', cl: 1, score: 73, cite: 98, year: 2024, venue: 'ICML', auth: 'Hu E., Shen Y., Wallis P. et al.',               abs: 'LoRA의 변형 기법들을 체계적으로 비교 분석한 연구. AdaLoRA, QLoRA 등 다양한 변형의 효율성과 성능 트레이드오프를 실험적으로 규명한다.', rel: [0,1,4] },
  { title: 'Multi-Agent Debate for Factual Consistency in Generation',          short: 'Multi-Agent Debate',               cl: 5, score: 89, cite: 201, year: 2025, venue: 'ACL',     auth: 'Du Y., Li S., Torralba A. et al.',             abs: '여러 LLM 에이전트가 토론을 통해 사실 일관성을 높이는 프레임워크. 단일 모델 대비 환각 발생률을 40% 감소시키는 결과를 보인다.', rel: [0,1,3] },
  { title: 'Vision-Language Alignment without Human Annotations',               short: 'Vision-Language Alignment',        cl: 3, score: 68, cite: 76,  year: 2024, venue: 'CVPR',    auth: 'Radford A., Kim J., Hallacy C. et al.',        abs: '인간 레이블 없이 웹 크롤링 데이터만으로 비전-언어 정렬을 달성하는 방법론. 자기지도 학습 목표 함수를 통해 멀티모달 표현 학습을 수행한다.', rel: [2,3,6] },
  { title: 'Federated Learning under Non-IID Data Distribution',                short: 'Federated Learning Non-IID',       cl: 4, score: 52, cite: 44,  year: 2024, venue: 'AAAI',    auth: 'Li T., Sahu A., Zaheer M. et al.',             abs: '비독립동일분포(Non-IID) 데이터 환경에서 연합 학습의 수렴 문제를 다룬 연구. FedProx 알고리즘을 통해 이질적인 클라이언트 데이터에서의 학습 안정성을 개선한다.', rel: [1,2,5] },
]
