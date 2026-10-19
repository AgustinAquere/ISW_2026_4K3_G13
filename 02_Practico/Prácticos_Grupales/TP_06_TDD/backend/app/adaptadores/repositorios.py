class RepositorioUsuariosEnMemoria:
    def __init__(self, emails_registrados=()):
        self._emails = set(emails_registrados)

    def esta_registrado(self, email):
        return email in self._emails


class RepositorioComprasEnMemoria:
    def __init__(self):
        self._compras = {}
        self._ultimo_id = 0

    def guardar(self, compra):
        self._ultimo_id += 1
        compra.id = self._ultimo_id
        self._compras[compra.id] = compra
        return compra

    def obtener(self, id_compra):
        return self._compras.get(id_compra)

    def listar(self):
        return list(self._compras.values())

    def actualizar_estado(self, compra):
        self._compras[compra.id] = compra

    def entradas_compradas(self, email, fecha_visita):
        return sum(
            compra.cantidad
            for compra in self._compras.values()
            if compra.email_usuario == email
            and compra.fecha_visita == fecha_visita
        )
