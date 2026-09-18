/* Genera el dataset de practica para la evidencia AA2-EV03.
   Ventas de una tienda de tecnologia, con imperfecciones deliberadas
   (duplicados, nulos, formatos mixtos, valores fuera de dominio y atipicos)
   para que la etapa de limpieza con la IA tenga algo real que corregir. */
const fs = require('fs');
const path = require('path');

let semilla = 20260918;
function rnd() { semilla = (semilla * 1103515245 + 12345) & 0x7fffffff; return semilla / 0x7fffffff; }
function elegir(a) { return a[Math.floor(rnd() * a.length)]; }
function normal(mu, sd) {
  const u = Math.max(rnd(), 1e-9), v = Math.max(rnd(), 1e-9);
  return mu + sd * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

const CIUDADES = ['Bogota', 'Medellin', 'Cali', 'Barranquilla', 'Bucaramanga', 'Cartagena', 'Pereira'];
const CATALOGO = [
  { cat: 'Computadores', prod: 'Portatil 14 pulgadas', precio: 2450000 },
  { cat: 'Computadores', prod: 'Portatil gamer', precio: 4890000 },
  { cat: 'Computadores', prod: 'Todo en uno 24', precio: 2190000 },
  { cat: 'Perifericos', prod: 'Teclado mecanico', precio: 289000 },
  { cat: 'Perifericos', prod: 'Mouse inalambrico', precio: 96000 },
  { cat: 'Perifericos', prod: 'Monitor 27 pulgadas', precio: 1090000 },
  { cat: 'Audio', prod: 'Audifonos bluetooth', precio: 349000 },
  { cat: 'Audio', prod: 'Parlante portatil', precio: 259000 },
  { cat: 'Audio', prod: 'Microfono USB', precio: 419000 },
  { cat: 'Almacenamiento', prod: 'Disco SSD 1 TB', precio: 389000 },
  { cat: 'Almacenamiento', prod: 'Memoria USB 128 GB', precio: 79000 },
  { cat: 'Accesorios', prod: 'Base refrigerante', precio: 139000 },
  { cat: 'Accesorios', prod: 'Cargador universal', precio: 119000 },
  { cat: 'Accesorios', prod: 'Maletin para portatil', precio: 169000 },
];
const PAGOS = ['Tarjeta credito', 'Tarjeta debito', 'Efectivo', 'Transferencia', 'PSE'];

function fechaMixta(d) {
  const y = d.getFullYear(), m = String(d.getMonth() + 1).padStart(2, '0'), dd = String(d.getDate()).padStart(2, '0');
  const r = rnd();
  if (r < 0.68) return `${y}-${m}-${dd}`;
  if (r < 0.89) return `${dd}/${m}/${y}`;
  return `${dd}-${m}-${y}`;
}

const filas = [];
const inicio = new Date('2026-01-05');
for (let i = 1; i <= 480; i++) {
  const art = elegir(CATALOGO);
  const fecha = new Date(inicio.getTime() + Math.floor(rnd() * 250) * 86400000);
  // El descuento impulsa las unidades vendidas: esa es la relacion que
  // debera encontrar la regresion lineal.
  const descuento = Math.round(Math.max(0, Math.min(40, normal(17, 11))));
  const unidades = Math.max(1, Math.round(2 + 0.22 * descuento + normal(0, 1.1)));
  const total = Math.round(unidades * art.precio * (1 - descuento / 100));

  let f = {
    id_venta: 'V-' + String(1000 + i),
    fecha: fechaMixta(fecha),
    ciudad: elegir(CIUDADES),
    categoria: art.cat,
    producto: art.prod,
    unidades: String(unidades),
    precio_unitario: String(art.precio),
    descuento_pct: String(descuento),
    total: String(total),
    metodo_pago: elegir(PAGOS),
    calificacion_cliente: String(Math.max(1, Math.min(5, Math.round(normal(4.1, 0.9))))),
  };

  // --- Imperfecciones controladas ---
  const r = rnd();
  if (r < 0.050) f.total = '';                                     // nulos en total
  else if (r < 0.080) f.precio_unitario = '';                      // nulos en precio
  else if (r < 0.100) f.unidades = '-' + f.unidades;               // unidades negativas
  else if (r < 0.120) f.total = String(Number(f.total) * 12);       // atipico extremo
  else if (r < 0.150) f.calificacion_cliente = '';                 // nulos en calificacion

  if (rnd() < 0.18) f.ciudad = '  ' + f.ciudad.toUpperCase() + ' ';
  if (rnd() < 0.14) f.categoria = f.categoria.toLowerCase();
  if (rnd() < 0.12) f.metodo_pago = f.metodo_pago.toUpperCase();
  if (rnd() < 0.22 && f.total) f.total = '$ ' + Number(f.total).toLocaleString('es-CO');
  if (rnd() < 0.10 && f.precio_unitario) f.precio_unitario = '$' + Number(f.precio_unitario).toLocaleString('es-CO');

  filas.push(f);
}

// Duplicados exactos (ventas registradas dos veces en la caja)
for (let i = 0; i < 31; i++) filas.push({ ...filas[Math.floor(rnd() * filas.length)] });

// Mezcla para que los duplicados no queden contiguos
for (let i = filas.length - 1; i > 0; i--) {
  const j = Math.floor(rnd() * (i + 1));
  [filas[i], filas[j]] = [filas[j], filas[i]];
}

const cols = Object.keys(filas[0]);
const csv = [cols.join(',')].concat(
  filas.map((f) => cols.map((c) => {
    const v = String(f[c] ?? '');
    return /[",]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }).join(','))
).join('\n');

const salida = path.join(__dirname, '..', 'datos', 'ventas_tienda_tecnologia.csv');
fs.writeFileSync(salida, csv + '\n', 'utf8');
console.log('Filas:', filas.length, '->', salida);
