import axios from "axios";

export const monitoringClient = axios.create({
  baseURL: import.meta.env.VITE_MONITORING_API || "/api",
  timeout: 10000,
});
