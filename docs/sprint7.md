# Sprint 7 – Datos de simulación (demo)

**Rama:** `sprint/7`
**Estado:** Completado

## Alcance

- **Generador de datos de simulación** realistas para el sistema: alimentos por
  categoría, lotes con distintas fechas de vencimiento (vencidos, próximos a
  vencer y saludables) y movimientos históricos de entrada/salida.
- **Carga por línea de comandos** (`flask seed-demo`) y **desde el panel**
  (solo administradores), con opción de regenerar.
- **Reproducible e idempotente**: usa una semilla fija y, por defecto, no
  duplica datos si ya existen; `--forzar` regenera desde cero.

## Para qué sirve

Permite **demostrar y probar** todas las funcionalidades sin cargar datos a
mano: gráficos del dashboard, alertas (vencimientos), notificaciones de la
campana, reportes exportables, stock bajo, trazabilidad y búsquedas.

## Módulos nuevos

### Servicio `simulacion_service`

Nuevo servicio con las siguientes funciones:

| Función | Qué hace |
|---|---|
| `generar_datos_demo(forzar=False)` | Crea alimentos, lotes y movimientos de forma coherente; si `forzar` es `True`, borra los datos previos y los regenera. Devuelve un resumen (alimentos, lotes, movimientos, usuario demo). |
| `existen_datos_demo()` | Indica si ya hay alimentos cargados (control de idempotencia). |
| `ALIMENTOS_DEMO` | Catálogo de 26 alimentos por categoría con lotes realistas. |
| `USUARIO_DEMO` / `PASSWORD_DEMO` | Usuario encargado creado para simular operaciones (`demo`/`demo123`). |

### Comando Flask `seed-demo`

```
flask --app run.py seed-demo          # siembra si no hay datos
flask --app run.py seed-demo --forzar  # borra y regenera
```

### Ruta / Panel

- `POST /demo/datos` (solo `admin`): recibe `accion=cargar|regenerar` y siembra
  o regenera los datos. Visible como tarjeta "Datos de demostración" en el
  panel principal para el rol administrador.

## Diseño

- **Movimientos coherentes**: para cada lote se registra una entrada (compra) y
  una salida (consumo) cuando corresponde; el `stock_resultante` de cada
  movimiento y el `stock_actual` del alimento se calculan en orden cronológico,
  de modo que **stock = suma de lotes activos**.
- **Reproducibilidad**: `random.seed(1488)` fija el comportamiento.
- **Idempotencia**: si ya hay alimentos y no se usa `--forzar`, no duplica nada.

## Contenido de la simulación

- **26 alimentos** en 8 categorías (granos, lácteos, carnes, frutas, verduras,
  abarrotes, bebidas, otros).
- **28 lotes** con fechas de vencimiento variadas: incluidos vencidos, próximos
  a vencer (alimentan alertas) y saludables.
- **53 movimientos** históricos repartidos en varios días/meses para poblar
  gráficos y reportes.
- 1 alimento con **stock bajo** para activar la alerta correspondiente.

## Pruebas funcionales

Nuevo archivo `tests/test_simulacion.py`.

- **81 → 95 pruebas**, todas pasando.
- Cobertura: generación de alimentos/lotes/movimientos; usuario demo creado y
  con contraseña correcta; coherencia stock↔lotes; variedad de vencimientos
  (vencidos/próximos/sanos); movimientos de entrada y salida; stock bajo;
  idempotencia y regeneración (`--forzar`); comandos CLI (`seed-demo`,
  `--forzar`); ruta `/demo/datos` con admin (cargar y regenerar) y bloqueo a
  no administradores.
- Smoke test contra la BD de desarrollo: **26 alimentos, 28 lotes, 53
  movimientos, 15 alertas**, 5 lotes vencidos, 9 próximos a vencer y 1 stock
  bajo.

## Verificación de requerimientos

- [x] Datos de simulación **completos** (alimentos, lotes, movimientos).
- [x] Vencimientos variados que alimentan las **alertas** y **notificaciones**.
- [x] Movimientos históricos que alimentan **dashboard**, **reportes** y
  **gráficos**.
- [x] Carga por **CLI** y por **panel** (solo admin), con regeneración.
- [x] **Idempotente** (no duplica datos) y **reproducible**.

## Errores identificados y corregidos

1. **IndexError al calcular `stock_actual`**: se accedía a `movs[-1][3]` en una
   tupla de 3 elementos; se corrigió usando el acumulado final.
2. **`click.echo` con formato `%`**: los argumentos posicionales se
   interpretaban como `file`; se cambió a f-strings.
3. **SAWarning al regenerar** en el mismo contexto de sesión: se limpia el mapa
   de identidad (`db.session.remove()`) tras el borrado forzado.

## Evaluación del incremento

El Sprint 7 entrega un dataset de demostración realista y fácil de cargar, que
hace que el sistema se vea completo y tangible para la presentación o defensa:
el panel, las alertas, las notificaciones y los reportes muestran datos
significativos sin esfuerzo manual.

## Siguiente paso

Consolidación final: juntar `sprint/1` a `sprint/7` en `main`, actualizar el
README con el roadmap completo (✅ 7 sprints) y consolidar la documentación
global del sistema.
