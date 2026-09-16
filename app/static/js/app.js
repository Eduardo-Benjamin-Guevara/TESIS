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
        document.dispatchEvent(new CustomEvent("tema:cambio", { detail: tema }));
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

        // ---- Sidebar colapsable (retráctil) en escritorio ----
        var layout = document.querySelector(".app-layout");
        var collapseBtn = document.getElementById("sidebarCollapse");
        function guardarColapso(colapsado) {
            try { localStorage.setItem("sidebarColapsado", colapsado ? "1" : "0"); } catch (e) {}
        }
        function actualizarTooltips() {
            if (!layout || window.innerWidth < 992) { return; }
            var colapsado = layout.classList.contains("sidebar-collapsed");
            layout.querySelectorAll(".nav-link").forEach(function (enlace) {
                var span = enlace.querySelector(".nav-text");
                if (colapsado) {
                    if (span && !enlace.title) { enlace.title = span.textContent.trim(); }
                } else {
                    enlace.removeAttribute("title");
                }
            });
        }
        function aplicarEstadoColapso() {
            if (window.innerWidth < 992) { return; } // el colapso solo aplica en escritorio
            var guardado = "0";
            try { guardado = localStorage.getItem("sidebarColapsado") || "0"; } catch (e) {}
            if (guardado === "1" && layout) {
                layout.classList.add("sidebar-collapsed");
            }
            actualizarTooltips();
        }
        if (collapseBtn && layout) {
            collapseBtn.addEventListener("click", function () {
                var colapsado = layout.classList.toggle("sidebar-collapsed");
                guardarColapso(colapsado);
                actualizarTooltips();
            });
        }
        aplicarEstadoColapso();

        // ---- Notificaciones ----
        var notifToggle = document.getElementById("notifToggle");
        var notifPanel = document.getElementById("notifPanel");
        var notifList = document.getElementById("notifList");
        var notifCount = document.getElementById("notifCount");
        var markAllBtn = document.getElementById("notifMarkAll");
        var notifWrap = document.querySelector(".notif-wrap");
        var userMenu = document.querySelector(".user-menu");

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
            if (notifPanel && notifWrap && !notifPanel.hidden && !notifWrap.contains(e.target)) {
                notifPanel.hidden = true;
                if (notifToggle) { notifToggle.setAttribute("aria-expanded", "false"); }
            }
            if (userDropdown && userMenu && !userDropdown.hidden && !userMenu.contains(e.target)) {
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

        // ---- Loading state en formularios ----
        // Al enviar un formulario, el botón submit muestra un spinner para
        // indicar progreso y evitar dobles envíos.
        document.querySelectorAll("form").forEach(function (form) {
            form.addEventListener("submit", function () {
                var btn = form.querySelector('button[type="submit"]');
                if (!btn || btn.hasAttribute("data-no-loading") || btn.classList.contains("disabled")) {
                    return;
                }
                var etiqueta = btn.textContent.trim().replace(/\s+/g, " ");
                btn.classList.add("disabled");
                btn.setAttribute("aria-busy", "true");
                btn.innerHTML =
                    '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>' +
                    '<span class="btn-label">' + etiqueta + '</span>';
            });
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
