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
  $("sesion").hidden = !email;
  $("sesion-email").textContent = email || "";
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
  $("dialogo").showModal();
}

function mostrarCompra(compra) {
  const pase = compra.tipo_pase === "VIP" ? "VIP" : "Regular";
  const pendiente = compra.estado === "PENDIENTE_DE_PAGO";
  let pago = "Pagás en la boletería del parque el día de tu visita.";
  if (compra.medio_pago === "TARJETA") {
    pago = pendiente
      ? "Completá el pago con Mercado Pago: te enviamos el mail de confirmación cuando se apruebe."
      : "No tenés nada para pagar.";
  }
  abrirDialogo({
    titulo: pendiente ? "¡Compra registrada!" : "¡Compra confirmada!",
    mensaje: `${compra.mensaje}.`,
    detalle: `Pase ${pase} · Total ${pesos.format(compra.total)}. ${pago}`,
    mail: pendiente ? null : sesionEnMemoria,
    urlPago: pendiente ? compra.url_pago : null,
  });
}

$("dialogo-cerrar").addEventListener("click", () => $("dialogo").close());

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
      abrirDialogo({
        titulo: "¡Pago aprobado!",
        mensaje: `${compra.mensaje}. Tus entradas están confirmadas.`,
        detalle: `${detalle} Total ${pesos.format(compra.total)}.`,
        mail: sesionEnMemoria,
      });
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
informarVueltaDeMercadoPago();
