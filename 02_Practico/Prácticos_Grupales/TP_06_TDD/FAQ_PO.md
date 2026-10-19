# FAQ del PO — EcoHarmony Park (TP 6 TDD)

Ingeniería y Calidad de Software · UTN FRC · 2026 · 4K3 · Grupo 13

Fuente: *FAQ PO TDD EcoHarmony Park* (guía de respuestas del equipo docente). Algunas preguntas aplican a las dos User Stories y otras a una sola. Las consultas fuera de este compendio se hacen al equipo docente de la comisión.

En el código y en la documentación se cita cada respuesta como "FAQ n" (por ejemplo, FAQ 27).

## Preguntas que aplican a "Comprar entradas"

| N.º | Pregunta | Respuesta del PO | Cómo se aplica en el proyecto |
|---|---|---|---|
| 1 | ¿Qué días abre el parque? | Todos los días, menos los lunes y los días festivos: 25 de diciembre y 1 de enero. | `dominio/calendario.py` (CP-13, CP-14, CP-15) |
| 2 | ¿Qué se debe mostrar cuando la fecha corresponde a un día en que el parque está cerrado? | Si el campo es un calendario, debería marcar el día como deshabilitado o no dejar seleccionarlo. | Calendario del front con las fechas de `GET /fechas-disponibles` |
| 3 | ¿Qué paleta de colores y fuente usar? | Paleta: [coolors.co/palette/386641-6a994e-a7c957-f2e8cf-bc4749](https://coolors.co/palette/386641-6a994e-a7c957-f2e8cf-bc4749). Fuente: Lato. | `static/styles.css` |
| 4 | Al redirigir hacia Mercado Pago, ¿podemos simularlo mostrando una pantalla que diga, por ejemplo, "Mercado Pago Compra Exitosa"? | Desarrollo (queda a criterio del equipo de desarrollo). | Se integra Mercado Pago Checkout Pro real (modo prueba). Sin credenciales, la aplicación simula el pago aprobado. |
| 5 | Al enviar el mail, ¿podemos simularlo mostrando un modal que diga, por ejemplo, "Mail enviado a tu@email.com"? | Desarrollo (queda a criterio del equipo de desarrollo). | Se envía el mail real por SMTP y además el front muestra el aviso. Sin credenciales, el mail se escribe en el log. |
| 6 | Precio de las entradas | VIP: $20.000. Común: $10.000. | `dominio/precios.py` |
| 7 | Descuentos por edad | Hasta 3 años inclusive: no pagan. Hasta 15 años inclusive: 50 % off. Desde 60 años inclusive: 50 % off. | `dominio/precios.py` (CP-19 a CP-22) |
| 11 | Horario del parque | De 8:30 a 19. | Base de la hora límite de compra para el día actual (FAQ 26) |
| 17 | Logo | Hay que diseñarlo y mandarlo para su validación. | El logo del front es provisorio |
| 19 | El registro/login del usuario, ¿es parte de esta US o asumimos que el usuario ya está logueado cuando compra? | No hace falta, pueden comenzar con la sesión y el usuario mockeados. | Cabecera `X-Usuario-Email` y usuarios registrados en `.env` (CP-07) |
| 20 | ¿Hay un cupo máximo de visitantes por día? | No hay máximo de visitantes por día. | No se controla un cupo diario |
| 21 | Diferencia entre pase VIP y regular | Para esta US, solo el precio. | `TipoPase` solo cambia el precio base |
| 24 | ¿Tiene que estar adaptada para celulares (responsive) o alcanza con que funcione en computadora? | Se pide una app mobile. Pueden hacerla web responsive. | Front web responsive |
| 25 | Horizonte de compra: ¿hasta cuántos días en adelante se puede seleccionar una fecha de visita? | Se pueden comprar las entradas con no más de un mes de anticipación. | 31 días como máximo (CP-16) |
| 26 | Límite horario de compra: ¿hasta qué hora del día actual se permite comprar una entrada para el mismo día? | Hasta 1 hora y media antes del cierre, es decir, hasta las 17:30. | `dominio/calendario.py` (CP-17) |
| 27 | Validación de cantidad máxima: ¿el límite de 10 entradas aplica por usuario logueado por día o por transacción? | Solo puede comprar 10 entradas para una fecha específica, ya sea en una o varias transacciones. | `ServicioCompra` y `entradas_compradas()` (CP-28) |

## Preguntas que aplican a "Inscribirme a actividad"

No corresponden a este grupo (impar), pero se registran para que el documento esté completo.

| N.º | Pregunta | Respuesta del PO |
|---|---|---|
| 8 | Visibilidad de cupos | El usuario puede ver los cupos disponibles. |
| 9 | Actividades que requieren vestimenta | Palestra y Tirolesa. |
| 12 | Horario de las actividades | De 9 a 18, un turno por hora. A las 18:00 no hay turno: es la cota superior. |
| 13 | Cupos por actividad | Safari 8, Palestra 12, Jardinería 12, Tirolesa 10. |
| 14 | Talles | XS, S, M, L, XL y XXL. |
| 15 | Límite de edad por actividad | Jardinería y Safari: todas las edades. Palestra: 12 o más. Tirolesa: 8 o más. |
| 16 | Términos y condiciones | Uno diferente por cada actividad. Hay que diseñarlos y mandarlos para su validación. |
| 18 | ¿Qué información debe incluir el mail de confirmación (número de orden, detalle de visitantes, QR de acceso)? | Esa información, más los subtotales y el total. |
| 22 | ¿Pueden agregar el nombre de la persona de la actividad? | Sí, pero opcional. |
| 23 | ¿Hasta cuándo se puede inscribir (anticipación respecto al turno)? | Se puede reservar dentro de las 24 h antes del turno: no se puede inscribir a una actividad del viernes siendo martes. |
| 28 | Información del mail de la actividad | Resumen de la inscripción y los QR. |
| 29 | ¿Puede una persona reservar actividades diferentes que ocurren al mismo tiempo? | No, se debe validar que esa persona no tenga inscripciones en otros turnos del mismo horario. |
| 30 | ¿Existe una ventana límite previa al inicio de la actividad para inscribirse? | Sí, de 15 minutos antes del inicio del turno. |
| 31 | ¿Existe una cantidad máxima de personas que un titular puede inscribir en una misma transacción? | No, mientras haya cupo para la actividad en ese horario puede inscribir la cantidad que desee. |
| 32 | La historia pide "DNI". ¿Se debe ampliar a "Documento / Pasaporte"? | Solo DNI. |

El documento no tiene pregunta 10.

## Tarjetas de las User Stories incluidas en el FAQ

El FAQ repite las tarjetas de las dos User Stories. La de "Comprar entradas" coincide con la del enunciado (ver [CONSIGNA.md](CONSIGNA.md)). La de "Inscribirme a actividad" figura con 3 SP en el FAQ y con 5 SP en el enunciado.
