# Ciclo TDD — HU-01 Comprar entradas

Trabajo Práctico 6 — TDD · Ingeniería y Calidad de Software · UTN FRC · 4K3 · Grupo 13

Este documento muestra cómo se aplicó el ciclo Red-Green-Refactor para construir la User Story y cómo se comprobó que las pruebas automatizadas son efectivas. Las decisiones de diseño y los supuestos están en [DECISIONES_DE_DISENO.md](DECISIONES_DE_DISENO.md), y los casos de prueba en [BACKLOG.md](BACKLOG.md).

## 1. El ciclo Red-Green-Refactor

1. **Red:** se escribe una prueba para un comportamiento que el sistema **todavía no tiene**, y se ejecuta para verla fallar. Esto demuestra que la prueba es capaz de detectar la ausencia de ese comportamiento.
2. **Green:** se escribe el código **mínimo** para que la prueba pase, sin romper las anteriores.
3. **Refactor:** se mejora el diseño (nombres, duplicación, estructura) con todas las pruebas en verde, que actúan como red de seguridad.

**Red no significa "probar un valor incorrecto".** Hay que distinguir dos cosas:

- **Qué verifica la prueba:** una prueba *positiva* espera que la compra se acepte; una prueba *negativa* espera que se rechace (por ejemplo, comprar 11 entradas).
- **En qué estado está:** *Red* es cuando la prueba falla porque el sistema todavía no hace lo esperado; *Green* es cuando pasa.

Por ejemplo, la prueba de CP-10 espera que comprar 11 entradas lance `CompraInvalidaError`. Antes de implementar la validación, el sistema aceptaba la compra y la prueba fallaba (**Red**). Después de implementarla, el sistema rechaza la compra y la prueba pasa (**Green**). Que la tarjeta de la User Story indique "(falla)" para esa prueba de usuario se refiere a que **la compra** se rechaza, no a que la prueba automatizada quede en rojo.

Un buen Red falla **por el motivo correcto**: el mensaje de la falla describe el comportamiento que falta (por ejemplo, `assert 200 == 401`: "se esperaba 401 y la API respondió 200").

## 2. Registro de los ciclos

| Ciclo | Casos | Red (prueba que falla) | Green (código mínimo) | Refactor |
|---|---|---|---|---|
| 0 | CP-02 a CP-06 | *(realizado por el grupo)* faltan campos → se esperaba 422 | `CompraRequest` con campos obligatorios | — |
| 1 | CP-07 | sin sesión se esperaba 401 y la API respondía 200; además fallaba la importación de servicio y adaptadores | cabecera `X-Usuario-Email`, `ServicioCompra` que verifica el usuario en `RepositorioUsuariosEnMemoria` | pruebas de API movidas a `test_api_compras.py` con un helper de solicitud válida; las pruebas existentes reciben la cabecera para fallar solo por el dato faltante |
| 2 | CP-08 a CP-11, CP-27 | `CompraInvalidaError` inexistente | validación de rango 1..10 y de una edad por entrada | el mensaje usa la constante `CANTIDAD_MAXIMA` en lugar del número fijo |
| 3 | CP-12 a CP-17 | módulo `calendario` inexistente | `validar_fecha_visita(fecha, ahora)` y `esta_abierto(fecha)` | — |
| 4 | CP-18 a CP-22 | módulo `precios` y enum `TipoPase` inexistentes | `calcular_precio_entrada`, validación de edad negativa, total de la compra | `comprar()` dividido en `_validar`, `_validar_cantidad_y_edades` y `_calcular_total` |
| 5 | CP-23 a CP-26 | `RepositorioComprasEnMemoria`, `url_pago`, `resumen()` inexistentes | registro de la compra, pago con Mercado Pago simulado, envío del mail, resumen | — |
| 6 | CP-01, contrato HTTP | 7 pruebas fallan: la API devolvía 200 sin datos, aceptaba `"COMUN"` y no traducía errores a 400 | `CompraResponse`, enums en el esquema, mapeo de errores a 400/401, composición en `dependencias.py` | `CompraResponse.desde_compra()`; ajustes de estilo con Ruff (`Annotated` en dependencias, `raise ... from`, líneas ≤ 79) |
| 7 | Persistencia en SQLite | 10 pruebas nuevas en `test_repositorios_sqlite.py`; falla la importación porque `repositorios_sqlite` no existe | `RepositorioUsuariosSQLite` y `RepositorioComprasSQLite` con `sqlite3` | `dependencias.py` usa los repositorios SQLite sobre `backend/ecoharmony.db`, sin cambios en el dominio ni en el servicio |
| 8 | CP-28 (FAQ 27 del PO) | el servicio aceptaba 6 + 5 entradas para la misma fecha (`DID NOT RAISE CompraInvalidaError`) y `RepositorioComprasSQLite` no tenía `entradas_compradas` (`AttributeError`) | `entradas_compradas(email, fecha)` en ambos repositorios y `_validar_limite_por_fecha` en `ServicioCompra` | orden de imports y largo de línea de las pruebas nuevas con Ruff |
| 9 | Mercado Pago Checkout Pro | `PasarelaMercadoPago` y `PagoNoDisponibleError` inexistentes; con tarjeta y total $0 se redirigía a Mercado Pago (`assert '...SIMULADO-1' is None`) | `PasarelaMercadoPago` con `httpx`, `total > 0` en el servicio, 502 en el router | imports del router agrupados con Ruff |
| 10 | Mail por SMTP | `NotificadorSMTP` inexistente | `NotificadorSMTP` con `smtplib`, STARTTLS y el error registrado en el log | cuerpo del mail en una función aparte (`_cuerpo_del_mail`) |
| 11 | Datos para el front | `fechas_disponibles` y `obtener_reloj` inexistentes | `fechas_disponibles(ahora)`, `GET /fechas-disponibles`, `POST /cotizacion`, front estático en `/` | la prueba de `GET /` que esperaba JSON se reemplazó por la del front |
| 12 | Configuración por `.env` | `crear_pasarela_pago`, `crear_notificador` y `usuarios_registrados` inexistentes | selección de adaptadores según la configuración | `dependencias.py` arma el servicio con esas funciones |
| 13 | CP-29: estado de la compra | `EstadoCompra` inexistente; la API no informaba el estado (`KeyError: 'estado'`) | con tarjeta la compra queda pendiente de pago y no envía el mail; SQLite guarda el estado y actualiza bases anteriores | `ServicioCompra._estado_inicial` |
| 14 | CP-30 a CP-33: confirmar el pago | `PagoInformado` y `CompraNoEncontradaError` inexistentes | `ServicioCompra.confirmar_pago`, `actualizar_estado` en los repositorios, pasarela simulada que vuelve al sitio aprobada | se quita la URL de checkout simulado sin uso |
| — | Fechas dinámicas en las pruebas | *(solo refactor)* | — | `tests/fechas.py`: ninguna prueba usa fechas fijas |
| 15 | Consulta del pago en Mercado Pago | `URL_PAGOS_MERCADO_PAGO` inexistente | `PasarelaMercadoPago.consultar_pago` y `auto_return` con URL https | cabecera de autorización en `_cabeceras()` |
| 16 | Endpoint de confirmación y CP-01 completo | las 5 pruebas reciben `405 Method Not Allowed` | `POST /compras/{id}/pago` | control de sesión en la dependencia `usuario_en_sesion` |
| 17 | Mail con el pago aprobado | 3 pruebas fallan: el mail no tiene número de compra y usa el link de pago para elegir el texto | el texto depende del medio de pago y del total | — |
| 18 | CP-34: Mercado Pago no disponible | `EstadoCompra.ANULADA` inexistente y un reintento se rechazaba con "ya compraste 6" | la compra se anula y no cuenta para el límite | `_iniciar_pago` y `_cambiar_estado` |
| 19 a 27 | Mercado Pago simulado y pago en otra pestaña (CP-35, CP-36) | ver sección 8 | ver sección 8 | ver sección 8 |

Al cerrar cada ciclo se ejecutó la batería completa de pruebas, que quedó en verde (52 pruebas al cerrar el ciclo 6, 62 al cerrar el ciclo 7, 68 al cerrar el ciclo 8, 93 al cerrar el ciclo 12, 129 al cerrar el ciclo 18, 201 al cerrar el ciclo 27, 236 al cerrar el ciclo 35, 251 con las pruebas complementarias de la sección 10 y 256 al cerrar el ciclo 37). Las mutaciones de la sección 3 se hicieron con 52 pruebas; las de los ciclos 7 y 8 están en las secciones 4 y 5, las de los ciclos 9 a 12, en la sección 6, las de los ciclos 13 a 18, en la sección 7, y las de los ciclos 19 a 27, en la sección 8.

