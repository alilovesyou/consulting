import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export function createApiClient(initData) {
  return axios.create({
    baseURL: API_BASE_URL,
    headers: {
      "X-Telegram-Init-Data": initData || "",
    },
  });
}