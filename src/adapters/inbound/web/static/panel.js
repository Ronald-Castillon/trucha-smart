// Panel en vivo: consulta /api/panel cada 1 s (sesión por cookie HttpOnly) y actualiza lecturas,
// mini gráficos de tendencia, riesgo, alertas y el control del sensor simulado.
// Con 1 s, una lectura del sensor queda visible en < 2 s (RF-03/RF-04, mejora MC-01).
(function () {
  "use strict";
  const INTERVALO_MS = 1000;
  const graficos = new Map(); // estanque_id -> Chart
  const ultimaMarca = new Map(); // estanque_id -> medido_en de la última lectura pintada

  function fmt(n) { return Number(n).toFixed(2); }
  function fecha(iso) {
    const d = new Date(iso);
    const p = (x) => String(x).padStart(2, "0");
    return `${p(d.getUTCDate())}/${p(d.getUTCMonth() + 1)}/${d.getUTCFullYear()} ` +
           `${p(d.getUTCHours())}:${p(d.getUTCMinutes())}:${p(d.getUTCSeconds())} UTC`;
  }
  function hora(iso) {
    const d = new Date(iso);
    const p = (x) => String(x).padStart(2, "0");
    return `${p(d.getUTCDate())}/${p(d.getUTCMonth() + 1)} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
  }
  function escapar(t) {
    const div = document.createElement("div");
    div.textContent = t;
    return div.innerHTML;
  }
  function destellar(el) {
    if (!el) return;
    el.classList.remove("cambio");
    void el.offsetWidth; // reinicia la animación
    el.classList.add("cambio");
  }

  function pintarLectura(tarjeta, id, l, niveles) {
    const caja = tarjeta.querySelector(".ultima-lectura");
    if (!caja || !l) return;
    const nueva = ultimaMarca.has(id) && ultimaMarca.get(id) !== l.medido_en;
    ultimaMarca.set(id, l.medido_en);
    const n = (p) => `nivel-${(niveles && niveles[p]) || "NORMAL"}`;
    caja.innerHTML =
      `🌡️ <span class="temperatura ${n("TEMPERATURA")}">${fmt(l.temperatura_c)}</span> °C · ` +
      `💧 OD <span class="oxigeno ${n("OXIGENO_DISUELTO")}">${fmt(l.oxigeno_mg_l)}</span> mg/L · ` +
      `pH <span class="ph ${n("PH")}">${fmt(l.ph)}</span><br>` +
      `<span class="suave">Última lectura: <time class="medido-en" datetime="${escapar(l.medido_en)}">${fecha(l.medido_en)}</time></span>`;
    if (nueva) caja.querySelectorAll(".temperatura, .oxigeno, .ph").forEach(destellar);
  }

  function pintarAlertas(tarjeta, alertas) {
    const caja = tarjeta.querySelector(".alertas-abiertas");
    if (!caja || !alertas) return;
    caja.innerHTML = alertas.length === 0
      ? '<span class="etiqueta NORMAL">Sin alertas abiertas</span>'
      : alertas.map((a) =>
          `<div class="alerta" data-alerta="${a.id}"><span class="etiqueta ${a.nivel}">${a.nivel === "CRITICA" ? "CRÍTICA" : "PRECAUCIÓN"}</span> ${escapar(a.mensaje)}</div>`
        ).join("");
    const enlace = tarjeta.querySelector(".enlace-atender");
    if (enlace) enlace.hidden = alertas.length === 0;
    tarjeta.classList.toggle("con-critica", alertas.some((a) => a.nivel === "CRITICA"));
  }

  function pintarRiesgo(tarjeta, r) {
    const et = tarjeta.querySelector(".riesgo");
    if (!et || !r) return;
    const texto = `Riesgo ${r.valor} · ${r.nivel}`;
    if (et.textContent !== texto) destellar(et);
    et.className = `etiqueta riesgo ${r.semaforo.toLowerCase()}`;
    et.title = r.formula;
    et.textContent = texto;
  }

  function pintarTendencia(tarjeta, id, puntos) {
    const lienzo = tarjeta.querySelector("canvas.sparkline");
    if (!lienzo || !window.Chart || !puntos) return;
    const etiquetas = puntos.map((p) => hora(p.medido_en));
    const series = [puntos.map((p) => p.temperatura_c), puntos.map((p) => p.oxigeno_mg_l),
                    puntos.map((p) => p.ph)];
    let g = graficos.get(id);
    if (!g) {
      g = new Chart(lienzo, {
        type: "line",
        data: {
          labels: etiquetas,
          datasets: [
            { label: "T °C", data: series[0], borderColor: "#c0392b" },
            { label: "OD mg/L", data: series[1], borderColor: "#0b6e8a" },
            { label: "pH", data: series[2], borderColor: "#1f8a4c" },
          ].map((d) => ({ ...d, borderWidth: 2, pointRadius: 0, tension: 0.35 })),
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          animation: { duration: 400 },
          interaction: { mode: "index", intersect: false },
          plugins: { legend: { display: true, labels: { boxWidth: 10, font: { size: 10 } } } },
          scales: { x: { display: false }, y: { ticks: { font: { size: 9 } } } },
        },
      });
      graficos.set(id, g);
      lienzo.dataset.listo = "1";
      return;
    }
    g.data.labels = etiquetas;
    g.data.datasets.forEach((d, i) => { d.data = series[i]; });
    g.update();
  }

  function pintarSimulacion(tarjeta, escenario) {
    const caja = tarjeta.querySelector(".simulador");
    if (!caja || caja.dataset.ocupado === "1") return;
    const boton = caja.querySelector(".sim-boton");
    const estado = caja.querySelector(".sim-estado");
    const activo = Boolean(escenario);
    caja.classList.toggle("activo", activo);
    caja.dataset.activo = activo ? "1" : "";
    boton.textContent = activo ? "■ Detener sensor" : "▶ Simular sensor";
    if (activo) caja.querySelector(".sim-escenario").value = escenario;
    caja.querySelector(".sim-escenario").disabled = activo;
    estado.innerHTML = activo ? '<span class="punto"></span> enviando lecturas cada 2 s' : "";
  }

  async function alternarSimulacion(caja) {
    const id = Number(caja.dataset.estanqueSim);
    const activo = caja.dataset.activo === "1";
    caja.dataset.ocupado = "1";
    try {
      const r = activo
        ? await fetch(`/api/simulador/${id}`, { method: "DELETE", credentials: "same-origin" })
        : await fetch("/api/simulador", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              estanque_id: id,
              escenario: caja.querySelector(".sim-escenario").value,
              intervalo_s: 2,
            }),
          });
      if (!r.ok && r.status !== 404) {
        const e = await r.json().catch(() => ({}));
        window.TS && TS.aviso(e.detalle || "No se pudo cambiar el simulador", "error");
      }
    } finally {
      caja.dataset.ocupado = "";
      refrescar();
    }
  }

  function pintarPrediccion(tarjeta, texto) {
    const caja = tarjeta.querySelector(".prediccion");
    if (!caja) return;
    caja.hidden = !texto;
    if (texto) caja.querySelector(".texto-prediccion").textContent = texto;
  }

  async function refrescar() {
    try {
      const r = await fetch("/api/panel", { credentials: "same-origin" });
      if (r.status === 401) { window.location.href = "/login"; return; }
      if (!r.ok) return;
      for (const e of await r.json()) {
        const tarjeta = document.querySelector(`[data-estanque="${e.estanque_id}"]`);
        if (!tarjeta) continue;
        pintarLectura(tarjeta, e.estanque_id, e.ultima_lectura, e.niveles);
        pintarAlertas(tarjeta, e.alertas_abiertas);
        pintarRiesgo(tarjeta, e.riesgo);
        pintarTendencia(tarjeta, e.estanque_id, e.tendencia);
        pintarSimulacion(tarjeta, e.simulacion);
        pintarPrediccion(tarjeta, e.prediccion);
      }
      document.getElementById("actualizado").textContent =
        "actualizado " + new Date().toLocaleTimeString();
    } catch (_) { /* reintenta en el siguiente ciclo */ }
  }

  document.addEventListener("click", (ev) => {
    const boton = ev.target.closest(".sim-boton");
    if (boton) alternarSimulacion(boton.closest(".simulador"));
  });
  // Una alerta nueva hace parpadear la tarjeta de su estanque (aviso emitido por vivo.js).
  window.addEventListener("ts:alerta", (ev) => {
    const tarjeta = document.querySelector(`[data-estanque="${ev.detail.estanque_id}"]`);
    if (!tarjeta) return;
    tarjeta.classList.remove("parpadeo");
    void tarjeta.offsetWidth;
    tarjeta.classList.add("parpadeo");
  });

  refrescar();
  setInterval(refrescar, INTERVALO_MS);
})();
