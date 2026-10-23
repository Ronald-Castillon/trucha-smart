"""db/schema.sql y db/seed.sql se cargan y respetan las restricciones de integridad."""

import sqlite3

import pytest

from tools.init_db import cargar_sqlite


@pytest.fixture
def bd():
    cx = sqlite3.connect(":memory:")
    cargar_sqlite(cx)
    yield cx
    cx.close()


def test_seed_carga_datos_demo(bd):
    conteos = {
        t: bd.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ("usuarios", "estanques", "lotes", "lecturas_agua")
    }
    assert conteos == {"usuarios": 3, "estanques": 3, "lotes": 3, "lecturas_agua": 168}
    roles = {r for (r,) in bd.execute("SELECT rol FROM usuarios")}
    assert roles == {"ADMINISTRADOR", "PISCICULTOR", "OPERARIO"}


def test_seed_cubre_siete_dias_de_lecturas(bd):
    desde, hasta = bd.execute("SELECT MIN(medido_en), MAX(medido_en) FROM lecturas_agua").fetchone()
    assert desde.startswith("2026-10-16") and hasta.startswith("2026-10-22")


def test_lote_con_cero_peces_es_rechazado(bd):
    with pytest.raises(sqlite3.IntegrityError):
        bd.execute(
            "INSERT INTO lotes (estanque_id, codigo, num_peces_inicial, peso_medio_inicial_g, "
            "peso_medio_actual_g, fecha_siembra) VALUES (1, 'X', 0, 10, 10, '2026-10-01')"
        )


def test_un_solo_lote_activo_por_estanque(bd):
    with pytest.raises(sqlite3.IntegrityError):
        bd.execute(
            "INSERT INTO lotes (estanque_id, codigo, num_peces_inicial, peso_medio_inicial_g, "
            "peso_medio_actual_g, fecha_siembra, activo) VALUES (1, 'X', 10, 10, 10, "
            "'2026-10-01', TRUE)"
        )


def test_lectura_con_ph_imposible_es_rechazada(bd):
    with pytest.raises(sqlite3.IntegrityError):
        bd.execute(
            "INSERT INTO lecturas_agua (estanque_id, temperatura_c, oxigeno_mg_l, ph, fuente, "
            "medido_en) VALUES (1, 12, 8, 15, 'MANUAL', '2026-10-23 00:00:00')"
        )


def test_clave_foranea_de_estanque_inexistente(bd):
    with pytest.raises(sqlite3.IntegrityError):
        bd.execute(
            "INSERT INTO lecturas_agua (estanque_id, temperatura_c, oxigeno_mg_l, ph, fuente, "
            "medido_en) VALUES (999, 12, 8, 7, 'MANUAL', '2026-10-23 00:00:00')"
        )


def test_modelos_orm_coinciden_con_schema_sql(bd):
    """Cada tabla del ORM existe en db/schema.sql con exactamente las mismas columnas."""
    from src.adapters.outbound.persistence import orm  # noqa: F401
    from src.adapters.outbound.persistence.db import Base

    for nombre, tabla in Base.metadata.tables.items():
        columnas_sql = {fila[1] for fila in bd.execute(f"PRAGMA table_info({nombre})")}
        assert columnas_sql, f"La tabla {nombre} no existe en schema.sql"
        assert {c.name for c in tabla.columns} == columnas_sql, nombre


def test_mensajes_de_alertas_del_seed_siguen_el_formato_del_dominio(bd):
    """Regresión Issue #11: el seed usa el mismo formato de mensaje que Umbral.describir."""
    from src.domain.model.lectura_agua import Parametro
    from src.domain.model.umbral import Nivel
    from tests.umbrales import UMBRALES

    filas = bd.execute("SELECT parametro, nivel, valor, mensaje FROM alertas").fetchall()
    assert filas
    for parametro, nivel, valor, mensaje in filas:
        esperado = UMBRALES.de(Parametro(parametro)).describir(valor, Nivel(nivel))
        assert mensaje == esperado
