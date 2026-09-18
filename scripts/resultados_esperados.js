/* Calcula los resultados de referencia del dataset, para poder verificar
   que lo que responde la IA en el video es correcto. */
const fs = require('fs'), path = require('path');
const txt = fs.readFileSync(path.join(__dirname, '..', 'datos', 'ventas_tienda_tecnologia.csv'), 'utf8');

const lineas = txt.trim().split(/\r?\n/);
const cols = lineas[0].split(',');
const crudo = lineas.slice(1).map((l) => {
  const celdas = []; let act = '', dentro = false;
  for (let i = 0; i < l.length; i++) {
    const ch = l[i];
    if (ch === '"') { if (dentro && l[i + 1] === '"') { act += '"'; i++; } else dentro = !dentro; }
    else if (ch === ',' && !dentro) { celdas.push(act); act = ''; } else act += ch;
  }
  celdas.push(act);
  const o = {}; cols.forEach((c, i) => (o[c] = celdas[i] ?? '')); return o;
});

const num = (v) => {
  const s = String(v ?? '').replace(/[^0-9,.\-]/g, '').replace(/\.(?=\d{3}\b)/g, '').replace(',', '.');
  if (s === '' || s === '-') return null;
  const n = Number(s); return Number.isFinite(n) ? n : null;
};
const titulo = (s) => String(s ?? '').trim().replace(/\s+/g, ' ').toLowerCase().replace(/(^|\s)\p{L}/gu, (c) => c.toUpperCase());
const media = (a) => a.reduce((x, y) => x + y, 0) / a.length;
const desv = (a) => { const m = media(a); return Math.sqrt(media(a.map((x) => (x - m) ** 2))); };
const cuantil = (arr, q) => {
  const a = [...arr].sort((x, y) => x - y), p = (a.length - 1) * q, b = Math.floor(p), r = p - b;
  return a[b + 1] !== undefined ? a[b] + r * (a[b + 1] - a[b]) : a[b];
};

console.log('=== DIAGNOSTICO DEL DATASET CRUDO ===');
console.log('Registros:', crudo.length, '| Columnas:', cols.length);
const vacias = cols.map((c) => [c, crudo.filter((f) => String(f[c]).trim() === '').length]).filter(([, n]) => n);
console.log('Celdas vacias por columna:', vacias.map(([c, n]) => `${c}=${n}`).join(', '));
console.log('Total celdas vacias:', vacias.reduce((s, [, n]) => s + n, 0));
const ids = crudo.map((f) => f.id_venta);
console.log('IDs duplicados:', ids.length - new Set(ids).size);
console.log('Unidades negativas:', crudo.filter((f) => num(f.unidades) < 0).length);
console.log('Variantes de "ciudad":', new Set(crudo.map((f) => f.ciudad)).size, '-> normalizadas:', new Set(crudo.map((f) => titulo(f.ciudad))).size);
console.log('Variantes de "categoria":', new Set(crudo.map((f) => f.categoria)).size, '-> normalizadas:', new Set(crudo.map((f) => titulo(f.categoria))).size);
console.log('Formatos de fecha detectados: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY');
console.log('Totales escritos como moneda ($ 1.234.500):', crudo.filter((f) => /\$/.test(f.total)).length);

console.log('\n=== LIMPIEZA PASO A PASO ===');
let d = crudo.map((f) => ({ ...f }));
const vistos = new Set(); let n0 = d.length;
d = d.filter((f) => (vistos.has(f.id_venta) ? false : (vistos.add(f.id_venta), true)));
console.log('R1 deduplicacion por id_venta:', n0 - d.length, 'eliminados ->', d.length);

d.forEach((f) => { f.ciudad = titulo(f.ciudad); f.categoria = titulo(f.categoria); f.metodo_pago = titulo(f.metodo_pago); });
console.log('R2 normalizacion de texto: ciudad, categoria y metodo_pago homologados');

d.forEach((f) => {
  f.unidades = num(f.unidades); f.precio_unitario = num(f.precio_unitario);
  f.descuento_pct = num(f.descuento_pct); f.total = num(f.total);
  f.calificacion_cliente = num(f.calificacion_cliente);
});
console.log('R3 conversion de tipos: montos y fechas a formato unico');

n0 = d.length; d = d.filter((f) => !(f.unidades !== null && f.unidades <= 0));
console.log('R4 validacion de dominio (unidades <= 0):', n0 - d.length, 'eliminados ->', d.length);

n0 = d.length; d = d.filter((f) => f.total !== null && f.unidades !== null && f.descuento_pct !== null);
const sinCrit = n0 - d.length;
const cal = d.map((f) => f.calificacion_cliente).filter((v) => v !== null);
const pre = d.map((f) => f.precio_unitario).filter((v) => v !== null);
const medCal = cuantil(cal, 0.5), medPre = cuantil(pre, 0.5);
let imp = 0;
d.forEach((f) => {
  if (f.calificacion_cliente === null) { f.calificacion_cliente = medCal; imp++; }
  if (f.precio_unitario === null) { f.precio_unitario = medPre; imp++; }
});
console.log('R5 nulos criticos eliminados:', sinCrit, '| valores imputados con la mediana:', imp, '->', d.length);

