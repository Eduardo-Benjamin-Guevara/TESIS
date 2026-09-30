// Asistente inteligente: envía la pregunta al backend y pinta la respuesta.
(function () {
    "use strict";

    var contenedor = document.getElementById("iaMensajes");
    var texto = document.getElementById("iaTexto");
    var boton = document.getElementById("iaEnviar");
    if (!contenedor || !texto || !boton) {
        return;
    }

    var enviando = false;

    function tokenCsrf() {
        var meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute("content") : "";
    }

    function añadirMensaje(textoUsuario, esUsuario) {
        var div = document.createElement("div");
        div.className = "ia-burbuja " + (esUsuario ? "usuario" : "asistente");
        div.textContent = textoUsuario;
        contenedor.appendChild(div);
        contenedor.scrollTop = contenedor.scrollHeight;
        return div;
    }

    function enviar() {
        var mensaje = (texto.value || "").trim();
        if (!mensaje || enviando) {
            return;
        }
        enviando = true;
        añadirMensaje(mensaje, true);
        texto.value = "";

        var indicador = añadirMensaje("✍️ Escribiendo...", false);

        fetch("/ia/api/preguntar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": tokenCsrf()
            },
            body: JSON.stringify({ mensaje: mensaje })
        })
            .then(function (resp) { return resp.json(); })
            .then(function (datos) {
                indicador.remove();
                if (datos.error) {
                    añadirMensaje("⚠️ " + datos.error, false);
                } else {
                    añadirMensaje(datos.respuesta, false);
                }
            })
            .catch(function () {
                indicador.remove();
                añadirMensaje("⚠️ Ocurrió un error al intentar responderte. Intenta de nuevo.", false);
            })
            .finally(function () {
                enviando = false;
                texto.focus();
            });
    }

    boton.addEventListener("click", enviar);
    texto.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            enviar();
        }
    });

    document.querySelectorAll("[data-sugerencia]").forEach(function (chip) {
        chip.addEventListener("click", function () {
            texto.value = chip.getAttribute("data-sugerencia");
            enviar();
        });
    });

    texto.focus();
})();