/* =====================================================================
   Graba el video de la evidencia AA2-EV03 recorriendo la consola de
   analitica paso a paso. Genera:
     entrega/AA2-EV03-configuracion-analitica.mp4
     entrega/guion-narracion.md   (guion con codigos de tiempo)
   ===================================================================== */
import { chromium } from 'playwright';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const TMP = path.join(RAIZ, '.video-tmp');
const SALIDA = path.join(RAIZ, 'entrega');
const URL_APP = 'http://localhost:4173/';
const CHROMIUM = '/opt/pw-browsers/chromium';
const FFMPEG = fs.existsSync('/usr/bin/ffmpeg') ? '/usr/bin/ffmpeg' : '/opt/pw-browsers/ffmpeg-1011/ffmpeg-linux';

fs.rmSync(TMP, { recursive: true, force: true });
fs.mkdirSync(TMP, { recursive: true });
fs.mkdirSync(SALIDA, { recursive: true });

const guion = [];
let t0 = 0;
const reloj = () => {
  const s = Math.round((Date.now() - t0) / 1000);
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
};

const navegador = await chromium.launch({ executablePath: CHROMIUM });
const ctx = await navegador.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: TMP, size: { width: 1280, height: 720 } },
  deviceScaleFactor: 1,
});
const pag = await ctx.newPage();
await pag.addInitScript({ path: path.join(RAIZ, 'scripts', 'overlay.js') });

const esperar = (ms) => pag.waitForTimeout(ms);

/** Muestra un subtitulo, lo deja el tiempo necesario para leerlo/narrarlo y lo registra en el guion. */
async function narrar(texto, extra = 0) {
  const ms = Math.max(2600, texto.length * 62) + extra;
  guion.push({ t: reloj(), texto });
  await pag.evaluate((t) => window.ov.sub(t), texto);
  await esperar(ms);
}

async function paso(etiqueta) {
  await pag.evaluate((t) => window.ov.paso(t), etiqueta);
}

/** Mueve el cursor simulado hasta el elemento y hace clic. */
async function clic(sel, pausa = 900) {
  const el = pag.locator(sel).first();
  await el.scrollIntoViewIfNeeded();
  await esperar(320);
  const caja = await el.boundingBox();
  if (caja) {
    const x = caja.x + caja.width / 2, y = caja.y + caja.height / 2;
    await pag.evaluate(([x, y]) => window.ov.mover(x, y), [x, y]);
    await esperar(430);
    await pag.evaluate(() => window.ov.clic());
    await esperar(190);
  }
  await el.click();
  await esperar(pausa);
}

async function elegir(sel, valor) {
  const el = pag.locator(sel);
  await el.scrollIntoViewIfNeeded();
  const caja = await el.boundingBox();
  if (caja) {
    await pag.evaluate(([x, y]) => window.ov.mover(x, y), [caja.x + caja.width / 2, caja.y + caja.height / 2]);
    await esperar(380);
    await pag.evaluate(() => window.ov.clic());
  }
  await el.selectOption(valor);
  await esperar(750);
}

async function desplazar(px) {
  await pag.mouse.wheel(0, px);
  await esperar(750);
}

/* ==================== INICIO ==================== */
await pag.goto(URL_APP, { waitUntil: 'networkidle' });
t0 = Date.now();

await pag.evaluate(() => window.ov.titulo(`
  <div class="t-ico">🚛</div>
  <h1>Configuración de una herramienta<br>de analítica de datos</h1>
  <h2>CG CARGA · Operación de transporte de carga</h2>
  <div class="t-meta">
    Evidencia <b>AA2-EV03</b> · Video configuración de analítica de datos<br>
    Programa: Aplicación de la inteligencia artificial en la integración de datos<br>
    Resultado de aprendizaje <b>220501115-02</b>
  </div>`));
guion.push({ t: reloj(), texto: 'PORTADA · Presentarse: nombre completo, ficha y programa de formación. Enunciar la evidencia AA2-EV03.' });
await esperar(8500);
await pag.evaluate(() => window.ov.ocultarTitulo());
await esperar(1000);

/* ==================== PASO 1 · JUSTIFICACION ==================== */
await paso('Paso 1 · Justificación');
await narrar('La operación de CG CARGA genera cada semana un archivo de viajes exportado desde la app de conductores.');
await narrar('Ese archivo llega con registros repetidos, celdas vacías, montos con símbolo de moneda y fechas en tres formatos distintos.');
await desplazar(180);
await narrar('Se evaluaron Excel, Power BI y Looker Studio. Se eligió una consola propia por reproducibilidad, trazabilidad, costo cero y portabilidad.');
await desplazar(220);
await narrar('El flujo tiene siete etapas y aplica técnicas concretas: deduplicación, imputación, rango intercuartil, regresión lineal y K-Means.', 900);
await desplazar(-400);

