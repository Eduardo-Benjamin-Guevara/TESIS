# Sprint 1 – Registro y control de alimentos

**Rama:** `sprint/1`
**Estado:** Completado

## Alcance

- Registro de usuarios (ampliado: administración completa de cuentas).
- Registro de alimentos.
- Registro de categorías (**nueva entidad gestionable**).
- Registro de fechas de vencimiento (**nueva entidad Lote**).
- Consulta de alimentos (búsqueda y filtros).

## Cambios de base de datos (migración `931bf2245183`)

Se crean dos tablas y se refactoriza `alimentos`:

| Elemento | Detalle |
|---|---|
| Tabla `categorias` | Nueva entidad gestionable (nombre único, descripción, activo). Reemplaza la lista fija de categorías de la V1. |
| Tabla `lotes` | Nueva entidad con `fecha_vencimiento`, `cantidad`, código de lote; FK a `alimentos`. |
| `alimentos.categoria_id` | Nuevo FK a `categorias`. |
| `alimentos.categoria` (texto) | Eliminado; se migran los datos existentes al FK. |

La migración **preserva los datos**: siembra las categorías por defecto y
mapea los alimentos existentes de su categoría en texto al id correspondiente.

## Nuevas reglas de negocio (servicios)

- `categoria_service`: nombre único, alta lógica.
- `lote_service`: registro de lotes que **incrementa el stock** del alimento;
  validación de cantidad > 0 y código de lote único.
- `alimento_service`: ahora valida contra categorías reales.

## Módulos/funcionalidad nuevos

- Blueprint `categorias` (`/categorias`) — CRUD de categorías.
- Blueprint `lotes` (`/lotes`) — CRUD de lotes y fechas de vencimiento.
- Vista de detalle de alimento ampliada con la tabla de **lotes**.
- Sidebar con accesos a **Categorías** y **Fechas de vencimiento**.
- Comando CLI `flask init-db` ahora también siembra las categorías por defecto.

## Pruebas funcionales

Se añadieron pruebas y se actualizaron las existentes a la nueva estructura.

- **20 → 24 pruebas**, todas pasando.
- Cobertura de: registro/edición/consulta de alimentos, código duplicado,
  validación de obligatorios, registro de categorías, categoría duplicada,
  registro de lote y actualización de stock, cantidad inválida en lote,
  acceso por rol y autenticación.

## Verificación de requerimientos

- [x] Registro de usuarios (administración de cuentas).
- [x] Registro de alimentos.
- [x] Registro de categorías.
- [x] Registro de fechas de vencimiento (lotes).
- [x] Consulta de alimentos (búsqueda + filtro por categoría).
- [x] Migración de datos sin pérdida (SQLite lote/fecha).

## Errores identificados y corregidos

1. **Despliegue de migración con FK sin nombre** en SQLite (batch mode):
   se asignó nombre explícito `fk_alimentos_categoria_id`.
2. **Barra de stock en 0 rechazada por `DataRequired`** (WTForms trata
   `Decimal('0')` como vacío): se sustituyó por `InputRequired` en los campos
   numéricos para permitir stock 0 y delegar la validación de negocio al
   servicio.
3. **Pruebas desactualizadas** tras el cambio de modelo (campo `categoria`
   texto → `categoria_id`): se actualizaron y ampliaron.

## Evaluación del incremento

El sprint deja el registro y control de alimentos completo y preparado:
cada alimento pertenece a una categoría gestionable y cuenta con lotes con
fecha de vencimiento, base indispensable para el módulo de inventario
(Sprint 2) y el de alertas (Sprint 3).
