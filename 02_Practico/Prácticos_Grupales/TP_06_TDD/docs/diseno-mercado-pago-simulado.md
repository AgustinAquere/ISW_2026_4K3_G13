# Diseño: Mercado Pago simulado para la demo

TP 6 — TDD · Ingeniería y Calidad de Software · UTN FRC · 4K3 · Grupo 13 · 19/10/2026

> **Estado (19/10/2026):** las Tareas 1 a 4 del [plan](plan-mercado-pago-simulado.md) están hechas (ciclos 19 a 22): el núcleo, la API, las rutas y la conexión con la aplicación. La página de checkout (Tarea 5) quedó mínima, porque el grupo priorizó la integración con el Mercado Pago real en modo prueba. Con esa integración, el pago se abre en otra pestaña y el sitio lo verifica por el número de compra (decisión 18 de [DECISIONES_DE_DISENO.md](../DECISIONES_DE_DISENO.md)).

## 1. Para qué

El grupo tiene que mostrarle el TP al profesor **sin una cuenta real de Mercado Pago**. En esa demo el profesor toca "Pagar con Mercado Pago", completa una tarjeta, el pago se aprueba y vuelve al sitio, donde la compra queda confirmada y se envía el mail. También se tiene que poder mostrar un **pago rechazado** y cómo reacciona el sitio.

Hoy, sin credenciales, `PasarelaMercadoPagoSimulada` devuelve un link que vuelve directo al sitio con el pago aprobado: no hay pantalla de pago, no se puede mostrar un rechazo y el recorrido no se parece al real.

## 2. Qué se construye

**El grupo eligió el modo simulado** (19/10/2026): no hay tiempo para configurar y depurar la integración con el Mercado Pago real. El código de esa integración se queda como está, pero el grupo no lo va a configurar ni probar con credenciales para esta entrega.

La aplicación sigue eligiendo el modo por el `.env`:

| Modo | Cuándo | Qué pasa |
|---|---|---|
| **Simulado** (el que se usa) | `MP_ACCESS_TOKEN` vacío | **Nuevo:** un Mercado Pago simulado dentro de la misma aplicación, con pantalla de checkout, resultado y vuelta al sitio. |
| Real (modo prueba de Mercado Pago) | `MP_ACCESS_TOKEN` tiene un valor | Sin cambios y fuera del alcance de esta entrega ([CONFIGURACION_CREDENCIALES.md](../CONFIGURACION_CREDENCIALES.md)). |

### 2.1 Recorrido de la demo (modo simulado)

1. En EcoHarmony Park, el usuario compra con tarjeta. La compra queda pendiente de pago y el front muestra "Pagar con Mercado Pago" (sin cambios respecto de hoy).
2. El botón lleva a la **página de checkout simulada**, que tiene:
   - **Franja superior celeste** con el logo de Mercado Pago a la izquierda y, a la derecha, un aviso siempre visible: "Simulación · no se cobra dinero".
   - **Formulario de tarjeta:** número, nombre del titular, vencimiento (MM/AA), código de seguridad y DNI. El botón dice "Pagar $<total>".
   - **Resumen de la compra:** la descripción (por ejemplo, "EcoHarmony Park: 2 entradas REGULAR para el 23/10/2026") y el total.
   - **Ayuda:** qué titular da cada resultado.
3. Al pagar se muestra la **pantalla de resultado**:
   - **Aprobado:** tilde verde, "¡Listo! Se acreditó tu pago", monto, número de operación y botón "Volver al sitio".
   - **Rechazado:** ícono rojo, "No pudimos procesar tu pago", y los botones "Pagar con otra tarjeta" (vuelve al formulario de la misma preferencia) y "Volver al sitio".
   - **Pendiente:** ícono amarillo, "Tu pago está en proceso" y "Volver al sitio".
4. "Volver al sitio" redirige a la `back_url` de la preferencia, con los mismos parámetros que agrega Mercado Pago. Desde ahí, el sitio sigue el camino que ya existe: `POST /compras/{id}/pago` → consulta del pago → compra confirmada y mail, o pago rechazado o pendiente informado.

