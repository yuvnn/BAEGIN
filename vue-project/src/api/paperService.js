import { monitoringClient } from "./client";

export async function runMonitoring(keyword) {
	const response = await monitoringClient.post("/monitor/run", { keyword });
	return response.data;
}

export async function comparePaperWithInternal(paperId, queryText) {
	const response = await monitoringClient.post("/compare", { paper_id: paperId, query_text: queryText });
	return response.data;
}

