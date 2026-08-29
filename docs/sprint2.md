# Sprint 2 – Gestión de inventario

**Rama:** `sprint/2`
**Estado:** Completado

## Alcance

- Registro de **entradas** de stock.
- Registro de **salidas** de stock.
- **Actualización automática** del stock (entrada suma, salida resta).
- **Consulta de disponibilidad** (stock y desglose por lote).
- **Historial de movimientos** con filtros y trazabilidad (usuario, motivo, lote).

## Cambios de base de datos (migración `87f7549a6b65`)

| Elemento | Detalle |
|---|---|
| Tabla `movimientos` | Nueva entidad que registra entrada/salida: `tipo`, `alimento_id`, `lote_id` (opcional), `cantidad`, `stock_resultante`, `motivo`, `usuario_id`, `fecha`. |
| Índices | `ix_movimientos_alimento_id`, `ix_movimientos_tipo`, `ix_movimientos_fecha`. |

FKs: `alimentos`, `lotes` (opcional), `usuarios`. Cada movimiento deja
**trazabilidad** (quién, cuándo, cuánto y por qué), base del historial y de la
trazabilidad total del Sprint 5.

## Nuevas reglas de negocio (servicios)

Nuevo módulo `inventario_service`:

- `registrar_entrada(...)` — valida cantidad > 0, aumenta el stock del alimento
  y, si se indica lote, también la cantidad del lote.
- `registrar_salida(...)` — valida **stock suficiente** antes de restar
  (error `Stock insuficiente`); si se indica lote valida también la cantidad
  del lote.
- `disponibilidad(...)` — devuelve el total disponible y los lotes activos.
- `listar_movimientos(...)` — historial con filtros (texto, tipo, rango).

Las operaciones son **transaccionales**: o se aplica el movimiento completo o
no se cambia nada (sin efectos parciales).

## Módulos/funcionalidad nuevos

- Blueprint `inventario` (`/inventario`):
  - `/inventario/entradas/nueva` — registrar entrada.
  - `/inventario/salidas/nueva` — registrar salida.
  - `/inventario/disponibilidad` — consulta de stock disponible por alimento/lote.
  - `/inventario/historial` — historial de movimientos con filtros.
  - `/inventario/alimento/<id>/lotes` — JSON para el selector dinámico de lotes.
- Templates: `inventario/form.html`, `disponibilidad.html`, `historial.html`.
- JS `inventario.js` — carga dinámica de lotes según el alimento elegido.
- Sidebar con sección **Movimientos** (Entradas, Salidas, Disponibilidad, Historial).

## Pruebas funcionales

Nuevo archivo `tests/test_inventario.py`.

- **24 → 36 pruebas**, todas pasando.
- Cobertura: entrada suma stock, salida resta stock, salida con stock
  insuficiente rechazada, entrada con lote (stock y lote), disponibilidad,
  cantidad no positiva rechazada, formularios de entrada/salida, error de
  stock insuficiente en la vista, historial y filtro por tipo.

## Verificación de requerimientos

- [x] Registro de entradas.
- [x] Registro de salidas.
- [x] Actualización de stock (automática y transaccional).
- [x] Consulta de disponibilidad.
- [x] Historial de movimientos con trazabilidad.

## Errores identificados y corregidos

1. **Selector de lotes dependiente del alimento**: se implementa un endpoint
   JSON y un `<select>` dinámico en JS para no listar todos los lotes de la BD.
2. **`fecha_vencimiento` como `Date`** exige objeto `date` en las pruebas (no
   cadena): corregido en los tests que creaban lotes directamente.
3. **Doble validación de stock**: el servicio valida la disponibilidad real en
   base de datos (no solo en el formulario), evitando salidas que dejen stock
   negativo.

## Evaluación del incremento

El módulo de inventario queda operativo: entradas y salidas ajustan el stock de
forma segura y quedan registradas con trazabilidad. La consulta de
disponibilidad y el historial preparan la base para el módulo de **alertas**
(Sprint 3, próximos a vencer y stock bajo) y para el **dashboard y reportes**
(Sprint 4-5).
