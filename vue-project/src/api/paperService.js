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

// 3. 논문 목록 조회 (이미 잘 되어 있음)
export async function fetchPapers(limit = 20) {
  const response = await paperServiceClient.get("/api/papers", { params: { limit } });
  return response.data;
}

// 4. 특정 논문 상세 조회 (이미 잘 되어 있음)
export async function fetchPaperById(paperId) {
  const response = await paperServiceClient.get(`/api/papers/${encodeURIComponent(paperId)}`);
  return response.data;
}