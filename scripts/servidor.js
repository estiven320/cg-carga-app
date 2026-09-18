// Servidor estatico minimo para servir la consola durante la grabacion.
const http = require('http'), fs = require('fs'), path = require('path');
const raiz = path.join(__dirname, '..', 'analitica');
const tipos = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.csv': 'text/csv; charset=utf-8' };
http.createServer((req, res) => {
  const rel = decodeURIComponent(req.url.split('?')[0]);
  const archivo = path.join(raiz, rel === '/' ? 'index.html' : rel);
  if (!archivo.startsWith(raiz) || !fs.existsSync(archivo)) { res.writeHead(404); return res.end('404'); }
  res.writeHead(200, { 'Content-Type': tipos[path.extname(archivo)] || 'application/octet-stream' });
  fs.createReadStream(archivo).pipe(res);
}).listen(4173, () => console.log('Consola disponible en http://localhost:4173'));
