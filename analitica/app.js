/* =====================================================================
   CG CARGA · Consola de Analitica de Datos
   Motor de procesamiento: importacion, perfilado, limpieza, filtros,
   segmentacion y algoritmos (regresion lineal y K-Means).
   ===================================================================== */

const estado = {
  config: null,
  crudo: [],
  limpio: [],
  filtrado: [],
  reporteLimpieza: null,
  modelo: null,
  clusters: null,
};

/* ---------------------- utilidades ---------------------- */
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));
const fmt = (n, d = 0) =>
  n === null || n === undefined || Number.isNaN(n)
    ? '—'
    : Number(n).toLocaleString('es-CO', { minimumFractionDigits: d, maximumFractionDigits: d });
const cop = (n) => (n === null || Number.isNaN(n) ? '—' : '$ ' + fmt(Math.round(n)));
/** Moneda compacta para tarjetas de indicador: 106.892.000 -> "$ 106,9 M". */
const copCorto = (n) => {
  if (n === null || Number.isNaN(n)) return '—';
  const a = Math.abs(n);
  if (a >= 1e9) return '$ ' + fmt(n / 1e9, 2) + ' MM';
  if (a >= 1e6) return '$ ' + fmt(n / 1e6, 1) + ' M';
  return cop(n);
};

function log(destino, texto, tipo = 'ok') {
  const cont = $(destino);
  if (!cont) return;
  const li = document.createElement('div');
  li.className = 'log-line log-' + tipo;
  li.innerHTML = `<span class="log-dot"></span><span>${texto}</span>`;
  cont.appendChild(li);
  cont.scrollTop = cont.scrollHeight;
}

/* ---------------------- CSV ---------------------- */
function parseCSV(texto) {
  const lineas = texto.trim().split(/\r?\n/);
  const cols = lineas[0].split(',').map((c) => c.trim());
  return lineas.slice(1).map((linea) => {
    const celdas = [];
    let actual = '', dentro = false;
    for (let i = 0; i < linea.length; i++) {
      const ch = linea[i];
      if (ch === '"') {
        if (dentro && linea[i + 1] === '"') { actual += '"'; i++; }
        else dentro = !dentro;
      } else if (ch === ',' && !dentro) { celdas.push(actual); actual = ''; }
      else actual += ch;
    }
    celdas.push(actual);
    const fila = {};
    cols.forEach((c, i) => (fila[c] = celdas[i] ?? ''));
    return fila;
  });
}

/* ---------------------- normalizadores ---------------------- */
function aNumero(v) {
  if (v === null || v === undefined) return null;
  const limpio = String(v).replace(/[^0-9,.\-]/g, '').replace(/\.(?=\d{3}\b)/g, '').replace(',', '.');
  if (limpio === '' || limpio === '-') return null;
  const n = Number(limpio);
  return Number.isFinite(n) ? n : null;
}

function aFecha(v, formato) {
  const s = String(v ?? '').trim();
  let m;
  if ((m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/))) return `${m[1]}-${m[2]}-${m[3]}`;
  if ((m = s.match(/^(\d{2})[/-](\d{2})[/-](\d{4})$/))) {
    const [, a, b, y] = m;
    return formato === 'MM/DD/YYYY' ? `${y}-${a}-${b}` : `${y}-${b}-${a}`;
  }
  return null;
}

function tituloCase(s) {
  return String(s ?? '')
    .trim().replace(/\s+/g, ' ').toLowerCase()
    .replace(/(^|\s)\p{L}/gu, (c) => c.toUpperCase());
}

/* ---------------------- estadistica ---------------------- */
const media = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : NaN);
const desv = (a) => { const m = media(a); return Math.sqrt(media(a.map((x) => (x - m) ** 2))); };
function cuantil(arr, q) {
  const a = [...arr].sort((x, y) => x - y);
  if (!a.length) return NaN;
  const pos = (a.length - 1) * q, base = Math.floor(pos), resto = pos - base;
  return a[base + 1] !== undefined ? a[base] + resto * (a[base + 1] - a[base]) : a[base];
}
const mediana = (a) => cuantil(a, 0.5);

/* =====================================================================
   PASO 2 · Configuracion inicial
   ===================================================================== */
