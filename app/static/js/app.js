// Comportamiento general de la interfaz.
(function () {
    "use strict";

    // Toggle del sidebar en pantallas pequeñas
    document.addEventListener("DOMContentLoaded", function () {
        var toggle = document.getElementById("sidebarToggle");
        var sidebar = document.getElementById("sidebar");
        if (toggle && sidebar) {
            toggle.addEventListener("click", function () {
                sidebar.classList.toggle("show");
            });
        }

        // Auto-cerrar los mensajes flash después de unos segundos
        var alerts = document.querySelectorAll(".alert-dismissible");
        alerts.forEach(function (alert) {
            setTimeout(function () {
                if (window.bootstrap && bootstrap.Alert) {
                    bootstrap.Alert.getOrCreateInstance(alert).close();
                }
            }, 6000);
        });
    });
})();
