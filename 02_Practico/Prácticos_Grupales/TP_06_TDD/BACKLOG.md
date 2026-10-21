# Backlog de casos de prueba — Sistema de compra de entradas

## Objetivo

Documentar los casos de prueba definidos para el sistema de compra de entradas, indicando el comportamiento esperado y el estado de implementación de cada prueba, siguiendo la metodología Test-Driven Development (TDD).

## Estados

- **Pendiente:** el caso todavía no fue implementado.
- **Red:** la prueba está implementada y falla porque el sistema todavía no cumple el comportamiento esperado.
- **Green:** la prueba pasa porque el sistema cumple el comportamiento esperado.
- **Refactorizado:** se mejoró la implementación y las pruebas siguen pasando.

## HU-01 — Comprar entradas

### 1. Compra y datos obligatorios

| ID | Caso de prueba | Resultado esperado | Estado | Prueba automatizada |
|---|---|---|---|---|
| CP-01 | Comprar entradas con fecha disponible, cantidad menor a 10, edades de todos los visitantes, tipo de pase seleccionado y pago con tarjeta mediante Mercado Pago | La compra queda pendiente de pago; al volver de Mercado Pago con el pago aprobado se confirma y se recibe el correo de confirmación | Refactorizado | `test_api_compras::test_cp01_compra_con_tarjeta_mediante_mercado_pago_y_mail` |
| CP-02 | Intentar comprar entradas sin seleccionar la forma de pago | La compra es rechazada | Refactorizado | `test_api_compras::test_comprar_sin_dato_obligatorio_es_rechazado[CP-02]` |
| CP-03 | Intentar comprar entradas sin seleccionar el día de visita | La compra es rechazada | Refactorizado | `test_api_compras::test_comprar_sin_dato_obligatorio_es_rechazado[CP-03]` |
| CP-04 | Intentar comprar entradas sin seleccionar la cantidad | La compra es rechazada | Refactorizado | `test_api_compras::test_comprar_sin_dato_obligatorio_es_rechazado[CP-04]` |
| CP-05 | Intentar comprar entradas sin indicar la edad de los visitantes | La compra es rechazada | Refactorizado | `test_api_compras::test_comprar_sin_dato_obligatorio_es_rechazado[CP-05]` |
| CP-06 | Intentar comprar entradas sin seleccionar el tipo de pase (VIP o regular) | La compra es rechazada | Refactorizado | `test_api_compras::test_comprar_sin_dato_obligatorio_es_rechazado[CP-06]` |
| CP-07 | Intentar comprar entradas con un usuario que no está registrado | La compra es rechazada | Refactorizado | `test_api_compras::test_cp07_*`, `test_servicio_compra::test_cp07_*` |

### 2. Validación de la cantidad de entradas

| ID | Caso de prueba | Resultado esperado | Estado | Prueba automatizada |
|---|---|---|---|---|
| CP-08 | Comprar 0 entradas | La compra es rechazada | Refactorizado | `test_servicio_compra::test_cantidad_fuera_de_rango_es_rechazada[CP-08]` |
| CP-09 | Comprar una cantidad negativa de entradas | La compra es rechazada | Refactorizado | `test_servicio_compra::test_cantidad_fuera_de_rango_es_rechazada[CP-09]` |
| CP-10 | Comprar más de 10 entradas | La compra es rechazada | Refactorizado | `test_servicio_compra::test_cantidad_fuera_de_rango_es_rechazada[CP-10]`, `test_api_compras::test_cp10_*` |
| CP-11 | Comprar una cantidad entre 1 y 10 entradas, inclusive | La cantidad es aceptada | Refactorizado | `test_servicio_compra::test_cp11_cantidad_entre_1_y_10_es_aceptada` |
| CP-27 | Indicar una cantidad de edades distinta a la cantidad de entradas | La compra es rechazada | Refactorizado | `test_servicio_compra::test_cp27_cantidad_distinta_a_edades_informadas_es_rechazada` |
| CP-28 | Superar las 10 entradas para una misma fecha sumando varias compras del mismo usuario (FAQ 27 del PO) | La compra es rechazada; completar 10, comprar para otra fecha o que compre otro usuario se acepta | Refactorizado | `test_servicio_compra::test_cp28_*`, `test_repositorios_sqlite::test_entradas_compradas_*`, `test_repositorios_sqlite::test_sin_compras_para_la_fecha_*` |

### 3. Validación de la fecha de visita

