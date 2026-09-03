import { PrismaClient, UserRole } from '@prisma/client';
import { hash } from 'bcryptjs';
import { colorForRoute } from '../src/modules/import/route-color';

const prisma = new PrismaClient();

/** Datos minimos para levantar el dashboard sin tener el Excel a la mano. */
async function main(): Promise<void> {
  const admin = await prisma.user.upsert({
    where: { email: 'admin@cgcarga.co' },
    create: {
      email: 'admin@cgcarga.co',
      passwordHash: await hash('cgcarga2026', 10),
      fullName: 'Administrador CG CARGA',
      role: UserRole.ADMIN,
    },
    update: {},
  });

  const driver = await prisma.driver.upsert({
    where: { documentNumber: '1032456789' },
    create: {
      documentNumber: '1032456789',
      fullName: 'Carlos Ramirez',
      phone: '573001112233',
      vehiclePlate: 'SXY123',
      vehicleCapacityKg: 3500,
    },
    update: {},
  });

  const dispatchDate = new Date(Date.UTC(2026, 8, 3)); // 2026-09-03

  const demo = [
    { route: '1', doc: '900123456', name: 'SUPERMERCADO LA 68', address: 'Carrera 68 24-35', locality: 'Bogota', lat: 4.6395, lng: -74.1004, weight: 320.5, units: 42, items: 12, comments: 'ENTREGAR DE 8:00 A 12:00' },
    { route: '1', doc: '830987654', name: 'DISTRIBUIDORA EL SOL', address: 'Calle 13 65-20', locality: 'Bogota', lat: 4.6238, lng: -74.1119, weight: 140.0, units: 18, items: 5, comments: 'CITA 10:30 - MUELLE 4' },
    { route: '2', doc: '901555222', name: 'MINIMERCADO NORTE', address: 'Calle 170 54-30', locality: 'Bogota', lat: 4.7461, lng: -74.0475, weight: 88.25, units: 9, items: 3, comments: 'RECIBEN DE 7 AM A 3 PM' },
    { route: '2', doc: '860111333', name: 'ALMACEN CENTRAL', address: 'Avenida Suba 116-40', locality: 'Bogota', lat: 4.7003, lng: -74.0736, weight: 512.75, units: 61, items: 20, comments: 'SOLO ANTES DE LAS 11' },
    { route: '3', doc: '901777888', name: 'BODEGA SOACHA', address: 'Autopista Sur 45-10', locality: 'Soacha', lat: 4.5794, lng: -74.2168, weight: 1020.0, units: 130, items: 34, comments: 'LLAMAR AL LLEGAR' },
  ];

  for (const item of demo) {
    const route = await prisma.route.upsert({
      where: { code_dispatchDate: { code: item.route, dispatchDate } },
      create: { code: item.route, dispatchDate, color: colorForRoute(item.route), driverId: driver.id },
      update: {},
    });

    const client = await prisma.client.upsert({
      where: { documentNumber: item.doc },
      create: { documentNumber: item.doc, name: item.name, defaultAddress: item.address, defaultLocality: item.locality },
      update: {},
    });

    await prisma.order.upsert({
      where: { routeId_documentNumber: { routeId: route.id, documentNumber: item.doc } },
      create: {
        routeId: route.id,
        clientId: client.id,
        documentNumber: item.doc,
        clientNameRaw: item.name,
        address: item.address,
        locality: item.locality,
        lat: item.lat,
        lng: item.lng,
        geocodeStatus: 'RESOLVED',
        geocodeSource: 'MANUAL',
        weightKg: item.weight,
        units: item.units,
        items: item.items,
        comments: item.comments,
      },
      update: {},
    });
  }

  // Totales por ruta
  for (const route of await prisma.route.findMany({ where: { dispatchDate } })) {
    const agg = await prisma.order.aggregate({
      where: { routeId: route.id },
      _count: { _all: true },
      _sum: { weightKg: true, units: true, items: true },
    });
    await prisma.route.update({
      where: { id: route.id },
      data: {
        totalOrders: agg._count._all,
        totalWeightKg: agg._sum.weightKg ?? 0,
        totalUnits: agg._sum.units ?? 0,
        totalItems: agg._sum.items ?? 0,
      },
    });
  }

  console.log(`Seed listo. Admin: ${admin.email} / cgcarga2026`);
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
