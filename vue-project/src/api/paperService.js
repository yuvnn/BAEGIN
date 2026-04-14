import { monitoringClient, paperServiceClient } from "./client";

export async function runMonitoring(keyword) {
	const response = await monitoringClient.post("/monitor/run", { keyword });
	return response.data;
}

export async function comparePaperWithInternal(paperId, queryText) {
	const response = await monitoringClient.post("/compare", { paper_id: paperId, query_text: queryText });
	return response.data;
}

export async function fetchPapers(limit = 20) {
  const response = await paperServiceClient.get("/papers", { params: { limit } });
  return response.data;
}

export async function fetchPaperById(paperId) {
  const response = await paperServiceClient.get(`/papers/${encodeURIComponent(paperId)}`);
  return response.data;
}