Las secciones 3 a 6 citan fechas puntuales (por ejemplo, "el 09/11/2026") porque registran cómo eran las pruebas en ese momento. Desde el refactor de la sección 7.2, las pruebas calculan sus fechas a partir del día en que se ejecutan.

**Tipos de Red observados.** En los ciclos 1 y 6 el Red fue una falla de comportamiento: la aserción no se cumplía (por ejemplo, `assert 200 == 401`). En los ciclos 2 a 5 el Red fue una falla de importación: la prueba usaba algo que todavía no existía (`CompraInvalidaError`, los módulos `calendario` y `precios`, el repositorio de compras), por lo que pytest no podía ejecutarla. Ambos son válidos en TDD (Kent Beck considera Red también cuando la prueba "no compila"), pero el segundo tipo no muestra cada aserción fallando. Por eso, en la sección 3 se verificó cada prueba por separado mediante mutaciones.

## 3. Verificación de las pruebas (pruebas de mutación)

Que todas las pruebas pasen no demuestra que sean correctas: una prueba mal escrita puede pasar siempre. Para comprobar que **cada prueba es capaz de fallar y falla por el motivo correcto** (el "Red" de su caso), se aplicaron **mutaciones**: sobre una copia del código se rompe a propósito **una sola regla** por vez, se ejecuta la batería completa y se registra qué pruebas fallan.

- **Mutación detectada:** al menos una prueba falla. La prueba de esa regla es efectiva.
- **Mutación que sobrevive:** todas las pruebas siguen pasando. La prueba es débil o el código mutado es redundante.

Se hicieron dos rondas, en las dos sobre una copia y sin modificar el código de producción:

1. **Primera ronda:** 26 de 27 mutaciones detectadas. Se encontraron dos pruebas débiles (CP-07 y CP-12, ver hallazgos 1 y 2).
2. **Se reforzaron esas dos pruebas** (solo cambiaron las pruebas, no el código de la aplicación) y se verificó que la batería siguiera en verde: `52 passed`.
3. **Segunda ronda:** **27 de 27 mutaciones detectadas.**

### Resultado

| Caso | Mutación (regla que se rompe) | Primera ronda | Segunda ronda |
|---|---|---|---|
| CP-02 | Medio de pago opcional en el esquema | igual | ✅ Detectada (1 de 52 falla) |
| CP-07 (sin sesión) | Se quita el control de cabecera del router | ❌ **Sobrevive** (52 de 52 pasan) | ✅ Detectada (1 de 52 falla) |
| CP-07 (no registrado) | Se quita el control de usuario registrado del servicio | igual | ✅ Detectada (2 de 52 fallan) |
| CP-08 a CP-10 | Se quita la validación de cantidad | igual | ✅ Detectada (5 de 52 fallan) |
| CP-10 | Límite máximo 10 → 11 | igual | ✅ Detectada (3 de 52 fallan) |
| CP-11 | Límite mínimo 1 → 2 | igual | ✅ Detectada (2 de 52 fallan) |
| CP-27 | Se quita el control de una edad por entrada | igual | ✅ Detectada (1 de 52 falla) |
| CP-18 | Edad mínima 0 → -1 | igual | ✅ Detectada (1 de 52 falla) |
| CP-12 | Se acepta el día anterior a hoy | ⚠️ Detectada solo por el `match` (ver hallazgo 2) | ✅ Detectada (1 de 52 falla) |
| CP-13 | Se quita el cierre de los lunes | igual | ✅ Detectada (3 de 52 fallan) |
| CP-14 y CP-15 | Se quitan los feriados | igual | ✅ Detectada (2 de 52 fallan) |
| CP-16 | Anticipación máxima 31 → 32 días | igual | ✅ Detectada (1 de 52 falla) |
| CP-17 | Hora límite: `>` → `>=` | igual | ✅ Detectada (1 de 52 falla) |
| CP-19 | Gratis hasta 3 → hasta 2 años | igual | ✅ Detectada (1 de 52 falla) |
| CP-20 | Descuento de menores hasta 15 → hasta 14 años | igual | ✅ Detectada (1 de 52 falla) |
| CP-21 | Descuento de mayores desde 60 → desde 59 años | igual | ✅ Detectada (1 de 52 falla) |
| CP-22 | Descuento de mayores desde 60 → desde 61 años | igual | ✅ Detectada (1 de 52 falla) |
| Total | El total toma el máximo en lugar de la suma | igual | ✅ Detectada (2 de 52 fallan) |
| CP-23 | Siempre se redirige a Mercado Pago | igual | ✅ Detectada (2 de 52 fallan) |
| CP-24 | Nunca se redirige a Mercado Pago | igual | ✅ Detectada (2 de 52 fallan) |
| CP-25 | No se envía el mail | igual | ✅ Detectada (2 de 52 fallan) |
| Registro | No se guarda la compra | igual | ✅ Detectada (4 de 52 fallan) |
| Compra rechazada | Se valida después de guardar y enviar el mail | igual | ✅ Detectada (1 de 52 falla) |
| CP-26 (fecha) | Fecha del resumen en formato mm/dd/aaaa | igual | ✅ Detectada (3 de 52 fallan) |
| CP-26 (singular) | Siempre en plural | igual | ✅ Detectada (1 de 52 falla) |
| Medio de pago inexistente | El esquema acepta cualquier texto como medio de pago | igual | ✅ Detectada (1 de 52 falla) |
| Errores de negocio → 400 | Los errores de negocio se devuelven como 409 | igual | ✅ Detectada (2 de 52 fallan) |

"igual" indica que en la primera ronda fallaron las mismas pruebas con los mismos mensajes.

En casi todos los casos fallan **solo** las pruebas de la regla rota, mientras el resto sigue en verde. Esto muestra que las pruebas son independientes: cada una controla una regla concreta. Las mutaciones de valores límite (31 → 32 días, `>` → `>=` a las 17:30, edades 3/15/59/60) fallan exactamente en la prueba del borde, lo que confirma que se eligieron bien los valores límite.

### Hallazgos y mejoras aplicadas

1. **CP-07 (sin sesión): sobrevivía en la primera ronda. Corregido.** Al quitar del router el control `if x_usuario_email is None`, CP-07 seguía pasando: sin cabecera, el email llega como `None`, el servicio no lo encuentra registrado y lanza `UsuarioNoRegistradoError`, que el router también convierte en 401. La prueba solo verificaba el código 401, así que no distinguía "sin sesión" de "usuario no registrado". **Mejora:** las dos pruebas de CP-07 ahora verifican también el mensaje (`detail`). En la segunda ronda, la mutación se detecta:

   ```text
   AssertionError: assert 'Usuario no registrado' == 'Debe iniciar sesión'
   ```

2. **CP-12 (fecha pasada): se detectaba solo gracias al mensaje. Corregido.** La fecha de la prueba (09/11/2026, el día anterior al "hoy" de las pruebas) caía lunes. Con la mutación, el sistema igualmente rechazaba esa fecha, pero por estar cerrado el parque, y la prueba fallaba solo porque exigía `match="pasada"` (`Regex pattern did not match ... 'El parque está cerrado en la fecha elegida'`). **Mejora:** la prueba usa como "hoy" el miércoles 11/11/2026 y como visita el martes 10/11/2026. Sigue probando el valor límite (ayer), pero en un día abierto, así que depende de una sola regla. Usar una fecha más lejana, como el 08/11, habría evitado el lunes pero habría perdido el valor límite: la mutación "aceptar el día anterior" la seguiría rechazando. En la segunda ronda falla directamente con `DID NOT RAISE CompraInvalidaError`.

3. **CP-09 (cantidad negativa): el `match` es decisivo.** Sin la validación de cantidad, `-1` se rechaza igual, pero por el control de "una edad por entrada". La prueba lo detecta porque exige que el mensaje mencione la `cantidad`. Esto justifica verificar el motivo del error y no solo que haya un error.

4. **CP-02 y medio de pago inexistente: detectadas, pero no en la aserción.** La API acepta la solicitud inválida, pero falla después, al armar la respuesta (`ValidationError for CompraResponse`), antes de llegar al `assert ... == 422`. La prueba falla (Red), aunque el mensaje es menos claro que un `assert 201 == 422`.

