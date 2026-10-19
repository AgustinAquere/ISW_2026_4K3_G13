from app.dominio.modelos import TipoPase

# Supuesto: el enunciado no fija precios. Se expresan en pesos y son
# configurables.
PRECIO_BASE = {
    TipoPase.REGULAR: 10000,
    TipoPase.VIP: 20000,
}

EDAD_MAXIMA_SIN_COSTO = 3
EDAD_MAXIMA_MENOR = 15
EDAD_MINIMA_JUBILADO = 60
DESCUENTO_POR_EDAD = 50  # porcentaje


def porcentaje_descuento(edad):
    if edad <= EDAD_MAXIMA_SIN_COSTO:
        return 100
    if edad <= EDAD_MAXIMA_MENOR or edad >= EDAD_MINIMA_JUBILADO:
        return DESCUENTO_POR_EDAD
    return 0


def calcular_precio_entrada(edad, tipo_pase):
    precio_base = PRECIO_BASE[tipo_pase]
    return precio_base * (100 - porcentaje_descuento(edad)) // 100
