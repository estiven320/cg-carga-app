/* Renderiza entrega/informe.html como PDF A4 usando Chromium. */
import { chromium } from 'playwright';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const RAIZ = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = path.join(RAIZ, 'entrega', 'informe.html');
const pdf = path.join(RAIZ, 'entrega', 'AA2-EV03-entrega.pdf');

const nav = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pag = await nav.newPage();
await pag.goto(pathToFileURL(html).href, { waitUntil: 'networkidle' });
await pag.pdf({
  path: pdf, format: 'A4', printBackground: true,
  margin: { top: '17mm', bottom: '16mm', left: '16mm', right: '16mm' },
  displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate: `<div style="width:100%;font-size:8pt;color:#66768e;padding:0 16mm;
    font-family:sans-serif;text-align:right">Página <span class="pageNumber"></span> de <span class="totalPages"></span></div>`,
});
await nav.close();
console.log('PDF generado:', pdf);