### Salida de pytest de cada mutación (segunda ronda)

**CP-02 — Medio de pago opcional en el esquema**  
Cambio: `schemas.py`: `medio_pago: MedioPago` → `medio_pago: MedioPago | None = None`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_api_compras::test_comprar_sin_dato_obligatorio_es_rechazado[CP-02]
       ValidationError: 1 validation error for CompraResponse medio_pago Input should be 'EFECTIVO' or 'TARJETA'
```

**CP-07 (sin sesión) — Se quita el control de cabecera del router**  
Cambio: `compras.py`: `if x_usuario_email is None:` → `(se elimina)`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_api_compras::test_cp07_comprar_sin_iniciar_sesion_es_rechazado
       AssertionError: assert 'Usuario no registrado' == 'Debe iniciar sesión'
```

**CP-07 (no registrado) — Se quita el control de usuario registrado del servicio**  
Cambio: `compra_service.py`: `if not self._usuarios.esta_registrado(solicitud.email_usuario):` → `(se elimina)`  
Resultado: `2 failed, 50 passed`

```text
FAILED test_api_compras::test_cp07_comprar_con_usuario_no_registrado_es_rechazado
       assert 201 == 401
FAILED test_servicio_compra::test_cp07_usuario_no_registrado_no_puede_comprar
       Failed: DID NOT RAISE UsuarioNoRegistradoError
```

**CP-08 a CP-10 — Se quita la validación de cantidad**  
Cambio: `compra_service.py`: `if not 1 <= solicitud.cantidad <= CANTIDAD_MAXIMA:` → `if False:`  
Resultado: `5 failed, 47 passed`

```text
FAILED test_api_compras::test_cp10_api_rechaza_mas_de_10_entradas_con_mensaje
       assert 201 == 400
FAILED test_servicio_compra::test_cantidad_fuera_de_rango_es_rechazada[CP-08]
       Failed: DID NOT RAISE CompraInvalidaError
FAILED test_servicio_compra::test_cantidad_fuera_de_rango_es_rechazada[CP-09]
       AssertionError: Regex pattern did not match. Expected regex: 'cantidad' Actual message: 'Debe indicar la edad de cada visitante'
FAILED test_servicio_compra::test_cantidad_fuera_de_rango_es_rechazada[CP-10]
       Failed: DID NOT RAISE CompraInvalidaError
FAILED test_servicio_compra::test_compra_rechazada_no_envia_mail_ni_se_registra
       Failed: DID NOT RAISE CompraInvalidaError
```

**CP-10 — Límite máximo 10 → 11**  
Cambio: `compra_service.py`: `CANTIDAD_MAXIMA = 10` → `CANTIDAD_MAXIMA = 11`  
Resultado: `3 failed, 49 passed`

```text
FAILED test_api_compras::test_cp10_api_rechaza_mas_de_10_entradas_con_mensaje
       assert 201 == 400
FAILED test_servicio_compra::test_cantidad_fuera_de_rango_es_rechazada[CP-10]
       Failed: DID NOT RAISE CompraInvalidaError
FAILED test_servicio_compra::test_compra_rechazada_no_envia_mail_ni_se_registra
       Failed: DID NOT RAISE CompraInvalidaError
```

**CP-11 — Límite mínimo 1 → 2**  
Cambio: `compra_service.py`: `if not 1 <= solicitud.cantidad` → `if not 2 <= solicitud.cantidad`  
Resultado: `2 failed, 50 passed`

```text
FAILED test_servicio_compra::test_cp11_cantidad_entre_1_y_10_es_aceptada[CP-11-min]
       CompraInvalidaError: La cantidad de entradas debe estar entre 1 y 10
FAILED test_servicio_compra::test_cp26_resumen_en_singular_para_una_entrada
       CompraInvalidaError: La cantidad de entradas debe estar entre 1 y 10
```

**CP-27 — Se quita el control de una edad por entrada**  
Cambio: `compra_service.py`: `if len(solicitud.edades) != solicitud.cantidad:` → `if False:`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_servicio_compra::test_cp27_cantidad_distinta_a_edades_informadas_es_rechazada
       Failed: DID NOT RAISE CompraInvalidaError
