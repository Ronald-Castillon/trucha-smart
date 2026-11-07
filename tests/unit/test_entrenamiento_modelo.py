"""CP-RF12-03 (MLOps): el entrenamiento es reproducible y supera a la regla del Incremento 3."""

import pytest

pytest.importorskip("sklearn", reason="instalar el extra [ml] para reentrenar el modelo")


def test_cp_rf12_03_reentrenar_reproduce_el_modelo_versionado():
    from tools.entrenar_modelo_riesgo import main

    assert main(["--verificar"]) == 0
