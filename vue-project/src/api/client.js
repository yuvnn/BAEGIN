import axios from "axios";
import { store } from "../store.js";

// Gateway 주소 (로컬: http://localhost:18080, 도커: 배포 환경 주소)
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
// Internal 서비스 주소
const INTERNAL_BASE_URL = import.meta.env.VITE_INTERNAL_API || "/internal-api";

// 공통 인터셉터 설정 함수
const addAuthInterceptor = (instance) => {
  instance.interceptors.request.use((config) => {
    const token = store.token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  return instance;
};

// 1. 기본 API 클라이언트
export const apiClient = addAuthInterceptor(axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
}));

// 2. 모니터링 서비스 클라이언트
export const monitoringClient = addAuthInterceptor(axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
}));

// 3. 논문 서비스 클라이언트
export const paperServiceClient = addAuthInterceptor(axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
}));

// 4. [Feat 추가] 내부 문서 처리 클라이언트
export const internalClient = addAuthInterceptor(axios.create({
  baseURL: INTERNAL_BASE_URL,
  timeout: 15000,
}));