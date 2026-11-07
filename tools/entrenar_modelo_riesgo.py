"""Entrena el modelo de riesgo de evento crítico (RF-12, ADR-007) con datos sintéticos.

1. Genera trayectorias de 36 h (una lectura cada 30 min) de temperatura, oxígeno disuelto y pH
   con ciclo diario y ruido, y eventos aleatorios: hipoxia (el OD cae), calentamiento (la
   temperatura sube) y falsas alarmas (una caída que se detiene antes del límite).
2. En cada trayectoria toma instantes t entre la hora 24 y la 30; las características se calculan
   con la misma función del dominio (src.domain.service.riesgo_modelo.caracteristicas) sobre las
   24 h previas, y la etiqueta es 1 si en (t, t + 6 h] el OD baja del límite o la temperatura lo
   supera. Se descartan instantes ya críticos (el dominio los informa sin modelo).
3. Separa entrenamiento y prueba por trayectoria (sin fuga entre conjuntos), entrena una
   regresión logística con características estandarizadas y la compara con la regla de
   tendencia del Incremento 3 (ADR-006) sobre el mismo conjunto de prueba.
4. Exporta models/riesgo/modelo_v1.json (sin pickle) y models/riesgo/tarjeta_modelo_v1.md.

Todo es reproducible con --semilla. Uso:
  pip install -e ".[ml]"
  python tools/entrenar_modelo_riesgo.py            # entrena y escribe el modelo
  python tools/entrenar_modelo_riesgo.py --verificar # reentrena y compara con el archivo guardado
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.domain.model.lectura_agua import Parametro  # noqa: E402
from src.domain.model.umbral import Umbral  # noqa: E402
from src.domain.service.predictor_tendencia import EstadoPrediccion, predecir  # noqa: E402
from src.domain.service.riesgo_modelo import CARACTERISTICAS, caracteristicas  # noqa: E402

VERSION = "riesgo-v1"
DESTINO = RAIZ / "models" / "riesgo"
OD_LIMITE, T_LIMITE = 5.0, 18.0  # límites de precaución de config/umbrales.yaml
PASO = timedelta(minutes=30)
HORAS = 36
UMBRAL_OD = Umbral(Parametro.OXIGENO_DISUELTO, "mg/L", 7.0, None, OD_LIMITE, None)
UMBRAL_T = Umbral(Parametro.TEMPERATURA, "°C", 10.0, 16.0, 8.0, T_LIMITE)
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def trayectoria(rnd: random.Random) -> list[tuple[datetime, float, float, float]]:
    od0, t0, ph0 = rnd.uniform(6.8, 9.5), rnd.uniform(10.0, 14.5), rnd.uniform(6.8, 7.8)
    fase = rnd.uniform(0, 24)
    evento = rnd.choices(["ninguno", "hipoxia", "calor", "falsa_alarma"], [0.40, 0.30, 0.15, 0.15])[
        0
    ]
    inicio = rnd.uniform(18, 33)
    tasa = rnd.uniform(0.12, 0.8)
    duracion_falsa = rnd.uniform(2, 5)
    puntos = []
    for i in range(int(HORAS * 2) + 1):
        h = i * 0.5
        ciclo = math.sin(2 * math.pi * (h + fase - 14) / 24)
        od = od0 + 0.5 * ciclo + rnd.gauss(0, 0.12)
        t = t0 + 0.8 * ciclo + rnd.gauss(0, 0.08)
        ph = ph0 + rnd.gauss(0, 0.04)
        d = max(0.0, h - inicio)
        if evento == "hipoxia":
            od -= tasa * d
        elif evento == "calor":
            t += tasa * 0.6 * d
        elif evento == "falsa_alarma":
            od -= tasa * 0.6 * min(d, duracion_falsa)
        puntos.append((T0 + i * PASO, round(t, 2), round(max(od, 0.0), 2), round(ph, 2)))
    return puntos


def muestras(tray, id_tray):
    filas = []
    for k in range(48, 61, 2):  # t entre la hora 24 y la 30, cada hora
        t = tray[k][0]
        ventana = [p for p in tray if t - timedelta(hours=24) < p[0] <= t]
        x = caracteristicas(ventana, OD_LIMITE, T_LIMITE)
        if x is None or x["od_margen"] < 0 or x["t_margen"] < 0:
            continue
        futuro = [p for p in tray if t < p[0] <= t + timedelta(hours=6)]
        y = int(any(od < OD_LIMITE or temp > T_LIMITE for _, temp, od, _ in futuro))
        regla = any(
            predecir(par, [(m, v) for m, v in serie], umb).estado
            in (EstadoPrediccion.RIESGO, EstadoPrediccion.YA_CRITICO)
            for par, serie, umb in (
                (Parametro.OXIGENO_DISUELTO, [(m, od) for m, _, od, _ in ventana], UMBRAL_OD),
                (Parametro.TEMPERATURA, [(m, temp) for m, temp, _, _ in ventana], UMBRAL_T),
            )
        )
        filas.append((id_tray, [x[c] for c in CARACTERISTICAS], y, int(regla)))
    return filas


def metricas(y, pred, prob=None):
    m = {
        "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
    }
    if prob is not None:
        m["auc"] = round(float(roc_auc_score(y, prob)), 4)
    return m


def entrenar(semilla: int, n: int) -> tuple[dict, dict]:
    rnd = random.Random(semilla)
    filas = [f for i in range(n) for f in muestras(trayectoria(rnd), i)]
    ids = sorted({f[0] for f in filas})
    random.Random(semilla + 1).shuffle(ids)
    prueba_ids = set(ids[: len(ids) // 4])
    entrena = [f for f in filas if f[0] not in prueba_ids]
    prueba = [f for f in filas if f[0] in prueba_ids]
    xe, ye = np.array([f[1] for f in entrena]), np.array([f[2] for f in entrena])
    xp, yp = np.array([f[1] for f in prueba]), np.array([f[2] for f in prueba])
    escalador = StandardScaler().fit(xe)
    clf = LogisticRegression(C=1.0, max_iter=2000).fit(escalador.transform(xe), ye)
    prob = clf.predict_proba(escalador.transform(xp))[:, 1]
    modelo = {
        "version": VERSION,
        "algoritmo": "Regresión logística (scikit-learn) sobre características estandarizadas",
        "caracteristicas": list(CARACTERISTICAS),
        "media": [round(float(v), 6) for v in escalador.mean_],
        "escala": [round(float(v), 6) for v in escalador.scale_],
        "coeficientes": [round(float(v), 6) for v in clf.coef_[0]],
        "intercepto": round(float(clf.intercept_[0]), 6),
        "datos": "Sintéticos (no hay historial real etiquetado); ver tarjeta_modelo_v1.md",
        "semilla": semilla,
        "trayectorias": n,
    }
    # ejemplos para verificar que el adaptador reproduce exactamente al modelo entrenado
    modelo["ejemplos_verificacion"] = [
        {"x": dict(zip(CARACTERISTICAS, map(float, xp[i]), strict=True)),
         "probabilidad": round(float(prob[i]), 6)}
        for i in range(0, len(xp), max(1, len(xp) // 5))
    ][:5]  # fmt: skip
    informe = {
        "muestras": {"entrenamiento": len(entrena), "prueba": len(prueba),
                     "positivos_prueba": int(yp.sum()), "trayectorias_prueba": len(prueba_ids)},
        "modelo_umbral_0_5": metricas(yp, (prob >= 0.5).astype(int), prob),
        "modelo_umbral_alto_0_6": metricas(yp, (prob >= 0.6).astype(int)),
        "regla_tendencia_inc3": metricas(yp, np.array([f[3] for f in prueba])),
    }  # fmt: skip
    return modelo, informe


def tarjeta(modelo: dict, informe: dict) -> str:
    m, r, a = (
        informe["modelo_umbral_0_5"],
        informe["regla_tendencia_inc3"],
        informe["modelo_umbral_alto_0_6"],
    )
    s = informe["muestras"]
    coef = sorted(
        zip(modelo["caracteristicas"], modelo["coeficientes"], strict=True),
        key=lambda c: -abs(c[1]),
    )
    return "\n".join([
        f"# Tarjeta del modelo `{modelo['version']}` (RF-12, ADR-007)",
        "",
        "Generada por `tools/entrenar_modelo_riesgo.py`; no se edita a mano.",
        "",
        "## Uso previsto",
        "Estimar la probabilidad de que un estanque llegue a condición crítica (OD < 5 mg/L o",
        "temperatura > 18 °C) en las próximas 6 h, para priorizar revisiones. Es apoyo a la",
        "decisión: no reemplaza las alertas por umbral ni el criterio del técnico.",
        "",
        "## Datos",
        f"- **Sintéticos**: {modelo['trayectorias']} trayectorias de 36 h "
        f"(semilla {modelo['semilla']}) con",
        "  ciclo diario, ruido y eventos de hipoxia, calentamiento y falsas alarmas.",
        f"- Entrenamiento: {s['entrenamiento']} muestras; prueba: {s['prueba']} muestras de",
        f"  {s['trayectorias_prueba']} trayectorias no vistas ({s['positivos_prueba']} positivas).",
        "- **Limitación**: no hay historial real etiquetado de la piscigranja. Las métricas miden",
        "  qué tan bien el modelo aprende el generador sintético, no su desempeño en campo.",
        "",
        "## Métricas en el conjunto de prueba",
        "",
        "| Método | Precisión | Recall | F1 | AUC |",
        "|---|---:|---:|---:|---:|",
        f"| Modelo, umbral 0.5 | {m['precision']} | {m['recall']} | {m['f1']} | {m['auc']} |",
        f"| Modelo, umbral ALTO 0.6 | {a['precision']} | {a['recall']} | {a['f1']} | — |",
        f"| Regla de tendencia del Inc. 3 (ADR-006) | {r['precision']} | {r['recall']} "
        f"| {r['f1']} | — |",
        "",
        "## Coeficientes (características estandarizadas)",
        "",
        "| Característica | Coeficiente |",
        "|---|---:|",
        *[f"| `{c}` | {v:+.3f} |" for c, v in coef],
        f"| intercepto | {modelo['intercepto']:+.3f} |",
        "",
        "## Antes de usarlo en producción",
        "Reentrenar con lecturas reales etiquetadas (eventos críticos registrados en las alertas),",
        "validar con el técnico de la piscigranja y comparar otra vez con la regla del Inc. 3.",
        "",
    ])  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--semilla", type=int, default=2026)
    ap.add_argument("--trayectorias", type=int, default=1500)
    ap.add_argument("--verificar", action="store_true", help="reentrena y compara con el archivo")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    modelo, informe = entrenar(args.semilla, args.trayectorias)
    print(json.dumps(informe, ensure_ascii=False, indent=2))
    ruta = DESTINO / "modelo_v1.json"
    if args.verificar:
        guardado = json.loads(ruta.read_text(encoding="utf-8"))
        claves = ("media", "escala", "coeficientes", "intercepto")
        iguales = all(guardado[k] == modelo[k] for k in claves)
        mejor = informe["modelo_umbral_0_5"]["f1"] > informe["regla_tendencia_inc3"]["f1"]
        print(
            f"Modelo reproducible: {'sí' if iguales else 'NO'} · F1 del modelo mayor que el de "
            f"la regla del Inc. 3: {'sí' if mejor else 'NO'}"
        )
        return 0 if iguales and mejor else 1
    DESTINO.mkdir(parents=True, exist_ok=True)
    modelo["metricas_prueba"] = informe
    ruta.write_text(
        json.dumps(modelo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (DESTINO / "tarjeta_modelo_v1.md").write_text(
        tarjeta(modelo, informe), encoding="utf-8", newline="\n"
    )
    print(f"Escrito {ruta.relative_to(RAIZ)} y tarjeta_modelo_v1.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
