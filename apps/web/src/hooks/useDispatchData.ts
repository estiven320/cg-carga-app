'use client';

import useSWR from 'swr';
import { useMemo } from 'react';
import { api } from '@/lib/api';
import type { DashboardSummary, Order, Route } from '@/types/tms';

export interface DispatchData {
  routes: Route[];
  summary: DashboardSummary | undefined;
  /** Todas las ordenes en un solo arreglo, con el color de su ruta resuelto. */
  orders: Array<Order & { routeId: string; routeCode: string; color: string }>;
  isLoading: boolean;
  error: unknown;
  refresh: () => void;
}

export function useDispatchData(date: string): DispatchData {
  const routesQuery = useSWR<Route[]>(['routes', date], () => api.routes(date), {
    // El realtime empuja los cambios; el polling es solo la red de seguridad
    // por si el WebSocket se cae.
    refreshInterval: 60_000,
    revalidateOnFocus: true,
    keepPreviousData: true,
  });

  const summaryQuery = useSWR<DashboardSummary>(['summary', date], () => api.summary(date), {
    refreshInterval: 30_000,
    keepPreviousData: true,
  });

  const orders = useMemo(
    () =>
      (routesQuery.data ?? []).flatMap((route) =>
        route.orders.map((order) => ({
          ...order,
          routeId: route.id,
          routeCode: route.code,
          color: route.color,
        })),
      ),
    [routesQuery.data],
  );

  return {
    routes: routesQuery.data ?? [],
    summary: summaryQuery.data,
    orders,
    isLoading: routesQuery.isLoading,
    error: routesQuery.error ?? summaryQuery.error,
    refresh: () => {
      void routesQuery.mutate();
      void summaryQuery.mutate();
    },
  };
}
