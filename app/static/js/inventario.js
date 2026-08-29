// Gestión de inventario: carga dinámica de lotes según el alimento seleccionado.
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        var alimentoSelect = document.getElementById("alimentoSelect");
        var loteSelect = document.getElementById("loteSelect");
        if (!alimentoSelect || !loteSelect) return;

        function cargarLotes() {
            var alimentoId = alimentoSelect.value;
            loteSelect.disabled = true;
            loteSelect.innerHTML = '<option value="">Cargando...</option>';
            if (!alimentoId) {
                loteSelect.innerHTML = '<option value="">Sin lote específico</option>';
                loteSelect.disabled = false;
                return;
            }
            fetch("/inventario/alimento/" + alimentoId + "/lotes")
                .then(function (resp) { return resp.json(); })
                .then(function (opciones) {
                    loteSelect.innerHTML = opciones
                        .map(function (o) {
                            return '<option value="' + o.id + '">' + o.texto + "</option>";
                        })
                        .join("");
                    loteSelect.disabled = false;
                })
                .catch(function () {
                    loteSelect.innerHTML = '<option value="">Sin lote específico</option>';
                    loteSelect.disabled = false;
                });
        }

        alimentoSelect.addEventListener("change", cargarLotes);
        cargarLotes();
    });
})();