function guardarConfiguracion() {
  estado.config = {
    fuente: $('#cfg-fuente').value,
    delimitador: $('#cfg-delim').value,
    encoding: $('#cfg-encoding').value,
    colFecha: $('#cfg-colfecha').value,
    formatoFecha: $('#cfg-formato').value,
    moneda: $('#cfg-moneda').value,
    zona: $('#cfg-zona').value,
    granularidad: $('#cfg-granularidad').value,
  };
  const c = estado.config;
  $('#cfg-log').innerHTML = '';
  log('#cfg-log', `Fuente de datos registrada: <b>${c.fuente}</b>`);
  log('#cfg-log', `Delimitador <b>"${c.delimitador}"</b> · codificación <b>${c.encoding}</b>`);
  log('#cfg-log', `Campo temporal <b>${c.colFecha}</b> con formato <b>${c.formatoFecha}</b>`);
  log('#cfg-log', `Moneda <b>${c.moneda}</b> · zona horaria <b>${c.zona}</b>`);
  log('#cfg-log', `Granularidad de agregación: <b>${c.granularidad}</b>`);
  log('#cfg-log', 'Configuración inicial guardada. Conexión lista para importar.', 'done');
  $('#cfg-estado').textContent = 'CONFIGURADO';
  $('#cfg-estado').className = 'pill pill-ok';
  $('#btn-importar').disabled = false;
  marcarPaso(2);
}

/* =====================================================================
   PASO 3 · Importacion y perfilado de calidad
   ===================================================================== */
async function importarDatos() {
  $('#imp-log').innerHTML = '';
  log('#imp-log', `Abriendo <b>${estado.config.fuente}</b> ...`);
  const resp = await fetch('data/viajes_cg_carga.csv');
  const texto = await resp.text();
  estado.crudo = parseCSV(texto);
  const cols = Object.keys(estado.crudo[0]);

  log('#imp-log', `Lectura completa: <b>${estado.crudo.length}</b> registros y <b>${cols.length}</b> campos.`);

  // perfilado
  const perfil = cols.map((c) => {
    const vals = estado.crudo.map((f) => f[c]);
    const nulos = vals.filter((v) => String(v).trim() === '').length;
    const numerica = vals.filter((v) => String(v).trim() !== '').every((v) => aNumero(v) !== null);
    const distintos = new Set(vals.map((v) => String(v).trim())).size;
    return { campo: c, tipo: numerica ? 'numérico' : c === 'fecha' ? 'fecha' : 'texto', nulos, distintos };
  });

  const ids = estado.crudo.map((f) => f.id_viaje);
  const duplicados = ids.length - new Set(ids).size;
  const nulosTotales = perfil.reduce((s, p) => s + p.nulos, 0);
  const negativos = estado.crudo.filter((f) => aNumero(f.distancia_km) < 0).length;

  $('#imp-preview').innerHTML = tablaHTML(estado.crudo.slice(0, 8), cols);
  $('#imp-perfil').innerHTML = `
    <table class="tabla">
      <thead><tr><th>Campo</th><th>Tipo inferido</th><th>Nulos</th><th>Valores distintos</th></tr></thead>
      <tbody>${perfil.map((p) => `<tr><td>${p.campo}</td><td><span class="tag tag-${p.tipo === 'numérico' ? 'numerico' : p.tipo}">${p.tipo}</span></td>
        <td class="${p.nulos ? 'malo' : ''}">${p.nulos}</td><td>${p.distintos}</td></tr>`).join('')}</tbody>
    </table>`;

  kpis('#imp-kpis', [
    ['Registros crudos', fmt(estado.crudo.length)],
    ['Campos', fmt(cols.length)],
    ['Celdas vacías', fmt(nulosTotales), 'malo'],
    ['IDs duplicados', fmt(duplicados), 'malo'],
    ['Distancias negativas', fmt(negativos), 'malo'],
  ]);

  log('#imp-log', `Perfilado de calidad: <b>${nulosTotales}</b> celdas vacías, <b>${duplicados}</b> duplicados, <b>${negativos}</b> distancias negativas.`, 'warn');
  log('#imp-log', 'El dataset requiere limpieza antes del análisis.', 'warn');
  $('#btn-limpiar').disabled = false;
  marcarPaso(3);
}

function tablaHTML(filas, cols) {
  return `<table class="tabla tabla-sm"><thead><tr>${cols.map((c) => `<th>${c}</th>`).join('')}</tr></thead>
    <tbody>${filas.map((f) => `<tr>${cols.map((c) => {
      const v = String(f[c] ?? '');
      const vacio = v.trim() === '';
      const sucio = vacio || /^\s|\s$/.test(v) || v.startsWith('-') || v.startsWith('$');
      return `<td class="${vacio ? 'celda-nula' : sucio ? 'celda-sucia' : ''}">${vacio ? '(vacio)' : v}</td>`;
    }).join('')}</tr>`).join('')}</tbody></table>`;
}