| ID | Caso de prueba | Resultado esperado | Estado | Prueba automatizada |
|---|---|---|---|---|
| CP-12 | Seleccionar una fecha anterior a la fecha actual | La compra es rechazada | Refactorizado | `test_calendario::test_cp12_fecha_anterior_a_hoy_es_rechazada` |
| CP-13 | Seleccionar un lunes como fecha de visita | La compra es rechazada | Refactorizado | `test_calendario::test_cp13_lunes_es_rechazado` |
| CP-14 | Seleccionar el 1 de enero como fecha de visita | La compra es rechazada | Refactorizado | `test_calendario::test_feriado_en_que_cierra_el_parque_es_rechazado[CP-14-1-de-enero]` |
| CP-15 | Seleccionar el 25 de diciembre como fecha de visita | La compra es rechazada | Refactorizado | `test_calendario::test_feriado_en_que_cierra_el_parque_es_rechazado[CP-15-25-de-diciembre]` |
| CP-16 | Seleccionar una fecha a más de 31 días de la fecha actual | La compra es rechazada | Refactorizado | `test_calendario::test_cp16_*` (31 días acepta, 32 rechaza) |
| CP-17 | Intentar comprar entradas para el día actual después de las 17:30 | La compra es rechazada | Refactorizado | `test_calendario::test_cp17_*` (17:30 acepta, 17:31 rechaza, y después de las 17:30 se puede comprar para otro día) |

### 4. Validación de la edad y descuentos

| ID | Caso de prueba | Resultado esperado | Estado | Prueba automatizada |
|---|---|---|---|---|
| CP-18 | Ingresar una edad negativa | La compra es rechazada | Refactorizado | `test_servicio_compra::test_cp18_edad_negativa_es_rechazada`, `test_servicio_compra::test_cp18_edad_0_es_aceptada` (valor límite) |
| CP-19 | Comprar una entrada para una persona de hasta 3 años, inclusive | La entrada no tiene costo | Refactorizado | `test_precios::test_cp19_hasta_3_anios_no_tiene_costo` (0 y 3) |
| CP-20 | Comprar una entrada para una persona mayor de 3 y hasta 15 años, inclusive | Se aplica un descuento del 50 % | Refactorizado | `test_precios::test_cp20_*` (4 y 15) |
| CP-21 | Comprar una entrada para una persona mayor de 15 y menor de 60 años | No se aplica descuento por edad | Refactorizado | `test_precios::test_cp21_*` (16 y 59) |
| CP-22 | Comprar una entrada para una persona de 60 años o más | Se aplica un descuento del 50 % | Refactorizado | `test_precios::test_cp22_*` (60 y 85) |
| CP-39 | Ingresar una edad mayor a 100 años | La compra es rechazada y no se cotiza el total | Refactorizado | `test_servicio_compra::test_cp39_edad_mayor_a_100_es_rechazada` (101 y 549), `test_servicio_compra::test_cp39_edad_100_es_aceptada` (valor límite), `test_api_compras::test_api_rechaza_la_compra_con_un_mensaje_claro[CP-39]`, `test_api_front::test_api_no_cotiza_edades_mayores_a_100` |

### 5. Modalidades de pago