Los bocetos aprobados son el checkout con el logo, las pantallas de resultado aprobado y rechazado, y la vuelta al sitio.

### 2.2 El titular define el resultado

Igual que las [tarjetas de prueba reales](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro/integration-test/test-purchases):

| Titular | Resultado (`status` / `status_detail`) |
|---|---|
| `APRO` | `approved` / `accredited` |
| `CONT` | `pending` / `pending_contingency` |
| `OTHE` | `rejected` / `cc_rejected_other_reason` |
| `FUND` | `rejected` / `cc_rejected_insufficient_amount` |
| `SECU` | `rejected` / `cc_rejected_bad_filled_security_code` |
| cualquier otro | `rejected` / `cc_rejected_other_reason` |

El grupo pidió aprobado y rechazado. `CONT` (pendiente) y los rechazos con motivo son **decisión del diseño**: cuestan poco y el front ya sabe mostrar un pago pendiente.

### 2.3 Validación de la tarjeta

Según lo que definió el grupo, la simulación **solo comprueba que el número tenga formato de tarjeta**. No compara contra una lista de tarjetas de prueba. El grupo no va a usar tarjetas reales en la simulación. Las validaciones son:

- **Número:** solo dígitos (se aceptan espacios), con un largo y un prefijo de una marca conocida, y que pase el dígito verificador (algoritmo de Luhn), que es el control estándar de formato de las tarjetas:

  | Marca | Prefijo | Largo |
  |---|---|---|
  | Visa | 4 | 13, 16 o 19 |
  | Mastercard | 51 a 55, o 2221 a 2720 | 16 |
  | American Express | 34 o 37 | 15 |

  Si no cumple, el formulario muestra "Revisá el número de tarjeta".
- **Código de seguridad:** 4 dígitos para American Express y 3 para las demás.
- **Vencimiento:** formato MM/AA con un mes futuro. Se calcula contra la fecha actual, nunca contra una fecha fija.
- **Titular y DNI:** obligatorios; el DNI, de 7 u 8 dígitos.

Las [tarjetas de prueba de Mercado Pago](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro/integration-test/test-purchases) cumplen el formato (se verificó el Luhn de las cinco), así que se pueden usar en la demo; por ejemplo, Mastercard 5031 7557 3453 0604, código 123.

**Decisión del diseño:** sin selector de crédito o débito. Todos los pagos simulados son con tarjeta de crédito (`payment_type=credit_card`).

## 3. Cómo funciona por dentro

### 3.1 La misma API que Mercado Pago

El simulador implementa las dos operaciones de la API que ya usa `PasarelaMercadoPago`, con los mismos caminos, el mismo JSON y los mismos códigos de error:

| Operación | Request | Respuesta |
|---|---|---|
| Crear preferencia | `POST /checkout/preferences` con `items`, `external_reference`, `back_urls` y opcionalmente `auto_return`, y `Authorization: Bearer <token>` | `201` con `id`, `init_point` y `sandbox_init_point` (los dos apuntan a la página de checkout simulada) |
| Consultar pago | `GET /v1/payments/{id}` con `Authorization: Bearer <token>` | `200` con `id` (número), `status`, `status_detail`, `external_reference`, `transaction_amount`, `currency_id`, `payment_method_id`, `date_created`; `404` si no existe |

Sin cabecera `Authorization`, o con un token distinto del de simulación, responde `401`, como el real.

**Decisión del diseño:** `init_point` y `sandbox_init_point` son URLs absolutas armadas con `URL_PUBLICA`, por ejemplo `http://127.0.0.1:8000/mercadopago-simulado/checkout?pref_id=...`, como las del real.

**`PasarelaMercadoPago` es la misma clase en los dos modos.** Solo cambia a qué API le habla. La demo pasa por el mismo código que el pago real: crear la preferencia, redirigir, volver, consultar el pago y confirmar.

### 3.2 Cómo llega la pasarela al simulador

