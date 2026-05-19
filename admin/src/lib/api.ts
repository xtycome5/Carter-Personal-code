const API_BASE = '/api';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('admin_token');
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });

  if (res.status === 401) {
    localStorage.removeItem('admin_token');
    window.location.href = '/admin/login';
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export const adminAPI = {
  // Dashboard
  getStats: () => request<any>('/admin/stats'),
  getRecentGenerations: (limit = 10) => request<any>(`/admin/recent-generations?limit=${limit}`),

  // Artists
  listArtists: () => request<any>('/admin/artists'),
  createArtist: (data: any) => request<any>('/admin/artists', { method: 'POST', body: JSON.stringify(data) }),
  updateArtist: (id: string, data: any) => request<any>(`/admin/artists/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteArtist: (id: string) => request<void>(`/admin/artists/${id}`, { method: 'DELETE' }),

  // Content / Generations
  listGenerations: (params?: { page?: number; status?: string; gen_type?: string }) => {
    const clean: Record<string, string> = {};
    if (params?.page) clean.page = String(params.page);
    if (params?.status) clean.status = params.status;
    if (params?.gen_type) clean.gen_type = params.gen_type;
    const query = new URLSearchParams(clean).toString();
    return request<any>(`/admin/generations?${query}`);
  },

  // Users
  listUsers: (params?: { page?: number; search?: string }) => {
    const clean: Record<string, string> = {};
    if (params?.page) clean.page = String(params.page);
    if (params?.search) clean.search = params.search;
    const query = new URLSearchParams(clean).toString();
    return request<any>(`/admin/users?${query}`);
  },

  // API Call Monitoring
  getApiCalls: (params?: { page?: number; model?: string; status?: string; endpoint?: string; hours?: number }) => {
    const clean: Record<string, string> = {};
    if (params?.page) clean.page = String(params.page);
    if (params?.model) clean.model = params.model;
    if (params?.status) clean.status = params.status;
    if (params?.endpoint) clean.endpoint = params.endpoint;
    if (params?.hours) clean.hours = String(params.hours);
    const query = new URLSearchParams(clean).toString();
    return request<any>(`/admin/api-calls?${query}`);
  },
  getApiStats: (hours = 24) => request<any>(`/admin/api-stats?hours=${hours}`),

  // Gallery Review
  galleryPending: (page = 1) => request<any>(`/admin/gallery/pending?page=${page}`),
  galleryFeatured: (page = 1) => request<any>(`/admin/gallery/featured?page=${page}`),
  galleryApprove: (ids: string[]) => request<any>('/admin/gallery/approve', { method: 'POST', body: JSON.stringify({ ids }) }),
  galleryReject: (ids: string[]) => request<any>('/admin/gallery/reject', { method: 'POST', body: JSON.stringify({ ids }) }),
};
