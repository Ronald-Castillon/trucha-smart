# C4 · Nivel 3 — Diagrama de componentes (aplicación FastAPI)

```mermaid
flowchart LR
    subgraph IN["adapters/inbound"]
        REST["rest/ routers FastAPI + esquemas Pydantic"]
        WEB["web/ plantillas Jinja2"]
        SIM["simulator/ sensor simulado"]
    end

    subgraph PIN["ports/inbound (casos de uso)"]
        P1["registrar_usuario · autenticar"]
        P2["gestionar_estanque"]
        P3["registrar_lectura · atender_alerta"]
        P4["consultar_historial"]
        P5["registrar_alimentacion · recomendar_racion"]
        P6["exportar_reporte"]
    end

    subgraph DOM["domain"]
        MODEL["model/ usuario, estanque, lote, lectura_agua, umbral, alerta, registro_alimentacion, registro_mortalidad"]
        SRV["service/ evaluador_calidad_agua, indice_riesgo, calculadora_fcr, recomendador_racion + casos de uso"]
    end

    subgraph POUT["ports/outbound"]
        REPO["repositorios (usuario, estanque, lote, lectura, alerta, alimentacion, mortalidad)"]
        OTH["notificador · generador_reportes · hasher_password · reloj"]
    end

    subgraph OUT["adapters/outbound"]
        PERS["persistence/ SQLAlchemy"]
        NOTI["notification/"]
        REP["reports/ PDF y CSV"]
        SEC["security/ bcrypt y JWT"]
    end

    REST --> PIN
    WEB --> PIN
    SIM -- HTTP --> REST
    PIN --> SRV
    SRV --> MODEL
    SRV --> POUT
    PERS -. implementa .-> REPO
    NOTI -. implementa .-> OTH
    REP -. implementa .-> OTH
    SEC -. implementa .-> OTH
```

Regla de dependencia: `adapters -> ports -> domain`. `domain` y `ports` solo usan la biblioteca
estándar (verificado por `tools/check_domain_purity.py` e import-linter).
