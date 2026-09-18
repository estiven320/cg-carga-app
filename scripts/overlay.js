/* Capa de presentacion usada solo durante la grabacion del video:
   portada, indicador de paso, subtitulos y cursor visible.
   Se inyecta antes que la pagina, por eso el DOM se construye de forma
   perezosa la primera vez que se invoca una funcion de window.ov. */
(() => {
  const CSS = `
  #ov-cursor{position:fixed;width:22px;height:22px;border-radius:50%;
    background:rgba(76,201,240,.35);border:2px solid #4cc9f0;pointer-events:none;
    z-index:99999;transform:translate(-50%,-50%);
    transition:left .32s cubic-bezier(.4,0,.2,1),top .32s cubic-bezier(.4,0,.2,1);
    box-shadow:0 0 14px rgba(76,201,240,.6);opacity:0}
  #ov-cursor.click{animation:ovclick .45s ease}
  @keyframes ovclick{0%{transform:translate(-50%,-50%) scale(1)}
    45%{transform:translate(-50%,-50%) scale(2.1);background:rgba(255,183,3,.45);border-color:#ffb703}
    100%{transform:translate(-50%,-50%) scale(1)}}
  #ov-sub{position:fixed;left:0;right:0;bottom:0;z-index:99998;
    background:linear-gradient(to top,rgba(4,9,18,.97) 58%,rgba(4,9,18,0));
    padding:34px 60px 24px;text-align:center;opacity:0;transition:opacity .3s;pointer-events:none}
  #ov-sub.on{opacity:1}
  #ov-sub p{display:inline-block;background:rgba(10,18,32,.93);border:1px solid #2b415f;
    border-radius:11px;padding:11px 26px;font-size:21px;line-height:1.42;color:#eef4ff;
    font-family:system-ui,"DejaVu Sans",sans-serif;max-width:1060px;
    box-shadow:0 8px 30px rgba(0,0,0,.55)}
  #ov-paso{position:fixed;top:17px;right:22px;z-index:99998;background:rgba(10,18,32,.93);
    border:1px solid #2b415f;border-radius:9px;padding:7px 16px;font-size:13.5px;letter-spacing:1.1px;
    color:#4cc9f0;font-family:system-ui,"DejaVu Sans",sans-serif;font-weight:700;text-transform:uppercase;
    opacity:0;transition:opacity .3s;pointer-events:none}
  #ov-paso.on{opacity:1}
  #ov-titulo{position:fixed;inset:0;z-index:99999;background:#070d18;display:flex;flex-direction:column;
    align-items:center;justify-content:center;gap:16px;font-family:system-ui,"DejaVu Sans",sans-serif;
    transition:opacity .6s}
  #ov-titulo.off{opacity:0;pointer-events:none}
  #ov-titulo .t-ico{font-size:66px}
  #ov-titulo h1{font-size:43px;color:#eef4ff;letter-spacing:-.8px;text-align:center;line-height:1.24}
  #ov-titulo h2{font-size:23px;color:#4cc9f0;font-weight:600;text-align:center}
  #ov-titulo .t-meta{margin-top:20px;color:#9fb2d0;font-size:16.5px;text-align:center;line-height:1.85}
  #ov-titulo .t-meta b{color:#eef4ff}`;

  let listo = false, cur, sub, paso;

  function montar() {
    if (listo) return;
    const st = document.createElement('style');
    st.textContent = CSS;
    document.head.appendChild(st);
    cur = document.createElement('div'); cur.id = 'ov-cursor';
    sub = document.createElement('div'); sub.id = 'ov-sub'; sub.innerHTML = '<p></p>';
    paso = document.createElement('div'); paso.id = 'ov-paso';
    document.body.append(cur, sub, paso);
    listo = true;
  }

  window.ov = {
    mover(x, y) { montar(); cur.style.opacity = 1; cur.style.left = x + 'px'; cur.style.top = y + 'px'; },
    clic() { montar(); cur.classList.remove('click'); void cur.offsetWidth; cur.classList.add('click'); },
    sub(t) {
      montar();
      if (!t) { sub.classList.remove('on'); return; }
      sub.querySelector('p').textContent = t;
      sub.classList.add('on');
    },
    paso(t) {
      montar();
      if (!t) { paso.classList.remove('on'); return; }
      paso.textContent = t; paso.classList.add('on');
    },
    titulo(html) {
      montar();
      const d = document.createElement('div');
      d.id = 'ov-titulo'; d.innerHTML = html;
      document.body.appendChild(d);
    },
    ocultarTitulo() {
      const d = document.getElementById('ov-titulo');
      if (d) { d.classList.add('off'); setTimeout(() => d.remove(), 900); }
    },
  };
})();
