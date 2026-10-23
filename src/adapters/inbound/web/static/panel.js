// Refresca el panel cada 2 s consultando /api/panel (sesión por cookie HttpOnly).
(function () {
  "use strict";
  const INTERVALO_MS = 2000;

  function fmt(n) { return Number(n).toFixed(2); }
  function fecha(iso) {
    const d = new Date(iso);
    const p = (x) => String(x).padStart(2, "0");
    return `${p(d.getUTCDate())}/${p(d.getUTCMonth() + 1)}/${d.getUTCFullYear()} ` +
           `${p(d.getUTCHours())}:${p(d.getUTCMinutes())}:${p(d.getUTCSeconds())} UTC`;
  }
  function escapar(t) {
    const div = document.createElement("div");
    div.textContent = t;
    return div.innerHTML;
  }

  function pintarLectura(tarjeta, l) {
    const caja = tarjeta.querySelector(".ultima-lectura");
    if (!caja || !l) return;
    caja.innerHTML =
      `🌡️ <span class="temperatura">${fmt(l.temperatura_c)}</span> °C · ` +
      `💧 OD <span class="oxigeno">${fmt(l.oxigeno_mg_l)}</span> mg/L · ` +
      `pH <span class="ph">${fmt(l.ph)}</span><br>` +
      `<span class="suave">Última lectura: <time class="medido-en" datetime="${escapar(l.medido_en)}">${fecha(l.medido_en)}</time></span>`;
  }

  function pintarAlertas(tarjeta, alertas) {
    const caja = tarjeta.querySelector(".alertas-abiertas");
    if (!caja || !alertas) return;
    caja.innerHTML = alertas.length === 0
      ? '<span class="etiqueta NORMAL">Sin alertas abiertas</span>'
      : alertas.map((a) =>
          `<div class="alerta" data-alerta="${a.id}"><span class="etiqueta ${a.nivel}">${a.nivel === "CRITICA" ? "CRÍTICA" : "PRECAUCIÓN"}</span> ${escapar(a.mensaje)}</div>`
        ).join("");
  }

  async function refrescar() {
    try {
      const r = await fetch("/api/panel", { credentials: "same-origin" });
      if (r.status === 401) { window.location.href = "/login"; return; }
      if (!r.ok) return;
      for (const e of await r.json()) {
        const tarjeta = document.querySelector(`[data-estanque="${e.estanque_id}"]`);
        if (!tarjeta) continue;
        pintarLectura(tarjeta, e.ultima_lectura);
        pintarAlertas(tarjeta, e.alertas_abiertas);
      }
      document.getElementById("actualizado").textContent =
        "actualizado " + new Date().toLocaleTimeString();
    } catch (_) { /* reintenta en el siguiente ciclo */ }
  }

  setInterval(refrescar, INTERVALO_MS);
})();