| ID | Caso de prueba | Resultado esperado | Estado | Prueba automatizada |
|---|---|---|---|---|
| CP-23 | Comprar entradas seleccionando el pago en boletería | La compra se procesa correctamente | Refactorizado | `test_servicio_compra::test_cp23_*`, `test_api_compras::test_cp23_*` |
| CP-24 | Comprar entradas con tarjeta de crédito y confirmar la compra | El usuario es redirigido a Mercado Pago | Refactorizado | `test_servicio_compra::test_cp24_pago_con_tarjeta_redirige_a_mercado_pago` |
| CP-29 | Comprar entradas con tarjeta (total mayor a $0) | La compra queda pendiente de pago y todavía no se envía el correo | Refactorizado | `test_servicio_compra::test_cp29_*`, `test_api_compras::test_cp01_*` |
| CP-30 | Volver de Mercado Pago con el pago aprobado | La compra se confirma y se envía el correo de confirmación | Refactorizado | `test_servicio_compra::test_cp30_*`, `test_api_compras::test_cp01_*` |
| CP-31 | Volver de Mercado Pago con el pago rechazado o pendiente | La compra sigue pendiente y no se envía el correo | Refactorizado | `test_servicio_compra::test_cp31_*` |
| CP-32 | Informar un pago que es de otra compra o por otro monto | Se rechaza la confirmación (400) | Refactorizado | `test_servicio_compra::test_cp32_*[CP-32-otra-compra]`, `[CP-32-otro-monto]`, `test_api_compras::test_confirmar_un_pago_que_no_corresponde_*` |
| CP-33 | Confirmar dos veces el mismo pago (por ejemplo, recargando la página) | Se envía un solo correo | Refactorizado | `test_servicio_compra::test_cp33_*` |
| CP-34 | Comprar con tarjeta cuando Mercado Pago no está disponible | La compra se anula (502) y no cuenta para el límite de 10 entradas por fecha | Refactorizado | `test_servicio_compra::test_cp34_*`, `test_api_compras::test_api_informa_si_mercado_pago_no_esta_disponible` |
| CP-35 | Pago rechazado en el checkout (titular `OTHE`) y reintento con otra tarjeta | La compra sigue pendiente y sin mail; con el reintento aprobado se confirma y se envía un solo mail | Refactorizado | `test_api_compras::test_cp35_*` |
| CP-37 | Un pago aprobado de otra compra con el mismo número y total (otra base u otro integrante con las mismas credenciales) | La compra no se confirma: el pago se busca por una referencia única de la compra | Refactorizado | `test_api_compras::test_cp37_*`, `test_servicio_compra::test_cp37_*` |
| CP-38 | Comprar con un email no registrado, registrarlo con el registro simulado y volver a comprar | La primera compra se rechaza ("Usuario no registrado"); después del registro se acepta | Refactorizado | `test_api_usuarios::test_cp38_*`, `test_api_usuarios::*`, `test_repositorios_de_usuarios::*` |
| CP-36 | Pagar en otra pestaña y volver a la pestaña del sitio | El sitio verifica el pago por el número de compra, confirma la compra, informa cantidad y fecha y envía el mail | Refactorizado | `test_servicio_compra::test_cp36_*`, `test_api_compras::test_cp36_*`, `test_api_verificacion_*` |

### 6. Confirmación de la compra

| ID | Caso de prueba | Resultado esperado | Estado | Prueba automatizada |
|---|---|---|---|---|
| CP-25 | Completar una compra correctamente (en efectivo, sin costo o con el pago aprobado) | Se envía el correo electrónico de confirmación | Refactorizado | `test_servicio_compra::test_cp25_compra_exitosa_envia_mail_de_confirmacion`, `test_cp30_*` |
| CP-26 | Finalizar una compra correctamente | Se informa la cantidad de entradas compradas y la fecha de visita | Refactorizado | `test_servicio_compra::test_cp26_*`, `test_api_compras::test_cp26_*` |

### 7. Pruebas complementarias (surgidas durante TDD)