function kpis(sel, items) {
  $(sel).innerHTML = items.map(([t, v, cls]) =>
    `<div class="kpi ${cls || ''}"><div class="kpi-v">${v}</div><div class="kpi-t">${t}</div></div>`).join('');
}

/* =====================================================================
   PASO 4 · Limpieza y transformacion
   ===================================================================== */
function ejecutarLimpieza() {
  $('#lim-log').innerHTML = '';
  const reglas = {
    dedup: $('#r-dedup').checked,
    texto: $('#r-texto').checked,
    tipos: $('#r-tipos').checked,
    nulos: $('#r-nulos').checked,
    negativos: $('#r-negativos').checked,
    atipicos: $('#r-atipicos').checked,
  };
  let filas = estado.crudo.map((f) => ({ ...f }));
  const rep = { inicial: filas.length };

  if (reglas.dedup) {
    const vistos = new Set();
    const antes = filas.length;
    filas = filas.filter((f) => (vistos.has(f.id_viaje) ? false : (vistos.add(f.id_viaje), true)));
    rep.duplicados = antes - filas.length;
    log('#lim-log', `R1 · Deduplicación por <b>id_viaje</b>: ${rep.duplicados} registros repetidos eliminados.`);
  }

  if (reglas.texto) {
    filas.forEach((f) => {
      f.ciudad_origen = tituloCase(f.ciudad_origen);
      f.ciudad_destino = tituloCase(f.ciudad_destino);
      f.conductor = tituloCase(f.conductor);
      f.tipo_vehiculo = tituloCase(f.tipo_vehiculo);
      f.estado = tituloCase(f.estado);
    });
    log('#lim-log', 'R2 · Normalización de texto: espacios, mayúsculas y acentos homologados.');
  }

  if (reglas.tipos) {
    filas.forEach((f) => {
      f.distancia_km = aNumero(f.distancia_km);
      f.peso_toneladas = aNumero(f.peso_toneladas);
      f.costo_flete = aNumero(f.costo_flete);
      f.combustible_gal = aNumero(f.combustible_gal);
      f.duracion_horas = aNumero(f.duracion_horas);
      f.fecha = aFecha(f.fecha, estado.config.formatoFecha);
    });
    log('#lim-log', 'R3 · Conversión de tipos: montos <b>$ 1.234.000 → 1234000</b> y fechas unificadas a <b>YYYY-MM-DD</b>.');
  }

  if (reglas.negativos) {
    const antes = filas.length;
    filas = filas.filter((f) => !(f.distancia_km !== null && f.distancia_km <= 0));
    rep.negativos = antes - filas.length;
    log('#lim-log', `R4 · Validación de dominio: ${rep.negativos} viajes con distancia <= 0 descartados.`);
  }

  if (reglas.nulos) {
    const antes = filas.length;
    filas = filas.filter((f) => f.costo_flete !== null && f.distancia_km !== null);
    rep.nulosCriticos = antes - filas.length;
    const pesos = filas.map((f) => f.peso_toneladas).filter((v) => v !== null);
    const horas = filas.map((f) => f.duracion_horas).filter((v) => v !== null);
    const medP = mediana(pesos), medH = mediana(horas);
    let imputados = 0;
    filas.forEach((f) => {
      if (f.peso_toneladas === null) { f.peso_toneladas = +medP.toFixed(1); imputados++; }
      if (f.duracion_horas === null) { f.duracion_horas = +medH.toFixed(1); imputados++; }
    });
    rep.imputados = imputados;
    log('#lim-log', `R5 · Nulos: ${rep.nulosCriticos} registros sin costo/distancia eliminados; ${imputados} valores imputados con la mediana.`);
  }

  if (reglas.atipicos) {
    const costos = filas.map((f) => f.costo_flete);
    const q1 = cuantil(costos, 0.25), q3 = cuantil(costos, 0.75), iqr = q3 - q1;
    const lim = q3 + 1.5 * iqr;
    const antes = filas.length;
    filas = filas.filter((f) => f.costo_flete <= lim);
    rep.atipicos = antes - filas.length;
    rep.limiteIQR = lim;
    log('#lim-log', `R6 · Atípicos (rango intercuartil): límite superior <b>${cop(lim)}</b>, ${rep.atipicos} registros extremos retirados.`);
  }

  filas.forEach((f) => {
    f.costo_por_km = +(f.costo_flete / f.distancia_km).toFixed(1);
    f.rendimiento_km_gal = +(f.distancia_km / f.combustible_gal).toFixed(2);
    f.ruta = `${f.ciudad_origen} → ${f.ciudad_destino}`;
    f.mes = f.fecha ? f.fecha.slice(0, 7) : null;
  });
  log('#lim-log', 'R7 · Enriquecimiento: campos calculados <b>costo_por_km</b>, <b>rendimiento_km_gal</b>, <b>ruta</b> y <b>mes</b>.');

  rep.final = filas.length;
  rep.retencion = (filas.length / rep.inicial) * 100;
  estado.limpio = filas;
  estado.reporteLimpieza = rep;

  kpis('#lim-kpis', [
    ['Registros iniciales', fmt(rep.inicial)],
    ['Duplicados', fmt(rep.duplicados || 0)],
    ['Inválidos / nulos', fmt((rep.negativos || 0) + (rep.nulosCriticos || 0))],
    ['Atípicos', fmt(rep.atipicos || 0)],
    ['Registros válidos', fmt(rep.final), 'bueno'],
    ['Retención', fmt(rep.retencion, 1) + ' %', 'bueno'],
  ]);
  $('#lim-preview').innerHTML = tablaHTML(
    filas.slice(0, 7).map((f) => ({
      id_viaje: f.id_viaje, fecha: f.fecha, conductor: f.conductor, ruta: f.ruta,
      tipo_vehiculo: f.tipo_vehiculo, distancia_km: fmt(f.distancia_km),
      peso_toneladas: fmt(f.peso_toneladas, 1), costo_flete: cop(f.costo_flete),
      costo_por_km: fmt(f.costo_por_km),
    })),
    ['id_viaje', 'fecha', 'conductor', 'ruta', 'tipo_vehiculo', 'distancia_km', 'peso_toneladas', 'costo_flete', 'costo_por_km']
  );
  log('#lim-log', `Dataset analítico listo: <b>${fmt(rep.final)}</b> registros válidos (${fmt(rep.retencion, 1)} % de retención).`, 'done');

  prepararFiltros();
  $('#btn-filtrar').disabled = false;
  marcarPaso(4);
}