/* ==================== PASO 2 · CONFIGURACION ==================== */
await paso('Paso 2 · Configuración inicial');
await clic('.nav-item[data-ir="2"]');
await narrar('Primer paso de la configuración: declarar el origen de datos y el contrato que debe cumplir el archivo.');
await elegir('#cfg-delim', ',');
await narrar('Se define el archivo fuente, la coma como delimitador y UTF-8 como codificación, que es lo que exporta la aplicación móvil.');
await elegir('#cfg-encoding', 'UTF-8');
await elegir('#cfg-granularidad', 'Mensual');
await narrar('La granularidad de agregación se fija en mensual, porque así se revisa la operación en los comités de la empresa.');
await elegir('#cfg-colfecha', 'fecha');
await elegir('#cfg-formato', 'DD/MM/YYYY');
await narrar('En el contrato de datos se marca "fecha" como campo temporal, formato día, mes y año, moneda en pesos colombianos y zona horaria de Bogotá.');
await elegir('#cfg-moneda', 'COP (peso colombiano)');
await elegir('#cfg-zona', 'America/Bogota (UTC-5)');
await clic('#btn-config', 1500);
await narrar('Al guardar, el estado pasa a CONFIGURADO y la consola deja registrado cada parámetro. La conexión ya está lista para importar.', 1200);

/* ==================== PASO 3 · IMPORTACION ==================== */
await paso('Paso 3 · Importación y perfilado');
await clic('.nav-item[data-ir="3"]');
await narrar('Con la configuración guardada se importa el conjunto de datos.');
await clic('#btn-importar', 2000);
await narrar('Se cargaron 554 registros y 12 campos. La consola ejecuta de inmediato un perfilado de calidad.');
await narrar('El perfilado detecta 70 celdas vacías, 34 identificadores duplicados y 15 viajes con distancia negativa.', 600);
await desplazar(260);
await narrar('En la vista previa las celdas rojas son valores vacíos y las ámbar tienen formato inconsistente: montos con signo pesos y ciudades en mayúsculas.', 900);
await desplazar(330);
await narrar('El perfilado por campo infiere el tipo de dato de cada columna y cuenta nulos y valores distintos. Estos datos no se pueden analizar todavía.', 900);
await desplazar(-560);

/* ==================== PASO 4 · LIMPIEZA ==================== */
await paso('Paso 4 · Limpieza de datos');
await clic('.nav-item[data-ir="4"]');
await narrar('Cuarto paso: la limpieza. Se activan seis reglas de calidad y cada una queda registrada con los registros que afecta.');
await narrar('R1 deduplica por identificador de viaje. R2 normaliza el texto. R3 convierte tipos: los montos pasan a número y las fechas a formato ISO.', 700);
await narrar('R4 valida el dominio y descarta distancias menores o iguales a cero. R5 elimina nulos críticos e imputa peso y duración con la mediana.', 700);
await narrar('R6 aplica la técnica del rango intercuartil para retirar los fletes atípicos por encima de Q3 más 1,5 veces el IQR.', 700);
await clic('#btn-limpiar', 2200);
await narrar('La consola reporta cada regla ejecutada con su conteo exacto: 34 duplicados, 52 registros inválidos o nulos y 27 atípicos.', 800);
await desplazar(300);
await narrar('Del total original quedan 441 registros válidos, una retención del 79,6 por ciento del volumen.', 700);
await desplazar(300);
await narrar('El dataset resultante ya está tipado y enriquecido con los campos calculados costo por kilómetro, rendimiento y ruta.', 900);
await desplazar(-600);

/* ==================== PASO 5 · FILTROS Y SEGMENTACION ==================== */
await paso('Paso 5 · Filtros y segmentación');
await clic('.nav-item[data-ir="5"]');
await narrar('Quinto paso: parametrizar el análisis con filtros y segmentaciones.');
await clic('#btn-filtrar', 1600);
await narrar('Sin filtros se analiza el universo completo: 441 viajes, 829 millones de pesos en flete y un ticket promedio de 1,88 millones.', 800);
await desplazar(300);
await narrar('La segmentación por tipo de vehículo compara kilómetros, flete y costo unitario entre categorías. El turbo es el de mayor costo por kilómetro.', 900);
await desplazar(-300);
await narrar('Ahora se aplica un filtro real: solo viajes entregados con tractomula y distancia mínima de 200 kilómetros.');
await elegir('#f-vehiculo', 'Tractomula');
await elegir('#f-estado', 'Entregado');
await pag.locator('#f-kmmin').fill('200');
await esperar(600);
await clic('#btn-filtrar', 1800);
await narrar('El subconjunto se recalcula al instante y todos los indicadores responden al filtro aplicado.', 900);
await desplazar(300);
await esperar(1600);
await desplazar(-300);
await narrar('Ese recorte deja solo 34 viajes: sirve para una revisión puntual, pero son pocas observaciones para ajustar un modelo.');
await pag.locator('#f-kmmin').fill('0');
await esperar(600);
await clic('#btn-filtrar', 1800);
await narrar('Se libera la distancia mínima y se conserva la flota de tractomulas efectivamente entregadas: un segmento homogéneo, que es lo correcto para calcular un tarifario por kilómetro.', 1000);

