# Sprint 4 – Monitoreo y reportes

**Rama:** `sprint/4`
**Estado:** Completado

## Alcance

- **Dashboard de monitoreo** con indicadores clave (KPIs).
- **Stock en tiempo real** (siempre derivado de los movimientos del inventario).
- **Reportes** de vencimientos y de stock por categoría.
- **Indicadores de actividad**: entradas, salidas y total de movimientos.

## Módulos/funcionalidad nuevos

Nuevo módulo `reportes_service` (sin cambios de base de datos: todo se calcula
de los datos existentes):

| Función | Qué reporta |
|---|---|
| `kpis()` | Total de alimentos, categorías, stock total, con stock, stock bajo, alertas activas/críticas, próximos a vencer, vencidos, entradas y salidas. |
| `stock_tiempo_real()` | Stock actual de cada alimento con desglose de lotes activos. |
| `reporte_vencimientos()` | Lotes por vencer/vencidos dentro del horizonte del reporte. |
| `reporte_por_categoria()` | Cantidad de alimentos, stock y bajos por categoría. |
| `actividad_reciente()` | Últimos movimientos registrados. |

Blueprint `monitoreo` (`/monitoreo`):

- `/monitoreo/` — dashboard con KPIs, actividad reciente y stock por categoría.
- `/monitoreo/stock` — stock en tiempo real con filtros (búsqueda/categoría).
- `/monitoreo/reportes` — reporte de vencimientos y stock por categoría.

Accesos añadidos en el sidebar (sección **Monitoreo**: Dashboard, Stock en
tiempo real, Reportes, Alertas).

## Diseño

- Todos los indicadores se **derivan** del estado real: stocks, lotes y
  movimientos. No se almacena ningún dato redundante.
- El "stock en tiempo real" se actualiza de forma automática porque las
  entradas/salidas (Sprint 2) modifican `stock_actual` y se reflejan aquí.

## Pruebas funcionales

Nuevo archivo `tests/test_monitoreo.py`.

- **47 → 56 pruebas**, todas pasando.
- Cobertura: KPIs de alimentos/stock, KPIs de movimientos, desglose en stock
  en tiempo real, reporte de vencimientos (incluye/excluye según horizonte),
  reporte por categoría, límite de actividad reciente y renderizado de las
  tres páginas de monitoreo.

## Verificación de requerimientos

- [x] Dashboard de monitoreo (indicadores/KPIs).
- [x] Stock en tiempo real.
- [x] Reportes de inventario (vencimientos y por categoría).
- [x] Indicadores de actividad (entradas/salidas/total de movimientos).
- [x] Acceso por roles (páginas protegidas con sesión).

## Errores identificados y corregidos

1. **Template `reportes.html` usaba `hoy`** no definido: se pasa
   `date.today()` desde la ruta para calcular el estado del lote.
2. **Cálculo de "con stock"** contaba solo positivos; se definió stock total
   (suma) y alimentos con stock > 0 como indicadores separados.

## Evaluación del incremento

El módulo de monitoreo consolida la información del inventario en indicadores
y reportes. Esto prepara directamente el **Sprint 5**, donde los mismos datos
alimentan los **gráficos interactivos** (Chart.js), la **exportación** de
reportes (CSV/Excel) y las **recomendaciones de compra** a partir del stock
bajo y los vencimientos.