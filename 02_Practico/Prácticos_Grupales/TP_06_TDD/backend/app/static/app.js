"use strict";

const CLAVE_SESION = "ecoharmony.email";
const CANTIDAD_MAXIMA = 10;
const $ = (id) => document.getElementById(id);

const pesos = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 0,
});

let fechaElegida = null;

// Sesión simulada (FAQ 19): el email representa al usuario logueado.
function leerSesion() {
  try {
    return localStorage.getItem(CLAVE_SESION);
  } catch {
    return null;
  }
}

function guardarSesion(email) {
  try {
    if (email) localStorage.setItem(CLAVE_SESION, email);
    else localStorage.removeItem(CLAVE_SESION);
  } catch {
    // Sin almacenamiento la sesión dura hasta recargar la página.
  }
  sesionEnMemoria = email;
}

let sesionEnMemoria = leerSesion();

function mostrarPantalla() {
  const email = sesionEnMemoria;
  $("pantalla-ingreso").hidden = Boolean(email);
  $("pantalla-compra").hidden = !email;
  $("pantalla-confirmacion").hidden = true;
  $("sesion").hidden = !email;
  $("sesion-email").textContent = email || "";
}

// Pantalla propia para la compra confirmada (pago aprobado, efectivo o sin
// costo), con el resumen de la compra (cantidad de entradas y fecha) y el
// botón para volver al inicio del flujo.
function mostrarConfirmacion(compra, { titulo, etiquetaTotal, pago = "" }) {
  if ($("dialogo").open) $("dialogo").close();
  $("pantalla-ingreso").hidden = true;
  $("pantalla-compra").hidden = true;
  $("confirmacion-titulo").textContent = titulo;
  $("confirmacion-resumen").textContent = `${compra.mensaje}.`;
  $("confirmacion-numero").textContent = compra.id;
  $("confirmacion-pase").textContent = compra.tipo_pase === "VIP" ? "VIP" : "Regular";
  $("confirmacion-total-etiqueta").textContent = etiquetaTotal;
  $("confirmacion-total").textContent = pesos.format(compra.total);
  $("confirmacion-pago").textContent = pago;
  $("confirmacion-pago").hidden = !pago;
  $("confirmacion-mail").textContent = `Te enviamos un mail de confirmación a ${sesionEnMemoria}.`;
  $("pantalla-confirmacion").hidden = false;
  window.scrollTo(0, 0);
  $("volver-al-inicio").focus();
}

function mostrarPagoAprobado(compra) {
  mostrarConfirmacion(compra, {
    titulo: "¡Pago aprobado!",
    etiquetaTotal: "Total pagado",
  });
}

$("form-ingreso").addEventListener("submit", (evento) => {
  evento.preventDefault();
  const campo = $("email");
  if (!campo.value.trim() || !campo.checkValidity()) {
    $("error-ingreso").textContent = "Ingresá un email válido.";
    return;
  }
  $("error-ingreso").textContent = "";
  guardarSesion(campo.value.trim());
  mostrarPantalla();
});

$("cerrar-sesion").addEventListener("click", () => {
  // La espera del pago es de la sesión que se cierra.
  compraEnEspera = null;
  clearInterval(temporizadorDePago);
  guardarSesion(null);
  mostrarPantalla();
});

