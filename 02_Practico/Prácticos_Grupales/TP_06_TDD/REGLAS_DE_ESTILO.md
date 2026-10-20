# Reglas de estilo de código

Ingeniería y Calidad de Software · UTN FRC · 2026 · 4K3 · Grupo 13

La consigna del TP 6 pide implementar la User Story con el lenguaje y el documento de estilos de código que el grupo eligió en el Trabajo Práctico 2. Ese documento no está en el repositorio. Por eso el grupo adopta como reglas de estilo:

- **[PEP 8](https://peps.python.org/pep-0008/):** la guía de estilo oficial de Python.
- **[PEP 257](https://peps.python.org/pep-0257/):** las convenciones para docstrings a las que remite PEP 8.

Este documento resume esas reglas y aclara qué decidió el grupo en los puntos que PEP 8 deja abiertos.

## Alcance

- **Se aplica a** todo el código Python del backend: `backend/app/` y `backend/tests/`.
- **No se aplica al front** (`backend/app/static/`, en HTML, CSS y JavaScript), porque PEP 8 es solo para Python.

## Cómo se verifica

Las reglas se verifican automáticamente con **Ruff**, salvo las marcadas con "—" en las tablas, que se cuidan en la revisión del código. La configuración está en [`backend/pyproject.toml`](backend/pyproject.toml). Desde `backend/`:

```bash
ruff check app tests          # reglas de PEP 8, PEP 257 y errores comunes
ruff format --check app tests # formato: sangría, espacios, comillas, saltos de línea
```

Los dos comandos tienen que terminar sin errores antes de cada commit.

Ruff está fijado en la versión 0.17.1 (`requirements.txt`). Parte de las reglas de espaciado de PEP 8 son *preview* en Ruff y pueden cambiar entre versiones; con la versión fija, el chequeo da lo mismo a todo el grupo.

Para contrastar, el verificador oficial de PEP 8 (`pycodestyle`) tampoco encuentra errores:

```bash
pip install pycodestyle
pycodestyle --max-line-length=79 --max-doc-length=72 app tests
```

## Reglas

### Diseño del código

| Regla | Ejemplo en el proyecto | Verificación |
|---|---|---|
| Sangría de 4 espacios, sin tabulaciones. | Todo el código. | `ruff format`, E1, W191 |
| Líneas de código de 79 columnas como máximo. | `line-length = 79` | E501 |
| Comentarios y docstrings de 72 columnas como máximo. | `max-doc-length = 72` | W505 |
| Líneas largas cortadas dentro de paréntesis, no con `\`. | Los mensajes de `CompraInvalidaError` en `compra_service.py`. | `ruff format` |
| Dos líneas en blanco entre funciones y clases de primer nivel; una entre métodos. | Todo el código. | E3, `ruff format` |
| Archivos en UTF-8, sin declaración de codificación. | Todo el código. | — |
| Sin espacios al final de la línea, y el archivo termina con un salto de línea. | Todo el código. | W291, W292, W293 |

### Imports

| Regla | Ejemplo en el proyecto | Verificación |
|---|---|---|
| Un import por línea, al principio del archivo, después del docstring del módulo. | `dependencias.py` | E401, E402 |
| Agrupados en este orden: biblioteca estándar, terceros y módulos propios, con una línea en blanco entre grupos. | `routers/compras.py` | I001 |
| Imports absolutos (`from app.dominio.modelos import ...`). Nada de `import *`. | Todo el código. | F403 |

### Espacios en expresiones

| Regla | Ejemplo en el proyecto | Verificación |
|---|---|---|
| Sin espacios dentro de paréntesis, corchetes o llaves, ni antes de una coma. | `calcular_precio_entrada(edad, tipo_pase)` | E201, E202, E203 |
| Un espacio a cada lado de la asignación y de los operadores de comparación y aritméticos. | `precio_base * (100 - porcentaje_descuento(edad)) // 100` | E225, E226 |
| Sin espacios alrededor de `=` en argumentos con nombre, salvo que tengan anotación de tipo. | `Compra(id=id_compra, ...)` | E251, E252 |

### Nombres

| Elemento | Convención | Ejemplo en el proyecto | Verificación |
|---|---|---|---|
| Módulos y paquetes | `minusculas_con_guiones_bajos` | `compra_service.py`, `mercado_pago_simulado` | N999 |
| Funciones, métodos y variables | `snake_case` | `validar_fecha_visita`, `entradas_compradas` | N802, N803, N806 |
| Clases | `PascalCase` | `ServicioCompra`, `RepositorioComprasSQLite` | N801 |
| Excepciones | `PascalCase` terminado en `Error` | `CompraInvalidaError` | N818 |
| Constantes | `MAYUSCULAS` | `CANTIDAD_MAXIMA`, `PRECIO_BASE` | — |
| Uso interno | prefijo `_` | `_validar_limite_por_fecha`, `_a_compra` | — |

### Comentarios y docstrings

- **Docstrings (PEP 257):**
  - Todo módulo, clase, función y método público tiene docstring.
  - La primera línea es un resumen de una sola línea, terminado en punto.
  - Si hace falta más detalle, va después de una línea en blanco.
  - Ejemplo: `validar_fecha_visita` en `dominio/calendario.py`.
- **Comentarios:** explican el *por qué* de una decisión, no repiten lo que hace el código. Ejemplo: el comentario de `PagoNoDisponibleError` en `ServicioCompra._iniciar_pago`.
- **Comentarios desactualizados:** se corrigen o se borran en el mismo commit que cambia el código.

### Recomendaciones de programación

| Regla | Ejemplo en el proyecto | Verificación |
|---|---|---|
| Comparar con `None` usando `is` o `is not`, nunca `==`. | `if compra is None` | E711 |
| Comparar tipos con `isinstance()`. | `isinstance(email, str)` en `routers/usuarios.py` | E721 |
| Nada de `except:` sin tipo: se captura la excepción concreta. | `except httpx.HTTPError as error` | E722 |
| Al traducir una excepción, se encadena con `raise ... from`. | Los routers, al pasar a `HTTPException`. | B904 |
| No usar `lambda` asignada a un nombre: se define una función. | `atender` en `mercado_pago_simulado/api.py` | E731 |
| No usar argumentos por defecto mutables. | `emails_registrados=()` | B006 |

## Decisiones del grupo en lo que PEP 8 deja abierto

- **Idioma:**
  - **Nombres, comentarios, docstrings y mensajes en español:** es el idioma de la User Story. Así el código usa el vocabulario del negocio (`fecha_visita`, `tipo_pase`, `medio_pago`).
  - **Nombres sin tildes ni ñ:** por ejemplo, `contrasena`.
- **Docstrings en español:** el resumen se escribe en tercera persona del presente ("Calcula el precio…", "Devuelve la compra…"). Es el equivalente en español del modo imperativo que PEP 257 pide en inglés.
- **Comillas dobles:** PEP 8 no elige entre simples y dobles. `ruff format` usa dobles y el grupo sigue esa elección.
- **Formato automático:** `ruff format` decide los saltos de línea y la coma final en las listas largas. Así el estilo no depende de quién escribe el código.
- **Pruebas sin docstrings:** las funciones de prueba no son API pública. Su nombre ya describe el caso y el número de caso del backlog (por ejemplo, `test_cp13_lunes_es_rechazado`). En `tests/` se aplican todas las demás reglas.
