import axios from "axios";

export const monitoringClient = axios.create({
  baseURL: import.meta.env.VITE_MONITORING_API || "http://localhost:18085",
  timeout: 10000,
});
