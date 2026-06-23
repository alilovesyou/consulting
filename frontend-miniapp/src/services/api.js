// frontend-miniapp/src/services/api.js
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const DEV_TELEGRAM_ID = import.meta.env.VITE_DEV_TELEGRAM_ID || "";

export function createApiClient(initData) {
  const headers = {};

  if (initData) {
    headers["X-Telegram-Init-Data"] = initData;
  }

  // Faqat local development uchun.
  // Backend .env ichida API_DEV_AUTH=1 bo'lsa ishlaydi.
  if (!initData && DEV_TELEGRAM_ID) {
    headers["X-Dev-Telegram-Id"] = DEV_TELEGRAM_ID;
  }

  const api = axios.create({
    baseURL: API_BASE_URL,
    headers,
    timeout: 30000,
  });

  api.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = error.response?.status;
      const detail = error.response?.data?.detail;

      if (status === 401) {
        error.friendlyMessage =
          detail ||
          "Telegram Mini App auth ma'lumoti noto'g'ri yoki yuborilmagan.";
      } else if (status === 403) {
        error.friendlyMessage =
          detail || "Bu bo'limga kirish uchun ruxsat yo'q.";
      } else if (status === 404) {
        error.friendlyMessage = detail || "Ma'lumot topilmadi.";
      } else if (status === 413) {
        error.friendlyMessage = detail || "Fayl hajmi juda katta.";
      } else if (detail) {
        error.friendlyMessage = detail;
      } else if (error.code === "ECONNABORTED") {
        error.friendlyMessage = "Server javob berishda kechikdi.";
      } else {
        error.friendlyMessage = "Server bilan aloqa qilishda xatolik yuz berdi.";
      }

      return Promise.reject(error);
    }
  );

  return api;
}