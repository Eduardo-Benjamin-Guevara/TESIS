#!/usr/bin/env bash
# build.sh — Script de inicio para Render.com
set -e

echo "=== Creando directorio instance ==="
mkdir -p instance

echo "=== Aplicando migraciones ==="
flask --app run.py db upgrade

echo "=== Creando admin y categorías ==="
flask --app run.py init-db

echo "=== Sembrando datos de demostración ==="
flask --app run.py seed-demo

echo "=== Build completado ==="
