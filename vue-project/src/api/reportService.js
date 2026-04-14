import axios from "axios";
import { store } from "../store.js"; // 인증 토큰을 가져오기 위해 필요

// 1. 환경 변수에서 베이스 URL을 가져오거나 기본값 사용
const BASE_URL = (import.meta.env.VITE_INTERNAL_API || "/internal-api").replace(/\/$/, "");

const internalClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
});

// 2. [Main의 핵심] 모든 요청에 JWT 토큰을 자동으로 주입하는 인터셉터
internalClient.interceptors.request.use((config) => {
  const token = store.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const REPORT_GENERATION_TIMEOUT_MS = 120000;

// 리포트 생성 시작 API
export async function startReportGeneration(payload) {
  const response = await internalClient.post("/reports/generate", payload, {
    timeout: REPORT_GENERATION_TIMEOUT_MS,
  });
  return response.data;
}

// 3. [Feat의 유연함] 리포트 스트리밍 URL 생성 (환경 변수 적용)
export function getReportStreamUrl(reportId) {
  return `${BASE_URL}/reports/stream/${encodeURIComponent(reportId)}`;
}

export async function getReportList(limit = 50) {
  const response = await internalClient.get('/reports/', { params: { limit } });
  return response.data;
}

export async function getReportById(reportId) {
  const response = await internalClient.get(`/reports/${encodeURIComponent(reportId)}`);
  return response.data;
}