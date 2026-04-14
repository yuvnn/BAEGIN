<template>
  <div id="p6" class="page">
    <div class="p6-inner">

      <!-- Hero -->
      <div class="p6-hero">
        <div class="p6-hero-badge">BAEGIN · AI Research Assessment</div>
        <div class="p6-hero-title">
          <span>AIRA</span> — AI Research Assessment Score
        </div>
        <div class="p6-hero-sub">
          Sakana AI의 The AI Scientist 아키텍처를 기반으로 한 자동화된 논문 심사 시스템입니다.
          3인 심사 앙상블과 자기 반성 루프, Area Chair 메타리뷰를 통해 1~10점으로 논문을 평가합니다.
        </div>
      </div>

      <!-- Stats -->
      <div class="p6-stats">
        <div class="p6-stat-card">
          <div class="p6-stat-val">70%</div>
          <div class="p6-stat-label">인간 리뷰어와의 균형 정확도<br><span style="font-size:11px;color:var(--t3)">Balanced Accuracy</span></div>
        </div>
        <div class="p6-stat-card">
          <div class="p6-stat-val">0.57</div>
          <div class="p6-stat-label">AIRA F1 Score<br><span style="font-size:11px;color:var(--t3)">인간 평균(0.49) 상회</span></div>
        </div>
        <div class="p6-stat-card">
          <div class="p6-stat-val">6.0</div>
          <div class="p6-stat-label">Accept 임계값<br><span style="font-size:11px;color:var(--t3)">이상이면 학술적 가치 인정</span></div>
        </div>
      </div>

      <!-- Pipeline -->
      <div class="p6-section">
        <div class="p6-section-title">평가 파이프라인</div>
      </div>
      <div class="p6-pipeline">
        <div class="p6-step">
          <div class="p6-step-num">1</div>
          <div class="p6-step-title">초기 리뷰</div>
          <div class="p6-step-desc">3명의 독립 LLM 리뷰어가 논문 전문을 분석하여 1차 점수와 평가 초안을 작성합니다.</div>
          <div class="p6-step-arrow">›</div>
        </div>
        <div class="p6-step">
          <div class="p6-step-num">2</div>
          <div class="p6-step-title">자기 반성</div>
          <div class="p6-step-desc">각 리뷰어가 자신의 초안을 비판적으로 재검토하여 논리적 허점과 편향을 수정합니다.</div>
          <div class="p6-step-arrow">›</div>
        </div>
        <div class="p6-step">
          <div class="p6-step-num">3</div>
          <div class="p6-step-title">앙상블</div>
          <div class="p6-step-desc">3개의 독립된 리뷰를 종합하여 통계적 안정성을 확보하고 이상치를 제거합니다.</div>
          <div class="p6-step-arrow">›</div>
        </div>
        <div class="p6-step">
          <div class="p6-step-num">4</div>
          <div class="p6-step-title">Area Chair</div>
          <div class="p6-step-desc">GPT-4o가 메타리뷰어로서 앙상블 결과를 종합해 최종 점수와 판정을 확정합니다.</div>
        </div>
      </div>

      <!-- Score Scale -->
      <div class="p6-section">
        <div class="p6-section-title">AIRA 점수 기준표 (NeurIPS 가이드라인)</div>
      </div>
      <div class="p6-scores">
        <div class="p6-score-card s10">
          <div class="p6-score-num">10</div>
          <div class="p6-score-label">상위 5% 논문<br>획기적 혁신 + 완벽한 검증</div>
          <div class="p6-score-decision">Accept</div>
        </div>
        <div class="p6-score-card s8">
          <div class="p6-score-num">8</div>
          <div class="p6-score-label">상위 50% 논문<br>견고한 연구 + 유의미한 기여</div>
          <div class="p6-score-decision">Accept</div>
        </div>
        <div class="p6-score-card s6">
          <div class="p6-score-num">6</div>
          <div class="p6-score-label">임계값 이상<br>일부 약점 있으나 가치 있음</div>
          <div class="p6-score-decision">Weak Accept</div>
        </div>
        <div class="p6-score-card s4">
          <div class="p6-score-num">4</div>
          <div class="p6-score-label">임계값 미만<br>방법론 또는 실험의 결함</div>
          <div class="p6-score-decision">Weak Reject</div>
        </div>
        <div class="p6-score-card s1">
          <div class="p6-score-num">1</div>
          <div class="p6-score-label">가치 없음<br>심각한 오류 또는 자명한 작업</div>
          <div class="p6-score-decision">Reject</div>
        </div>
      </div>

      <!-- Evaluation Criteria -->
      <div class="p6-section">
        <div class="p6-section-title">6가지 평가 기준 (NeurIPS Review Form)</div>
      </div>
      <div class="p6-criteria">
        <div class="p6-criterion">
          <div class="p6-criterion-title">Originality · 독창성</div>
          <div class="p6-criterion-desc">제안된 방법론이 기존 연구와 차별화되는지, 단순히 알려진 기술의 결합인지 평가합니다.</div>
        </div>
        <div class="p6-criterion">
          <div class="p6-criterion-title">Quality · 품질</div>
          <div class="p6-criterion-desc">실험 결과가 주장을 뒷받침하기에 충분한지, 기술적으로 건전한지 분석합니다.</div>
        </div>
        <div class="p6-criterion">
          <div class="p6-criterion-title">Clarity · 명확성</div>
          <div class="p6-criterion-desc">논문이 잘 조직되어 있으며, 결과의 재현이 가능한 수준으로 명확하게 서술되었는지 확인합니다.</div>
        </div>
        <div class="p6-criterion">
          <div class="p6-criterion-title">Significance · 중요성</div>
          <div class="p6-criterion-desc">해당 연구가 머신러닝 커뮤니니티에 미칠 영향력과 후속 연구의 가능성을 점검합니다.</div>
        </div>
        <div class="p6-criterion">
          <div class="p6-criterion-title">Summary · 요약</div>
          <div class="p6-criterion-desc">논문의 핵심 기여도를 저자의 주장에 치우치지 않고 객관적으로 요약합니다.</div>
        </div>
        <div class="p6-criterion">
          <div class="p6-criterion-title">Questions to Authors · 질문</div>
          <div class="p6-criterion-desc">리뷰어로서 저자에게 던질 구체적인 질문들을 제시하여 세부 파악 깊이를 검증합니다.</div>
        </div>
      </div>

      <!-- Human Comparison -->
      <div class="p6-section">
        <div class="p6-section-title">인간 리뷰어와의 성능 비교 (ICLR 2025 워크숍)</div>
      </div>
      <div class="p6-comparison">
        <table class="p6-table">
          <thead>
            <tr>
              <th>논문</th>
              <th>인간 리뷰어 평균</th>
              <th>AIRA 평균</th>
              <th>최종 판정</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Compositional Regularization</td>
              <td>6.33</td>
              <td>6.50</td>
              <td class="accept">Accept</td>
            </tr>
            <tr>
              <td>Real-World Pest Detection</td>
              <td>4.67</td>
              <td>4.30</td>
              <td class="reject">Reject</td>
            </tr>
            <tr>
              <td>Impact of Label Noise</td>
              <td>3.00</td>
              <td>3.20</td>
              <td class="reject">Reject</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Back button -->
      <button class="p6-back-btn" @click="store.go('p1')">← 탐색 화면으로 돌아가기</button>
    </div>
  </div>
</template>

<script setup>
import { store } from '../store.js'
</script>