// 1. Calendario: solo se habilitan las fechas que informa el backend.
function fechaLarga(iso) {
  return new Date(`${iso}T00:00`).toLocaleDateString("es-AR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

async function iniciarCalendario() {
  let fechas = [];
  try {
    const respuesta = await fetch("/fechas-disponibles");
    fechas = (await respuesta.json()).fechas;
  } catch {
    $("fecha-elegida").textContent =
      "No se pudieron cargar las fechas. Recargá la página.";
    return;
  }
  if (fechas.length === 0) {
    $("fecha-elegida").textContent = "No hay fechas disponibles.";
  }
  flatpickr("#fecha", {
    inline: true,
    locale: flatpickr.l10ns.es,
    dateFormat: "Y-m-d",
    enable: fechas,
    onChange: (_seleccion, iso) => {
      fechaElegida = iso || null;
      $("fecha-elegida").textContent = iso
        ? `Visitás el ${fechaLarga(iso)}.`
        : "Elegí un día en el calendario.";
    },
  });
}

// 2. Cantidad y una edad por visitante.
function cantidad() {
  return Number.parseInt($("cantidad").value, 10);
}

function dibujarEdades() {
  const contenedor = $("edades");
  const anteriores = [...contenedor.querySelectorAll("input")].map(
    (campo) => campo.value,
  );
  const n = Math.min(Math.max(cantidad() || 0, 0), CANTIDAD_MAXIMA);
  contenedor.replaceChildren();
  for (let i = 0; i < n; i += 1) {
    const caja = document.createElement("div");
    const etiqueta = document.createElement("label");
    const campo = document.createElement("input");
    campo.type = "number";
    campo.min = "0";
    campo.max = "120";
    campo.inputMode = "numeric";
    campo.id = `edad-${i}`;
    campo.value = anteriores[i] ?? "";
    campo.addEventListener("input", cotizar);
    etiqueta.htmlFor = campo.id;
    etiqueta.textContent = `Edad visitante ${i + 1}`;
    caja.append(etiqueta, campo);
    contenedor.append(caja);
  }
  cotizar();
}

function cambiarCantidad(delta) {
  const actual = cantidad() || 0;
  $("cantidad").value = Math.min(Math.max(actual + delta, 1), CANTIDAD_MAXIMA);
  dibujarEdades();
}

$("menos").addEventListener("click", () => cambiarCantidad(-1));
$("mas").addEventListener("click", () => cambiarCantidad(1));
$("cantidad").addEventListener("input", dibujarEdades);

function edades() {
  return [...$("edades").querySelectorAll("input")].map((campo) =>
    campo.value === "" ? null : Number(campo.value),
  );
}

function opcionElegida(nombre) {
  return document.querySelector(`input[name="${nombre}"]:checked`)?.value;
}

// Total mostrado antes de elegir la forma de pago, calculado por el backend.
let ultimaCotizacion = 0;

async function cotizar() {
  const lista = edades();
  const tipoPase = opcionElegida("tipo_pase");
  const completo =
    tipoPase && lista.length > 0 && lista.every((e) => e !== null && e >= 0);
  if (!completo) {
    $("total").textContent = "—";
    return;
  }
  const numero = ++ultimaCotizacion;
  try {
    const respuesta = await fetch("/cotizacion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ edades: lista, tipo_pase: tipoPase }),
    });
    if (numero !== ultimaCotizacion) return;
    $("total").textContent = respuesta.ok
      ? pesos.format((await respuesta.json()).total)
      : "—";
  } catch {
    $("total").textContent = "—";
  }
}

document
  .querySelectorAll('input[name="tipo_pase"]')
  .forEach((opcion) => opcion.addEventListener("change", cotizar));

// Confirmar la compra.
function validar() {
  const n = cantidad();
  if (!fechaElegida) return "Elegí la fecha de visita.";
  if (!Number.isInteger(n) || n < 1 || n > CANTIDAD_MAXIMA) {
    return `La cantidad de entradas debe estar entre 1 y ${CANTIDAD_MAXIMA}.`;
  }
  if (edades().some((e) => e === null || e < 0)) {
    return "Indicá la edad de cada visitante.";
  }
  if (!opcionElegida("tipo_pase")) return "Elegí el tipo de pase.";
  if (!opcionElegida("medio_pago")) return "Elegí la forma de pago.";
  return null;
}

$("form-compra").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const error = validar();
  $("error-compra").textContent = error || "";
  if (error) return;

  const boton = $("confirmar");
  boton.disabled = true;
  try {
    const respuesta = await fetch("/compras", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Usuario-Email": sesionEnMemoria,
      },
      body: JSON.stringify({
        fecha_visita: fechaElegida,
        cantidad: cantidad(),
        edades: edades(),
        tipo_pase: opcionElegida("tipo_pase"),
        medio_pago: opcionElegida("medio_pago"),
      }),
    });
    const datos = await respuesta.json();
    if (respuesta.ok) {
      mostrarCompra(datos);
    } else if (respuesta.status === 422) {
      $("error-compra").textContent = "Revisá los datos ingresados.";
    } else if (respuesta.status === 401) {
      $("error-compra").textContent =
        `${datos.detail}. Tocá "Cambiar" para ingresar con otro email.`;
    } else {
      $("error-compra").textContent = datos.detail;
    }
  } catch {
    $("error-compra").textContent =
      "No se pudo conectar con el servidor. Intentá de nuevo.";
  } finally {
    boton.disabled = false;
  }
});

// Resultado: resumen, aviso del mail (FAQ 5) y redirección a Mercado Pago.
function abrirDialogo({ titulo, mensaje, detalle = "", mail = null, urlPago = null }) {
  $("dialogo-titulo").textContent = titulo;
  $("dialogo-mensaje").textContent = mensaje;
  $("dialogo-detalle").textContent = detalle;
  $("dialogo-mail").hidden = !mail;
  $("dialogo-mail").textContent = mail ? `Te enviamos un mail de confirmación a ${mail}.` : "";
  $("dialogo-pagar").hidden = !urlPago;
  if (urlPago) $("dialogo-pagar").href = urlPago;
  $("dialogo-cerrar").textContent = urlPago ? "Pagar más tarde" : "Listo";
  $("dialogo-espera").hidden = true;
  $("dialogo-verificar").hidden = true;
  if (!$("dialogo").open) $("dialogo").showModal();
}

