# Sprint 6 – Usabilidad, notificaciones y profesionalismo

**Rama:** `sprint/6`
**Estado:** Completado

## Alcance

- **Sistema de notificaciones funcional** (campana del topbar): lista real de
  alertas (próximos a vencer y stock bajo), contador de no leídas y opción de
  marcar todas como leídas con persistencia por usuario.
- **Cambio de tema claro/oscuro** persistido, con detección automática de la
  preferencia del sistema.
- **Responsive mejorado**: fondo oscuro al abrir el menú en móvil, cierre
  automático al navegar, tablas con desplazamiento y topbar adaptada.
- **Extras profesionales**: búsqueda global funcional, menú de usuario y
  mejores indicadores de accesibilidad (ARIA).

## Módulos/funcionalidad nuevos

### Notificaciones

Nueva tabla **`notificaciones_leidas`** (migración `8e04164a2ab3`) para
persistir qué alertas ha confirmado cada usuario sin duplicar el estado del
inventario (las alertas siguen siendo derivadas).

Nuevo servicio `notificaciones_service`:

| Función | Qué hace |
|---|---|
| `notificaciones_usuario(usuario)` | Une las alertas (vencimiento + stock) con su estado de lectura y devuelve `items`, `no_leidas` y `total`. |
| `marcar_todas_como_leidas(usuario)` | Registra las alertas actuales como leídas para el usuario. |

Nuevo blueprint `notificaciones` (`/notificaciones`):

- `GET /notificaciones/` — JSON con las notificaciones del usuario.
- `POST /notificaciones/leidas` — marca todas como leídas (protegido por CSRF).

La **campana** del topbar carga estas notificaciones mediante `fetch`, muestra
el contador de no leídas, distingue visualmente las nuevas y permite marcarlas
todas como leídas. El badge ahora muestra el número real de notificaciones
pendientes.

### Tema claro/oscuro

- Botón de tema en la barra superior (icono luna/sol) que alterna entre
  `claro` y `oscuro`.
- La elección se guarda en `localStorage` y se aplica de forma anticipada
  (script en `<head>`) para evitar parpadeos.
- Si no hay preferencia previa, se respeta `prefers-color-scheme` del sistema.
- El tema oscuro define una paleta propia vía variables CSS y sobreescribe los
  componentes de Bootstrap (tarjetas, tablas, dropdowns, botones, paneles).

### Responsive

- Fondo oscuro (`sidebar-backdrop`) al abrir el sidebar en pantallas pequeñas.
- Cierre automático del sidebar al hacer clic en cualquier enlace de navegación.
- Ajustes de tipografía/tamaño para pantallas muy pequeñas y tablas con
  desplazamiento táctil suave.

### Extras profesionales

- **Búsqueda global funcional**: campo en la barra superior que envía `?q=` a
  la lista de alimentos (el CRUD ya filtraba por ese parámetro).
- **Menú de usuario**: cambia el chip por un menú desplegable con panel de
  información y accesos (Panel, Usuarios para admin, Cerrar sesión).
- **Accesibilidad**: atributos `aria-*`, `role` y `aria-expanded` en los
  controles desplegables; `alt`/`aria-label` en botones de icono.
- **CSRF para peticiones AJAX**: meta `csrf-token` global en el `<head>`.

## Diseño

- Las **notificaciones** no almacenan alertas duplicadas: solo registran la
  "lectura" (tipo + referencia) por usuario mediante `NotificacionLeida`, de
  modo que las alertas siempre reflejan el estado real del inventario.
- El **tema** se mantiene íntegramente en el cliente (CSS variables +
  `localStorage`), sin coste de sesión ni de base de datos.
- El responsive conserva el comportamiento escritorio (sidebar fijo) y mejora
  la experiencia en móvil con el backdrop y el cierre automático.

## Pruebas funcionales

Nuevo archivo `tests/test_notificaciones.py`.

- **71 → 79 pruebas**, todas pasando.
- Cobertura: notificaciones sin alertas, generación y estado no leído,
  marcar-leídas reduce el contador y persiste, contenido/mensaje de las alertas
  de vencimiento, rutas JSON y marcar-leídas (con sesión) y redirección sin
  sesión; presencia del botón de tema, campana, menú de usuario, búsqueda,
  backdrop y meta CSRF.
- Smoke test contra la BD de desarrollo: notificaciones y marcado-leídas
  funcionan con CSRF real; los datos temporales se limpian al final.

## Verificación de requerimientos

- [x] Diseño **responsive** (backdrop móvil, cierre al navegar, tablas).
- [x] **Sistema de notificaciones funcional** (campana real, contador, marcar leídas).
- [x] **Cambio de tema** claro/oscuro persisto con detección del sistema.
- [x] Extras profesionales (búsqueda global, menú de usuario, accesibilidad, CSRF AJAX).

## Errores identificados y corregidos

1. **CSRF en la petición AJAX**: el `POST /notificaciones/leidas` requiere el
   token de CSRF; se añadió la meta `csrf-token` global y el encabezado
   `X-CSRFToken` en el `fetch`.
2. **Persistencia de la preferencia de tema**: se aplica el tema en un script
   temprano en `<head>` (antes de pintar) para evitar el parpadeo al recargar.

## Evaluación del incremento

El Sprint 6 fortalece la experiencia de usuario y el acabado profesional del
sistema: un centro de notificaciones real, un tema claro/oscuro cómodo y un
comportamiento responsive pulido con extras de usabilidad y accesibilidad
hacen que la aplicación se sienta completa y lista para su consolidación final.

## Consolidación final (siguiente paso)

Juntar `sprint/1` a `sprint/6` en `main`, actualizar el README con el roadmap
completo (✅ Completado para los 6 sprints) y escribir/consolidar la
documentación global del sistema.
