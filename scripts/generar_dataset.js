// Genera el dataset "crudo" de viajes de CG CARGA con imperfecciones reales
// (nulos, duplicados, formatos mixtos, atipicos) para demostrar la limpieza.
const fs = require('fs');
const path = require('path');

let seed = 20260918;
function rnd() { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; }
function pick(a) { return a[Math.floor(rnd() * a.length)]; }
function gauss(mu, sd) {
  const u = Math.max(rnd(), 1e-9), v = Math.max(rnd(), 1e-9);
  return mu + sd * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

const RUTAS = [
  ['Bogota', 'Medellin', 415], ['Bogota', 'Cali', 460], ['Bogota', 'Barranquilla', 995],
  ['Medellin', 'Cartagena', 640], ['Cali', 'Buenaventura', 120], ['Bogota', 'Bucaramanga', 395],
  ['Medellin', 'Bogota', 415], ['Barranquilla', 'Santa Marta', 95], ['Cali', 'Medellin', 420],
  ['Bogota', 'Villavicencio', 125], ['Bucaramanga', 'Cucuta', 200], ['Cartagena', 'Bogota', 1050],
];
const VEHICULOS = [
  { tipo: 'Turbo', cap: 4.5, tarifa: 2100 },
  { tipo: 'Sencillo', cap: 9, tarifa: 2950 },
  { tipo: 'Doble troque', cap: 16, tarifa: 3900 },
  { tipo: 'Tractomula', cap: 32, tarifa: 5400 },
];
const CONDUCTORES = [
  'Luis Ramirez', 'Andres Gomez', 'Carlos Pena', 'Jorge Muñoz', 'Diego Salazar',
  'Wilson Ortiz', 'Fabian Rojas', 'Hector Vargas', 'Mauricio Leon', 'Julian Castro',
];
const ESTADOS = ['Entregado', 'Entregado', 'Entregado', 'Entregado', 'En ruta', 'Cancelado'];

function fechaMixta(d) {
  const y = d.getFullYear(), m = String(d.getMonth() + 1).padStart(2, '0'), day = String(d.getDate()).padStart(2, '0');
  const r = rnd();
  if (r < 0.70) return `${y}-${m}-${day}`;
  if (r < 0.90) return `${day}/${m}/${y}`;
  return `${day}-${m}-${y}`;
}

const filas = [];
const inicio = new Date('2026-01-06');
for (let i = 1; i <= 520; i++) {
  const [origen, destino, kmBase] = pick(RUTAS);
  const veh = pick(VEHICULOS);
  const fecha = new Date(inicio.getTime() + Math.floor(rnd() * 250) * 86400000);
  const km = Math.max(40, Math.round(gauss(kmBase, kmBase * 0.06)));
  const peso = Math.max(0.8, +(gauss(veh.cap * 0.78, veh.cap * 0.16)).toFixed(1));
  const costo = Math.round((km * veh.tarifa + peso * 42000 + gauss(0, 110000)) / 1000) * 1000;
  const galones = Math.max(4, +(km / gauss(9.2 - veh.cap * 0.12, 0.5)).toFixed(1));
  const horas = +(km / gauss(46, 4) + gauss(1.6, 0.5)).toFixed(1);

  let f = {
    id_viaje: 'CG-' + String(1000 + i),
    fecha: fechaMixta(fecha),
    conductor: pick(CONDUCTORES),
    ciudad_origen: origen,
    ciudad_destino: destino,
    tipo_vehiculo: veh.tipo,
    distancia_km: String(km),
    peso_toneladas: String(peso),
    costo_flete: String(costo),
    combustible_gal: String(galones),
    duracion_horas: String(horas),
    estado: pick(ESTADOS),
  };

  // --- Imperfecciones controladas para la fase de limpieza ---
  const r = rnd();
  if (r < 0.055) f.costo_flete = '';                                   // nulos en costo
  else if (r < 0.085) f.peso_toneladas = '';                           // nulos en peso
  else if (r < 0.105) f.distancia_km = '-' + f.distancia_km;           // distancia negativa
  else if (r < 0.125) f.costo_flete = String(Number(f.costo_flete) * 14); // atipico extremo
  else if (r < 0.150) f.duracion_horas = '';                           // nulos en duracion

  if (rnd() < 0.18) f.ciudad_origen = '  ' + f.ciudad_origen.toUpperCase() + ' ';
  if (rnd() < 0.14) f.ciudad_destino = f.ciudad_destino.toLowerCase();
  if (rnd() < 0.20) f.conductor = f.conductor.toUpperCase();
  if (rnd() < 0.22 && f.costo_flete) {
    f.costo_flete = '$ ' + Number(f.costo_flete).toLocaleString('es-CO'); // formato moneda
  }
  filas.push(f);
}

// Duplicados exactos (registros reenviados por la app movil)
for (let i = 0; i < 34; i++) filas.push({ ...filas[Math.floor(rnd() * filas.length)] });

// Mezcla para que los duplicados no queden contiguos
for (let i = filas.length - 1; i > 0; i--) {
  const j = Math.floor(rnd() * (i + 1));
  [filas[i], filas[j]] = [filas[j], filas[i]];
}

const cols = Object.keys(filas[0]);
const csv = [cols.join(',')].concat(
  filas.map(f => cols.map(c => {
    const v = String(f[c] ?? '');
    return /[",]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }).join(','))
).join('\n');

const out = path.join(__dirname, '..', 'analitica', 'data', 'viajes_cg_carga.csv');
fs.writeFileSync(out, csv + '\n', 'utf8');
console.log('Filas generadas:', filas.length, '->', out);