/* ==================== PASO 6 · ALGORITMOS ==================== */
await paso('Paso 6 · Algoritmos de análisis');
await clic('.nav-item[data-ir="6"]');
await narrar('Sexto paso: aplicar los algoritmos sobre el subconjunto ya depurado y filtrado.');
await narrar('El primero es una regresión lineal por mínimos cuadrados que predice el flete a partir de la distancia recorrida.');
await clic('#btn-regresion', 2200);
await narrar('La consola entrega la ecuación estimada, el coeficiente de determinación R cuadrado, la correlación de Pearson y los errores RMSE y MAE.', 900);
await desplazar(300);
await narrar('La nube de puntos con la recta de ajuste muestra la relación, y la tabla simula el flete estimado para rutas de 200, 450 y 800 kilómetros.', 1000);
await narrar('Esa pendiente es el tarifario base por kilómetro que la empresa puede usar para cotizar rutas nuevas.', 700);
await desplazar(-300);
await narrar('El segundo algoritmo es K-Means, un agrupamiento no supervisado con tres clusters sobre distancia, peso y costo estandarizados.');
await elegir('#k-clusters', '3');
await clic('#btn-kmeans', 2400);
await narrar('K-Means converge en pocas iteraciones y separa la operación en tres perfiles logísticos sin usar etiquetas previas.', 800);
await desplazar(320);
await narrar('Cada cluster queda caracterizado con su número de viajes, kilómetros, peso, flete y costo unitario promedio.', 900);
await narrar('El gráfico muestra los tres grupos diferenciados por color, lo que permite priorizar dónde renegociar tarifas.', 900);
await desplazar(-320);

/* ==================== PASO 7 · RESULTADOS ==================== */
await paso('Paso 7 · Resultados');
await clic('.nav-item[data-ir="7"]');
await narrar('Séptimo y último paso: los resultados del proceso completo de configuración.');
await narrar('Se procesaron 554 registros crudos, quedaron 441 registros válidos con 79,6 por ciento de calidad final, más el R cuadrado del modelo y los tres segmentos identificados.', 900);
await desplazar(240);
await narrar('Las conclusiones resumen el aporte de cada etapa y dejan el tablero parametrizado y reproducible para el próximo archivo de la app de conductores.', 1200);
await desplazar(-240);

/* ==================== CIERRE ==================== */
await pag.evaluate(() => window.ov.sub(''));
await pag.evaluate(() => window.ov.paso(''));
await pag.evaluate(() => window.ov.titulo(`
  <div class="t-ico">✅</div>
  <h1>Configuración completada</h1>
  <h2>Herramienta de analítica de datos operativa</h2>
  <div class="t-meta">
    Configuración inicial · Importación · Limpieza · Filtros y segmentación<br>
    Regresión lineal · K-Means · Resultados<br><br>
    <b>CG CARGA</b> · Evidencia AA2-EV03
  </div>`));
guion.push({ t: reloj(), texto: 'CIERRE · Recapitular las siete etapas y despedirse agradeciendo al instructor.' });
await esperar(8000);

await ctx.close();
await navegador.close();

/* ==================== EXPORTAR ==================== */
const webm = fs.readdirSync(TMP).find((f) => f.endsWith('.webm'));
if (!webm) { console.error('No se genero el video.'); process.exit(1); }
const origen = path.join(TMP, webm);
const mp4 = path.join(SALIDA, 'AA2-EV03-configuracion-analitica.mp4');

const r = spawnSync(FFMPEG, [
  '-y', '-i', origen,
  '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p', '-r', '25',
  '-c:a', 'aac', '-b:a', '96k', '-shortest', '-movflags', '+faststart', mp4,
], { stdio: ['ignore', 'ignore', 'pipe'] });

if (r.status !== 0) {
  console.error('ffmpeg fallo:\n' + r.stderr.toString().slice(-1500));
  fs.copyFileSync(origen, path.join(SALIDA, 'AA2-EV03-configuracion-analitica.webm'));
  console.log('Se conservo la version .webm.');
} else {
  console.log('Video MP4 generado:', mp4);
}

const md = `# Guion de narración · Evidencia AA2-EV03

**Video:** Configuración de una herramienta de analítica de datos — CG CARGA
**Archivo:** \`entrega/AA2-EV03-configuracion-analitica.mp4\`

Los códigos de tiempo corresponden al video generado. Cada línea es el texto que
aparece como subtítulo en pantalla y que debe narrarse en voz propia.

| Tiempo | Narración |
|:------:|:----------|
${guion.map((g) => `| \`${g.t}\` | ${g.texto} |`).join('\n')}

**Duración aproximada:** ${guion.length ? guion[guion.length - 1].t : '—'} más el cierre.
`;
fs.writeFileSync(path.join(SALIDA, 'guion-narracion.md'), md, 'utf8');
console.log('Guion generado con', guion.length, 'intervenciones.');
fs.rmSync(TMP, { recursive: true, force: true });
