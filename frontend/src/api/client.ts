
import axios from "axios";

export const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 300000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function setAccessToken(token: string | undefined) {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common.Authorization;
  }
}

