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
    window.location.href = '/login';
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
};
