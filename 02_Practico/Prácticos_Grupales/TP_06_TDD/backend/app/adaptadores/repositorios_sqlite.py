import json
from datetime import date

from app.dominio.modelos import Compra, MedioPago, TipoPase


class RepositorioUsuariosSQLite:
    def __init__(self, conexion, emails_registrados=()):
        self._conexion = conexion
        with self._conexion:
            self._conexion.execute(
                "CREATE TABLE IF NOT EXISTS usuarios (email TEXT PRIMARY KEY)"
            )
            self._conexion.executemany(
                "INSERT OR IGNORE INTO usuarios (email) VALUES (?)",
                [(email,) for email in emails_registrados],
            )

    def esta_registrado(self, email):
        fila = self._conexion.execute(
            "SELECT 1 FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        return fila is not None


class RepositorioComprasSQLite:
    # url_pago no se guarda: se genera después de registrar la compra.
    _COLUMNAS = (
        "id, email_usuario, fecha_visita, cantidad, edades, tipo_pase, "
        "medio_pago, total"
    )

    def __init__(self, conexion):
        self._conexion = conexion
        with self._conexion:
            self._conexion.execute(
                "CREATE TABLE IF NOT EXISTS compras ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "email_usuario TEXT NOT NULL, "
                "fecha_visita TEXT NOT NULL, "
                "cantidad INTEGER NOT NULL, "
                "edades TEXT NOT NULL, "
                "tipo_pase TEXT NOT NULL, "
                "medio_pago TEXT NOT NULL, "
                "total INTEGER NOT NULL)"
            )

    def guardar(self, compra):
        with self._conexion:
            cursor = self._conexion.execute(
                "INSERT INTO compras (email_usuario, fecha_visita, cantidad, "
                "edades, tipo_pase, medio_pago, total) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    compra.email_usuario,
                    compra.fecha_visita.isoformat(),
                    compra.cantidad,
                    json.dumps(compra.edades),
                    compra.tipo_pase.value,
                    compra.medio_pago.value,
                    compra.total,
                ),
            )
        compra.id = cursor.lastrowid
        return compra

    def obtener(self, id_compra):
        fila = self._conexion.execute(
            f"SELECT {self._COLUMNAS} FROM compras WHERE id = ?",
            (id_compra,),
        ).fetchone()
        return None if fila is None else self._a_compra(fila)

    def listar(self):
        filas = self._conexion.execute(
            f"SELECT {self._COLUMNAS} FROM compras ORDER BY id"
        ).fetchall()
        return [self._a_compra(fila) for fila in filas]

    @staticmethod
    def _a_compra(fila):
        id_compra, email, fecha, cantidad, edades, pase, pago, total = fila
        return Compra(
            id=id_compra,
            email_usuario=email,
            fecha_visita=date.fromisoformat(fecha),
            cantidad=cantidad,
            edades=json.loads(edades),
            tipo_pase=TipoPase(pase),
            medio_pago=MedioPago(pago),
            total=total,
        )
