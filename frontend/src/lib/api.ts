const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RequestOptions {
  method?: string;
  body?: any;
  token?: string | null;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, token } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Auth API
export const authAPI = {
  register: (data: { email: string; password: string; nickname?: string }) =>
    apiRequest("/api/auth/register", { method: "POST", body: data }),

  login: (data: { email: string; password: string }) =>
    apiRequest("/api/auth/login", { method: "POST", body: data }),

  getMe: (token: string) =>
    apiRequest("/api/auth/me", { token }),

  getGoogleOAuthUrl: () =>
    apiRequest<{ url: string }>("/api/auth/oauth/google/url"),

  getGitHubOAuthUrl: () =>
    apiRequest<{ url: string }>("/api/auth/oauth/github/url"),

  googleCallback: (code: string) =>
    apiRequest("/api/auth/oauth/google", { method: "POST", body: { code } }),

  githubCallback: (code: string) =>
    apiRequest("/api/auth/oauth/github", { method: "POST", body: { code } }),
};

// Dreams API
export const dreamsAPI = {
  create: (token: string, data: { title?: string; content: string; mood?: string; tags?: string[] }) =>
    apiRequest("/api/dreams", { method: "POST", body: data, token }),

  list: (token: string, page = 1, pageSize = 20) =>
    apiRequest(`/api/dreams?page=${page}&page_size=${pageSize}`, { token }),

  get: (token: string, id: string) =>
    apiRequest(`/api/dreams/${id}`, { token }),

  update: (token: string, id: string, data: any) =>
    apiRequest(`/api/dreams/${id}`, { method: "PUT", body: data, token }),

  delete: (token: string, id: string) =>
    apiRequest(`/api/dreams/${id}`, { method: "DELETE", token }),
};

// Generate API
export const generateAPI = {
  enhance: (token: string, data: { dream_id: string; style?: string }) =>
    apiRequest("/api/generate/enhance", { method: "POST", body: data, token }),

  image: (token: string, data: {
    dream_id: string;
    style?: string;
    size?: string;
    count?: number;
  }) =>
    apiRequest("/api/generate/image", { method: "POST", body: data, token }),

  video: (token: string, data: {
    dream_id: string;
    style?: string;
    resolution?: string;
    duration?: number;
    ratio?: string;
  }) =>
    apiRequest("/api/generate/video", { method: "POST", body: data, token }),

  checkStatus: (token: string, generationId: string) =>
    apiRequest(`/api/generate/task/${generationId}`, { token }),
};
