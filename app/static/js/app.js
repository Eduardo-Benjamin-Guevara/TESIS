// Comportamiento general de la interfaz: tema, notificaciones, menús y contenedores móviles.
(function () {
    "use strict";

    function cargarTemaGuardado() {
        try {
            return localStorage.getItem("tema");
        } catch (e) {
            return null;
        }
    }

    function guardarTema(tema) {
        try {
            localStorage.setItem("tema", tema);
        } catch (e) {}
    }

    function aplicarTema(tema) {
        var root = document.documentElement;
        if (tema === "oscuro") {
            root.setAttribute("data-tema", "oscuro");
        } else {
            root.removeAttribute("data-tema");
        }
        var icono = document.getElementById("themeIcon");
        if (icono) {
            icono.className = tema === "oscuro" ? "bi bi-sun-fill" : "bi bi-moon-stars";
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        // ---- Cambio de tema ----
        aplicaTemaInicial();
        var themeToggle = document.getElementById("themeToggle");
        if (themeToggle) {
            themeToggle.addEventListener("click", function () {
                var esOscuro = document.documentElement.getAttribute("data-tema") === "oscuro";
                var nuevo = esOscuro ? "claro" : "oscuro";
                aplicarTema(nuevo);
                guardarTema(nuevo);
            });
        }

        // ---- Sidebar en móvil ----
        var toggle = document.getElementById("sidebarToggle");
        var sidebar = document.getElementById("sidebar");
        var backdrop = document.getElementById("sidebarBackdrop");
        function cerrarSidebar() {
            if (sidebar) { sidebar.classList.remove("show"); }
            if (backdrop) { backdrop.hidden = true; }
        }
        function abrirSidebar() {
            if (sidebar) { sidebar.classList.add("show"); }
            if (backdrop) { backdrop.hidden = false; }
        }
        if (toggle && sidebar) {
            toggle.addEventListener("click", function () {
                var abierto = sidebar.classList.contains("show");
                abierto ? cerrarSidebar() : abrirSidebar();
            });
        }
        if (backdrop) {
            backdrop.addEventListener("click", cerrarSidebar);
        }
        // Cierra el sidebar al hacer clic en un enlace de navegación (móvil)
        if (sidebar) {
            sidebar.querySelectorAll("a").forEach(function (a) {
                a.addEventListener("click", function () {
                    if (window.innerWidth < 992) { cerrarSidebar(); }
                });
            });
        }

        // ---- Notificaciones ----
        var notifToggle = document.getElementById("notifToggle");
        var notifPanel = document.getElementById("notifPanel");
        var notifList = document.getElementById("notifList");
        var notifCount = document.getElementById("notifCount");
        var markAllBtn = document.getElementById("notifMarkAll");

        function actualizarBadge(n) {
            if (!notifCount) { return; }
            if (n > 0) {
                notifCount.textContent = n > 99 ? "99+" : n;
                notifCount.classList.remove("d-none");
            } else {
                notifCount.classList.add("d-none");
            }
        }

        function nivelColor(nivel) {
            if (nivel === "critica") { return "danger"; }
            if (nivel === "alta") { return "warning"; }
            return "info";
        }

        function renderNotificaciones(items) {
            if (!notifList) { return; }
            if (!items || !items.length) {
                notifList.innerHTML =
                    '<div class="text-center text-muted small p-4">' +
                    '<i class="bi bi-check2-circle fs-3 d-block mb-2"></i>No hay notificaciones.</div>';
                return;
            }
            var html = "";
            items.forEach(function (n) {
                var claseNivel = n.leida ? "notif-leida" : "notif-nueva";
                html +=
                    '<a class="notif-item ' + claseNivel + '" href="' + n.url + '">' +
                    '<span class="notif-icon bg-' + nivelColor(n.nivel) + '-subtle text-' + nivelColor(n.nivel) + '">' +
                    '<i class="bi ' + n.icono + '"></i></span>' +
                    '<span class="notif-body">' +
                    '<span class="notif-title">' + n.titulo + '</span>' +
                    '<span class="notif-msg">' + n.mensaje + '</span>' +
                    '</span>' +
                    (!n.leida ? '<span class="notif-dot" title="No leída"></span>' : '') +
                    '</a>';
            });
            notifList.innerHTML = html;
        }

        function cargarNotificaciones() {
            if (!notifList) { return; }
            // Con una petición inicial sencilla (sin fetch): render desde datos del servidor
            // Se usa fetch cuando está disponible.
            if (window.fetch) {
                fetch("/notificaciones/", { headers: { "Accept": "application/json" } })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        renderNotificaciones(data.items);
                        actualizarBadge(data.no_leidas);
                        if (markAllBtn) { markAllBtn.classList.toggle("d-none", data.no_leidas === 0); }
                    })
                    .catch(function () {
                        if (notifList) {
                            notifList.innerHTML =
                                '<div class="text-muted small p-3 text-center">No se pudieron cargar las notificaciones.</div>';
                        }
                    });
            }
        }

        if (notifToggle && notifPanel) {
            notifToggle.addEventListener("click", function (e) {
                e.stopPropagation();
                var abierto = !notifPanel.hidden;
                notifPanel.hidden = abierto;
                notifToggle.setAttribute("aria-expanded", String(!abierto));
                if (!abierto) { cargarNotificaciones(); }
            });
        }
        if (markAllBtn) {
            markAllBtn.addEventListener("click", function (e) {
                e.preventDefault();
                e.stopPropagation();
                fetch("/notificaciones/leidas", {
                    method: "POST",
                    headers: { "X-CSRFToken": document.querySelector('meta[name="csrf-token"]') ?
                        document.querySelector('meta[name="csrf-token"]').getAttribute("content") : "" }
                }).then(function () {
                    cargarNotificaciones();
                });
            });
        }

        // ---- Menú de usuario ----
        var userToggle = document.getElementById("userToggle");
        var userDropdown = document.getElementById("userDropdown");
        if (userToggle && userDropdown) {
            userToggle.addEventListener("click", function (e) {
                e.stopPropagation();
                userDropdown.hidden = !userDropdown.hidden;
                userToggle.setAttribute("aria-expanded", String(!userDropdown.hidden));
            });
        }

        // Cierra panel/menú al hacer clic fuera
        document.addEventListener("click", function (e) {
            if (notifPanel && !notifPanel.hidden && !notifWrap.contains(e.target)) {
                notifPanel.hidden = true;
                if (notifToggle) { notifToggle.setAttribute("aria-expanded", "false"); }
            }
            if (userDropdown && !userDropdown.hidden && !userMenu.contains(e.target)) {
                userDropdown.hidden = true;
                if (userToggle) { userToggle.setAttribute("aria-expanded", "false"); }
            }
        });

        // ---- Auto-cerrar los mensajes flash ----
        var alerts = document.querySelectorAll(".alert-dismissible");
        alerts.forEach(function (alert) {
            setTimeout(function () {
                if (window.bootstrap && bootstrap.Alert) {
                    bootstrap.Alert.getOrCreateInstance(alert).close();
                }
            }, 6000);
        });
    });

    function aplicaTemaInicial() {
        var t = cargarTemaGuardado();
        if (!t) {
            t = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "oscuro" : "claro";
        }
        aplicarTema(t);
    }
})();
