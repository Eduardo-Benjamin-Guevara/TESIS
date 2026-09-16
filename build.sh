#!/usr/bin/env bash
# build.sh — Script de inicio para Render.com
# Aplica migraciones, crea el admin y siembra datos de demostración.

set -e

echo "=== Aplicando migraciones ==="
flask --app run.py db upgrade

echo "=== Creando admin y datos demo ==="
flask --app run.py init-db
flask --app run.py seed-demo

echo "=== Listo ==="