function mostrarCompra(compra) {
  if (compra.estado !== "PENDIENTE_DE_PAGO") {
    // En efectivo o sin costo, la compra ya quedó confirmada.
    const enEfectivo = compra.medio_pago === "EFECTIVO";
    mostrarConfirmacion(compra, {
      titulo: "¡Compra confirmada!",
      etiquetaTotal: enEfectivo ? "Total a pagar" : "Total",
      pago: enEfectivo
        ? "Pagás en la boletería del parque el día de tu visita."
        : "Tu compra no tiene costo.",
    });
    compraEnEspera = null;
    return;
  }
  const pase = compra.tipo_pase === "VIP" ? "VIP" : "Regular";
  abrirDialogo({
    titulo: "¡Compra registrada!",
    mensaje: `${compra.mensaje}.`,
    detalle: `Pase ${pase} · Total ${pesos.format(compra.total)}. Completá el pago con Mercado Pago: te enviamos el mail de confirmación cuando se apruebe.`,
    urlPago: compra.url_pago,
  });
  compraEnEspera = compra;
  $("dialogo-pagar").textContent = "Pagar con Mercado Pago";
}

$("dialogo-cerrar").addEventListener("click", () => $("dialogo").close());

// Mercado Pago se abre en otra pestaña: esta pestaña pregunta al backend si
// la compra ya se pagó, cada 5 segundos y al volver a mirarla.
$("dialogo-pagar").target = "_blank";
$("dialogo-pagar").rel = "noopener";

let compraEnEspera = null;
let temporizadorDePago = null;

// La compra que espera el pago se guarda en el navegador: si la pestaña se
// recarga o se cierra después de pagar, se vuelve a verificar al abrirla.
const CLAVE_COMPRA_PENDIENTE = "ecoharmony.compraPendiente";

function guardarCompraPendiente(compra) {
  try {
    if (compra) {
      localStorage.setItem(
        CLAVE_COMPRA_PENDIENTE,
        JSON.stringify({ id: compra.id, url_pago: compra.url_pago, email: sesionEnMemoria }),
      );
    } else {
      localStorage.removeItem(CLAVE_COMPRA_PENDIENTE);
    }
  } catch {
    // Sin almacenamiento solo se verifica mientras la pestaña siga abierta.
  }
}

function leerCompraPendiente() {
  try {
    const compra = JSON.parse(localStorage.getItem(CLAVE_COMPRA_PENDIENTE));
    return compra && compra.email === sesionEnMemoria ? compra : null;
  } catch {
    return null;
  }
}

function esperarPago(compra) {
  compraEnEspera = compra;
  guardarCompraPendiente(compra);
  $("dialogo-titulo").textContent = "Esperando tu pago en Mercado Pago…";
  $("dialogo-mensaje").textContent =
    "Completá el pago en la pestaña de Mercado Pago. Cuando termines, volvé a esta pestaña.";
  $("dialogo-detalle").textContent = `Compra n.º ${compra.id}.`;
  $("dialogo-mail").hidden = true;
  $("dialogo-pagar").hidden = !compra.url_pago;
  if (compra.url_pago) $("dialogo-pagar").href = compra.url_pago;
  $("dialogo-pagar").textContent = "Abrir Mercado Pago de nuevo";
  $("dialogo-cerrar").textContent = "Pagar más tarde";
  mostrarEspera(ESPERANDO_CONFIRMACION);
  $("dialogo-verificar").hidden = false;
  if (!$("dialogo").open) $("dialogo").showModal();
  clearInterval(temporizadorDePago);
  temporizadorDePago = setInterval(verificarPago, 5000);
}

const ESPERANDO_CONFIRMACION =
  "Estamos esperando la confirmación del pago. Esto puede demorar unos segundos…";

function mostrarEspera(texto) {
  $("dialogo-espera").textContent = texto;
  $("dialogo-espera").hidden = false;
}

// Mercado Pago tarda unos segundos en informar el pago: además de consultar
// solo, el usuario puede pedir la consulta en el momento.
$("dialogo-verificar").addEventListener("click", async () => {
  const boton = $("dialogo-verificar");
  boton.disabled = true;
  boton.textContent = "Consultando…";
  const resultado = await verificarPago();
  boton.disabled = false;
  boton.textContent = "Ya pagué: verificar ahora";
  if (resultado === "sin_pago" || resultado === "pendiente") {
    mostrarEspera(
      "Todavía no vemos el pago aprobado. Mercado Pago puede demorar unos segundos: volvé a probar en un momento.",
    );
  } else if (resultado === "error") {
    mostrarEspera("No pudimos consultar el pago. Probá de nuevo en un momento.");
  }
});

