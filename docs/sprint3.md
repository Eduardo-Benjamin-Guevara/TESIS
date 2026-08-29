# Sprint 3 – Sistema de alertas

**Rama:** `sprint/3`
**Estado:** Completado

## Alcance

- Alertas de **próximos a vencer** (lotes con fecha de vencimiento cercana o ya vencida).
- Alertas de **stock bajo** (alimento en o por debajo del stock mínimo).
- **Notificaciones** centralizadas (panel + badge del sidebar).
- **Priorización** de alertas por nivel de urgencia (crítica, alta, media).

## Diseño

Las alertas se calculan de forma **derivada** (no se duplica estado): se
consultan los lotes activos y el stock actual real. Esto evita
inconsistencias entre la alerta mostrada y el inventario registrado.

Niveles de prioridad:

| Nivel | Vencimiento (días) | Stock |
|---|---|---|
| Crítica | Vencido, hoy o en ≤ 3 días | Stock en 0 |
| Alta | En ≤ 7 días | Stock < 50 % del mínimo |
| Media | En ≤ 15 días | Stock ≤ mínimo |

## Módulos/funcionalidad nuevos

- `alertas_service` (nuevo):
  - `proximos_a_vencer()` — lotes activos por vencer/vencidos con su nivel.
  - `stock_bajo()` — alimentos con stock bajo y su nivel.
  - `todas()` — fusión ordenada por prioridad.
  - `contar()` — resumen (total, crítica, alta, media).
- Blueprint `alertas` (`/alertas`):
  - `/alertas/` — todas las alertas priorizadas.
  - `/alertas/vence-pronto` — lotes próximos a vencer.
  - `/alertas/stock-bajo` — alimentos con stock bajo.
- **Panel principal** actualizado: tarjeta "Próximos a vencer", contador de
  alertas en accesos rápidos.
- **Sidebar**: sección "Monitoreo" con link **Alertas** y badge con el número
  de alertas pendientes (context processor global, solo con sesión).
- Templates: `alertas/index.html`, `vencimiento.html`, `stock_bajo.html`.

## Pruebas funcionales

Nuevo archivo `tests/test_alertas.py`.

- **36 → 47 pruebas**, todas pasando.
- Cobertura: clasificación de prioridad por vencimiento, lote fuera de umbral
  (sin alerta), lote vencido (crítico), lote inactivo (sin alerta),
  clasificación de stock bajo, stock con mínimo no definido, resumen de
  conteo, y renderizado de las tres páginas de alertas y del panel.

## Verificación de requerimientos

- [x] Alertas de próximos a vencer.
- [x] Alertas de stock bajo.
- [x] Notificaciones (panel + badge del sidebar).
- [x] Priorización de alertas (crítica/alta/media).
- [x] Las alertas siempre reflejan el estado real del inventario (derivadas).

## Errores identificados y corregidos

1. **`fecha_vencimiento` al crear lotes en pruebas** requiere objeto `date`
   (no cadena) al insertar directamente; corregido en los tests.
2. **Contador de alertas en cada render** (context processor): se limita a
   sesiones autenticadas para no consultar la BD en la página de login.

## Evaluación del incremento

El sistema de alertas detecta oportunamente los alimentos por vencer y el
stock bajo, priorizando la acción sobre lo más urgente. Queda preparado el
terreno para el **Sprint 4** (monitoreo y reportes): los datos que alimentan
las alertas (vencimientos, stock) también alimentan los indicadores y
reportes del panel avanzado.
