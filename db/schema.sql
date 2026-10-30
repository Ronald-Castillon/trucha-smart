-- =============================================================================
-- TruchaSmart · Esquema de base de datos (dialecto PostgreSQL 16)
-- Se ejecuta automáticamente en docker-compose (/docker-entrypoint-initdb.d).
-- Para SQLite, tools/init_db.py aplica una traducción mínima de tipos (ADR-003).
-- Todas las fechas/horas se guardan en UTC.
-- =============================================================================

CREATE TABLE usuarios (
    id               SERIAL PRIMARY KEY,
    nombre_usuario   VARCHAR(50)  NOT NULL UNIQUE,
    nombre_completo  VARCHAR(120) NOT NULL,
    password_hash    VARCHAR(255) NOT NULL,
    rol              VARCHAR(20)  NOT NULL
                     CHECK (rol IN ('ADMINISTRADOR', 'PISCICULTOR', 'OPERARIO')),
    activo           BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en        TIMESTAMPTZ  NOT NULL
);

CREATE TABLE estanques (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(80)   NOT NULL UNIQUE,
    tipo        VARCHAR(10)   NOT NULL CHECK (tipo IN ('ESTANQUE', 'JAULA')),
    volumen_m3  NUMERIC(10,2) CHECK (volumen_m3 IS NULL OR volumen_m3 > 0),
    ubicacion   VARCHAR(120),
    activo      BOOLEAN       NOT NULL DEFAULT TRUE,
    creado_en   TIMESTAMPTZ   NOT NULL
);

CREATE TABLE lotes (
    id                    SERIAL PRIMARY KEY,
    estanque_id           INTEGER       NOT NULL REFERENCES estanques(id) ON DELETE RESTRICT,
    codigo                VARCHAR(40)   NOT NULL UNIQUE,
    num_peces_inicial     INTEGER       NOT NULL CHECK (num_peces_inicial > 0),
    peso_medio_inicial_g  NUMERIC(10,2) NOT NULL CHECK (peso_medio_inicial_g > 0),
    peso_medio_actual_g   NUMERIC(10,2) NOT NULL CHECK (peso_medio_actual_g > 0),
    fecha_siembra         DATE          NOT NULL,
    activo                BOOLEAN       NOT NULL DEFAULT TRUE,
    fecha_cierre          DATE
);
CREATE INDEX ix_lotes_estanque ON lotes (estanque_id);
-- Un estanque tiene como máximo un lote activo (RF-02).
CREATE UNIQUE INDEX ux_lotes_un_activo_por_estanque ON lotes (estanque_id) WHERE activo;

CREATE TABLE lecturas_agua (
    id               SERIAL PRIMARY KEY,
    estanque_id      INTEGER      NOT NULL REFERENCES estanques(id) ON DELETE RESTRICT,
    temperatura_c    NUMERIC(5,2) NOT NULL CHECK (temperatura_c BETWEEN 0 AND 40),
    oxigeno_mg_l     NUMERIC(5,2) NOT NULL CHECK (oxigeno_mg_l >= 0),
    ph               NUMERIC(4,2) NOT NULL CHECK (ph BETWEEN 0 AND 14),
    fuente           VARCHAR(10)  NOT NULL CHECK (fuente IN ('MANUAL', 'SENSOR')),
    registrado_por   INTEGER      REFERENCES usuarios(id) ON DELETE SET NULL,
    medido_en        TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_lecturas_estanque_fecha ON lecturas_agua (estanque_id, medido_en);

CREATE TABLE alertas (
    id              SERIAL PRIMARY KEY,
    estanque_id     INTEGER      NOT NULL REFERENCES estanques(id) ON DELETE RESTRICT,
    lectura_id      INTEGER      NOT NULL REFERENCES lecturas_agua(id) ON DELETE CASCADE,
    parametro       VARCHAR(20)  NOT NULL
                    CHECK (parametro IN ('TEMPERATURA', 'OXIGENO_DISUELTO', 'PH')),
    nivel           VARCHAR(12)  NOT NULL CHECK (nivel IN ('PRECAUCION', 'CRITICA')),
    valor           NUMERIC(6,2) NOT NULL,
    mensaje         VARCHAR(255) NOT NULL,
    estado          VARCHAR(10)  NOT NULL DEFAULT 'ABIERTA'
                    CHECK (estado IN ('ABIERTA', 'ATENDIDA')),
    creada_en       TIMESTAMPTZ  NOT NULL,
    atendida_por    INTEGER      REFERENCES usuarios(id) ON DELETE SET NULL,
    atendida_en     TIMESTAMPTZ,
    observacion     VARCHAR(255),
    CHECK (estado = 'ABIERTA' OR (atendida_por IS NOT NULL AND atendida_en IS NOT NULL))
);
CREATE INDEX ix_alertas_estanque_fecha ON alertas (estanque_id, creada_en);
CREATE INDEX ix_alertas_abiertas ON alertas (estanque_id, parametro, nivel, estado);

CREATE TABLE registros_alimentacion (
    id               SERIAL PRIMARY KEY,
    lote_id          INTEGER       NOT NULL REFERENCES lotes(id) ON DELETE RESTRICT,
    cantidad_kg      NUMERIC(10,3) NOT NULL CHECK (cantidad_kg > 0),
    registrado_por   INTEGER       REFERENCES usuarios(id) ON DELETE SET NULL,
    registrado_en    TIMESTAMPTZ   NOT NULL
);
CREATE INDEX ix_alimentacion_lote_fecha ON registros_alimentacion (lote_id, registrado_en);

CREATE TABLE registros_mortalidad (
    id               SERIAL PRIMARY KEY,
    lote_id          INTEGER      NOT NULL REFERENCES lotes(id) ON DELETE RESTRICT,
    cantidad         INTEGER      NOT NULL CHECK (cantidad > 0),
    causa            VARCHAR(120),
    registrado_por   INTEGER      REFERENCES usuarios(id) ON DELETE SET NULL,
    registrado_en    TIMESTAMPTZ  NOT NULL
);
CREATE INDEX ix_mortalidad_lote_fecha ON registros_mortalidad (lote_id, registrado_en);

-- Claves de integración para sistemas externos (RF-09). Solo se guarda la huella SHA-256.
CREATE TABLE claves_integracion (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(80)  NOT NULL,
    prefijo      VARCHAR(16)  NOT NULL,
    hash_clave   VARCHAR(64)  NOT NULL UNIQUE,
    creada_en    TIMESTAMPTZ  NOT NULL,
    creada_por   INTEGER      REFERENCES usuarios(id) ON DELETE SET NULL,
    activa       BOOLEAN      NOT NULL DEFAULT TRUE,
    ultimo_uso   TIMESTAMPTZ
);
