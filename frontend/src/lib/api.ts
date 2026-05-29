/**
 * SED Energy AI Marketing System — API Client
 */
import axios, { AxiosInstance, AxiosError } from "axios";
import Cookies from "js-cookie";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 60000,
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 globally — redirect to login
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      Cookies.remove("access_token");
      if (typeof window !== "undefined") window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", new URLSearchParams({ username: email, password }), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }),
  me: () => api.get("/auth/me"),
  createUser: (data: any) => api.post("/auth/users", data),
};

// ─── Content ──────────────────────────────────────────────────────────────
export const contentApi = {
  generate: (data: any)          => api.post("/content/generate", data),
  list: (params?: any)           => api.get("/content/", { params }),
  get: (id: string)              => api.get(`/content/${id}`),
  approve: (id: string, data: any) => api.patch(`/content/${id}/approve`, data),
  schedule: (id: string, data: any) => api.patch(`/content/${id}/schedule`, data),
  regenerate: (id: string)       => api.post(`/content/${id}/regenerate`),
  delete: (id: string)           => api.delete(`/content/${id}`),
};

// ─── Social ───────────────────────────────────────────────────────────────
export const socialApi = {
  publishNow: (contentItemId: string) => api.post("/social/publish-now", { content_item_id: contentItemId }),
  getCalendar: ()                      => api.get("/social/calendar"),
  getPublished: (platform?: string)    => api.get("/social/published", { params: { platform } }),
  getPendingApproval: ()               => api.get("/social/pending-approval"),
  getStats: ()                         => api.get("/social/stats"),
};

// ─── Analytics ────────────────────────────────────────────────────────────
export const analyticsApi = {
  getOverview: ()               => api.get("/analytics/overview"),
  getTopContent: (platform?: string) => api.get("/analytics/top-content", { params: { platform } }),
  getPlatformBreakdown: ()      => api.get("/analytics/platform-breakdown"),
  getContentTypePerf: ()        => api.get("/analytics/content-type-performance"),
  generateReport: ()            => api.post("/analytics/generate-report"),
};

// ─── Stock ────────────────────────────────────────────────────────────────
export const stockApi = {
  list: (params?: any)          => api.get("/stock/", { params }),
  create: (data: any)           => api.post("/stock/", data),
  updateQty: (id: string, data: any) => api.patch(`/stock/${id}/quantity`, data),
  getAlerts: (processed?: boolean) => api.get("/stock/alerts", { params: { processed } }),
  sagSync: ()                   => api.post("/stock/sage-sync"),
};

// ─── WhatsApp ─────────────────────────────────────────────────────────────
export const whatsappApi = {
  getGroups: ()                 => api.get("/whatsapp/groups"),
  createGroup: (data: any)      => api.post("/whatsapp/groups", data),
  generateMessage: (data: any)  => api.post("/whatsapp/generate-message", data),
  generateBulk: (topic: string) => api.post("/whatsapp/generate-bulk", null, { params: { topic } }),
  send: (data: any)             => api.post("/whatsapp/send", data),
};

// ─── Knowledge Base ───────────────────────────────────────────────────────
export const knowledgeApi = {
  upload: (formData: FormData) => api.post("/knowledge/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  }),
  search: (data: any)          => api.post("/knowledge/search", data),
  listDocuments: (params?: any) => api.get("/knowledge/documents", { params }),
  deleteDocument: (id: string) => api.delete(`/knowledge/documents/${id}`),
  getStats: ()                 => api.get("/knowledge/stats"),
};

// ─── Media ────────────────────────────────────────────────────────────────
export const mediaApi = {
  getGallery: (type: string)         => api.get(`/media/gallery?type=${type}`),
  generateImage: (data: any)        => api.post("/media/generate-image", data),
  generateDesignPrompt: (data: any) => api.post("/media/generate-design-prompt", data),
  generateVideoPrompt: (data: any)  => api.post("/media/generate-video-prompt", data),
  generateVideo: (data: any)        => api.post("/media/generate-video", data),
};

// ─── Settings ─────────────────────────────────────────────────────────────
export const settingsApi = {
  getSchedulerJobs: ()              => api.get("/settings/scheduler/jobs"),
  triggerJob: (name: string)        => api.post(`/settings/scheduler/trigger/${name}`),
  getBrandConfig: ()                => api.get("/settings/brand-config"),
  checkServiceHealth: ()            => api.get("/settings/health/services"),
};