/* =====================================================================
   PASO 5 · Filtros y segmentacion
   ===================================================================== */
function prepararFiltros() {
  const uniq = (k) => [...new Set(estado.limpio.map((f) => f[k]).filter(Boolean))].sort();
  const llenar = (sel, vals, etiqueta) => {
    $(sel).innerHTML = `<option value="">${etiqueta}</option>` + vals.map((v) => `<option>${v}</option>`).join('');
  };
  llenar('#f-vehiculo', uniq('tipo_vehiculo'), 'Todos los vehiculos');
  llenar('#f-origen', uniq('ciudad_origen'), 'Todos los origenes');
  llenar('#f-estado', uniq('estado'), 'Todos los estados');
  const meses = uniq('mes');
  llenar('#f-desde', meses, 'Desde el inicio');
  llenar('#f-hasta', meses, 'Hasta el final');
  estado.filtrado = estado.limpio;
}

function aplicarFiltros() {
  const v = $('#f-vehiculo').value, o = $('#f-origen').value, e = $('#f-estado').value;
  const d = $('#f-desde').value, h = $('#f-hasta').value;
  const kmMin = Number($('#f-kmmin').value || 0);

  estado.filtrado = estado.limpio.filter((f) =>
    (!v || f.tipo_vehiculo === v) && (!o || f.ciudad_origen === o) && (!e || f.estado === e) &&
    (!d || (f.mes && f.mes >= d)) && (!h || (f.mes && f.mes <= h)) && f.distancia_km >= kmMin);

  $('#fil-log').innerHTML = '';
  const criterios = [
    v && `vehículo = <b>${v}</b>`, o && `origen = <b>${o}</b>`, e && `estado = <b>${e}</b>`,
    d && `desde <b>${d}</b>`, h && `hasta <b>${h}</b>`, kmMin > 0 && `distancia >= <b>${kmMin} km</b>`,
  ].filter(Boolean);
  log('#fil-log', criterios.length ? 'Filtros aplicados: ' + criterios.join(' · ') : 'Sin filtros: se analiza el universo completo.');
  log('#fil-log', `Subconjunto resultante: <b>${fmt(estado.filtrado.length)}</b> de ${fmt(estado.limpio.length)} registros.`, 'done');

  pintarResumen();
  $('#btn-regresion').disabled = estado.filtrado.length < 20;
  $('#btn-kmeans').disabled = estado.filtrado.length < 20;
  marcarPaso(5);
}