```

**CP-18 — Edad mínima 0 → -1**  
Cambio: `compra_service.py`: `any(edad < 0 for` → `any(edad < -1 for`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_servicio_compra::test_cp18_edad_negativa_es_rechazada
       Failed: DID NOT RAISE CompraInvalidaError
```

**CP-12 — Se acepta el día anterior a hoy**  
Cambio: `calendario.py`: `if fecha_visita < hoy:` → `if fecha_visita < hoy - timedelta(days=1):`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_calendario::test_cp12_fecha_anterior_a_hoy_es_rechazada
       Failed: DID NOT RAISE CompraInvalidaError
```

**CP-13 — Se quita el cierre de los lunes**  
Cambio: `calendario.py`: `fecha.weekday() != LUNES` → `True`  
Resultado: `3 failed, 49 passed`

```text
FAILED test_api_compras::test_api_rechaza_fecha_con_parque_cerrado
       assert 201 == 400
FAILED test_calendario::test_cp13_lunes_es_rechazado
       Failed: DID NOT RAISE CompraInvalidaError
FAILED test_servicio_compra::test_compra_para_un_dia_cerrado_es_rechazada
       Failed: DID NOT RAISE CompraInvalidaError
```

**CP-14 y CP-15 — Se quitan los feriados**  
Cambio: `calendario.py`: `FERIADOS_CERRADO = {(1, 1), (12, 25)}` → `FERIADOS_CERRADO = set()`  
Resultado: `2 failed, 50 passed`

```text
FAILED test_calendario::test_feriado_en_que_cierra_el_parque_es_rechazado[CP-14-1-de-enero]
       Failed: DID NOT RAISE CompraInvalidaError
FAILED test_calendario::test_feriado_en_que_cierra_el_parque_es_rechazado[CP-15-25-de-diciembre]
       Failed: DID NOT RAISE CompraInvalidaError
```

**CP-16 — Anticipación máxima 31 → 32 días**  
Cambio: `calendario.py`: `DIAS_MAXIMOS_DE_ANTICIPACION = 31` → `DIAS_MAXIMOS_DE_ANTICIPACION = 32`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_calendario::test_cp16_fecha_a_mas_de_31_dias_es_rechazada
       Failed: DID NOT RAISE CompraInvalidaError
```

**CP-17 — Hora límite: `>` → `>=`**  
Cambio: `calendario.py`: `ahora.time() > HORA_LIMITE` → `ahora.time() >= HORA_LIMITE`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_calendario::test_cp17_comprar_para_hoy_a_las_17_30_es_aceptado
       CompraInvalidaError: Las entradas para hoy se venden hasta las 17:30
```

**CP-19 — Gratis hasta 3 → hasta 2 años**  
Cambio: `precios.py`: `EDAD_MAXIMA_SIN_COSTO = 3` → `EDAD_MAXIMA_SIN_COSTO = 2`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_precios::test_cp19_hasta_3_anios_no_tiene_costo[CP-19-3]
       AssertionError: assert 5000 == 0
```

**CP-20 — Descuento de menores hasta 15 → hasta 14 años**  
Cambio: `precios.py`: `EDAD_MAXIMA_MENOR = 15` → `EDAD_MAXIMA_MENOR = 14`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_precios::test_cp20_de_4_a_15_anios_tiene_50_por_ciento_de_descuento[CP-20-15]
       AssertionError: assert 10000 == (10000 / 2)
```

**CP-21 — Descuento de mayores desde 60 → desde 59 años**  
Cambio: `precios.py`: `EDAD_MINIMA_JUBILADO = 60` → `EDAD_MINIMA_JUBILADO = 59`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_precios::test_cp21_de_16_a_59_anios_paga_precio_completo[CP-21-59]
       AssertionError: assert 5000 == 10000
```

**CP-22 — Descuento de mayores desde 60 → desde 61 años**  
Cambio: `precios.py`: `EDAD_MINIMA_JUBILADO = 60` → `EDAD_MINIMA_JUBILADO = 61`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_precios::test_cp22_desde_60_anios_tiene_50_por_ciento_de_descuento[CP-22-60]
       AssertionError: assert 10000 == (10000 / 2)
```

**Total — El total toma el máximo en lugar de la suma**  
Cambio: `compra_service.py`: `return sum(` → `return max(`  
Resultado: `2 failed, 50 passed`

```text
FAILED test_api_compras::test_cp01_compra_con_tarjeta_mediante_mercado_pago_y_mail
       assert 20000 == 50000
FAILED test_servicio_compra::test_total_de_la_compra_suma_el_precio_de_cada_visitante
       AssertionError: assert 10000 == (10000 * 1.5)
```

**CP-23 — Siempre se redirige a Mercado Pago**  
Cambio: `compra_service.py`: `if compra.medio_pago == MedioPago.TARJETA:` → `if True:`  
Resultado: `2 failed, 50 passed`

```text
FAILED test_api_compras::test_cp23_api_compra_en_boleteria_sin_url_de_pago
       AssertionError: assert 'https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=SIMULADO-1' is None
FAILED test_servicio_compra::test_cp23_pago_en_boleteria_procesa_la_compra_sin_redirigir
       AssertionError: assert 'https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=SIMULADO-1' is None
```

**CP-24 — Nunca se redirige a Mercado Pago**  
Cambio: `compra_service.py`: `if compra.medio_pago == MedioPago.TARJETA:` → `if False:`  
Resultado: `2 failed, 50 passed`

```text
FAILED test_api_compras::test_cp01_compra_con_tarjeta_mediante_mercado_pago_y_mail
       AttributeError: 'NoneType' object has no attribute 'startswith'
FAILED test_servicio_compra::test_cp24_pago_con_tarjeta_redirige_a_mercado_pago
       AttributeError: 'NoneType' object has no attribute 'startswith'
```

**CP-25 — No se envía el mail**  
Cambio: `compra_service.py`: `self._notificador.enviar_confirmacion(compra)` → `(se elimina)`  
Resultado: `2 failed, 50 passed`

```text
FAILED test_api_compras::test_cp01_compra_con_tarjeta_mediante_mercado_pago_y_mail
       assert 0 == 1
FAILED test_servicio_compra::test_cp25_compra_exitosa_envia_mail_de_confirmacion
       AssertionError: assert [] == [Compra(email...rl_pago=None)] Right contains one more item
```

**Registro — No se guarda la compra**  
Cambio: `compra_service.py`: `self._compras.guardar(compra)` → `(se elimina)`  
Resultado: `4 failed, 48 passed`

```text
FAILED test_api_compras::test_cp01_compra_con_tarjeta_mediante_mercado_pago_y_mail
       ValidationError: 1 validation error for CompraResponse id Input should be a valid integer
FAILED test_api_compras::test_cp23_api_compra_en_boleteria_sin_url_de_pago
       ValidationError: 1 validation error for CompraResponse id Input should be a valid integer
FAILED test_api_compras::test_cp26_api_informa_cantidad_y_fecha_al_finalizar
       ValidationError: 1 validation error for CompraResponse id Input should be a valid integer
FAILED test_servicio_compra::test_compra_realizada_queda_registrada
       AssertionError: assert None is not None
```

**Compra rechazada — Se valida después de guardar y enviar el mail**  
Cambio: `compra_service.py`: `self._validar(solicitud)` → `compra = Compra(`<br>`compra_service.py`: `self._notificador.enviar_confirmacion(compra)` → `self._notificador.enviar_confirmacion(compra)`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_servicio_compra::test_compra_rechazada_no_envia_mail_ni_se_registra
       AssertionError: assert [Compra(email...rl_pago=None)] == [] Left contains one more item
```

**CP-26 (fecha) — Fecha del resumen en formato mm/dd/aaaa**  
Cambio: `modelos.py`: `{self.fecha_visita:%d/%m/%Y}` → `{self.fecha_visita:%m/%d/%Y}`  
Resultado: `3 failed, 49 passed`

```text
FAILED test_api_compras::test_cp26_api_informa_cantidad_y_fecha_al_finalizar
       AssertionError: assert 'Compraste 2 entradas para el 11/15/2026' == 'Compraste 2 entradas para el 15/11/2026'
FAILED test_servicio_compra::test_cp26_resumen_informa_cantidad_de_entradas_y_fecha
       AssertionError: assert 'Compraste 2 entradas para el 11/15/2026' == 'Compraste 2 entradas para el 15/11/2026'
FAILED test_servicio_compra::test_cp26_resumen_en_singular_para_una_entrada
       AssertionError: assert 'Compraste 1 entrada para el 11/15/2026' == 'Compraste 1 entrada para el 15/11/2026'
```

**CP-26 (singular) — Siempre en plural**  
Cambio: `modelos.py`: `"entrada" if self.cantidad == 1 else "entradas"` → `"entradas"`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_servicio_compra::test_cp26_resumen_en_singular_para_una_entrada
       AssertionError: assert 'Compraste 1 entradas para el 15/11/2026' == 'Compraste 1 entrada para el 15/11/2026'
```

**Medio de pago inexistente — El esquema acepta cualquier texto como medio de pago**  
Cambio: `schemas.py`: `medio_pago: MedioPago` → `medio_pago: str`  
Resultado: `1 failed, 51 passed`

```text
FAILED test_api_compras::test_opcion_inexistente_es_rechazada[medio-pago-inexistente]
       ValidationError: 1 validation error for CompraResponse medio_pago Input should be 'EFECTIVO' or 'TARJETA'
```

**Errores de negocio → 400 — Los errores de negocio se devuelven como 409**  
Cambio: `compras.py`: `status.HTTP_400_BAD_REQUEST` → `409`  
Resultado: `2 failed, 50 passed`

```text
FAILED test_api_compras::test_cp10_api_rechaza_mas_de_10_entradas_con_mensaje
       assert 409 == 400
FAILED test_api_compras::test_api_rechaza_fecha_con_parque_cerrado
       assert 409 == 400
```

## 4. Ciclo 7: persistencia con SQLite

Se reemplazaron los repositorios en memoria de la aplicación por repositorios SQLite, con el mismo ciclo:

1. **Red:** se escribieron las 10 pruebas de `tests/unit/test_repositorios_sqlite.py` antes que el código. La batería no pudo ejecutarse porque el módulo `app.adaptadores.repositorios_sqlite` no existía (`1 error during collection`).
2. **Green:** se implementaron `RepositorioUsuariosSQLite` y `RepositorioComprasSQLite` con `sqlite3`: `62 passed`.
3. **Refactor:** `dependencias.py` arma el servicio con los repositorios SQLite sobre `backend/ecoharmony.db`: `62 passed`. Además, se comprobó a mano que, tras reiniciar el servidor, la siguiente compra recibe el id 2: la primera compra sigue en la base.

Como el Red fue de importación, se verificaron las pruebas nuevas con mutaciones, igual que en la sección 3. Las 6 mutaciones se detectaron:

| Mutación (regla que se rompe) | Resultado | Prueba que la detecta |
|---|---|---|
| `INSERT OR IGNORE` → `INSERT` al cargar usuarios | ✅ Detectada (1 de 62 falla) | `test_cargar_un_usuario_ya_registrado_no_lo_duplica` |
| `esta_registrado` siempre devuelve `True` | ✅ Detectada (1 de 62 falla) | `test_usuario_no_cargado_no_esta_registrado` |
| `guardar` no asigna el id a la compra | ✅ Detectada (5 de 62 fallan) | `test_guardar_asigna_ids_correlativos`, entre otras |
| `guardar` no confirma la transacción (sin `with conexion`) | ✅ Detectada (1 de 62 falla) | `test_los_datos_persisten_al_reabrir_la_base` |
| Las edades se pierden al leer la compra | ✅ Detectada (4 de 62 fallan) | `test_obtener_devuelve_la_compra_guardada`, entre otras |
| `listar` devuelve las compras en orden inverso | ✅ Detectada (1 de 62 falla) | `test_listar_devuelve_todas_las_compras_en_orden` |

La mutación de la transacción solo la detecta la prueba que cierra y reabre un archivo real: con una base `:memory:` y la misma conexión, los datos sin confirmar igual se ven. Por eso esa prueba usa `tmp_path` en lugar de `:memory:`.

## 5. Ciclo 8: límite de 10 entradas por usuario y fecha (CP-28)

La respuesta 27 del FAQ del PO aclaró que el límite de 10 entradas no es solo por compra: un usuario puede comprar como máximo 10 entradas para una fecha, en una o varias compras. Hasta este ciclo el sistema aceptaba, por ejemplo, 6 entradas y después otras 6 para el mismo día.

1. **Red:** se escribieron 6 pruebas. Fallaron 3 por el motivo correcto: el servicio aceptaba 6 + 5 entradas para la misma fecha (`DID NOT RAISE CompraInvalidaError`) y el repositorio SQLite no sabía contar las entradas compradas (`AttributeError`). Las otras 3 (completar 10 entradas, comprar para otra fecha y que compre otro usuario) ya pasaban, y es lo esperado: verifican que la regla nueva no rechace de más.
2. **Green:** `entradas_compradas(email, fecha)` en los dos repositorios y `_validar_limite_por_fecha` en el servicio: `68 passed`.
3. **Refactor:** Ruff ordenó los imports y ajustó el largo de línea de las pruebas nuevas: `68 passed`. Se mantuvo el control por compra (1 a 10) porque su mensaje explica mejor el error cuando una sola compra ya supera el máximo.

Las 7 mutaciones se detectaron:

| Mutación (regla que se rompe) | Resultado | Prueba que la detecta |
|---|---|---|
| Se quita el control por fecha del servicio | ✅ Detectada (1 de 68 falla) | `test_cp28_superar_10_entradas_para_una_fecha_sumando_compras_es_rechazado` |
| Límite `>` → `>=` (rechaza al llegar justo a 10) | ✅ Detectada (2 de 68 fallan) | `test_cp28_completar_10_entradas_para_una_fecha_es_aceptado`, `test_cp11_...[CP-11-max]` |
| Repositorio en memoria: no filtra por fecha | ✅ Detectada (1 de 68 falla) | `test_cp28_el_limite_se_cuenta_por_fecha` |
| Repositorio en memoria: no filtra por usuario | ✅ Detectada (1 de 68 falla) | `test_cp28_el_limite_se_cuenta_por_usuario` |
| Repositorio SQLite: no filtra por fecha | ✅ Detectada (1 de 68 falla) | `test_entradas_compradas_suma_solo_las_del_usuario_y_la_fecha` |
| Repositorio SQLite: no filtra por usuario | ✅ Detectada (1 de 68 falla) | `test_entradas_compradas_suma_solo_las_del_usuario_y_la_fecha` |
| Repositorio SQLite: sin `COALESCE` (devuelve `None` sin compras) | ✅ Detectada (2 de 68 fallan) | `test_sin_compras_para_la_fecha_hay_0_entradas_compradas`, `test_servicio_registra_la_compra_en_sqlite` |

## 6. Ciclos 9 a 12: Mercado Pago, mail, front y configuración

Con el FAQ del PO, el grupo decidió integrar Mercado Pago (Checkout Pro en modo prueba) y el envío real del mail, y sumar un front web. La parte de backend siguió el ciclo Red-Green-Refactor (sección 2); las pruebas reemplazan Mercado Pago (`httpx.MockTransport`) y el servidor SMTP por dobles, así que no necesitan credenciales ni conexión.

Tipos de Red observados: en los ciclos 9 a 12 fallaron las importaciones (adaptadores y funciones inexistentes), salvo la regla del total $0, que falló por comportamiento. Por eso se verificaron con mutaciones, con 93 pruebas. Las 15 se detectaron:

| Mutación (regla que se rompe) | Resultado | Prueba que la detecta |
|---|---|---|
| Mercado Pago: no se envía el token | ✅ Detectada (1 de 93 falla) | `test_crea_la_preferencia_con_el_total_de_la_compra` |
| Mercado Pago: siempre el checkout real | ✅ Detectada (1 de 93 falla) | `test_con_credenciales_de_prueba_redirige_al_checkout_de_prueba` |
| Mercado Pago: no se controlan los errores HTTP | ✅ Detectada (1 de 93 falla) | `test_si_mercado_pago_rechaza_la_preferencia_se_informa_el_error` |
| Mercado Pago: precio fijo en lugar del total | ✅ Detectada (1 de 93 falla) | `test_crea_la_preferencia_con_el_total_de_la_compra` |
| Servicio: se cobra $0 con tarjeta | ✅ Detectada (1 de 93 falla) | `test_compra_con_tarjeta_sin_costo_no_redirige_a_mercado_pago` |
| API: Mercado Pago caído responde 500 en lugar de 502 | ✅ Detectada (1 de 93 falla) | `test_api_informa_si_mercado_pago_no_esta_disponible` |
| Mail: sin STARTTLS | ✅ Detectada (1 de 93 falla) | `test_se_conecta_con_tls_y_las_credenciales_configuradas` |
| Mail: un error de envío hace fallar la compra | ✅ Detectada (1 de 93 falla) | `test_si_el_mail_no_se_puede_enviar_la_compra_no_falla` |
| Mail: no incluye el link de pago | ✅ Detectada (1 de 93 falla) | `test_el_mail_informa_cantidad_fecha_total_y_link_de_pago` |
| Fechas: ventana de 30 días en lugar de 31 | ✅ Detectada (1 de 93 falla) | `test_fechas_disponibles_van_de_hoy_a_31_dias_sin_lunes` |
| Fechas: no se filtran los días cerrados | ✅ Detectada (4 de 93 fallan) | `test_fechas_disponibles_van_de_hoy_a_31_dias_sin_lunes`, entre otras |
| Cotización: máximo en lugar de suma | ✅ Detectada (1 de 93 falla) | `test_api_cotiza_el_total_antes_de_elegir_la_forma_de_pago` |
| Configuración: siempre se simula Mercado Pago | ✅ Detectada (1 de 93 falla) | `test_con_access_token_se_usa_mercado_pago` |
| Configuración: siempre se simula el mail | ✅ Detectada (1 de 93 falla) | `test_con_servidor_smtp_se_envian_mails_reales` |
| Configuración: no se separan los usuarios registrados | ✅ Detectada (1 de 93 falla) | `test_los_usuarios_registrados_se_pueden_configurar` |

El front (JavaScript) no se construyó con TDD ni tiene pruebas automatizadas: solo muestra datos y llama a la API, que tiene todas las reglas y sus pruebas. Se probó a mano en el navegador, en escritorio y en celular: inicio de sesión simulado, calendario con lunes y fechas pasadas deshabilitados, total de $15.000 para edades 40, 8 y 2 con pase regular, compra con tarjeta (aviso del mail y botón de Mercado Pago), rechazo por superar las 10 entradas para la misma fecha y pantalla de vuelta de Mercado Pago con el pago aprobado.

## 7. Ciclos 13 a 18: completar el pago con Mercado Pago

Hasta el ciclo 12, el backend creaba el pago en Mercado Pago y redirigía, pero no registraba si el pago se aprobaba. Además, con tarjeta el mail de confirmación se enviaba al registrar la compra, antes de pagar, y si Mercado Pago fallaba la compra quedaba registrada sin link de pago. Con el FAQ del PO (ver [FAQ_PO.md](FAQ_PO.md)), el grupo decidió que con tarjeta el mail se envía cuando Mercado Pago aprueba el pago (decisiones 14 y 15 de [DECISIONES_DE_DISENO.md](DECISIONES_DE_DISENO.md)).

### 7.1 Commits de cada ciclo

Cada paso tiene su propio commit en la rama `tp-tdd`, y se ejecutó la batería completa antes de cada uno:

| Ciclo | Red | Green | Refactor | Pruebas |
|---|---|---|---|---|
| 13 | `330c911` | `29543cc` | `aafc3f4` | 98 |
| 14 | `47c1da0` | `04525ab` | `9f13f76` | 110 |
| Fechas dinámicas | — | — | `0f9a9da` | 110 |
| 15 | `efb1769` | `33ea54a` | `0a75840` | 119 |
| 16 | `ca5257b` | `571b34f` | `0e69ce6` | 123 |
| 17 | `53fd474` | `ea611c6` | (sin refactor) | 125 |
| 18 | `66cafb6` | `5452807` | `e7a2566` | 129 |

El front se actualizó en un commit aparte (`20ead50`). Como en los ciclos anteriores, no tiene pruebas automatizadas: solo llama a la API.

**Tipos de Red observados.**
- **Ciclos 16, 17 y 18:** fallas de comportamiento. En el 16, las 5 pruebas recibían `405 Method Not Allowed`. En el 18, un reintento de 6 entradas se rechazaba con "ya compraste 6", porque la compra fallida contaba para el límite.
- **Ciclos 13, 14 y 15:** fallas de importación (`EstadoCompra`, `PagoInformado`, `URL_PAGOS_MERCADO_PAGO`), con algunas de comportamiento en la API (`KeyError: 'estado'`).

Por eso todos se verificaron con mutaciones (sección 7.3).

**Un desvío en el ciclo 14.** La pasarela simulada pasó a volver al sitio con el pago aprobado, en lugar de devolver un link de Mercado Pago. El Red de ese ciclo actualizó la prueba de CP-24, pero no la de CP-01, que todavía exigía el dominio de Mercado Pago en el link simulado. En el Green esa prueba falló. Se corrigió en el mismo commit Green, para que exija que haya un link de pago, y quedó explicado en el mensaje del commit.

### 7.2 Fechas dinámicas en las pruebas

Antes de este refactor, las pruebas usaban un reloj fijo con fechas puntuales: "hoy" era el martes 10/11/2026 y la visita, el 15/11/2026. Como el reloj era fijo, no fallaban con el paso del tiempo, pero cada fecha estaba escrita a mano.

El refactor agregó `tests/fechas.py`, que calcula cada fecha a partir del día en que se ejecutan las pruebas:
- **El "hoy" de las pruebas:** el primer día desde la fecha real en que el parque abre, abrió el día anterior y abre a 31 días. Así los valores límite de CP-12 (ayer) y CP-16 (31 días) siguen dependiendo de una sola regla.
- **El próximo lunes** y **el próximo 25 de diciembre y 1 de enero**.
- **Una fecha de visita abierta:** con día mayor a 12, para que `dd/mm/aaaa` y `mm/dd/aaaa` no coincidan al verificar el resumen.

Solo cambiaron las pruebas: el código de la aplicación quedó igual. Para comprobar que la batería pasa cualquier día, se ejecutó sobre una copia en la que "hoy" se reemplazó por 124 fechas simuladas: todos los días del 01/12/2026 al 15/01/2027, una fecha cada 9 días durante dos años y el 29/02/2028. Pasaron las 124.

También se repitieron las mutaciones de las reglas de fecha con las pruebas nuevas. Las 10 se detectaron:

| Mutación | Pruebas que fallan |
|---|---|
| Se acepta el día anterior a hoy (CP-12) | 1 |
| Se quita el cierre de los lunes (CP-13) | 5 |
| Se quitan los feriados (CP-14 y CP-15) | 3 |
| Se quita solo el 1 de enero (CP-14) | 2 |
| Anticipación 31 → 32 días (CP-16) | 2 |
| Anticipación 31 → 30 días (CP-16) | 3 |
| Hora límite `>` → `>=` (CP-17) | 1 |
| Calendario con ventana de 30 días | 1 |
| Calendario sin filtrar los días cerrados | 4 |
| Fecha del resumen en formato mm/dd/aaaa (CP-26) | 4 |

### 7.3 Verificación con mutaciones (ciclos 13 a 18)

Se aplicaron 29 mutaciones, una por vez, sobre una copia del código, con la batería de 129 pruebas. **Las 29 se detectaron:**

| Ciclo | Mutación (regla que se rompe) | Fallan | Prueba que la detecta |
|---|---|---|---|
| 13 | Con tarjeta la compra nunca queda pendiente | 14 de 129 | `test_cp29_compra_con_tarjeta_queda_pendiente_de_pago_sin_mail`, entre otras |
| 13 | Una compra con tarjeta de $0 queda pendiente | 2 de 129 | `test_compra_con_tarjeta_sin_costo_queda_confirmada_y_envia_mail` |
| 13 | La compra confirmada no envía el mail | 2 de 129 | `test_cp25_compra_exitosa_envia_mail_de_confirmacion` |
| 13 | SQLite no guarda el estado | 2 de 129 | `test_obtener_conserva_el_estado_de_la_compra` |
| 13 | SQLite no agrega la columna a bases anteriores | 1 de 129 | `test_una_base_anterior_sin_estado_se_actualiza` |
| 14 | Se confirma el pago de la compra de otro usuario | 1 de 129 | `test_confirmar_el_pago_de_una_compra_de_otro_usuario_es_rechazado` |
| 14 | Confirmar dos veces reenvía el mail | 1 de 129 | `test_cp33_confirmar_dos_veces_el_mismo_pago_envia_un_solo_mail` |
| 14 | No se verifica a qué compra corresponde el pago | 1 de 129 | `test_cp32_...[CP-32-otra-compra]` |
| 14 | No se verifica el monto del pago | 1 de 129 | `test_cp32_...[CP-32-otro-monto]` |
| 14 | Se confirma aunque el pago no esté aprobado | 1 de 129 | `test_cp31_pago_no_aprobado_deja_la_compra_pendiente_sin_mail` |
| 14 | El cambio de estado no se guarda en el repositorio | 1 de 129 | `test_servicio_confirma_el_pago_en_sqlite` |
| 14 | SQLite no actualiza el estado | 2 de 129 | `test_actualizar_estado_guarda_el_nuevo_estado` |
| 14 | La pasarela simulada aprueba un pago desconocido | 1 de 129 | `test_un_pago_simulado_desconocido_no_esta_aprobado` |
| 15 | Se consultan ids de pago no numéricos | 1 de 129 | `test_un_id_de_pago_que_no_es_numerico_no_se_consulta` |
| 15 | Todo pago figura aprobado | 3 de 129 | `test_un_pago_no_aprobado_se_informa_sin_aprobar[...]` |
| 15 | Se ignora la referencia de la compra | 1 de 129 | `test_un_pago_sin_referencia_no_corresponde_a_ninguna_compra` |
| 15 | Se ignora el monto pagado | 1 de 129 | `test_consulta_el_pago_aprobado_a_mercado_pago` |
| 15 | `auto_return` siempre | 1 de 129 | `test_con_url_local_no_se_pide_la_vuelta_automatica` |
| 15 | `auto_return` nunca | 1 de 129 | `test_con_url_publica_vuelve_sola_al_sitio_al_aprobarse_el_pago` |
| 16 | Se acepta una solicitud sin sesión | 2 de 129 | `test_confirmar_el_pago_sin_iniciar_sesion_es_rechazado`, `test_cp07_...` |
| 16 | Compra inexistente responde 400 en lugar de 404 | 1 de 129 | `test_confirmar_el_pago_de_una_compra_inexistente_responde_404` |
| 16 | Mercado Pago caído al confirmar responde 500 | 1 de 129 | `test_api_informa_si_no_se_puede_consultar_el_pago` |
| 17 | El mail no informa el número de compra | 1 de 129 | `test_el_mail_informa_numero_cantidad_fecha_y_total` |
| 17 | Todo mail dice "pago aprobado con Mercado Pago" | 1 de 129 | `test_el_mail_de_pago_en_boleteria_no_incluye_link_de_pago` |
| 17 | El mail de una compra de $0 menciona Mercado Pago | 1 de 129 | `test_el_mail_de_una_compra_sin_costo_no_pide_pagar` |
| 18 | La compra no se anula si Mercado Pago falla | 2 de 129 | `test_cp34_si_mercado_pago_no_esta_disponible_la_compra_se_anula` |
| 18 | En memoria, las compras anuladas cuentan para el límite | 1 de 129 | `test_cp34_una_compra_anulada_no_cuenta_para_el_limite_por_fecha` |
| 18 | En SQLite, las compras anuladas cuentan para el límite | 1 de 129 | `test_entradas_compradas_no_cuenta_las_compras_anuladas` |
| 18 | Se confirma el pago de una compra anulada | 1 de 129 | `test_confirmar_el_pago_de_una_compra_anulada_es_rechazado` |

La primera mutación hace fallar 14 pruebas porque todo el flujo con tarjeta depende de que la compra quede pendiente. En las demás falla solo la prueba de la regla rota.

### 7.4 Prueba del flujo completo

Con la aplicación levantada y sin credenciales (Mercado Pago y mail simulados), se recorrió el flujo por la API:

1. Una compra con tarjeta quedó `PENDIENTE_DE_PAGO`, sin mail.
2. Al confirmar el pago, quedó `CONFIRMADA` y el mail se escribió en el log una sola vez.
3. Una segunda confirmación no reenvió el mail.
4. Otro usuario recibió 404 al intentar confirmar esa compra.
5. Una compra en efectivo quedó confirmada y envió el mail en el momento.

La base creada antes del ciclo 13 se actualizó sola con la columna del estado. La prueba con Mercado Pago (modo prueba) y Gmail reales se hace siguiendo [CONFIGURACION_CREDENCIALES.md](CONFIGURACION_CREDENCIALES.md).

## 8. Ciclos 19 a 27: Mercado Pago simulado y pago en otra pestaña

### 8.1 Contexto

- **Ciclos 19 a 22:** construyen un Mercado Pago simulado que responde con el mismo contrato que la API real, para usarlo cuando no hay credenciales.
- **Integración real, en modo prueba:** a mitad de esos ciclos el grupo decidió priorizarla y la probó con la cuenta de un integrante.
- **Mercado Pago no vuelve solo a una dirección local:** al crear una preferencia con `auto_return` y `back_urls` en `http://127.0.0.1` o `http://localhost`, la API respondió `400 auto_return invalid. back_url.success must be defined`. Con una URL `https` respondió `201`.
- **La solución:** el checkout se abre en otra pestaña, y la pestaña del sitio le pregunta al backend si la compra ya se pagó. El backend busca el pago en Mercado Pago por el número de compra (ciclos 23 a 25).
- **Lo que queda en pausa:** la página de checkout simulada queda mínima.

### 8.2 Commits de cada ciclo

| Ciclo | Qué | Red | Green | Refactor | Pruebas |
|---|---|---|---|---|---|
| 19 | Núcleo del simulador (preferencias, pagos, titular → resultado, URL de vuelta) | `6010ec3` | `e237371` | — | 149 |
| 20 | API simulada con el contrato real y `url_api` en `PasarelaMercadoPago` | `d86c669` | `840e6ee` | — | 160 |
| 21 | Rutas del checkout simulado (datos, pago del formulario, API por HTTP) | `0558456` | `4ae2d22` | — | 174 |
| 22 | Sin credenciales, la aplicación usa el simulador | `e4fba59` | `bc95775` | — | 173 |
| 23 | Buscar los pagos de una compra (`GET /v1/payments/search`) | `2fc2fe0` | `d134aaf` | — | 183 |
| 24 | `ServicioCompra.verificar_pago` | `3c874c3` | `23e50ba` | (en el Green) | 190 |
| 25 | `POST /compras/{id}/verificacion-de-pago` | `e173870` | `77bf5ab` | `dcb07df` | 198 |
| 26 | Fecha del título del pago con palabras | `d8448eb` | `20debb4` | — | 199 |
| 27 | El transporte en proceso atiende solo la API simulada | `221c189` | `0dd53dc` | — | 201 |
| 28 | Referencia de pago única por compra (hallazgo de la revisión final) | `f987c3a` | `579ece0` | — | 207 |
| 29 | Dos verificaciones simultáneas envían un solo mail (hallazgo de la revisión final) | `c73a980`* | `36c5a4b` | — | 208 |
| 30 | Email del comprador de prueba en la preferencia (`payer.email`) | `facab4a` | `4431c26` | — | 211 |

**El front** se actualizó en un commit aparte (`fda1650`): el checkout se abre en otra pestaña y la pestaña del sitio espera el pago. **El ciclo 22 baja de 174 a 173 pruebas** porque borra las 3 de la pasarela simulada vieja y agrega 2.

### 8.3 Tipos de Red y desvíos

**Tipos de Red:**
- **Por importación (ciclos 19 a 22):** el módulo o la función todavía no existían.
- **Por comportamiento:** en el ciclo 23, `buscar_pago` no existía como método; en el 24, `verificar_pago`; en el 25, el endpoint respondía 405; en el 26, el título usaba barras; en el 27, el transporte respondía 200 a la URL real.
- **En el ciclo 22 el Red falla en una sola prueba:** `crear_pasarela_pago` no recibía el simulador. El resto de las pruebas migradas ya pasaba, porque el `conftest` usaba el simulador de los ciclos 19 a 21.

**Desvíos:**
- **Ruff en los Red de los ciclos 19 y 20:** marcó el orden de las importaciones porque el módulo nuevo todavía no existía y lo tomó como externo. Se commiteó el Red así y el aviso desapareció en el Green.
- **Ciclo 23:** una prueba anterior (`test_la_pasarela_informa_el_pago_del_simulador[OTHE]`) esperaba el pago sin el campo nuevo `rechazado`. Se actualizó en el Green, como en el ciclo 14.
- **Ciclo 24:** el Green extrajo directamente `_compra_con_pago_pendiente` y `_aplicar_pago`, compartidos con `confirmar_pago`, en lugar de duplicar la lógica y refactorizar después.

### 8.4 Verificación con mutaciones

Se aplicaron 23 mutaciones de los ciclos 19 a 27, con la misma técnica que en las secciones 3 a 7.

**Dos sobrevivieron en la primera ronda:**
- "La pasarela ignora `url_api`".
- "Sin credenciales no se usa la URL del simulador".

En los dos casos, el transporte en proceso respondía a cualquier dirección. El **ciclo 27** lo corrigió: ahora el transporte solo atiende `/mercadopago-simulado/api`. En la segunda ronda, **las 23 se detectaron:**

| Ciclo | Mutación | Pruebas que fallan |
|---|---|---|
| 19 | `APRO` da rechazado | 15 pruebas (por ejemplo, `test_el_titular_define_el_resultado[APRO...]`) |
| 19 | Un titular desconocido queda aprobado | `test_el_titular_define_el_resultado[JUAN PEREZ...]` |
| 19 | No se normaliza el titular | `test_el_titular_se_compara_sin_mayusculas_ni_espacios` |
| 19 | El total ignora la cantidad | `test_el_total_suma_precio_por_cantidad` |
| 19 | La vuelta usa siempre `success` | `test_la_url_de_vuelta_usa_la_back_url_del_resultado[OTHE/CONT]` |
| 19 | Sin control de preferencia ya pagada | `test_una_preferencia_aprobada_no_acepta_otro_pago`, entre otras |
| 20 | Sin control del token | `test_sin_token_la_api_responde_401`, entre otras |
| 20 | Un pago inexistente responde 200 | `test_un_pago_inexistente_responde_404` |
| 20 | La pasarela ignora `url_api` | 21 pruebas (después del ciclo 27) |
| 21 | Se acepta el número de tarjeta en el pago | `test_el_numero_de_tarjeta_no_se_acepta_en_el_pago` |
| 21 | Preferencia ya pagada responde 404 en lugar de 409 | `test_pagar_dos_veces_una_preferencia_aprobada_responde_409` |
| 21 | Se ignora `auto_return` | `test_con_auto_return_solo_un_pago_aprobado_vuelve_solo[APRO]` |
| 22 | Sin credenciales no se usa la URL del simulador | `test_sin_access_token_se_usa_el_mercado_pago_simulado` (después del ciclo 27) |
| 23 | La búsqueda no filtra por referencia | `test_la_busqueda_de_otra_referencia_no_devuelve_pagos` |
| 23 | Se informa el más reciente aunque haya uno aprobado | `test_si_hay_un_pago_aprobado_se_informa_ese_aunque_haya_otros` |
| 23 | Sin pagos se informa un pago vacío | `test_sin_pagos_la_busqueda_no_informa_ninguno` |
| 23 | `rechazado` siempre falso | `test_un_pago_rechazado_se_informa_como_rechazado`, entre otras |
| 23 | El simulador ordena del más viejo al más nuevo | `test_la_api_busca_los_pagos_por_referencia` |
| 24 | Verificar no controla el monto | `test_verificar_un_pago_por_otro_monto_es_rechazado` |
| 24 | Verificar busca aunque la compra esté confirmada | `test_verificar_una_compra_ya_confirmada_no_busca_ni_reenvia_el_mail` |
| 24 | Verificar acepta la compra de otro usuario | `test_verificar_el_pago_de_una_compra_de_otro_usuario_es_rechazado`, entre otras |
| 25 | Un pago rechazado se informa como pendiente | `test_api_verificacion_informa_el_pago_no_aprobado[OTHE-rechazado]` |
| 25 | Sin pago se informa como pendiente | `test_api_verificacion_sin_pago_todavia` |
| 26 | La fecha del título vuelve a llevar barras | `test_el_titulo_del_pago_escribe_la_fecha_con_palabras` |

### 8.5 Prueba con el Mercado Pago real (modo prueba)

La hizo un integrante con su cuenta, sus credenciales de prueba (`APP_USR-...`) y un comprador de prueba:

1. Una **compra en efectivo** envió el mail real por Gmail (SMTP), sin errores.
2. Una **compra con tarjeta** creó la preferencia en Mercado Pago, que aceptó la URL de vuelta local sin `auto_return`, y devolvió el `init_point`.
3. **El pago con la tarjeta de prueba y el titular `APRO`** quedó aprobado (operación 183951332111). Mercado Pago no volvió solo al sitio porque la URL era local.
4. **`POST /compras/7/pago` con ese id de pago:** el backend lo consultó en Mercado Pago, confirmó la compra y envió el mail de pago aprobado.
5. **La búsqueda por número de compra** (`GET /v1/payments/search?external_reference=7`) encontró el mismo pago aprobado. En la compra 6, que no se pagó, no encontró pagos.

Falta repetir el flujo completo desde el front con el pago en otra pestaña.

### 8.6 Revisión final de la rama

Al terminar los ciclos, un revisor independiente revisó toda la rama. Encontró un problema crítico y dos importantes, que se corrigieron:

1. **Crítico: un pago ajeno podía confirmar la compra (ciclo 28).**
   - **Causa:** el pago se buscaba por el número de compra, que se repite si se borra la base o si otro integrante usa las mismas credenciales.
   - **Red:** la prueba de punta a punta `test_cp37_un_pago_ajeno_con_el_mismo_numero_de_compra_no_la_confirma` crea con el simulador un pago aprobado de otra compra con el mismo número y total. Antes del arreglo, la compra quedaba `CONFIRMADA`.
   - **Green:** cada compra con tarjeta tiene una referencia de pago única.
   - **Aclaración sobre otra prueba del Red:** la prueba unitaria `test_cp37_un_pago_de_otra_compra_con_el_mismo_numero_no_la_confirma` ya pasaba antes del arreglo, pero solo porque comparaba un texto con un número. Por eso se agregó la de punta a punta.
2. **Importante: dos verificaciones simultáneas enviaban dos mails (ciclo 29).**
   - **Red:** `test_dos_verificaciones_al_mismo_tiempo_envian_un_solo_mail` lanza dos verificaciones en paralelo con un Mercado Pago lento: salían 2 mails.
   - **Green:** un candado en `ServicioCompra`.
3. **Importante: la espera del pago vivía solo en memoria.** Si se recargaba o cerraba la pestaña del sitio, la compra pagada quedaba pendiente. Se corrigió en el front (`localStorage`, commit `27171ca`), que no tiene pruebas automatizadas, y se corrigió la decisión 18, que lo describía de más.

\* El commit Red del ciclo 29 se rehízo para conservar los fines de línea CRLF del archivo.

Las observaciones menores quedaron registradas y no se corrigieron en esta entrega:
- Una respuesta de Mercado Pago sin algún campo puede dar error 500.
- La espera no se detiene al cerrar el diálogo.
- Un reintento que queda pendiente no actualiza el texto.
- Un JSON inválido en la API simulada da error 500.
- Las rutas del simulador también se publican cuando se usa el Mercado Pago real.
- Dos pagos simultáneos en el simulador.

## 9. Ciclos 31 a 35: mail en HTML y registro simulado

Estos ciclos se hicieron en las ramas `feat/pulido-ux-ui` y `feat/registro-simulado`. Usan la convención Conventional Commits del grupo: `test(...)` para el Red y `feat(...)`/`fix(...)` para el Green.

| Ciclo | Qué | Red | Green | Pruebas |
|---|---|---|---|---|
| 31 | Versión HTML del mail con la estética de la pantalla de confirmación | `4a8933a` | `5b0550b` | 218 |
| 32 | El logo va dentro del mensaje y no como adjunto | `c3cc6e6` | `268d5f8` | 219 |
| 33 | El mail no lleva imágenes: Gmail mostraba el logo como adjunto aun marcado `inline` | `46c8da4` | `b432673` | 218 |
| 34 | Medio de pago y detalle de cada entrada (edad y precio) con el total al final | `cf30145` | `c95daf1` | 224 |
| 35 | Registro simulado sin contraseña (`POST /usuarios`, CP-38) | `6b86b4b` | `cc0f316` | 236 |

**Ciclo 33:** reemplaza las dos pruebas del logo de los ciclos 31 y 32 por una que exige que el mail no tenga imágenes. El cambio de pantallas y el botón "Registrarme" son front y no tienen pruebas automatizadas.

## 10. Pruebas complementarias: valores límite y reglas sin verificar

En el commit `1ff2ffb` (Luca Olguin) se agregaron 15 pruebas, de 236 a 251, para valores límite y reglas que ya estaban implementadas pero que la batería no verificaba. **No son un ciclo Red-Green-Refactor:** el comportamiento ya existía, así que las pruebas pasaron desde el primer momento y no cambió el código de la aplicación. Su objetivo es que, si alguien rompe una de esas reglas más adelante, una prueba falle.

| Prueba | Qué verifica | Casos |
|---|---|---|
| `test_api_compras::test_api_rechaza_la_compra_con_un_mensaje_claro` | Las reglas de negocio también se respetan por la API: responde 400 con un mensaje que explica el motivo | 5: fecha pasada (CP-12), a más de 31 días (CP-16), cantidad 0 (CP-08), edades que no coinciden con la cantidad (CP-27) y edad negativa (CP-18) |
| `test_calendario::test_los_dias_vecinos_a_los_feriados_estan_abiertos` | Valores límite de CP-14 y CP-15: el parque abre el día antes y el día después de cada feriado | 4: 24/12, 26/12, 31/12 y 2/1 |
| `test_calendario::test_cp17_despues_de_las_17_30_se_puede_comprar_para_otro_dia` | La hora límite de las 17:30 solo aplica a la compra para el mismo día | 1 |
| `test_servicio_compra::test_cp18_edad_0_es_aceptada` | Valor límite de CP-18: 0 años es una edad válida | 1 |
| `test_servicio_compra::test_cp28_una_compra_pendiente_de_pago_cuenta_para_el_limite` | Una compra con tarjeta que espera el pago cuenta para el límite de 10 entradas por fecha (FAQ 27) | 1 |
| `test_servicio_compra::test_total_con_pase_vip_aplica_los_descuentos_por_edad` | El total de una compra VIP aplica los descuentos por edad | 1 |
| `test_dependencias::test_el_mail_del_log_informa_destinatario_cantidad_y_fecha` | Sin SMTP, el mail que se escribe en el log informa el destinatario, la cantidad y la fecha | 1 |
| `test_dependencias::test_la_aplicacion_usa_la_hora_del_sistema` | La aplicación usa la hora real del sistema (las demás pruebas usan un reloj fijo) | 1 |

Las dos últimas pruebas cubren líneas que antes quedaban sin cubrir: con ellas, la única sentencia sin cubrir de `app/` es la que crea el Mercado Pago simulado de la aplicación. Los casos quedaron registrados en [BACKLOG.md](BACKLOG.md).

## 11. Ciclos 36 y 37: edad máxima de 100 años (CP-39)

Probando la aplicación se encontró que se podía comprar con una edad de 549 años: solo se rechazaban las edades negativas (CP-18). El grupo fijó como supuesto que la edad de cada visitante está entre 0 y 100 años, inclusive.

| Ciclo | Qué | Red | Green | Refactor | Pruebas |
|---|---|---|---|---|---|
| 36 | El servicio rechaza edades mayores a 100 años (CP-39) | `77a615d` | `88de218` | `8e62e5e` | 255 |
| 37 | `/cotizacion` no cotiza edades mayores a 100 años | `2816d86` | `eb6470c` | — | 256 |

- **Red del ciclo 36:** con 101 y 549 años, el servicio no lanzaba `CompraInvalidaError` (`DID NOT RAISE`) y la API registraba la compra (`assert 201 == 400`). La prueba del valor límite (100 años se acepta) pasó desde el principio: documenta el borde válido, que el sistema ya cumplía.
- **Mensaje esperado:** la prueba busca "100 años" en el mensaje y no solo "edad", porque "edad" también aparece en el mensaje de CP-27 (hallazgo 3 de la sección 3).
- **Refactor del ciclo 36:** las validaciones de edad negativa y de edad mayor a 100 quedaron en una sola regla de rango, con la constante `EDAD_MAXIMA`, igual que `CANTIDAD_MAXIMA`. El esquema de la cotización usa la misma constante, así que el límite está en un solo lugar del backend.
- **Front:**
  - `validar()` avisa "La edad de cada visitante debe estar entre 0 y 100 años." antes de llamar a la API.
  - El total no se cotiza con una edad fuera de rango.
  - El campo tenía `max="120"`, pero el formulario es `novalidate`, así que el navegador no lo controlaba.
  - Como el resto del front, no tiene pruebas automatizadas: la regla que vale es la del backend.
