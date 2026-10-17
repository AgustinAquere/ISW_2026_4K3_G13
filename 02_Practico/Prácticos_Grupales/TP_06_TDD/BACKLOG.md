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
| CP-01 | Comprar entradas con fecha disponible, cantidad menor a 10, edades de todos los visitantes, tipo de pase seleccionado y pago con tarjeta mediante Mercado Pago | La compra se procesa correctamente y se recibe el correo de confirmación | Refactorizado | `test_api_compras::test_cp01_compra_con_tarjeta_mediante_mercado_pago_y_mail` |
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

### 3. Validación de la fecha de visita

| ID | Caso de prueba | Resultado esperado | Estado | Prueba automatizada |
|---|---|---|---|---|
| CP-12 | Seleccionar una fecha anterior a la fecha actual | La compra es rechazada | Refactorizado | `test_calendario::test_cp12_fecha_anterior_a_hoy_es_rechazada` |
| CP-13 | Seleccionar un lunes como fecha de visita | La compra es rechazada | Refactorizado | `test_calendario::test_cp13_lunes_es_rechazado` |
| CP-14 | Seleccionar el 1 de enero como fecha de visita | La compra es rechazada | Refactorizado | `test_calendario::test_feriado_en_que_cierra_el_parque_es_rechazado[CP-14-1-de-enero]` |
| CP-15 | Seleccionar el 25 de diciembre como fecha de visita | La compra es rechazada | Refactorizado | `test_calendario::test_feriado_en_que_cierra_el_parque_es_rechazado[CP-15-25-de-diciembre]` |
| CP-16 | Seleccionar una fecha a más de 31 días de la fecha actual | La compra es rechazada | Refactorizado | `test_calendario::test_cp16_*` (31 días acepta, 32 rechaza) |
| CP-17 | Intentar comprar entradas para el día actual después de las 17:30 | La compra es rechazada | Refactorizado | `test_calendario::test_cp17_*` (17:30 acepta, 17:31 rechaza) |

### 4. Validación de la edad y descuentos

| ID | Caso de prueba | Resultado esperado | Estado | Prueba automatizada |
|---|---|---|---|---|
| CP-18 | Ingresar una edad negativa | La compra es rechazada | Refactorizado | `test_servicio_compra::test_cp18_edad_negativa_es_rechazada` |
| CP-19 | Comprar una entrada para una persona de hasta 3 años, inclusive | La entrada no tiene costo | Refactorizado | `test_precios::test_cp19_hasta_3_anios_no_tiene_costo` (0 y 3) |
| CP-20 | Comprar una entrada para una persona mayor de 3 y hasta 15 años, inclusive | Se aplica un descuento del 50 % | Refactorizado | `test_precios::test_cp20_*` (4 y 15) |
| CP-21 | Comprar una entrada para una persona mayor de 15 y menor de 60 años | No se aplica descuento por edad | Refactorizado | `test_precios::test_cp21_*` (16 y 59) |
| CP-22 | Comprar una entrada para una persona de 60 años o más | Se aplica un descuento del 50 % | Refactorizado | `test_precios::test_cp22_*` (60 y 85) |

### 5. Modalidades de pago

| ID | Caso de prueba | Resultado esperado | Estado | Prueba automatizada |
|---|---|---|---|---|
| CP-23 | Comprar entradas seleccionando el pago en boletería | La compra se procesa correctamente | Refactorizado | `test_servicio_compra::test_cp23_*`, `test_api_compras::test_cp23_*` |
| CP-24 | Comprar entradas con tarjeta de crédito y confirmar la compra | El usuario es redirigido a Mercado Pago | Refactorizado | `test_servicio_compra::test_cp24_pago_con_tarjeta_redirige_a_mercado_pago` |

### 6. Confirmación de la compra

| ID | Caso de prueba | Resultado esperado | Estado | Prueba automatizada |
|---|---|---|---|---|
| CP-25 | Completar una compra correctamente | Se envía el correo electrónico de confirmación | Refactorizado | `test_servicio_compra::test_cp25_compra_exitosa_envia_mail_de_confirmacion` |
| CP-26 | Finalizar una compra correctamente | Se informa la cantidad de entradas compradas y la fecha de visita | Refactorizado | `test_servicio_compra::test_cp26_*`, `test_api_compras::test_cp26_*` |

### 7. Pruebas complementarias (surgidas durante TDD)

| Caso | Resultado esperado | Prueba automatizada |
|---|---|---|
| Tipo de pase o medio de pago inexistente | La compra es rechazada (422) | `test_api_compras::test_opcion_inexistente_es_rechazada` |
| Pase VIP y descuento por edad sobre VIP | El VIP cuesta más y también recibe el descuento | `test_precios::test_pase_vip_*`, `test_precios::test_descuento_por_edad_*` |
| Total de una compra con edades mixtas | Suma el precio de cada visitante | `test_servicio_compra::test_total_de_la_compra_*` |
| Compra válida | Queda registrada con un id | `test_servicio_compra::test_compra_realizada_queda_registrada` |
| Compra rechazada | No se registra ni envía mail | `test_servicio_compra::test_compra_rechazada_no_envia_mail_ni_se_registra` |

Las decisiones de diseño y los supuestos están en [DECISIONES_DE_DISENO.md](DECISIONES_DE_DISENO.md), y el registro de cada ciclo Red-Green-Refactor junto con la verificación de las pruebas, en [CICLO_TDD.md](CICLO_TDD.md).