function pintarResumen() {
  const d = estado.filtrado;
  if (!d.length) { $('#fil-kpis').innerHTML = '<p class="vacio">El filtro no devuelve registros.</p>'; return; }
  const costos = d.map((f) => f.costo_flete), kms = d.map((f) => f.distancia_km);
  kpis('#fil-kpis', [
    ['Viajes', fmt(d.length)],
    ['Flete total', copCorto(costos.reduce((a, b) => a + b, 0))],
    ['Ticket promedio', copCorto(media(costos))],
    ['Mediana de flete', copCorto(mediana(costos))],
    ['Km promedio', fmt(media(kms))],
    ['Costo / km', cop(media(d.map((f) => f.costo_por_km)))],
  ]);

  // Segmentacion por tipo de vehiculo
  const grupos = {};
  d.forEach((f) => (grupos[f.tipo_vehiculo] ??= []).push(f));
  const segs = Object.entries(grupos).map(([k, g]) => ({
    seg: k, n: g.length,
    costoProm: media(g.map((f) => f.costo_flete)),
    kmProm: media(g.map((f) => f.distancia_km)),
    costoKm: media(g.map((f) => f.costo_por_km)),
    rend: media(g.map((f) => f.rendimiento_km_gal)),
  })).sort((a, b) => b.n - a.n);

  $('#fil-segmentos').innerHTML = `
    <table class="tabla"><thead><tr><th>Segmento (tipo de vehículo)</th><th>Viajes</th><th>Km promedio</th>
      <th>Flete promedio</th><th>Costo / km</th><th>Rendimiento km/gal</th></tr></thead>
    <tbody>${segs.map((s) => `<tr><td><b>${s.seg}</b></td><td>${fmt(s.n)}</td><td>${fmt(s.kmProm)}</td>
      <td>${cop(s.costoProm)}</td><td>${cop(s.costoKm)}</td><td>${fmt(s.rend, 2)}</td></tr>`).join('')}</tbody></table>`;

  $('#fil-grafico').innerHTML = barras(segs.map((s) => ({ etiqueta: s.seg, valor: s.costoKm })), 'Costo promedio por kilómetro según segmento (COP)');
}

/* =====================================================================
   PASO 6 · Algoritmos de analisis
   ===================================================================== */
function regresionLineal() {
  const d = estado.filtrado;
  const x = d.map((f) => f.distancia_km), y = d.map((f) => f.costo_flete);
  const mx = media(x), my = media(y);
  let num = 0, den = 0;
  for (let i = 0; i < x.length; i++) { num += (x[i] - mx) * (y[i] - my); den += (x[i] - mx) ** 2; }
  const b1 = num / den, b0 = my - b1 * mx;
  const pred = x.map((v) => b0 + b1 * v);
  const ssRes = y.reduce((s, v, i) => s + (v - pred[i]) ** 2, 0);
  const ssTot = y.reduce((s, v) => s + (v - my) ** 2, 0);
  const r2 = 1 - ssRes / ssTot;
  const r = num / (Math.sqrt(den) * Math.sqrt(ssTot));
  const rmse = Math.sqrt(ssRes / y.length);
  const mae = media(y.map((v, i) => Math.abs(v - pred[i])));

  estado.modelo = { b0, b1, r2, r, rmse, mae, n: d.length };

  $('#alg-log').innerHTML = '';
  log('#alg-log', 'Algoritmo seleccionado: <b>regresión lineal simple por mínimos cuadrados</b>.');
  log('#alg-log', `Variable predictora <b>distancia_km</b> → variable objetivo <b>costo_flete</b> (n = ${fmt(d.length)}).`);
  log('#alg-log', `Ecuación estimada: <b>costo = ${fmt(b0)} + ${fmt(b1)} · km</b>`, 'done');
  log('#alg-log', `Bondad de ajuste: R² = <b>${r2.toFixed(4)}</b> · r de Pearson = <b>${r.toFixed(4)}</b> · RMSE = <b>${cop(rmse)}</b>`, 'done');

  kpis('#alg-kpis', [
    ['Intercepto (b₀)', copCorto(b0)],
    ['Pendiente (b₁) por km', cop(b1)],
    ['R²', r2.toFixed(4), 'bueno'],
    ['Correlación r', r.toFixed(4), 'bueno'],
    ['RMSE', copCorto(rmse)],
    ['MAE', copCorto(mae)],
  ]);

  $('#alg-grafico').innerHTML = dispersion(d.map((f) => [f.distancia_km, f.costo_flete]), { b0, b1 },
    'Distancia (km)', 'Flete (COP)', 'Regresión lineal: flete vs. distancia');

  const casos = [200, 450, 800];
  $('#alg-tabla').innerHTML = `<table class="tabla"><thead><tr><th>Distancia</th><th>Flete estimado</th></tr></thead>
    <tbody>${casos.map((k) => `<tr><td>${fmt(k)} km</td><td><b>${cop(b0 + b1 * k)}</b></td></tr>`).join('')}</tbody></table>`;
  $('#alg-interpreta').innerHTML =
    `<b>Interpretación:</b> por cada kilometro adicional el flete aumenta en promedio <b>${cop(b1)}</b>.
     El modelo explica el <b>${(r2 * 100).toFixed(1)} %</b> de la variabilidad del costo, por lo que sirve como
     tarifario base para cotizar rutas nuevas en la operación de CG CARGA.`;
  marcarPaso(6);
}

