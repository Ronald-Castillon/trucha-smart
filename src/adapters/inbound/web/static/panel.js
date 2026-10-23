// Refresca el panel cada 1 s consultando /api/panel (sesión por cookie HttpOnly).
// Con 1 s, una lectura del sensor queda visible en < 2 s (RF-03/RF-04), incluida
// la latencia de la consulta (mejora continua tras el reporte GQM del Inc. 1).
(function () {
  "use strict";
  const INTERVALO_MS = 1000;

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

  function pintarLectura(tarjeta, l, niveles) {
    const caja = tarjeta.querySelector(".ultima-lectura");
    if (!caja || !l) return;
    const n = (p) => `nivel-${(niveles && niveles[p]) || "NORMAL"}`;
    caja.innerHTML =
      `🌡️ <span class="temperatura ${n("TEMPERATURA")}">${fmt(l.temperatura_c)}</span> °C · ` +
      `💧 OD <span class="oxigeno ${n("OXIGENO_DISUELTO")}">${fmt(l.oxigeno_mg_l)}</span> mg/L · ` +
      `pH <span class="ph ${n("PH")}">${fmt(l.ph)}</span><br>` +
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
        pintarLectura(tarjeta, e.ultima_lectura, e.niveles);
        pintarAlertas(tarjeta, e.alertas_abiertas);
      }
      document.getElementById("actualizado").textContent =
        "actualizado " + new Date().toLocaleTimeString();
    } catch (_) { /* reintenta en el siguiente ciclo */ }
  }

  setInterval(refrescar, INTERVALO_MS);
})();
