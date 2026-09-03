export type OrderStatus =
  | 'PENDING'
  | 'ASSIGNED'
  | 'IN_TRANSIT'
  | 'ARRIVED'
  | 'DELIVERED'
  | 'PARTIAL'
  | 'FAILED'
  | 'RESCHEDULED'
  | 'CANCELLED';

export type GeocodeStatus =
  | 'PENDING'
  | 'RESOLVED'
  | 'LOW_CONFIDENCE'
  | 'MANUAL'
  | 'NOT_FOUND'
  | 'ERROR';

export interface Order {
  id: string;
  documentNumber: string;
  clientNameRaw: string;
  address: string;
  locality: string | null;
  lat: number | null;
  lng: number | null;
  geocodeStatus: GeocodeStatus;
  geocodeLabel: string | null;
  weightKg: number;
  units: number;
  items: number;
  comments: string | null;
  timeWindowStart: string | null;
  timeWindowEnd: string | null;
  requiresAppointment: boolean;
  status: OrderStatus;
  sequence: number | null;
  deliveredAt: string | null;
  proofCount: number;
}

export interface Driver {
  id: string;
  fullName: string;
  phone: string;
  vehiclePlate: string | null;
  lastLat: number | null;
  lastLng: number | null;
  lastPingAt: string | null;
}

export interface Route {
  id: string;
  code: string;
  name: string | null;
  dispatchDate: string;
  status: 'DRAFT' | 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  /** Color asignado por el backend a partir de `N/RUTA`. */
  color: string;
  driver: Driver | null;
  totalOrders: number;
  deliveredCount: number;
  failedCount: number;
  totalWeightKg: number;
  totalUnits: number;
  totalItems: number;
  orders: Order[];
}

export interface DashboardSummary {
  dispatchDate: string;
  routes: number;
  orders: number;
  delivered: number;
  failed: number;
  inTransit: number;
  pendingGeocode: number;
  totalWeightKg: number;
  totalUnits: number;
  completionRate: number;
}

export interface ImportResult {
  batchId: string;
  sheetName: string;
  dispatchDate: string;
  totalRows: number;
  imported: number;
  skipped: number;
  failed: number;
  pendingGeocode: number;
  estimatedGeocodeMs: number;
  unmappedHeaders: string[];
  issues: Array<{ row: number; column?: string; message: string }>;
}

export type RealtimeEvent =
  | { type: 'import.progress'; batchId: string; stage: string; done: number; total: number; etaMs?: number }
  | { type: 'import.completed'; batchId: string; imported: number; failed: number }
  | { type: 'order.updated'; orderId: string; routeId: string; status: string; lat?: number | null; lng?: number | null }
  | { type: 'driver.ping'; driverId: string; routeId?: string | null; lat: number; lng: number; recordedAt: string };
