import { monitoringClient, paperServiceClient } from "./client";

// 1. 모니터링 서비스 실행 (경로 앞에 /api 추가)
export async function runMonitoring(keyword) {
  const response = await monitoringClient.post("/api/monitor/run", { keyword });
  return response.data;
}

// 2. 논문 비교 (경로 앞에 /api/monitor 추가)
export async function comparePaperWithInternal(paperId, queryText) {
  const response = await monitoringClient.post("/api/monitor/compare", { 
    paper_id: paperId, 
    query_text: queryText 
  });
  return response.data;
}

// 3. 논문 목록 조회 (키워드 필터링 적용 - P1View 최신 논문용)
export async function fetchPapers(limit = 20) {
  const response = await paperServiceClient.get("/api/papers", { params: { limit } });
  return response.data;
}

// 3-1. 전체 논문 목록 조회 (필터링 없음 - P2View 논문 리스트용)
export async function fetchAllPapers(limit = 100) {
  const response = await paperServiceClient.get("/api/papers", { params: { limit, no_filter: true } });
  return response.data;
}

// 4. 특정 논문 상세 조회 (이미 잘 되어 있음)
export async function fetchPaperById(paperId) {
  const response = await paperServiceClient.get(`/api/papers/${encodeURIComponent(paperId)}`);
  return response.data;
}

// 5. 커스텀 파라미터로 arXiv 직접 검색
export async function searchPapers({ dateFrom, dateTo, keywords, categories, maxResults = 50 }) {
  const response = await monitoringClient.post('/api/monitor/search', {
    date_from: dateFrom || null,
    date_to: dateTo || null,
    keywords: keywords || [],
    categories: categories || [],
    max_results: maxResults,
  }, { timeout: 60000 })
  return response.data  // { count, papers[] }
}

// 6. 논문 관련 사내문서 조회
export async function fetchPaperRelates(paperId) {
  const response = await paperServiceClient.get(`/api/papers/${encodeURIComponent(paperId)}/relates`)
  return response.data  // { paper_id, relates: [{ internal_doc_id, rank, reason }] }
}