- `PasarelaMercadoPago` recibe la URL base de la API, cuyo valor por defecto es `https://api.mercadopago.com`. Las constantes `URL_PREFERENCIAS_MERCADO_PAGO` y `URL_PAGOS_MERCADO_PAGO` pasan a armarse a partir de esa base.
- En modo simulado, `dependencias.crear_pasarela_pago` crea `PasarelaMercadoPago` con un token fijo de simulación (por ejemplo, `SIMULADO`). Usa un cliente `httpx` cuyo transporte (`httpx.MockTransport`) atiende las solicitudes con el simulador **dentro del mismo proceso**.

**Decisión del diseño:** usar un transporte en proceso en lugar de una llamada HTTP del servidor a sí mismo. Así no depende de en qué puerto corre la aplicación ni ocupa un hilo del servidor esperando su propia respuesta. Los caminos, el JSON y los códigos siguen siendo los de la API real, así que el adaptador no nota la diferencia. El simulador también se expone por HTTP en `/mercadopago-simulado/api/...`, para que se pueda ver en `/docs` y probar con `curl`.

### 3.3 Componentes

| Componente | Responsabilidad |
|---|---|
| `MercadoPagoSimulado` (núcleo, sin FastAPI) | Guarda preferencias y pagos, crea un pago a partir del titular, arma la URL de vuelta y responde las operaciones de la API |
| Transporte en proceso | Traduce `httpx.Request` ⇄ operaciones del núcleo, para `PasarelaMercadoPago` |
| Router `/mercadopago-simulado` | La API por HTTP, la página de checkout, el endpoint que recibe el pago del formulario y la pantalla de resultado |
| Página de checkout (HTML, CSS y JS estáticos) | El formulario, la validación del formato de la tarjeta en el navegador y el envío del pago |
| Logo | Archivo estático tomado de los recursos de marca oficiales de Mercado Pago |

### 3.4 Pagar desde el formulario

