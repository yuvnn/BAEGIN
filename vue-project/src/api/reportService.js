import axios from "axios";
import { store } from "../store.js";

const internalClient = axios.create({
  baseURL: "/internal-api",
  timeout: 15000,
});

internalClient.interceptors.request.use((config) => {
  const token = store.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const REPORT_GENERATION_TIMEOUT_MS = 120000;

export async function startReportGeneration(payload) {
  const response = await internalClient.post("/reports/generate", payload, {
    timeout: REPORT_GENERATION_TIMEOUT_MS,
  });
  return response.data;
}

export function getReportStreamUrl(reportId) {
  return `${"/internal-api".replace(/\/$/, "")}/reports/stream/${encodeURIComponent(reportId)}`;
}