$("dialogo-pagar").addEventListener("click", () => {
  if (compraEnEspera) esperarPago(compraEnEspera);
});

// Al abrir la página, una compra que quedó esperando el pago se verifica.
function retomarCompraPendiente() {
  const compra = sesionEnMemoria && leerCompraPendiente();
  if (!compra) return;
  esperarPago(compra);
  verificarPago();
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && compraEnEspera) verificarPago();
});

// Devuelve el estado del pago ("aprobado", "rechazado", "pendiente",
// "sin_pago") o "error" si no se pudo consultar.
async function verificarPago() {
  const compra = compraEnEspera;
  if (!compra) return null;
  try {
    const respuesta = await fetch(`/compras/${compra.id}/verificacion-de-pago`, {
      method: "POST",
      headers: { "X-Usuario-Email": sesionEnMemoria },
    });
    const datos = await respuesta.json();
    if (!respuesta.ok) return "error";
    if (compraEnEspera !== compra) return datos.pago;
    if (datos.pago === "aprobado") {
      compraEnEspera = null;
      guardarCompraPendiente(null);
      clearInterval(temporizadorDePago);
      mostrarPagoAprobado(datos);
    } else if (datos.pago === "rechazado") {
      $("dialogo-titulo").textContent = "Pago rechazado";
      $("dialogo-mensaje").textContent =
        "Mercado Pago rechazó el pago. Podés intentar con otra tarjeta.";
      mostrarEspera("Si volvés a pagar, la confirmación se detecta sola.");
    } else {
      $("dialogo-titulo").textContent = "Esperando tu pago en Mercado Pago…";
    }
    return datos.pago;
  } catch {
    // Sin conexión: se vuelve a intentar en la próxima consulta.
    return "error";
  }
}

// Vuelta desde Mercado Pago: el backend consulta el pago a Mercado Pago y, si
// está aprobado, confirma la compra y envía el mail. El estado que trae la
// URL solo se usa para explicar un pago que todavía no se aprobó.
const ESTADOS_DE_PAGO = {
  pending: ["Pago pendiente", "Mercado Pago está procesando el pago. Te enviamos el mail cuando se apruebe."],
  in_process: ["Pago pendiente", "Mercado Pago está procesando el pago. Te enviamos el mail cuando se apruebe."],
  rejected: ["Pago rechazado", "Podés intentar de nuevo con otra tarjeta desde el link de pago."],
};

async function confirmarPago(idCompra, idPago) {
  const respuesta = await fetch(`/compras/${encodeURIComponent(idCompra)}/pago`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Usuario-Email": sesionEnMemoria,
    },
    body: JSON.stringify({ id_pago: idPago }),
  });
  const datos = await respuesta.json();
  if (!respuesta.ok) throw new Error(datos.detail || "No se pudo confirmar el pago.");
  return datos;
}

async function informarVueltaDeMercadoPago() {
  const parametros = new URLSearchParams(window.location.search);
  const estado = parametros.get("collection_status") || parametros.get("status");
  const idCompra = parametros.get("external_reference");
  const idPago = parametros.get("payment_id") || parametros.get("collection_id");
  if (!estado && !idPago) return;
  window.history.replaceState(null, "", window.location.pathname);
  const detalle = idCompra ? `Compra n.º ${idCompra}.` : "";

  if (!idCompra || !idPago || idPago === "null") {
    abrirDialogo({
      titulo: "Pago no completado",
      mensaje: "No se completó el pago en Mercado Pago.",
      detalle,
    });
    return;
  }
  try {
    const compra = await confirmarPago(idCompra, idPago);
    if (compra.estado === "CONFIRMADA") {
      mostrarPagoAprobado(compra);
      return;
    }
    const [titulo, mensaje] = ESTADOS_DE_PAGO[estado] || [
      "Pago no completado",
      "No se completó el pago en Mercado Pago.",
    ];
    abrirDialogo({ titulo, mensaje, detalle });
  } catch (error) {
    abrirDialogo({
      titulo: "No pudimos confirmar el pago",
      mensaje: error.message,
      detalle,
    });
  }
}

mostrarPantalla();
dibujarEdades();
iniciarCalendario();
// Si la página se abre por la vuelta de Mercado Pago, esa vuelta ya verifica
// el pago; si no, se retoma la compra que había quedado esperando.
if (!window.location.search) retomarCompraPendiente();
informarVueltaDeMercadoPago();
