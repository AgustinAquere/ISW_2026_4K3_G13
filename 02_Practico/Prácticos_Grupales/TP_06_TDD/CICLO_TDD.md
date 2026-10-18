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

Al cerrar cada ciclo se ejecutó la batería completa de pruebas, que quedó en verde (52 pruebas al cerrar el ciclo 6, 62 al cerrar el ciclo 7 y 68 al cerrar el ciclo 8). Las mutaciones de la sección 3 se hicieron con 52 pruebas; las de los ciclos 7 y 8 están en las secciones 4 y 5.

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
