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

  // Artists
  listArtists: () => request<any[]>('/admin/artists'),
  createArtist: (data: any) => request<any>('/admin/artists', { method: 'POST', body: JSON.stringify(data) }),
  updateArtist: (id: string, data: any) => request<any>(`/admin/artists/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteArtist: (id: string) => request<void>(`/admin/artists/${id}`, { method: 'DELETE' }),

  // Content
  listGenerations: (params?: { page?: number; status?: string }) => {
    const query = new URLSearchParams(params as any).toString();
    return request<any>(`/admin/generations?${query}`);
  },
  updateGenerationStatus: (id: string, status: string) =>
    request<any>(`/admin/generations/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) }),

  // Users
  listUsers: (params?: { page?: number; search?: string }) => {
    const query = new URLSearchParams(params as any).toString();
    return request<any>(`/admin/users?${query}`);
  },
  banUser: (id: string) => request<any>(`/admin/users/${id}/ban`, { method: 'POST' }),
  unbanUser: (id: string) => request<any>(`/admin/users/${id}/unban`, { method: 'POST' }),

  // Model Monitor
  getModelStats: (params?: { model?: string; timeRange?: string }) => {
    const query = new URLSearchParams(params as any).toString();
    return request<any>(`/admin/model-stats?${query}`);
  },
  listApiCalls: (params?: { model?: string; page?: number }) => {
    const query = new URLSearchParams(params as any).toString();
    return request<any>(`/admin/api-calls?${query}`);
  },
};
