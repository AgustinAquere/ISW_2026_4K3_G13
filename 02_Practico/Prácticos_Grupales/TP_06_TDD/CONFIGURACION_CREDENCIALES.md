# Configuración de credenciales: mail y Mercado Pago

Guía paso a paso para que la aplicación envíe el mail de confirmación real y cobre con Mercado Pago en modo prueba. Sin estas credenciales la aplicación funciona igual, con el mail y el pago simulados.

Las credenciales van en `backend/.env`, que está excluido del repositorio. **Nunca subir credenciales al repositorio ni pegarlas en el chat del grupo.**

## 0. Crear el archivo `.env`

Desde la carpeta `backend`, copiar `.env.example` como `.env` (si todavía no existe):

```powershell
Copy-Item .env.example .env
```

En `USUARIOS_REGISTRADOS` van los emails que pueden comprar, separados por coma (sesión simulada, FAQ 19). Para recibir el mail de confirmación hay que ingresar en el front con uno de esos emails y que sea una casilla real:

```
USUARIOS_REGISTRADOS=visitante@ecoharmony.com,tu-correo@gmail.com
```

## 1. Correo que envía los mails (Gmail)

Conviene usar una cuenta de Gmail nueva, solo para el proyecto: la contraseña de aplicación da acceso para enviar mails desde esa cuenta.

1. **Crear la cuenta.** Ir a [accounts.google.com/signup](https://accounts.google.com/signup) y crear la cuenta (por ejemplo, `ecoharmony.g13@gmail.com`).
2. **Activar la verificación en 2 pasos.** Con la cuenta nueva abierta, ir a [myaccount.google.com/security](https://myaccount.google.com/security) → *Verificación en 2 pasos* → *Activar*. Google pide un número de celular. Sin este paso no aparece la opción de contraseñas de aplicación.
3. **Crear una contraseña de aplicación.** Ir a [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), escribir un nombre (por ejemplo, `EcoHarmony Park`) y tocar *Crear*. Google muestra una contraseña de 16 letras: copiarla **sin espacios**. Solo se muestra una vez; si se pierde, se borra y se crea otra.
4. **Completar el `.env`:**

   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PUERTO=587
   SMTP_USUARIO=ecoharmony.g13@gmail.com
   SMTP_CONTRASENA=abcdefghijklmnop
   SMTP_REMITENTE=EcoHarmony Park <ecoharmony.g13@gmail.com>
   ```

   `SMTP_CONTRASENA` es la contraseña de aplicación, no la contraseña de la cuenta.

## 2. Mercado Pago en modo prueba (Checkout Pro)

Se necesita una cuenta de Mercado Pago (puede ser la personal de un integrante). En modo prueba no se cobra dinero real.

1. **Crear la aplicación.** Ingresar con la cuenta de Mercado Pago a [mercadopago.com.ar/developers/panel/app](https://www.mercadopago.com.ar/developers/panel/app) → *Crear aplicación*. Nombre: `EcoHarmony Park`. Tipo de solución: *Pagos online*. Producto a integrar: *Checkout Pro*.
2. **Copiar el Access Token de prueba.** Al crear la aplicación, Mercado Pago genera solas las credenciales de prueba ([novedad de noviembre de 2025](https://www.mercadopago.com.ar/developers/es/news/2025/11/19/Streamlined-integration-testing-with-automatic-credentials)). Dentro de la aplicación, ir a *Pruebas > Credenciales de prueba* y copiar el **Access Token**. Es privado: no compartirlo. La *Public Key* no hace falta. **No activar las credenciales de producción**: son las que cobran dinero real.
3. **Crear un comprador de prueba.** En la aplicación, ir a *Cuentas de prueba* → *Crear cuenta de prueba* → tipo **Comprador**, país Argentina. Anotar el usuario y la contraseña que muestra la tabla. Con este usuario se paga en el checkout: no se puede pagar con la misma cuenta que vende. Las cuentas de prueba no se pueden borrar (hay un máximo de 15), así que alcanza con crear una.
4. **Completar el `.env`:**

   ```
   MP_ACCESS_TOKEN=<Access Token de prueba>
   URL_PUBLICA=http://127.0.0.1:8000/
   ```

   `URL_PUBLICA` es a donde vuelve Mercado Pago al terminar el pago. En la computadora local se deja como está.

## 3. Probar el flujo completo

1. Reiniciar el servidor (`Ctrl+C` y de nuevo `uvicorn app.main:app --reload`): el `.env` se lee al iniciar. En la consola ya no deben aparecer los avisos "Sin SMTP_HOST" ni "Sin MP_ACCESS_TOKEN" al hacer la primera compra.
2. Abrir `http://127.0.0.1:8000` e ingresar con el email registrado en el paso 0.
3. Comprar con **tarjeta**. La compra queda pendiente de pago y el front muestra el botón para pagar con Mercado Pago.
4. Abrir el link de pago en una **ventana de incógnito**, iniciar sesión con el **comprador de prueba** (si pide un código por e-mail, es el de 6 dígitos que figura en *Cuentas de prueba*) y pagar con una [tarjeta de prueba](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro/integration-test/test-purchases). Por ejemplo, Mastercard `5031 7557 3453 0604`, código `123`, vencimiento `11/30`, DNI `12345678` y como titular **`APRO`** (pago aprobado). El titular define el resultado: `OTHE` lo rechaza, `CONT` lo deja pendiente y `FUND` lo rechaza por saldo insuficiente.
5. Al terminar, tocar **Volver al sitio**. El front envía el pago al backend, que lo consulta a Mercado Pago, confirma la compra y envía el mail.
6. Revisar la casilla del email con el que se compró (y la carpeta de spam).

Una compra en **efectivo** envía el mail en el momento, sin pasar por Mercado Pago: es la forma más rápida de probar solo el mail.

## Problemas frecuentes

| Síntoma | Causa probable |
|---|---|
| En la consola: "No se pudo enviar el mail de confirmación" con `SMTPAuthenticationError` | Se usó la contraseña de la cuenta en lugar de la contraseña de aplicación, o tiene espacios |
| No aparece la opción de contraseñas de aplicación | Falta activar la verificación en 2 pasos |
| La compra con tarjeta responde "No se pudo iniciar el pago con Mercado Pago" | Access Token mal copiado o de otra aplicación |
| Mercado Pago no deja pagar con la tarjeta de prueba | Se está pagando con la cuenta que vende o sin el comprador de prueba: usar una ventana de incógnito e iniciar sesión con el comprador de prueba |
| El mail no llega | Revisar spam; verificar que el email del front esté en `USUARIOS_REGISTRADOS` y que el servidor se haya reiniciado después de editar el `.env` |
