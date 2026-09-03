'use client';

import { useEffect, useRef, useState } from 'react';
import { io, type Socket } from 'socket.io-client';
import { API_URL } from '@/lib/api';
import type { RealtimeEvent } from '@/types/tms';

export interface RealtimeState {
  connected: boolean;
  /** Progreso de la geocodificacion en curso (Nominatim va a 1 direccion/s). */
  importProgress: { done: number; total: number; stage: string; etaMs?: number } | null;
  driverPositions: Record<string, { lat: number; lng: number; recordedAt: string }>;
}

/**
 * Suscripcion al canal en vivo del backend.
 *
 * `onEvent` se guarda en un ref para que cambiar el handler (cosa que ocurre en
 * cada render del dashboard) no reconecte el socket.
 */
export function useRealtime(onEvent?: (event: RealtimeEvent) => void): RealtimeState {
  const [connected, setConnected] = useState(false);
  const [importProgress, setImportProgress] = useState<RealtimeState['importProgress']>(null);
  const [driverPositions, setDriverPositions] = useState<RealtimeState['driverPositions']>({});
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    const base = API_URL.replace(/\/api$/, '');
    const socket: Socket = io(`${base}/realtime`, {
      transports: ['websocket'],
      reconnectionDelay: 1000,
      reconnectionDelayMax: 10_000,
    });

    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));

    const forward = (event: RealtimeEvent) => handlerRef.current?.(event);

    socket.on('import.progress', (event: Extract<RealtimeEvent, { type: 'import.progress' }>) => {
      setImportProgress({ done: event.done, total: event.total, stage: event.stage, etaMs: event.etaMs });
      forward(event);
    });

    socket.on('import.completed', (event: RealtimeEvent) => {
      setImportProgress(null);
      forward(event);
    });

    socket.on('order.updated', forward);

    socket.on('driver.ping', (event: Extract<RealtimeEvent, { type: 'driver.ping' }>) => {
      setDriverPositions((current) => ({
        ...current,
        [event.driverId]: { lat: event.lat, lng: event.lng, recordedAt: event.recordedAt },
      }));
      forward(event);
    });

    return () => {
      socket.close();
    };
  }, []);

  return { connected, importProgress, driverPositions };
}
