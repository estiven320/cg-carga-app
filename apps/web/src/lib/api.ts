import type { DashboardSummary, ImportResult, Route } from '@/types/tms';

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3001/api';

class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...init?.headers,
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new ApiError(detail || `Error ${response.status} en ${path}`, response.status);
  }
  return (await response.json()) as T;
}

export const api = {
  routes: (date: string) => request<Route[]>(`/routes?date=${date}`),
  summary: (date: string) => request<DashboardSummary>(`/routes/summary?date=${date}`),

  importDispatch: (file: File, sheet: string, date?: string) => {
    const body = new FormData();
    body.append('file', file);
    const params = new URLSearchParams({ sheet });
    if (date) params.set('date', date);
    return request<ImportResult>(`/import/dispatch?${params}`, { method: 'POST', body });
  },

  assignDriver: (routeId: string, driverId: string) =>
    request(`/routes/${routeId}/driver`, { method: 'POST', body: JSON.stringify({ driverId }) }),

  sendRouteWhatsapp: (routeId: string) =>
    request(`/notifications/routes/${routeId}/send`, { method: 'POST', body: JSON.stringify({}) }),

  setCoordinates: (orderId: string, lat: number, lng: number) =>
    request(`/geocoding/orders/${orderId}/coordinates`, {
      method: 'POST',
      body: JSON.stringify({ lat, lng }),
    }),

  retryGeocoding: (date: string) => request(`/geocoding/retry?date=${date}`, { method: 'POST' }),
};

export { ApiError };
