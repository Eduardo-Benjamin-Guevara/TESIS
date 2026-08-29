"""Sprint 1: categorias, lotes y fechas de vencimiento

Revision ID: 931bf2245183
Revises: d82d532e667e
Create Date: 2026-08-28 22:14:18.104104

"""
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '931bf2245183'
down_revision = 'd82d532e667e'
branch_labels = None
depends_on = None

# Categorías por defecto (deben coincidir con app/models/categoria.py)
CATEGORIAS_DEFECTO = [
    "granos", "lacteos", "carnes", "frutas",
    "verduras", "abarrotes", "bebidas", "otros",
]


def _ahora():
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def upgrade():
    op.create_table('categorias',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=50), nullable=False),
    sa.Column('descripcion', sa.String(length=255), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('categorias', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_categorias_nombre'), ['nombre'], unique=True)

    op.create_table('lotes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=30), nullable=True),
    sa.Column('alimento_id', sa.Integer(), nullable=False),
    sa.Column('fecha_ingreso', sa.Date(), nullable=True),
    sa.Column('fecha_vencimiento', sa.Date(), nullable=False),
    sa.Column('cantidad', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['alimento_id'], ['alimentos.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('lotes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_lotes_alimento_id'), ['alimento_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_lotes_codigo'), ['codigo'], unique=True)
        batch_op.create_index(batch_op.f('ix_lotes_fecha_vencimiento'), ['fecha_vencimiento'], unique=False)

    # Paso 1: añadir columna categoria_id como opcional
    with op.batch_alter_table('alimentos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('categoria_id', sa.Integer(), nullable=True))

    # Paso 2: sembrar categorías por defecto y mapear los alimentos existentes
    conn = op.get_bind()
    id_por_nombre = {}
    for nombre in CATEGORIAS_DEFECTO:
        conn.execute(
            sa.text(
                "INSERT INTO categorias (nombre, activo, fecha_creacion) "
                "VALUES (:nombre, 1, :fecha)"
            ),
            {"nombre": nombre, "fecha": _ahora()},
        )
        fila = conn.execute(
            sa.text("SELECT id FROM categorias WHERE nombre = :nombre"), {"nombre": nombre}
        ).fetchone()
        id_por_nombre[nombre] = fila[0]

    # Asignar la categoría correspondiente a cada alimento según su texto previo
    for nombre, cid in id_por_nombre.items():
        conn.execute(
            sa.text("UPDATE alimentos SET categoria_id = :cid WHERE categoria = :nombre"),
            {"cid": cid, "nombre": nombre},
        )
    # Alimentos sin categoría reconocible quedan sin categoría (NULL)

    # Paso 3: índice + FK y eliminar la columna texto `categoria`
    with op.batch_alter_table('alimentos', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_alimentos_categoria_id'), ['categoria_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_alimentos_categoria_id', 'categorias', ['categoria_id'], ['id']
        )
        batch_op.drop_column('categoria')

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('alimentos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('categoria', sa.String(length=30), nullable=True))

    # Volver a poblar la columna texto a partir de la categoría relacionada
    conn = op.get_bind()
    filas = conn.execute(
        sa.text(
            "SELECT a.id, c.nombre FROM alimentos a "
            "LEFT JOIN categorias c ON a.categoria_id = c.id"
        )
    ).fetchall()
    for aid, nombre in filas:
        conn.execute(
            sa.text("UPDATE alimentos SET categoria = :nombre WHERE id = :id"),
            {"nombre": nombre or "otros", "id": aid},
        )

    with op.batch_alter_table('alimentos', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_alimentos_categoria_id'))
        batch_op.drop_column('categoria_id')

    with op.batch_alter_table('lotes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_lotes_fecha_vencimiento'))
        batch_op.drop_index(batch_op.f('ix_lotes_codigo'))
        batch_op.drop_index(batch_op.f('ix_lotes_alimento_id'))

    op.drop_table('lotes')
    with op.batch_alter_table('categorias', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_categorias_nombre'))

    op.drop_table('categorias')
    # ### end Alembic commands ###