- **En el navegador:** el formulario valida el formato de la tarjeta (sección 2.3) y que estén todos los campos.
- **Qué se envía:** `POST /mercadopago-simulado/checkout/{pref_id}/pagos` con **solo** el titular, la marca de la tarjeta (`visa`, `master` o `amex`) y los últimos 4 dígitos. **El número completo, el código y el vencimiento no salen del navegador.**
- **En el servidor:** el endpoint crea el pago con el resultado que corresponde al titular, con monto igual al total de la preferencia. Después redirige a la pantalla de resultado.
- **La URL de vuelta** se arma con la `back_url` de la preferencia más `collection_id`, `collection_status`, `payment_id`, `status`, `external_reference`, `payment_type=credit_card`, `merchant_order_id`, `preference_id`, `site_id=MLA` y `processing_mode=aggregator`. Son los mismos parámetros que documenta Mercado Pago ([configurar back URLs](https://www.mercadopago.com.ar/developers/en/docs/checkout-pro-orders/web-integration/configure-back-urls)).
- **`auto_return`:** si la preferencia lo pide y el pago fue aprobado, la pantalla de resultado vuelve sola al sitio a los pocos segundos, como el real.

### 3.5 Datos

**Decisión del diseño:** preferencias y pagos simulados se guardan **en memoria**, mientras el servidor está levantado. Si el servidor se reinicia en medio de un pago, la preferencia se pierde: el checkout muestra "Preferencia inexistente", y la confirmación responde que el pago no corresponde a la compra. Para una demo alcanza. Guardarlos en SQLite sería un cambio chico si hiciera falta.

Los ids de pago son números, como en el real, porque `consultar_pago` no consulta ids no numéricos. El monto del pago es siempre el total de la preferencia.

**Decisión del diseño:** una preferencia que ya tiene un pago aprobado no acepta otro. Su página de checkout muestra "Este pago ya fue realizado" y el botón "Volver al sitio". Después de un rechazo o de un pendiente se puede volver a pagar, como en el real.

### 3.6 Qué pasa con `PasarelaMercadoPagoSimulada`

La aplicación deja de usarla. Las pruebas que hoy la usan como doble (fixture `pasarela_pago`, `test_pasarela_simulada.py`) se adaptan al nuevo simulador o se quedan con un doble mínimo dentro de `tests/`. Lo decide quien implemente. Lo que no puede pasar es que el código de la aplicación tenga una clase que solo usan las pruebas.

## 4. Objetivos, no objetivos y lo que no puede pasar

**Objetivos**
- La demo completa (aprobado y rechazado) funciona sin cuenta, sin credenciales y sin internet, salvo las fuentes y el calendario que el front ya carga desde CDN.
- El checkout se parece al real: colores, orden de los campos, logo, textos y pantallas de resultado.
- La API simulada respeta el contrato de la real, así que `PasarelaMercadoPago` no tiene ramas especiales para el modo simulado.
- El código del modo real no se rompe: sus pruebas automatizadas siguen pasando.

**No objetivos**
- Configurar o probar el modo real con credenciales (decisión del grupo, por tiempo).
- Inicio de sesión del comprador. El real lo pide para las cuentas de prueba; la simulación lo saltea para que la demo sea directa (decisión del grupo, por tiempo).
- Comparar el número contra la lista de tarjetas de prueba: solo se valida el formato.
- Cuotas, dinero en cuenta, Rapipago y Pago Fácil, notificaciones (webhooks) y devoluciones.
- Hacer pasar la simulación por el sitio real de Mercado Pago.

**Lo que no puede pasar**
- Que el número de tarjeta, el código o el vencimiento salgan del navegador o se guarden.
- Que la página simulada no se distinga del sitio real: el aviso "Simulación · no se cobra dinero" está siempre visible.
- Que el modo simulado se active con credenciales cargadas, o que el modo real se rompa.
- Pruebas con fechas fijas, por ejemplo vencimientos de tarjeta escritos a mano.

## 5. Restricciones

- **TDD con Red / Green / Refactor**, un commit por paso, como los ciclos 13 a 18. El núcleo, el transporte, la API y los endpoints del formulario se construyen desde pruebas. La página de checkout (JS) no tiene pruebas automatizadas, igual que el front del sitio: la validación de formato se prueba a mano en el navegador. Sí se prueba que la página se sirva y que tenga el formulario.
- **Verificación con mutaciones** de las reglas nuevas (titular → resultado, monto, parámetros de vuelta, 401 sin token, 404 de pago inexistente, que no viaje el número de tarjeta), como en `CICLO_TDD.md`.
- **Fechas dinámicas en las pruebas** ([decisión 16](../DECISIONES_DE_DISENO.md)).
- **Estilo:** PEP 8 con Ruff (79 columnas). Los archivos existentes guardan CRLF: hay que conservarlo.
- **Documentación:** actualizar `DECISIONES_DE_DISENO.md`, `CICLO_TDD.md`, `BACKLOG.md`, `README.md` (cómo hacer la demo) y `CONFIGURACION_CREDENCIALES.md` (qué modo se usa según el `.env`).

## 6. Riesgos y temas para el modo real (fuera de esta entrega)

- La documentación de Wallet Brick de Mercado Pago pide no usar dominios locales (`localhost`, `127.0.0.1`) en las URLs de vuelta ([modo de apertura](https://www.mercadopago.com.ar/developers/en/docs/checkout-bricks/wallet-brick/advanced-features/opening-mode)). La de Checkout Pro no lo menciona. Hay que comprobarlo cuando se pruebe el modo real con credenciales. Si Mercado Pago rechaza la preferencia, hará falta una URL pública (por ejemplo, un túnel con ngrok). El modo simulado no tiene esta limitación.
- **Logo:** se usa el de los recursos de marca que Mercado Pago ofrece para integraciones. Si no se consigue un archivo oficial, va el nombre "Mercado Pago" en texto, sin dibujar una imitación del logo.

## 7. Lo que queda a criterio de quien implemente

- Los nombres de módulos, clases y rutas internas, salvo los caminos de la API (sección 3.1), que copian los reales.
- Si la página de checkout es un HTML estático que pide los datos de la preferencia por JSON o una plantilla que arma el servidor.
- El formato de los ids (preferencia: texto con el formato `<número>-<uuid>` del real; pagos y `merchant_order_id`: números correlativos).
- Cuántos segundos espera `auto_return` antes de volver (el real usa unos 5).
