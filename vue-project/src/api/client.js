import axios from "axios";

export const monitoringClient = axios.create({
  baseURL: import.meta.env.VITE_MONITORING_API || "/api",
  timeout: 10000,
});

export const paperServiceClient = axios.create({
  baseURL: import.meta.env.VITE_PAPER_API || "http://localhost:18083",
  timeout: 10000,
});