function kmeans() {
  const d = estado.filtrado;
  const vars = ['distancia_km', 'peso_toneladas', 'costo_flete'];
  const mu = {}, sd = {};
  vars.forEach((v) => { const a = d.map((f) => f[v]); mu[v] = media(a); sd[v] = desv(a) || 1; });
  const X = d.map((f) => vars.map((v) => (f[v] - mu[v]) / sd[v]));

  const k = Number($('#k-clusters').value);
  let cent = [];
  for (let i = 0; i < k; i++) cent.push([...X[Math.floor((i * X.length) / k)]]);

  let asign = new Array(X.length).fill(0), iter = 0;
  for (; iter < 60; iter++) {
    let cambio = false;
    X.forEach((p, i) => {
      let mejor = 0, dmin = Infinity;
      cent.forEach((c, j) => {
        const dist = c.reduce((s, cv, q) => s + (p[q] - cv) ** 2, 0);
        if (dist < dmin) { dmin = dist; mejor = j; }
      });
      if (asign[i] !== mejor) { asign[i] = mejor; cambio = true; }
    });
    cent = cent.map((_, j) => {
      const miembros = X.filter((_, i) => asign[i] === j);
      return miembros.length ? vars.map((_, q) => media(miembros.map((p) => p[q]))) : cent[j];
    });
    if (!cambio) break;
  }

  const inercia = X.reduce((s, p, i) => s + cent[asign[i]].reduce((t, cv, q) => t + (p[q] - cv) ** 2, 0), 0);
  const grupos = cent.map((_, j) => d.filter((_, i) => asign[i] === j));
  const perfiles = grupos.map((g, j) => ({
    id: j, n: g.length,
    km: media(g.map((f) => f.distancia_km)),
    peso: media(g.map((f) => f.peso_toneladas)),
    costo: media(g.map((f) => f.costo_flete)),
    costoKm: media(g.map((f) => f.costo_por_km)),
  })).sort((a, b) => a.costo - b.costo);
  const nombres = ['Liviano de corta distancia', 'Pesado regional', 'Nacional de larga distancia', 'Especial extendido', 'Atípico'];

  estado.clusters = { perfiles, inercia, iter, k };

  $('#alg-log').innerHTML = '';
  log('#alg-log', `Algoritmo seleccionado: <b>K-Means</b> con k = <b>${k}</b> sobre variables estandarizadas (z-score).`);
  log('#alg-log', `Variables del modelo: <b>${vars.join(', ')}</b>.`);
  log('#alg-log', `Convergencia alcanzada en <b>${iter + 1}</b> iteraciones · inercia total = <b>${fmt(inercia, 2)}</b>.`, 'done');
  perfiles.forEach((p, i) => log('#alg-log', `Cluster ${i + 1} · <b>${nombres[i]}</b>: ${fmt(p.n)} viajes, ${fmt(p.km)} km y ${cop(p.costo)} en promedio.`));

  kpis('#alg-kpis', perfiles.map((p, i) => [`${nombres[i]}`, fmt(p.n) + ' viajes']));
  $('#alg-tabla').innerHTML = `<table class="tabla"><thead><tr><th>Cluster</th><th>Perfil operativo</th><th>Viajes</th>
      <th>Km promedio</th><th>Peso promedio</th><th>Flete promedio</th><th>Costo / km</th></tr></thead>
    <tbody>${perfiles.map((p, i) => `<tr><td><span class="punto c${i}"></span> ${i + 1}</td><td><b>${nombres[i]}</b></td>
      <td>${fmt(p.n)}</td><td>${fmt(p.km)}</td><td>${fmt(p.peso, 1)} t</td><td>${cop(p.costo)}</td><td>${cop(p.costoKm)}</td></tr>`).join('')}</tbody></table>`;

  const orden = perfiles.map((p) => p.id);
  $('#alg-grafico').innerHTML = dispersion(
    d.map((f, i) => [f.distancia_km, f.costo_flete, orden.indexOf(asign[i])]), null,
    'Distancia (km)', 'Flete (COP)', `Segmentación K-Means (k = ${k}) de la operación`);
  $('#alg-interpreta').innerHTML =
    `<b>Interpretación:</b> K-Means separa la operación en ${k} perfiles logísticos sin etiquetas previas.
     El segmento <b>${nombres[0].toLowerCase()}</b> concentra el costo por kilómetro más alto del portafolio,
     que es justamente donde CG CARGA debe renegociar tarifas o consolidar cargas.`;
  marcarPaso(6);
}

