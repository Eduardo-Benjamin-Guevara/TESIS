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
