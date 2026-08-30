"""Comandos de línea de comandos (Flask CLI).

Proporcionan tareas administrativas para configurar la base de datos y
crear de forma segura el usuario administrador inicial, sin exponer
credenciales en el código.

Uso desde la raíz del proyecto:
    flask --app run.py init-db     # aplica migraciones y crea el admin
    flask --app run.py create-admin
"""
import click
from flask import Flask
from flask.cli import with_appcontext


def registrar_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    @with_appcontext
    def init_db_command():
        """Aplica las migraciones pendientes y crea el administrador inicial."""
        from flask_migrate import upgrade

        from app.extensions import db

        click.echo("Aplicando migraciones...")
        upgrade()
        click.echo("Creando usuario administrador inicial...")
        from app.services.init_services import crear_admin_inicial, sembrar_categorias

        crear_admin_inicial()
        sembrar_categorias()
        db.session.remove()
        click.echo("Base de datos inicializada correctamente.")

    @app.cli.command("create-admin")
    @with_appcontext
    def create_admin_command():
        """Crea (si no existe) el usuario administrador desde .env."""
        from app.services.init_services import crear_admin_inicial

        crear_admin_inicial()
        click.echo("Verificación de administrador finalizada.")

    @app.cli.command("seed-demo")
    @click.option("--forzar", is_flag=True, help="Elimina los datos demo previos y los vuelve a generar.")
    @with_appcontext
    def seed_demo_command(forzar: bool):
        """Siembra datos de simulación realistas (Sprint 7).

        Alimentos por categoría, lotes con distintas fechas de vencimiento
        (incluidos vencidos/próximos a vencer) y movimientos históricos que
        alimentan los reportes, las alertas y las notificaciones.
        """
        from app.services.simulacion_service import PASSWORD_DEMO, generar_datos_demo

        if not forzar:
            from app.services.simulacion_service import existen_datos_demo

            if existen_datos_demo():
                click.echo("Ya existen datos. Usa --forzar para regenerarlos.")
                return

        resumen = generar_datos_demo(forzar=forzar)
        if not resumen["creado"] and not forzar:
            click.echo("Ya existen datos de simulación. Nada que hacer.")
            return
        click.echo(
            f"Datos de simulación sembrados: {resumen['alimentos']} alimentos, "
            f"{resumen['lotes']} lotes, {resumen['movimientos']} movimientos."
        )
        click.echo(f"Usuario demo: {resumen['usuario_demo']} / {PASSWORD_DEMO}")
