# Consigna — Práctico 6: TDD (Evaluable)

Ingeniería y Calidad de Software · UTN FRC · 2026 · 4K3 · Grupo 13

Fuente: *ISW_Enunciados TP evaluables 2026 – 2do Cuatrimestre*, Práctico 6.

| | |
|---|---|
| **Unidad** | Unidad Nro. 4: Aseguramiento de Calidad de Proceso y de Producto |
| **Consigna** | Implementar una funcionalidad determinada utilizando el enfoque de Desarrollo Conducido por Pruebas (TDD), en el lenguaje de programación elegido por el grupo, utilizando el enfoque Red-Green-Refactor para construir el código desde las pruebas. |
| **Objetivo** | Aplicar el enfoque TDD para diseñar y construir software a partir de pruebas automatizadas, poniendo en práctica buenas prácticas de diseño y desarrollo orientado a la calidad desde el inicio. |
| **Propósito** | Familiarizarse con el ciclo TDD (Red-Green-Refactor), incorporando buenas prácticas de diseño y testing, y fortaleciendo la disciplina del desarrollo guiado por pruebas como base para un código de calidad. |

## Entradas

- Conceptos teóricos sobre el tema desarrollados en clase.
- Bibliografía referenciada sobre el tema.
- Enunciado del Trabajo Práctico 2: EcoHarmony Park.
- Definición completa de las User Stories correspondientes al Trabajo Práctico 2 "Requerimientos Ágiles – User Stories y Estimaciones".
- Reglas de estilo de código seleccionadas por el grupo para el Trabajo Práctico 2.

## Salida

- Implementación funcional de la User Story asignada.
- Conjunto de pruebas automatizadas que cubran los distintos casos definidos.
- Documento que justifique las decisiones de diseño tomadas.

## Instrucciones

- Seleccionar una User Story a implementar de entre las siguientes opciones:
  - Comprar entradas (grupos impares)
  - Inscribirme a actividad (grupos pares)
- Utilizando el lenguaje y documento de estilos de código seleccionado para el Trabajo Práctico 2 "Requerimientos Ágiles – User Stories y Estimaciones", implementar la funcionalidad aplicando el ciclo TDD:
  - **Red:** Escribir una prueba que falle.
  - **Green:** Implementar el código mínimo para que pase.
  - **Refactor:** Mejorar el diseño del código sin romper las pruebas.

## User Story asignada

El Grupo 13 es impar, por lo que corresponde **Comprar entradas** (8 SP).

> COMO visitante QUIERO comprar una entrada PARA asegurar mi visita al parque.

**Criterios de aceptación**

- Debe indicar la fecha de visita deseada, la cantidad de entradas requeridas, la edad de cada visitante y tipo de pase (VIP o regular).
- La fecha de visita guiada puede ser del día actual o futuro.
- Debe enviar un mensaje de confirmación vía mail.
- Debe redirigir a Mercado Pago al confirmar la compra si el pago es con tarjeta de crédito.
- La fecha de la visita debe estar dentro de los días en que el parque está abierto.
- Debe seleccionar la forma de pago: efectivo en caso de querer pagar en boletería o con tarjeta.
- La cantidad de entradas requeridas no debe ser mayor a 10.
- Al finalizar la compra se debe informar la cantidad de entradas compradas y la fecha.
- Se debe permitir la compra de entradas solo a usuarios registrados.

**Pruebas de usuario**

- Probar comprar una entrada indicando la fecha de visita dentro de los días disponibles, una cantidad de entradas menor a 10, la edad de todos los visitantes, el tipo de pase, la forma de pago con tarjeta mediante Mercado Pago y recepción del mail de confirmación (pasa).
- Probar comprar entradas sin seleccionar forma de pago (falla).
- Probar comprar entradas ingresando una fecha de visita en la cual el parque se encuentra cerrado (falla).
- Probar comprar entradas ingresando una cantidad de entradas mayor a 10 (falla).

## Dónde se cumple cada salida

| Salida pedida | Ubicación en el repositorio |
|---|---|
| Implementación funcional de la User Story | [`backend/app/`](backend/app/) (API FastAPI y front en `backend/app/static/`) |
| Pruebas automatizadas | [`backend/tests/`](backend/tests/) y su trazabilidad en [BACKLOG.md](BACKLOG.md) |
| Documento de decisiones de diseño | [DECISIONES_DE_DISENO.md](DECISIONES_DE_DISENO.md) |
| Evidencia del ciclo Red-Green-Refactor | [CICLO_TDD.md](CICLO_TDD.md) |
