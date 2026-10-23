// Funciones "en vivo" comunes a todas las páginas con sesión:
//  - avisos emergentes cuando aparece una alerta nueva (consulta /api/alertas cada 2 s);
//  - TS.recargarSecciones(): actualiza partes de la página sin recargarla completa.
(function () {
  "use strict";
  const INTERVALO_ALERTAS_MS = 2000;
  const conocidas = new Set();
  const nombres = new Map();
  let inicializado = false;
  let audio = null;

  function contenedor() {
    let c = document.getElementById("avisos");
    if (!c) {
      c = document.createElement("div");
      c.id = "avisos";
      c.setAttribute("aria-live", "polite");
      document.body.appendChild(c);
    }
    return c;
  }

  function aviso(html, clase = "", enlace = null) {
    const t = document.createElement("div");
    t.className = `aviso ${clase}`;
    t.setAttribute("role", "status");
    t.innerHTML = `<button type="button" class="cerrar" aria-label="Cerrar">×</button>${html}` +
      (enlace ? ` <a href="${enlace}">Ver</a>` : "");
    t.querySelector(".cerrar").onclick = () => t.remove();
    contenedor().prepend(t);
    setTimeout(() => t.classList.add("saliendo"), 9000);
    setTimeout(() => t.remove(), 9600);
    return t;
  }

  function escapar(txt) {
    const d = document.createElement("div");
    d.textContent = txt;
    return d.innerHTML;
  }

  function pitido(critica) {
    try {
      audio = audio || new (window.AudioContext || window.webkitAudioContext)();
      if (audio.state === "suspended") return; // el navegador exige una interacción previa
      const osc = audio.createOscillator();
      const vol = audio.createGain();
      osc.frequency.value = critica ? 880 : 520;
      vol.gain.value = 0.05;
      osc.connect(vol).connect(audio.destination);
      osc.start();
      osc.stop(audio.currentTime + 0.18);
    } catch (_) { /* sin audio */ }
  }
  document.addEventListener("click", () => { if (audio && audio.state === "suspended") audio.resume(); });

  async function cargarNombres() {
    const r = await fetch("/api/estanques", { credentials: "same-origin" });
    if (r.ok) for (const e of await r.json()) nombres.set(e.id, e.nombre);
  }

  async function revisarAlertas() {
    try {
      const r = await fetch("/api/alertas?estado=ABIERTA&limite=200", { credentials: "same-origin" });
      if (!r.ok) return;
      const alertas = await r.json();
      const nuevas = alertas.filter((a) => !conocidas.has(a.id));
      alertas.forEach((a) => conocidas.add(a.id));
      if (!inicializado) { inicializado = true; return; } // las ya abiertas no se anuncian
      if (nuevas.some((a) => !nombres.has(a.estanque_id))) await cargarNombres();
      for (const a of nuevas.reverse()) {
        const critica = a.nivel === "CRITICA";
        const estanque = nombres.get(a.estanque_id) || `Estanque ${a.estanque_id}`;
        aviso(
          `<strong>${critica ? "⚠ Alerta CRÍTICA" : "Alerta de PRECAUCIÓN"}</strong> · ` +
          `${escapar(estanque)}<br><span>${escapar(a.mensaje)}</span>`,
          critica ? "critica" : "precaucion",
          "/alertas"
        );
        pitido(critica);
        window.dispatchEvent(new CustomEvent("ts:alerta", { detail: a }));
      }
    } catch (_) { /* reintenta */ }
  }

  // Reemplaza las secciones indicadas con su versión actual del servidor. Se omite una sección
  // si el usuario está escribiendo en ella, para no borrar lo que tipea.
  async function recargarSecciones(selectores) {
    const r = await fetch(window.location.href, { credentials: "same-origin" });
    if (!r.ok) return null;
    const doc = new DOMParser().parseFromString(await r.text(), "text/html");
    for (const sel of selectores) {
      const actual = document.querySelector(sel);
      const nuevo = doc.querySelector(sel);
      if (!actual || !nuevo) continue;
      const enUso = actual.contains(document.activeElement) ||
        [...actual.querySelectorAll("input, textarea")].some((i) => i.value);
      if (enUso || actual.innerHTML === nuevo.innerHTML) continue;
      actual.innerHTML = nuevo.innerHTML;
      actual.classList.remove("actualizada");
      void actual.offsetWidth;
      actual.classList.add("actualizada");
    }
    return doc;
  }

  window.TS = { aviso, recargarSecciones };
  cargarNombres().finally(revisarAlertas);
  setInterval(revisarAlertas, INTERVALO_ALERTAS_MS);
})();
