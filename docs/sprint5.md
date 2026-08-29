# Sprint 5 – Funciones innovadoras

**Rama:** `sprint/5`
**Estado:** Completado

## Alcance

- **Gráficos interactivos** del dashboard (Chart.js): stock por categoría,
  estado del inventario y entradas/salidas.
- **Código QR** por alimento para identificación rápida e impresión.
- **Trazabilidad total** por alimento (historial completo de movimientos).
- **Recomendaciones de compra** para reabastecer el stock bajo.
- **Exportación de reportes** en CSV y Excel.

## Módulos/funcionalidad nuevos

Nuevos servicios (sin cambios de base de datos: todos usan datos existentes):

| Servicio | Puerto | Qué aporta |
|---|---|---|
| `qr_service` | `generar_qr(alimento, datos_extra)` | PNG del código QR con código, nombre, stock y unidad. |
| `trazabilidad_service` | `trazabilidad_alimento(id)` | Reconstruye entradas/salidas, totales y stock actual. |
| `recomendaciones_service` | `recomendaciones()` | Sugiere reabastecer alimentos con stock < mínimo (objetivo = mínimo × 2), priorizando urgentes (sin stock). |
| `exportacion_service` | `exportar_csv` / `exportar_excel` | Convierte filas de reporte en CSV (con BOM) o XLSX (con ancho de columnas).

Rutas y páginas nuevas:

- `GET /alimentos/<id>/qr` — devuelve la imagen PNG del código QR.
- `GET /alimentos/<id>/trazabilidad` — historial completo del alimento.
- `GET /monitoreo/recomendaciones` — recomendaciones de compra priorizadas.
- `GET /monitoreo/reportes/exportar?formato=csv|xlsx` — exporta reportes.
- **Dashboard** — ahora incluye tres gráficos interactivos (Chart.js) y
  enlaces a trazabilidad/QR desde el detalle del alimento.

Accesos añadidos en el sidebar (sección **Monitoreo**: **Recomendaciones**) y
botones de **QR / Trazabilidad** en el detalle de cada alimento.

## Diseño

- Los **gráficos** se alimentan del `reportes_service` existente a través de un
  helper `_datos_graficos()` que prepara los datos en JSON para Chart.js.
- El **QR** contiene información clave del alimento para consulta rápida y
  escaneo; la trazabilidad reutiliza los movimientos del Sprint 2.
- Las **recomendaciones** son deterministas: se calculan del stock actual y
  mínimo sin persistir nada nuevo.

## Pruebas funcionales

Nuevo archivo `tests/test_innovacion.py`.

- **56 → 71 pruebas**, todas pasando.
- Cobertura: generación de QR (cabecera PNG y datos extra), trazabilidad
  (reconstrucción de entradas/salidas y totales), recomendaciones (stock bajo,
  urgente sin stock, sin recomendación cuando hay stock), exportación CSV/XLSX
  (BOM, cabecera, datos, título de hoja), y renderizado de rutas QR,
  trazabilidad, recomendaciones, exportación y gráficos del dashboard.
- Smoke test contra la BD de desarrollo: todas las rutas responden 200 con el
  mimetype esperado; los datos temporales se limpian al final.

## Verificación de requerimientos

- [x] Gráficos interactivos del dashboard (Chart.js, CDN).
- [x] Código QR por alimento.
- [x] Trazabilidad total por alimento.
- [x] Recomendaciones de compra.
- [x] Exportación a CSV y Excel.
- [x] Acceso por roles (páginas protegidas con sesión).

## Errores identificados y corregidos

1. **`trazabilidad_service` pasaba el id a `resumen_por_alimento`**, que espera
   el objeto `Alimento`: se corrigió a `resumen_por_alimento(alimento)`.
2. **`exportacion_service` usaba `font.copy()` obsoleto** de openpyxl: se
   reemplazó por `copy()` de la biblioteca estándar, eliminando el warning.
3. En las pruebas de rutas, acceder a `a.id` fuera del contexto de BD provocaba
   `DetachedInstanceError`: se captura el id dentro del contexto.

## Evaluación del incremento

El Sprint 5 cierra las funcionalidades innovadoras del sistema: el QR y la
trazabilidad dan visibilidad rápida sobre cada alimento; las recomendaciones y
la exportación automatizan decisiones y la descarga de reportes del inventario.
La integración de Chart.js hace el monitoreo más visual y accesible.

## Consolidación final (siguiente paso)

Juntar `sprint/1` a `sprint/5` en `main`, actualizar el README con el roadmap
completo (✅ Completado para los 5 sprints) y escribir/consolidar la
documentación global del sistema.
