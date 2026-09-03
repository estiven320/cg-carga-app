-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "public";

-- CreateExtension
CREATE EXTENSION IF NOT EXISTS "postgis" WITH SCHEMA "public";

-- CreateEnum
CREATE TYPE "UserRole" AS ENUM ('ADMIN', 'DISPATCHER', 'VIEWER');

-- CreateEnum
CREATE TYPE "RouteStatus" AS ENUM ('DRAFT', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');

-- CreateEnum
CREATE TYPE "OrderStatus" AS ENUM ('PENDING', 'ASSIGNED', 'IN_TRANSIT', 'ARRIVED', 'DELIVERED', 'PARTIAL', 'FAILED', 'RESCHEDULED', 'CANCELLED');

-- CreateEnum
CREATE TYPE "GeocodeStatus" AS ENUM ('PENDING', 'RESOLVED', 'LOW_CONFIDENCE', 'MANUAL', 'NOT_FOUND', 'ERROR');

-- CreateEnum
CREATE TYPE "GeocodeSource" AS ENUM ('NOMINATIM', 'CACHE', 'MANUAL', 'DRIVER_GPS');

-- CreateEnum
CREATE TYPE "ProofType" AS ENUM ('PHOTO', 'SIGNATURE', 'DOCUMENT', 'NOTE');

-- CreateEnum
CREATE TYPE "EventType" AS ENUM ('IMPORTED', 'ASSIGNED', 'GEOCODED', 'ROUTE_STARTED', 'ARRIVED', 'DELIVERED', 'FAILED', 'RESCHEDULED', 'COMMENT', 'NOTIFICATION_SENT', 'LOCATION_PING');

-- CreateEnum
CREATE TYPE "ImportStatus" AS ENUM ('PROCESSING', 'COMPLETED', 'COMPLETED_WITH_ERRORS', 'FAILED');

-- CreateEnum
CREATE TYPE "NotificationChannel" AS ENUM ('WHATSAPP', 'SYSTEM');

-- CreateEnum
CREATE TYPE "NotificationStatus" AS ENUM ('QUEUED', 'SENT', 'FAILED');

-- CreateTable
CREATE TABLE "users" (
    "id" UUID NOT NULL,
    "email" TEXT NOT NULL,
    "password_hash" TEXT NOT NULL,
    "full_name" TEXT NOT NULL,
    "role" "UserRole" NOT NULL DEFAULT 'DISPATCHER',
    "active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "clients" (
    "id" UUID NOT NULL,
    "document_number" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "phone" TEXT,
    "email" TEXT,
    "default_address" TEXT,
    "default_locality" TEXT,
    "notes" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "clients_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "drivers" (
    "id" UUID NOT NULL,
    "document_number" TEXT NOT NULL,
    "full_name" TEXT NOT NULL,
    "phone" TEXT NOT NULL,
    "vehicle_plate" TEXT,
    "vehicle_capacity_kg" DECIMAL(10,2),
    "active" BOOLEAN NOT NULL DEFAULT true,
    "last_lat" DOUBLE PRECISION,
    "last_lng" DOUBLE PRECISION,
    "last_ping_at" TIMESTAMP(3),
    "last_geom" geography(Point, 4326),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "drivers_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "driver_pings" (
    "id" BIGSERIAL NOT NULL,
    "driver_id" UUID NOT NULL,
    "route_id" UUID,
    "lat" DOUBLE PRECISION NOT NULL,
    "lng" DOUBLE PRECISION NOT NULL,
    "geom" geography(Point, 4326),
    "accuracy_m" DOUBLE PRECISION,
    "speed_kmh" DOUBLE PRECISION,
    "heading" DOUBLE PRECISION,
    "battery_pct" INTEGER,
    "recorded_at" TIMESTAMP(3) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "driver_pings_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "routes" (
    "id" UUID NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT,
    "dispatch_date" DATE NOT NULL,
    "status" "RouteStatus" NOT NULL DEFAULT 'DRAFT',
    "color" VARCHAR(7) NOT NULL,
    "driver_id" UUID,
    "total_orders" INTEGER NOT NULL DEFAULT 0,
    "delivered_count" INTEGER NOT NULL DEFAULT 0,
    "failed_count" INTEGER NOT NULL DEFAULT 0,
    "total_weight_kg" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "total_units" INTEGER NOT NULL DEFAULT 0,
    "total_items" INTEGER NOT NULL DEFAULT 0,
    "started_at" TIMESTAMP(3),
    "completed_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "routes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "orders" (
    "id" UUID NOT NULL,
    "route_id" UUID NOT NULL,
    "client_id" UUID NOT NULL,
    "document_number" TEXT NOT NULL,
    "client_name_raw" TEXT NOT NULL,
    "address" TEXT NOT NULL,
    "locality" TEXT,
    "address_normalized" TEXT,
    "lat" DOUBLE PRECISION,
    "lng" DOUBLE PRECISION,
    "geom" geography(Point, 4326),
    "geocode_status" "GeocodeStatus" NOT NULL DEFAULT 'PENDING',
    "geocode_source" "GeocodeSource",
    "geocode_score" DOUBLE PRECISION,
    "geocode_label" TEXT,
    "geocoded_at" TIMESTAMP(3),
    "weight_kg" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "units" INTEGER NOT NULL DEFAULT 0,
    "items" INTEGER NOT NULL DEFAULT 0,
    "comments" TEXT,
    "time_window_start" VARCHAR(5),
    "time_window_end" VARCHAR(5),
    "requires_appointment" BOOLEAN NOT NULL DEFAULT false,
    "status" "OrderStatus" NOT NULL DEFAULT 'PENDING',
    "sequence" INTEGER,
    "row_number" INTEGER,
    "delivered_at" TIMESTAMP(3),
    "failure_reason" TEXT,
    "received_by" TEXT,
    "received_by_document" TEXT,
    "import_batch_id" UUID,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "orders_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "delivery_proofs" (
    "id" UUID NOT NULL,
    "order_id" UUID NOT NULL,
    "driver_id" UUID,
    "type" "ProofType" NOT NULL DEFAULT 'PHOTO',
    "bucket" TEXT NOT NULL,
    "object_key" TEXT NOT NULL,
    "mime_type" TEXT NOT NULL,
    "size_bytes" INTEGER NOT NULL,
    "checksum" VARCHAR(64),
    "lat" DOUBLE PRECISION,
    "lng" DOUBLE PRECISION,
    "geom" geography(Point, 4326),
    "distance_to_target_m" DOUBLE PRECISION,
    "note" TEXT,
    "captured_at" TIMESTAMP(3) NOT NULL,
    "uploaded_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "delivery_proofs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "order_events" (
    "id" UUID NOT NULL,
    "order_id" UUID NOT NULL,
    "user_id" UUID,
    "type" "EventType" NOT NULL,
    "message" TEXT,
    "payload" JSONB,
    "lat" DOUBLE PRECISION,
    "lng" DOUBLE PRECISION,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "order_events_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "geocode_cache" (
    "id" UUID NOT NULL,
    "query_hash" VARCHAR(64) NOT NULL,
    "raw_query" TEXT NOT NULL,
    "normalized_query" TEXT NOT NULL,
    "locality" TEXT,
    "country_code" VARCHAR(2) NOT NULL DEFAULT 'co',
    "lat" DOUBLE PRECISION,
    "lng" DOUBLE PRECISION,
    "geom" geography(Point, 4326),
    "display_name" TEXT,
    "osm_type" TEXT,
    "osm_id" BIGINT,
    "osm_class" TEXT,
    "place_rank" INTEGER,
    "importance" DOUBLE PRECISION,
    "bounding_box" JSONB,
    "raw" JSONB,
    "status" "GeocodeStatus" NOT NULL DEFAULT 'PENDING',
    "hit_count" INTEGER NOT NULL DEFAULT 0,
    "last_hit_at" TIMESTAMP(3),
    "expires_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "geocode_cache_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "import_batches" (
    "id" UUID NOT NULL,
    "filename" TEXT NOT NULL,
    "sheet_name" TEXT NOT NULL,
    "dispatch_date" DATE NOT NULL,
    "status" "ImportStatus" NOT NULL DEFAULT 'PROCESSING',
    "total_rows" INTEGER NOT NULL DEFAULT 0,
    "imported_rows" INTEGER NOT NULL DEFAULT 0,
    "skipped_rows" INTEGER NOT NULL DEFAULT 0,
    "failed_rows" INTEGER NOT NULL DEFAULT 0,
    "geocode_hits" INTEGER NOT NULL DEFAULT 0,
    "geocode_misses" INTEGER NOT NULL DEFAULT 0,
    "geocode_failures" INTEGER NOT NULL DEFAULT 0,
    "errors" JSONB,
    "created_by_id" UUID,
    "started_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "finished_at" TIMESTAMP(3),

    CONSTRAINT "import_batches_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "notifications" (
    "id" UUID NOT NULL,
    "route_id" UUID,
    "channel" "NotificationChannel" NOT NULL DEFAULT 'WHATSAPP',
    "status" "NotificationStatus" NOT NULL DEFAULT 'QUEUED',
    "recipient" TEXT NOT NULL,
    "template" TEXT,
    "body" TEXT NOT NULL,
    "provider_message_id" TEXT,
    "error" TEXT,
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "sent_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "notifications_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "clients_document_number_key" ON "clients"("document_number");

-- CreateIndex
CREATE INDEX "clients_name_idx" ON "clients"("name");

-- CreateIndex
CREATE UNIQUE INDEX "drivers_document_number_key" ON "drivers"("document_number");

-- CreateIndex
CREATE UNIQUE INDEX "drivers_phone_key" ON "drivers"("phone");

-- CreateIndex
CREATE INDEX "drivers_active_idx" ON "drivers"("active");

-- CreateIndex
CREATE INDEX "driver_pings_driver_id_recorded_at_idx" ON "driver_pings"("driver_id", "recorded_at");

-- CreateIndex
CREATE INDEX "driver_pings_route_id_recorded_at_idx" ON "driver_pings"("route_id", "recorded_at");

-- CreateIndex
CREATE INDEX "routes_dispatch_date_status_idx" ON "routes"("dispatch_date", "status");

-- CreateIndex
CREATE INDEX "routes_driver_id_dispatch_date_idx" ON "routes"("driver_id", "dispatch_date");

-- CreateIndex
CREATE UNIQUE INDEX "routes_code_dispatch_date_key" ON "routes"("code", "dispatch_date");

-- CreateIndex
CREATE INDEX "orders_status_idx" ON "orders"("status");

-- CreateIndex
CREATE INDEX "orders_geocode_status_idx" ON "orders"("geocode_status");

-- CreateIndex
CREATE INDEX "orders_client_id_idx" ON "orders"("client_id");

-- CreateIndex
CREATE UNIQUE INDEX "orders_route_id_document_number_key" ON "orders"("route_id", "document_number");

-- CreateIndex
CREATE INDEX "delivery_proofs_order_id_idx" ON "delivery_proofs"("order_id");

-- CreateIndex
CREATE UNIQUE INDEX "delivery_proofs_order_id_checksum_key" ON "delivery_proofs"("order_id", "checksum");

-- CreateIndex
CREATE INDEX "order_events_order_id_created_at_idx" ON "order_events"("order_id", "created_at");

-- CreateIndex
CREATE UNIQUE INDEX "geocode_cache_query_hash_key" ON "geocode_cache"("query_hash");

-- CreateIndex
CREATE INDEX "geocode_cache_status_idx" ON "geocode_cache"("status");

-- CreateIndex
CREATE INDEX "geocode_cache_expires_at_idx" ON "geocode_cache"("expires_at");

-- CreateIndex
CREATE INDEX "import_batches_dispatch_date_idx" ON "import_batches"("dispatch_date");

-- CreateIndex
CREATE INDEX "notifications_status_created_at_idx" ON "notifications"("status", "created_at");

-- AddForeignKey
ALTER TABLE "driver_pings" ADD CONSTRAINT "driver_pings_driver_id_fkey" FOREIGN KEY ("driver_id") REFERENCES "drivers"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "driver_pings" ADD CONSTRAINT "driver_pings_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "routes"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "routes" ADD CONSTRAINT "routes_driver_id_fkey" FOREIGN KEY ("driver_id") REFERENCES "drivers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "orders" ADD CONSTRAINT "orders_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "routes"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "orders" ADD CONSTRAINT "orders_client_id_fkey" FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "orders" ADD CONSTRAINT "orders_import_batch_id_fkey" FOREIGN KEY ("import_batch_id") REFERENCES "import_batches"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "delivery_proofs" ADD CONSTRAINT "delivery_proofs_order_id_fkey" FOREIGN KEY ("order_id") REFERENCES "orders"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "delivery_proofs" ADD CONSTRAINT "delivery_proofs_driver_id_fkey" FOREIGN KEY ("driver_id") REFERENCES "drivers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_events" ADD CONSTRAINT "order_events_order_id_fkey" FOREIGN KEY ("order_id") REFERENCES "orders"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_events" ADD CONSTRAINT "order_events_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "import_batches" ADD CONSTRAINT "import_batches_created_by_id_fkey" FOREIGN KEY ("created_by_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "routes"("id") ON DELETE SET NULL ON UPDATE CASCADE;

