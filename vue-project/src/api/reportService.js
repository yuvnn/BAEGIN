import { internalClient } from "./client";

const REPORT_GENERATION_TIMEOUT_MS = 120000;

export async function startReportGeneration(payload) {
  const response = await internalClient.post("/reports/generate", payload, {
    timeout: REPORT_GENERATION_TIMEOUT_MS,
  });
  return response.data;
}

export function getReportStreamUrl(reportId) {
  const base = (import.meta.env.VITE_INTERNAL_API || "/internal-api").replace(/\/$/, "");
  return `${base}/reports/stream/${encodeURIComponent(reportId)}`;
}
