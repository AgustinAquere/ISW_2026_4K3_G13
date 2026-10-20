"""Repositorios en memoria, para las pruebas."""

from app.dominio.modelos import EstadoCompra


class RepositorioUsuariosEnMemoria:
    """Usuarios registrados, guardados en memoria."""

    def __init__(self, emails_registrados=()):
        """Recibe los emails que ya están registrados."""
        self._emails = set(emails_registrados)

    def esta_registrado(self, email):
        """Indica si el email está registrado."""
        return email in self._emails

    def registrar(self, email):
        """Registra el email; devuelve False si ya estaba registrado."""
        if email in self._emails:
            return False
        self._emails.add(email)
        return True


class RepositorioComprasEnMemoria:
    """Compras guardadas en memoria."""

    def __init__(self):
        """Empieza sin compras."""
        self._compras = {}
        self._ultimo_id = 0

    def guardar(self, compra):
        """Guarda la compra, le asigna un número y la devuelve."""
        self._ultimo_id += 1
        compra.id = self._ultimo_id
        self._compras[compra.id] = compra
        return compra

    def obtener(self, id_compra):
        """Devuelve la compra con ese número, o None si no existe."""
        return self._compras.get(id_compra)

    def listar(self):
        """Devuelve todas las compras."""
        return list(self._compras.values())

    def actualizar_estado(self, compra):
        """Guarda el nuevo estado de la compra."""
        self._compras[compra.id] = compra

    def entradas_compradas(self, email, fecha_visita):
        """Suma las entradas no anuladas del usuario para la fecha."""
        return sum(
            compra.cantidad
            for compra in self._compras.values()
            if compra.email_usuario == email
            and compra.fecha_visita == fecha_visita
            and compra.estado != EstadoCompra.ANULADA
        )