const tot = d.map((f) => f.total);
const q1 = cuantil(tot, 0.25), q3 = cuantil(tot, 0.75), iqr = q3 - q1, lim = q3 + 1.5 * iqr;
n0 = d.length; d = d.filter((f) => f.total <= lim);
console.log('R6 atipicos IQR: Q1=' + Math.round(q1), 'Q3=' + Math.round(q3), 'limite=' + Math.round(lim), '|', n0 - d.length, 'eliminados ->', d.length);
console.log('RETENCION FINAL:', d.length, 'de', crudo.length, '=', (d.length / crudo.length * 100).toFixed(1) + ' %');

console.log('\n=== SEGMENTACION POR CATEGORIA ===');
const g = {}; d.forEach((f) => (g[f.categoria] ??= []).push(f));
Object.entries(g).sort((a, b) => b[1].length - a[1].length).forEach(([k, v]) => {
  console.log(`${k.padEnd(16)} ventas=${String(v.length).padStart(3)} ingreso=${Math.round(v.reduce((s, f) => s + f.total, 0)).toLocaleString('es-CO').padStart(12)} ticket=${Math.round(media(v.map((f) => f.total))).toLocaleString('es-CO').padStart(10)} desc_prom=${media(v.map((f) => f.descuento_pct)).toFixed(1)}%`);
});

console.log('\n=== REGRESION LINEAL: unidades ~ descuento_pct ===');
const x = d.map((f) => f.descuento_pct), y = d.map((f) => f.unidades);
const mx = media(x), my = media(y);
let sxy = 0, sxx = 0;
for (let i = 0; i < x.length; i++) { sxy += (x[i] - mx) * (y[i] - my); sxx += (x[i] - mx) ** 2; }
const b1 = sxy / sxx, b0 = my - b1 * mx;
const pred = x.map((v) => b0 + b1 * v);
const ssRes = y.reduce((s, v, i) => s + (v - pred[i]) ** 2, 0);
const ssTot = y.reduce((s, v) => s + (v - my) ** 2, 0);
const r2 = 1 - ssRes / ssTot, r = sxy / (Math.sqrt(sxx) * Math.sqrt(ssTot));
console.log(`n = ${d.length}`);
console.log(`unidades = ${b0.toFixed(4)} + ${b1.toFixed(4)} * descuento_pct`);
console.log(`R2 = ${r2.toFixed(4)} | r de Pearson = ${r.toFixed(4)} | RMSE = ${Math.sqrt(ssRes / y.length).toFixed(3)} unidades`);
[0, 10, 20, 30, 40].forEach((k) => console.log(`  descuento ${String(k).padStart(2)}% -> ${(b0 + b1 * k).toFixed(2)} unidades estimadas`));

console.log('\n=== K-MEANS (k=3) sobre total, unidades y descuento_pct estandarizados ===');
const vars = ['total', 'unidades', 'descuento_pct'];
const mu = {}, sd = {};
vars.forEach((v) => { const a = d.map((f) => f[v]); mu[v] = media(a); sd[v] = desv(a) || 1; });
const X = d.map((f) => vars.map((v) => (f[v] - mu[v]) / sd[v]));
const k = 3;
let cent = []; for (let i = 0; i < k; i++) cent.push([...X[Math.floor((i * X.length) / k)]]);
let asig = new Array(X.length).fill(0), it = 0;
for (; it < 80; it++) {
  let cambio = false;
  X.forEach((p, i) => {
    let mejor = 0, dm = Infinity;
    cent.forEach((c, j) => { const dd = c.reduce((s, cv, q) => s + (p[q] - cv) ** 2, 0); if (dd < dm) { dm = dd; mejor = j; } });
    if (asig[i] !== mejor) { asig[i] = mejor; cambio = true; }
  });
  cent = cent.map((_, j) => {
    const m = X.filter((_, i) => asig[i] === j);
    return m.length ? vars.map((_, q) => media(m.map((p) => p[q]))) : cent[j];
  });
  if (!cambio) break;
}
const inercia = X.reduce((s, p, i) => s + cent[asig[i]].reduce((t, cv, q) => t + (p[q] - cv) ** 2, 0), 0);
console.log(`Convergencia en ${it + 1} iteraciones | inercia total = ${inercia.toFixed(2)}`);
cent.map((_, j) => d.filter((_, i) => asig[i] === j))
  .map((gr, j) => ({ j, n: gr.length, total: media(gr.map((f) => f.total)), un: media(gr.map((f) => f.unidades)), de: media(gr.map((f) => f.descuento_pct)) }))
  .sort((a, b) => a.total - b.total)
  .forEach((c, i) => console.log(`Cluster ${i + 1}: ${String(c.n).padStart(3)} ventas | ticket ${Math.round(c.total).toLocaleString('es-CO').padStart(10)} | ${c.un.toFixed(1)} unidades | ${c.de.toFixed(1)} % de descuento`));
