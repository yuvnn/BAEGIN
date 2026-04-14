import axios from "axios";
import { store } from "../store.js";

// Docker: 상대 경로 → nginx가 api-gateway:8080으로 프록시
// 로컬 개발: VITE_API_BASE_URL=http://localhost:18080 설정
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

apiClient.interceptors.request.use((config) => {
  const token = store.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Legacy monitoring client kept for backward compatibility
export const monitoringClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

monitoringClient.interceptors.request.use((config) => {
  const token = store.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const paperServiceClient = axios.create({
  baseURL: import.meta.env.VITE_PAPER_API || "http://localhost:18083",
  timeout: 10000,
});
