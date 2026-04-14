export const PAPERS = [
  {
    id: 1, title: 'Scaling Laws for Neural Language Models',
    authors: 'J. Kaplan, S. McCandlish, T. Henighan et al.',
    date: '2024-03-15', views: 1243,
    tags: ['NLP', 'LLM', 'Scaling'], cat: 'Language & Text',
    abs: 'We study empirical scaling laws for language model performance on the cross-entropy loss. The loss scales as a power-law with model size, dataset size, and the amount of compute used for training, with some trends spanning more than seven orders of magnitude.',
    orig: `1. Introduction\n\nLanguage modeling is a powerful benchmark task for deep learning. We study the scaling behavior of language model performance, examining how loss depends on model size N, dataset size D, and compute C.\n\nWe find that language model performance improves smoothly as we scale up model size, data, and compute:\n\n  L(N) ~ N^{-0.076}\n  L(D) ~ D^{-0.095}\n  L(C) ~ C^{-0.057}\n\n2. Methods\n\nWe train transformer language models ranging from 768 to 1.5 billion non-embedding parameters on the WebText2 dataset.\n\n3. Key Findings\n\n• Performance depends strongly on scale, weakly on model shape\n• Smooth power laws hold across 7 orders of magnitude\n• Large models are more sample-efficient than small models\n• Optimal compute allocation follows a specific ratio of model size to dataset size`,
    summ: `**핵심 발견:**\n• 모델 크기, 데이터, 컴퓨팅 자원 모두 성능과 거듭제곱 법칙 관계\n• 7 오더에 걸쳐 부드러운 스케일링 확인\n• 큰 모델이 작은 모델보다 샘플 효율 높음\n• 최적 컴퓨팅 배분: 모델 크기와 데이터 크기 비율이 핵심\n\n**실무 시사점:**\n같은 컴퓨팅 예산으로 더 큰 모델을 더 적은 데이터로 훈련하는 것이 최적임을 실증적으로 제시.`,
    relDocs: ['사내 LLM 도입 검토 보고서', '2024 AI 인프라 계획서', '모델 스케일링 실험 결과']
  },
  {
    id: 2, title: 'Attention Is All You Need',
    authors: 'A. Vaswani, N. Shazeer, N. Parmar et al.',
    date: '2024-02-28', views: 3891,
    tags: ['NLP', 'Transformer', 'Attention'], cat: 'Language & Text',
    abs: 'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. The Transformer achieves state of the art on machine translation tasks while being significantly more parallelizable.',
    orig: `Abstract\n\nThe dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.\n\n1. Introduction\n\nRecurrent neural networks have been firmly established as state of the art approaches in sequence modeling. The Transformer eschews recurrence and instead relies entirely on attention to draw global dependencies between input and output.\n\n2. Model Architecture\n\nEncoder: 6 identical layers\n  - Multi-head self-attention mechanism\n  - Position-wise fully connected feed-forward network\n\nDecoder: 6 identical layers\n  - Masked multi-head attention\n  - Multi-head attention over encoder output\n  - Position-wise feed-forward network\n\nAttention: Scaled Dot-Product\n  Attention(Q,K,V) = softmax(QK^T / √d_k) V`,
    summ: `**핵심 개념:**\n• 순환 신경망(RNN) 없이 오직 어텐션 메커니즘만 사용\n• 병렬 처리 가능으로 훈련 속도 획기적 향상\n• Multi-head Attention: 다양한 표현 공간에서 동시에 어텐션 계산\n• Positional Encoding으로 순서 정보 보완\n\n**현재 의미:**\n현대 거의 모든 NLP 모델(GPT, BERT, T5 등)의 기반 아키텍처.`,
    relDocs: ['사내 번역 모델 개선 계획', 'NLP 기술 스택 검토서']
  },
  {
    id: 3, title: 'Deep Residual Learning for Image Recognition',
    authors: 'K. He, X. Zhang, S. Ren, J. Sun',
    date: '2024-01-20', views: 2156,
    tags: ['Computer Vision', 'ResNet', 'Deep Learning'], cat: 'Vision & Graphics',
    abs: 'We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs.',
    orig: `1. Introduction\n\nDriven by the significance of depth, a question arises: Is learning better networks as easy as stacking more layers?\n\nHowever, training deeper networks is not easy. The vanishing gradient problem makes it hard to directly train very deep networks.\n\n2. Residual Learning\n\nInstead of hoping each few stacked layers directly fit a desired mapping H(x), we explicitly let these layers fit a residual mapping:\n  F(x) := H(x) − x\n\nThe original mapping is recast into F(x) + x.\n\nThe shortcut connections simply perform identity mapping, and their outputs are added to the outputs of the stacked layers:\n  y = F(x, {W_i}) + x\n\n3. Results\n\n• ImageNet ILSVRC 2015: 3.57% top-5 error\n• 152-layer ResNet trained successfully\n• Won 1st place in ILSVRC and COCO 2015`,
    summ: `**핵심 아이디어:**\n• Skip connection(잔차 연결)으로 기울기 소실 문제 해결\n• 152개 레이어 모델 훈련 성공\n• ImageNet에서 3.57% top-5 오류율 달성\n\n**실무 활용:**\n이미지 분류, 객체 탐지, 영상 처리 등 거의 모든 CV 태스크의 백본으로 활용 가능.`,
    relDocs: ['제품 이미지 분류 시스템 설계서', 'CV 모델 벤치마크 결과']
  },
  {
    id: 4, title: 'Proximal Policy Optimization Algorithms',
    authors: 'J. Schulman, F. Wolski, P. Dhariwal et al.',
    date: '2024-01-10', views: 987,
    tags: ['RL', 'PPO', 'Policy Gradient'], cat: 'Robotics & Control',
    abs: 'We propose a new family of policy gradient methods for reinforcement learning, which alternate between sampling data through interaction with the environment, and optimizing a surrogate objective function using stochastic gradient ascent.',
    orig: `Abstract\n\nWe propose PPO, a family of policy gradient methods that alternate between collecting data and optimizing objectives. PPO achieves the data efficiency of TRPO while being much simpler to implement.\n\n1. Background\n\nPolicy gradient methods work by computing an estimator of the policy gradient:\n  ĝ = E[∇θ log πθ(at|st) Ât]\n\n2. Clipped Surrogate Objective\n\nPPO's main innovation is the clipped probability ratio objective:\n  L^CLIP(θ) = E[min(r_t(θ)Ât, clip(r_t(θ), 1-ε, 1+ε)Ât)]\n\nThis prevents excessively large policy updates while maintaining good sample efficiency.\n\n3. Results\n\n• Outperforms previous methods on MuJoCo continuous control\n• Strong performance on Atari games\n• Simple to tune, widely adopted`,
    summ: `**주요 특징:**\n• TRPO의 성능을 유지하면서 구현 복잡도 대폭 감소\n• Clipped objective function으로 안정적 학습\n• 다양한 환경에서 SOTA 달성\n\n**활용 분야:**\n로봇 제어, 게임 AI, RLHF(인간 피드백 강화학습) 등에 광범위하게 사용됨.`,
    relDocs: ['AI 에이전트 개발 로드맵']
  },
  {
    id: 5, title: 'Graph Attention Networks',
    authors: 'P. Veličković, G. Cucurull, A. Casanova et al.',
    date: '2023-12-15', views: 756,
    tags: ['GNN', 'Graph', 'Attention'], cat: 'ML Foundation',
    abs: 'We present graph attention networks (GATs), novel neural network architectures that operate on graph-structured data, leveraging masked self-attentional layers to address the shortcomings of prior methods based on graph convolutions.',
    orig: `Abstract\n\nGraph attention networks (GATs) operate on graph-structured data. We leverage masked self-attentional layers to address shortcomings of prior graph convolution-based methods.\n\n1. GAT Architecture\n\nInput: set of node features h = {h_1, ..., h_N}, h_i ∈ R^F\nOutput: new node features h' = {h'_1, ..., h'_N}, h'_i ∈ R^{F'}\n\nAttention coefficients:\n  e_ij = a(W h_i, W h_j)\n  α_ij = softmax_j(e_ij)\n\n2. Multi-head Attention\n\nK independent attention heads, concatenated:\n  h'_i = ||_{k=1}^K σ(Σ_{j∈N_i} α_ij^k W^k h_j)\n\n3. Results\n\n• Cora: 83.0% classification accuracy\n• Citeseer: 72.5% classification accuracy\n• PPI: 97.3% micro-F1`,
    summ: `**핵심 특징:**\n• 이웃 노드들에 서로 다른 가중치 자동 학습\n• Transductive/Inductive 학습 모두 지원\n• Cora, Citeseer 벤치마크에서 SOTA\n\n**적용 사례:**\n소셜 네트워크 분석, 추천 시스템, 분자 구조 예측 등.`,
    relDocs: ['지식 그래프 구축 계획서', '추천 시스템 개선 보고서']
  },
  {
    id: 6, title: 'Denoising Diffusion Probabilistic Models',
    authors: 'J. Ho, A. Jain, P. Abbeel',
    date: '2023-11-28', views: 2341,
    tags: ['Generative AI', 'Diffusion', 'Image Generation'], cat: 'Vision & Graphics',
    abs: 'We present high quality image synthesis results using diffusion probabilistic models, a class of latent variable models inspired by considerations from nonequilibrium thermodynamics.',
    orig: `Abstract\n\nWe present DDPM, achieving high quality image synthesis using diffusion probabilistic models. These models define a Markov chain of diffusion steps to slowly add random noise to data, then learn to reverse this process.\n\n1. Forward Process (Diffusion)\n\nGiven data x_0, the forward process adds Gaussian noise over T steps:\n  q(x_t | x_{t-1}) = N(x_t; √(1-β_t) x_{t-1}, β_t I)\n\n2. Reverse Process (Denoising)\n\nThe learned reverse process:\n  p_θ(x_{t-1} | x_t) = N(x_{t-1}; μ_θ(x_t, t), Σ_θ(x_t, t))\n\nA U-Net backbone predicts the noise at each timestep.\n\n3. Results\n\n• CIFAR-10 FID: 3.17 (surpasses prior GAN methods)\n• High quality 256x256 image synthesis\n• Foundation for Stable Diffusion, DALL-E 3`,
    summ: `**작동 원리:**\n• Forward: 이미지에 점진적으로 노이즈 추가\n• Reverse: 노이즈에서 이미지 복원하도록 학습\n• U-Net 아키텍처로 각 타임스텝의 노이즈 예측\n\n**현재 활용:**\nStable Diffusion, DALL-E 3, Midjourney 등 거의 모든 현대 이미지 생성 AI의 기반 기술.`,
    relDocs: ['이미지 생성 AI 도입 검토서', '콘텐츠 생성 파이프라인 설계서', '저작권 및 윤리 가이드라인']
  }
]

export const CATS = ['전체', 'Language & Text', 'Vision & Graphics', 'Robotics & Control', 'ML Foundation', 'Multi-Agent & RL', 'Ethics & Society']
export const CAT_TAG = {
  'Language & Text': 'tt',
  'Vision & Graphics': 'tb',
  'Robotics & Control': 'to',
  'ML Foundation': 'tp',
  'Multi-Agent & RL': 'ta',
  'Ethics & Society': 'tt'
}
export const TAG_C = ['tt', 'tb', 'to', 'tp', 'ta']
