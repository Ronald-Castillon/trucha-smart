"""Adaptador del puerto HasherPassword con bcrypt."""

import bcrypt


class HasherBcrypt:
    def __init__(self, rondas: int = 12) -> None:
        self._rondas = rondas

    def hashear(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(self._rondas)).decode()

    def verificar(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False
