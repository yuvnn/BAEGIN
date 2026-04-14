import { monitoringClient, paperServiceClient } from "./client";

// 파이프라인 수동 실행 (게이트웨이 경로 반영)
export async function runMonitoring(keyword) {
  const response = await monitoringClient.post("/monitor/run", { keyword });
  return response.data;
}

// 논문 vs 내부 문서 유사도 비교
export async function comparePaperWithInternal(paperId, queryText) {
  const response = await monitoringClient.post("/compare", { paper_id: paperId, query_text: queryText });
  return response.data;
}

// 논문 목록 조회
export async function fetchPapers(limit = 20) {
  const response = await paperServiceClient.get("/api/papers", { params: { limit } });
  return response.data;
}

// 특정 논문 상세 조회
export async function fetchPaperById(paperId) {
  const response = await paperServiceClient.get(`/api/papers/${encodeURIComponent(paperId)}`);
  return response.data;
}