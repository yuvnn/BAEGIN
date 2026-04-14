import axios from "axios";

export const monitoringClient = axios.create({
  baseURL: import.meta.env.VITE_MONITORING_API || "/api",
  timeout: 10000,
});

export const internalClient = axios.create({
  baseURL: import.meta.env.VITE_INTERNAL_API || "/internal-api",
  timeout: 15000,
});