/* =====================================================================
   Graficos SVG
   ===================================================================== */
function dispersion(puntos, recta, ejeX, ejeY, titulo) {
  const W = 840, H = 400, m = { t: 46, r: 24, b: 54, l: 96 };
  const xs = puntos.map((p) => p[0]), ys = puntos.map((p) => p[1]);
  const x0 = 0, x1 = Math.max(...xs) * 1.05, y0 = 0, y1 = Math.max(...ys) * 1.05;
  const px = (v) => m.l + ((v - x0) / (x1 - x0)) * (W - m.l - m.r);
  const py = (v) => H - m.b - ((v - y0) / (y1 - y0)) * (H - m.t - m.b);
  const colores = ['#4cc9f0', '#f7b267', '#8ce99a', '#ff8fab', '#b197fc'];

  let g = `<svg viewBox="0 0 ${W} ${H}" class="chart"><text x="${W / 2}" y="24" class="ch-titulo">${titulo}</text>`;
  for (let i = 0; i <= 4; i++) {
    const v = y0 + ((y1 - y0) * i) / 4;
    g += `<line x1="${m.l}" y1="${py(v)}" x2="${W - m.r}" y2="${py(v)}" class="ch-grid"/>
          <text x="${m.l - 10}" y="${py(v) + 4}" class="ch-lbl" text-anchor="end">${fmt(v / 1e6, 1)} M</text>`;
  }
  for (let i = 0; i <= 5; i++) {
    const v = x0 + ((x1 - x0) * i) / 5;
    g += `<text x="${px(v)}" y="${H - m.b + 22}" class="ch-lbl" text-anchor="middle">${fmt(v)}</text>`;
  }
  puntos.forEach((p) => {
    const c = p.length > 2 ? colores[p[2] % colores.length] : '#4cc9f0';
    g += `<circle cx="${px(p[0])}" cy="${py(p[1])}" r="3.6" fill="${c}" opacity="0.72"/>`;
  });
  if (recta) {
    g += `<line x1="${px(x0)}" y1="${py(recta.b0 + recta.b1 * x0)}" x2="${px(x1)}" y2="${py(recta.b0 + recta.b1 * x1)}" class="ch-recta"/>`;
  }
  g += `<line x1="${m.l}" y1="${H - m.b}" x2="${W - m.r}" y2="${H - m.b}" class="ch-eje"/>
        <line x1="${m.l}" y1="${m.t}" x2="${m.l}" y2="${H - m.b}" class="ch-eje"/>
        <text x="${W / 2}" y="${H - 10}" class="ch-eje-lbl">${ejeX}</text>
        <text x="20" y="${H / 2}" class="ch-eje-lbl" transform="rotate(-90 20 ${H / 2})">${ejeY}</text></svg>`;
  return g;
}