| Caso | Resultado esperado | Prueba automatizada |
|---|---|---|
| Tipo de pase o medio de pago inexistente | La compra es rechazada (422) | `test_api_compras::test_opcion_inexistente_es_rechazada` |
| Pase VIP y descuento por edad sobre VIP | El VIP cuesta más y también recibe el descuento | `test_precios::test_pase_vip_*`, `test_precios::test_descuento_por_edad_*`, `test_servicio_compra::test_total_con_pase_vip_aplica_los_descuentos_por_edad` |
| Días vecinos a los feriados (24/12, 26/12, 31/12 y 2/1) | El parque abre (valores límite de CP-14 y CP-15) | `test_calendario::test_los_dias_vecinos_a_los_feriados_estan_abiertos` |
| Compra con tarjeta pendiente de pago (FAQ 27) | Cuenta para el límite de 10 entradas por fecha | `test_servicio_compra::test_cp28_una_compra_pendiente_de_pago_cuenta_para_el_limite` |
| Reglas de negocio por la API | Fecha pasada, a más de 31 días, cantidad 0, edades que no coinciden con la cantidad y edad negativa o mayor a 100 años responden 400 con un mensaje claro | `test_api_compras::test_api_rechaza_la_compra_con_un_mensaje_claro` |
| Total de una compra con edades mixtas | Suma el precio de cada visitante | `test_servicio_compra::test_total_de_la_compra_*` |
| Compra válida | Queda registrada con un id | `test_servicio_compra::test_compra_realizada_queda_registrada` |
| Compra rechazada | No se registra ni envía mail | `test_servicio_compra::test_compra_rechazada_no_envia_mail_ni_se_registra` |
| Usuarios en SQLite | Un usuario cargado está registrado, uno no cargado no, y cargarlo dos veces no lo duplica | `test_repositorios_sqlite::test_usuario_*`, `test_repositorios_sqlite::test_cargar_un_usuario_ya_registrado_no_lo_duplica` |
| Compras en SQLite | Se guardan con id correlativo y se recuperan iguales (fecha, edades, pase, pago y total) | `test_repositorios_sqlite::test_guardar_*`, `test_obtener_*`, `test_listar_*`, `test_sin_compras_*` |
| Persistencia | Los datos siguen al reabrir la base, y el servicio registra la compra en SQLite | `test_repositorios_sqlite::test_los_datos_persisten_al_reabrir_la_base`, `test_servicio_registra_la_compra_en_sqlite` |
| Mercado Pago Checkout Pro | Se crea la preferencia con el total y se redirige al checkout (de prueba con credenciales `TEST-`); con URL pública (https) vuelve solo al sitio | `test_pasarela_mercado_pago::*` |
| Consulta del pago | Se consulta `GET /v1/payments/{id}` y se informa si está aprobado, a qué compra corresponde y por qué monto; un id no numérico no se consulta | `test_pasarela_mercado_pago::test_consulta_*`, `test_un_*`, `test_si_no_se_puede_consultar_*` |
| Mercado Pago simulado | Sin credenciales, el pago vuelve al sitio aprobado (FAQ 4) | `test_pasarela_simulada::*` |
| Confirmación del pago por la API | `POST /compras/{id}/pago`: sin sesión 401, compra inexistente o de otro usuario 404, Mercado Pago caído 502 | `test_api_compras::test_confirmar_*`, `test_api_informa_si_no_se_puede_consultar_el_pago`, `test_servicio_compra::test_confirmar_*` |
| Estado de la compra en SQLite | Se guarda, se actualiza y una base anterior recibe la columna nueva | `test_repositorios_sqlite::test_obtener_conserva_el_estado_*`, `test_actualizar_estado_*`, `test_una_base_anterior_*`, `test_servicio_confirma_el_pago_en_sqlite` |
| Búsqueda de pagos por compra | `GET /v1/payments/search?external_reference=<compra>`: informa el aprobado o el más reciente (aprobado, rechazado o pendiente) | `test_pasarela_mercado_pago::test_busca_*`, `test_sin_pago*`, `test_si_hay_un_pago_aprobado_*`, `test_si_no_se_puede_buscar_*` |
| Título del pago | La fecha va con palabras ("20 de octubre de 2026") porque Mercado Pago le quita las barras | `test_pasarela_mercado_pago::test_el_titulo_del_pago_escribe_la_fecha_con_palabras` |
| Mercado Pago simulado | Titular → resultado, pagos correlativos, URL de vuelta con los parámetros reales, API con 401 y 404, búsqueda por referencia, una preferencia aprobada no acepta otro pago y el número de tarjeta no se acepta | `test_mercado_pago_simulado::*`, `test_api_mercado_pago_simulado::*`, `test_api_checkout_simulado::*` |
| Mercado Pago no disponible | La API responde 502 con un mensaje claro | `test_pasarela_mercado_pago::test_si_mercado_pago_*`, `test_api_compras::test_api_informa_si_mercado_pago_no_esta_disponible` |
| Compra con tarjeta de $0 | No se redirige a Mercado Pago | `test_servicio_compra::test_compra_con_tarjeta_sin_costo_no_redirige_a_mercado_pago` |
| Mail por SMTP | Llega al usuario con número de compra, cantidad, fecha y total, e informa el pago (aprobado con Mercado Pago, en boletería o sin costo); si el envío falla, la compra no falla | `test_notificador_smtp::*` |
| Fechas del calendario | Solo se ofrecen fechas abiertas, de hoy a 31 días, y hoy solo hasta las 17:30 | `test_calendario::test_fechas_disponibles_*`, `test_despues_de_las_17_30_*`, `test_api_front::test_api_informa_las_fechas_disponibles` |
| Total antes de pagar | Se cotiza con los mismos precios y descuentos que la compra | `test_api_front::test_api_cotiza_*`, `test_api_front::test_api_no_cotiza_edades_negativas`, `test_api_front::test_api_no_cotiza_edades_mayores_a_100` |
| Front | Se sirve en `/` | `test_api_front::test_la_pagina_de_compra_se_sirve_en_la_raiz` |
| Configuración | Con credenciales en `.env` se usan Mercado Pago y SMTP reales; sin ellas, los simulados (el mail del log informa destinatario, cantidad y fecha); la aplicación usa la hora del sistema | `test_dependencias::*` |

Las fechas de todas las pruebas se calculan a partir del día en que se ejecutan (`tests/fechas.py`), así que ninguna prueba depende de una fecha fija.

Las decisiones de diseño y los supuestos están en [DECISIONES_DE_DISENO.md](DECISIONES_DE_DISENO.md), y el registro de cada ciclo Red-Green-Refactor junto con la verificación de las pruebas, en [CICLO_TDD.md](CICLO_TDD.md).
