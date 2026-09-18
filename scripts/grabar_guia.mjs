/* Graba el video guia recorriendo las diapositivas de video/guia.html.
   Salida: entrega/AA2-EV03-guia-para-grabar.mp4 (objetivo: menos de 10 MB). */
import { chromium } from 'playwright';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const RAIZ = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const TMP = path.join(RAIZ, '.video-tmp');
const SALIDA = path.join(RAIZ, 'entrega');
const CHROMIUM = '/opt/pw-browsers/chromium';
const FFMPEG = fs.existsSync('/usr/bin/ffmpeg') ? '/usr/bin/ffmpeg' : '/opt/pw-browsers/ffmpeg-1011/ffmpeg-linux';
const MAX_MB = 10;

// Segundos en pantalla por diapositiva, en el orden del HTML.
const TIEMPOS = [11, 16, 17, 17, 16, 18, 18, 18, 18, 15, 17, 18, 15];

fs.rmSync(TMP, { recursive: true, force: true });
fs.mkdirSync(TMP, { recursive: true });
fs.mkdirSync(SALIDA, { recursive: true });

const nav = await chromium.launch({ executablePath: CHROMIUM });
const ctx = await nav.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: TMP, size: { width: 1280, height: 720 } },
});
const pag = await ctx.newPage();
await pag.goto(pathToFileURL(path.join(RAIZ, 'video', 'guia.html')).href, { waitUntil: 'load' });

const total = await pag.evaluate(() => window.total);
if (total !== TIEMPOS.length) {
  console.warn(`Aviso: ${total} diapositivas y ${TIEMPOS.length} tiempos definidos.`);
}
for (let i = 0; i < total; i++) {
  await pag.evaluate((n) => window.ir(n), i);
  await pag.waitForTimeout((TIEMPOS[i] ?? 15) * 1000);
}
await ctx.close();
await nav.close();

const webm = fs.readdirSync(TMP).find((f) => f.endsWith('.webm'));
if (!webm) { console.error('No se genero el video.'); process.exit(1); }
const origen = path.join(TMP, webm);
const mp4 = path.join(SALIDA, 'AA2-EV03-guia-para-grabar.mp4');

/* Diapositivas estaticas: con crf alto y 15 fps el archivo queda muy por debajo
   del limite. Si aun asi se pasa, se recomprime subiendo el crf. */
function comprimir(crf) {
  const r = spawnSync(FFMPEG, [
    '-y', '-i', origen,
    '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', String(crf),
    '-pix_fmt', 'yuv420p', '-r', '15', '-g', '150',
    '-c:a', 'aac', '-b:a', '64k', '-shortest', '-movflags', '+faststart', mp4,
  ], { stdio: ['ignore', 'ignore', 'pipe'] });
  if (r.status !== 0) { console.error('ffmpeg fallo:\n' + r.stderr.toString().slice(-1200)); process.exit(1); }
  return fs.statSync(mp4).size / 1024 / 1024;
}

let crf = 26, mb = comprimir(crf);
while (mb > MAX_MB && crf < 38) { crf += 4; mb = comprimir(crf); }

console.log(`Video generado: ${mp4}`);
console.log(`Tamano: ${mb.toFixed(2)} MB (crf ${crf}) · limite ${MAX_MB} MB`);
if (mb > MAX_MB) console.error('ATENCION: sigue por encima del limite.');
fs.rmSync(TMP, { recursive: true, force: true });