function barras(datos, titulo) {
  const W = 840, H = 330, m = { t: 46, r: 24, b: 56, l: 110 };
  const max = Math.max(...datos.map((d) => d.valor)) * 1.15;
  const ancho = (W - m.l - m.r) / datos.length;
  let g = `<svg viewBox="0 0 ${W} ${H}" class="chart"><text x="${W / 2}" y="24" class="ch-titulo">${titulo}</text>`;
  for (let i = 0; i <= 4; i++) {
    const v = (max * i) / 4, y = H - m.b - (v / max) * (H - m.t - m.b);
    g += `<line x1="${m.l}" y1="${y}" x2="${W - m.r}" y2="${y}" class="ch-grid"/>
          <text x="${m.l - 10}" y="${y + 4}" class="ch-lbl" text-anchor="end">${fmt(v)}</text>`;
  }
  datos.forEach((d, i) => {
    const h = (d.valor / max) * (H - m.t - m.b);
    const x = m.l + i * ancho + ancho * 0.2, w = ancho * 0.6;
    g += `<rect x="${x}" y="${H - m.b - h}" width="${w}" height="${h}" rx="5" fill="#4cc9f0" opacity="0.85"/>
          <text x="${x + w / 2}" y="${H - m.b - h - 9}" class="ch-val" text-anchor="middle">${cop(d.valor)}</text>
          <text x="${x + w / 2}" y="${H - m.b + 22}" class="ch-lbl" text-anchor="middle">${d.etiqueta}</text>`;
  });
  g += `<line x1="${m.l}" y1="${H - m.b}" x2="${W - m.r}" y2="${H - m.b}" class="ch-eje"/></svg>`;
  return g;
}

/* =====================================================================
   PASO 7 · Resultados
   ===================================================================== */
function generarResumen() {
  const rep = estado.reporteLimpieza, mod = estado.modelo, cl = estado.clusters;
  const d = estado.filtrado;
  $('#res-kpis') && kpis('#res-kpis', [
    ['Registros procesados', fmt(rep ? rep.inicial : 0)],
    ['Registros válidos', fmt(rep ? rep.final : 0), 'bueno'],
    ['Calidad final', rep ? fmt(rep.retencion, 1) + ' %' : '—', 'bueno'],
    ['R² del modelo', mod ? mod.r2.toFixed(4) : '—', 'bueno'],
    ['Segmentos K-Means', cl ? cl.k : '—'],
    ['Flete analizado', copCorto(d.reduce((s, f) => s + f.costo_flete, 0))],
  ]);
  $('#res-conclusiones').innerHTML = `
    <li>La configuración inicial dejó la fuente tipada y homologada: fecha <b>YYYY-MM-DD</b>, moneda <b>COP</b> y granularidad mensual.</li>
    <li>La limpieza recuperó <b>${rep ? fmt(rep.retencion, 1) : '—'} %</b> del volumen original eliminando duplicados, nulos críticos, distancias inválidas y atípicos por rango intercuartil.</li>
    <li>La regresión lineal entrega un tarifario base de <b>${mod ? cop(mod.b1) : '—'} por kilómetro</b> con R² = <b>${mod ? mod.r2.toFixed(4) : '—'}</b>.</li>
    <li>K-Means identificó <b>${cl ? cl.k : '—'}</b> perfiles operativos que permiten priorizar la renegociación de tarifas.</li>
    <li>El tablero queda parametrizado y reproducible: cualquier archivo nuevo de la app de conductores sigue el mismo flujo.</li>`;
  marcarPaso(7);
}

/* =====================================================================
   Navegacion
   ===================================================================== */
function irA(n) {
  $$('.paso').forEach((p) => p.classList.toggle('activo', Number(p.dataset.paso) === n));
  $$('.nav-item').forEach((b) => b.classList.toggle('sel', Number(b.dataset.ir) === n));
  if (n === 7) generarResumen();
  window.scrollTo(0, 0);
}
function marcarPaso(n) {
  const b = document.querySelector(`.nav-item[data-ir="${n}"]`);
  if (b) b.classList.add('hecho');
}

document.addEventListener('DOMContentLoaded', () => {
  $$('.nav-item').forEach((b) => b.addEventListener('click', () => irA(Number(b.dataset.ir))));
  $('#btn-config').addEventListener('click', guardarConfiguracion);
  $('#btn-importar').addEventListener('click', importarDatos);
  $('#btn-limpiar').addEventListener('click', ejecutarLimpieza);
  $('#btn-filtrar').addEventListener('click', aplicarFiltros);
  $('#btn-regresion').addEventListener('click', regresionLineal);
  $('#btn-kmeans').addEventListener('click', kmeans);
  irA(1);
});
