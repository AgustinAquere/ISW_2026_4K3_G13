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

| ID | Caso de prueba | Resultado esperado | Estado |
|---|---|---|---|
| CP-01 | Comprar entradas con fecha disponible, cantidad menor a 10, edades de todos los visitantes, tipo de pase seleccionado y pago con tarjeta mediante Mercado Pago | La compra se procesa correctamente y se recibe el correo de confirmación | Pendiente |
| CP-02 | Intentar comprar entradas sin seleccionar la forma de pago | La compra es rechazada | Pendiente |
| CP-03 | Intentar comprar entradas sin seleccionar el día de visita | La compra es rechazada | Pendiente |
| CP-04 | Intentar comprar entradas sin seleccionar la cantidad | La compra es rechazada | Pendiente |
| CP-05 | Intentar comprar entradas sin indicar la edad de los visitantes | La compra es rechazada | Pendiente |
| CP-06 | Intentar comprar entradas sin seleccionar el tipo de pase (VIP o regular) | La compra es rechazada | Pendiente |
| CP-07 | Intentar comprar entradas con un usuario que no está registrado | La compra es rechazada | Pendiente |

### 2. Validación de la cantidad de entradas

| ID | Caso de prueba | Resultado esperado | Estado |
|---|---|---|---|
| CP-08 | Comprar 0 entradas | La compra es rechazada | Pendiente |
| CP-09 | Comprar una cantidad negativa de entradas | La compra es rechazada | Pendiente |
| CP-10 | Comprar más de 10 entradas | La compra es rechazada | Pendiente |
| CP-11 | Comprar una cantidad entre 1 y 10 entradas, inclusive | La cantidad es aceptada | Pendiente |

### 3. Validación de la fecha de visita

| ID | Caso de prueba | Resultado esperado | Estado |
|---|---|---|---|
| CP-12 | Seleccionar una fecha anterior a la fecha actual | La compra es rechazada | Pendiente |
| CP-13 | Seleccionar un lunes como fecha de visita | La compra es rechazada | Pendiente |
| CP-14 | Seleccionar el 1 de enero como fecha de visita | La compra es rechazada | Pendiente |
| CP-15 | Seleccionar el 25 de diciembre como fecha de visita | La compra es rechazada | Pendiente |
| CP-16 | Seleccionar una fecha a más de 31 días de la fecha actual | La compra es rechazada | Pendiente |
| CP-17 | Intentar comprar entradas para el día actual después de las 17:30 | La compra es rechazada | Pendiente |

### 4. Validación de la edad y descuentos

| ID | Caso de prueba | Resultado esperado | Estado |
|---|---|---|---|
| CP-18 | Ingresar una edad negativa | La compra es rechazada | Pendiente |
| CP-19 | Comprar una entrada para una persona de hasta 3 años, inclusive | La entrada no tiene costo | Pendiente |
| CP-20 | Comprar una entrada para una persona mayor de 3 y hasta 15 años, inclusive | Se aplica un descuento del 50 % | Pendiente |
| CP-21 | Comprar una entrada para una persona mayor de 15 y menor de 60 años | No se aplica descuento por edad | Pendiente |
| CP-22 | Comprar una entrada para una persona de 60 años o más | Se aplica un descuento del 50 % | Pendiente |

### 5. Modalidades de pago

| ID | Caso de prueba | Resultado esperado | Estado |
|---|---|---|---|
| CP-23 | Comprar entradas seleccionando el pago en boletería | La compra se procesa correctamente | Pendiente |
| CP-24 | Comprar entradas con tarjeta de crédito y confirmar la compra | El usuario es redirigido a Mercado Pago | Pendiente |

### 6. Confirmación de la compra

| ID | Caso de prueba | Resultado esperado | Estado |
|---|---|---|---|
| CP-25 | Completar una compra correctamente | Se envía el correo electrónico de confirmación | Pendiente |
| CP-26 | Finalizar una compra correctamente | Se informa la cantidad de entradas compradas y la fecha de visita | Pendiente |

