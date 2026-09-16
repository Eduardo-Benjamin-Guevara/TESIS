"""Genera un reporte HTML con una captura de consola POR CADA TEST.

Proceso:
1. Recopila la lista de todos los tests con `pytest --collect-only`.
2. Ejecuta cada test por separado y captura su salida de consola.
3. Convierte la salida de cada test en una pequeña imagen PNG estilo consola.
4. Genera UN SOLO archivo HTML con una tabla donde cada fila es una prueba
   con su nombre, archivo, estado y su captura de consola incrustada.

Uso (desde la raíz del proyecto):
    .\venv\Scripts\python.exe generar_reportes.py
"""
import base64
import io
import os
import re
import subprocess
import sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ)
ENV["PYTHONIOENCODING"] = "utf-8"

FONDO = (18, 18, 24)
TEXTO = (216, 222, 233)
VERDE = (80, 200, 120)
ROJO = (235, 87, 87)
AMARILLO = (240, 196, 90)
GRIS = (150, 158, 170)


def _cargar_fuente(tam):
    for ruta in [
        "C:/Windows/Fonts/Consolas.ttf",
        "C:/Windows/Fonts/Cour.ttf",
    ]:
        if os.path.exists(ruta):
            try:
                return ImageFont.truetype(ruta, tam)
            except Exception:
                pass
    return ImageFont.load_default()


def _decodificar(bs):
    try:
        return bs.decode("utf-8")
    except UnicodeDecodeError:
        return bs.decode("cp1252", errors="replace")


def _limpiar(texto):
    texto = re.sub(r"\x1b\[[0-9;]*m", "", texto)
    texto = texto.replace("\r", "\n")
    lineas = [ln for ln in texto.split("\n")]
    return lineas


def _ancho(fuente, texto):
    try:
        return fuente.getlength(texto)
    except Exception:
        bbox = fuente.getbbox(texto)
        return (bbox[2] - bbox[0]) if bbox else len(texto) * 16


def _salida_a_png(lineas, tam=16):
    """Dibuja las líneas de consola como una imagen PNG (bytes)."""
    if not lineas:
        lineas = ["(sin salida)"]
    fuente = _cargar_fuente(tam)
    alto_linea = tam + 5
    padding = 12
    max_ancho = max((_ancho(fuente, ln) for ln in lineas), default=0)
    ancho = max(int(max_ancho) + padding * 2, 620)
    alto = alto_linea * len(lineas) + padding * 2

    img = Image.new("RGB", (ancho, alto), FONDO)
    draw = ImageDraw.Draw(img)
    y = padding
    for ln in lineas:
        color = TEXTO
        up = ln.upper()
        if "PASSED" in up:
            color = VERDE
        elif "FAILED" in up or "ERROR" in up:
            color = ROJO
        elif "WARNING" in up:
            color = AMARILLO
        elif up.startswith("====") or up.startswith("----"):
            color = GRIS
        draw.text((padding, y), ln, font=fuente, fill=color)
        y += alto_linea

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _ejecutar_test(ruta_test):
    """Ejecuta un solo test y devuelve (salida_png_b64, estado, detalle)."""
    cmd = [
        sys.executable, "-m", "pytest", ruta_test,
        "-q", "-o", "addopts=", "--no-header",
    ]
    proc = subprocess.run(cmd, cwd=BASE, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, env=ENV)
    salida = _decodificar(proc.stdout)
    lineas = [ln for ln in _limpiar(salida) if ln.strip()]

    # Determinar estado
    if "PASSED" in salida or (proc.returncode == 0 and "failed" not in salida
                              and "error" not in salida):
        estado = "aprobado"
    elif "FAILED" in salida:
        estado = "fallido"
    elif "ERROR" in salida:
        estado = "error"
    else:
        estado = "fallido" if proc.returncode != 0 else "aprobado"

    return _salida_a_png(lineas), estado, salida


def main():
    print("Recopilando lista de pruebas...")
    col = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q",
         "-o", "addopts="],
        cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=ENV,
    )
    lista = _decodificar(col.stdout).splitlines()
    tests = []
    for ln in lista:
        ln = ln.strip()
        if ln and "::" in ln and not ln.startswith("no tests ran"):
            tests.append(ln)

    print(f"Ejecutando {len(tests)} pruebas (una por una)...")

    resultados = []
    total = len(tests)
    for i, ruta in enumerate(tests, 1):
        sys.stdout.write(f"\r  Procesando {i}/{total}")
        sys.stdout.flush()
        try:
            img_b64, estado, detalle = _ejecutar_test(ruta)
        except Exception as e:
            img_b64, estado, detalle = "", "error", str(e)
        nombre = ruta.split("::")[-1]
        archivo = ruta.split("::")[0].replace("tests/", "")
        resultados.append((nombre, archivo, estado, img_b64))
    print()

    aprobadas = sum(1 for r in resultados if r[2] == "aprobado")
    fallidas = sum(1 for r in resultados if r[2] != "aprobado")
    porcentaje = round(aprobadas * 100 / total) if total else 0
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    filas = []
    for nombre, archivo, estado, img_b64 in resultados:
        color = "verde" if estado == "aprobado" else "rojo"
        etiqueta = {"aprobado": "Aprobado", "fallido": "Fallido",
                    "error": "Error"}.get(estado, estado)
        img_html = f'<img class="consola" src="data:image/png;base64,{img_b64}" alt="Consola {nombre}">' if img_b64 else '<span class="muted">sin captura</span>'
        filas.append(f"""<tr>
  <td class="nb"><span class="badge {color}">{etiqueta}</span></td>
  <td class="nombre">{nombre}</td>
  <td class="archivo">{archivo}</td>
  <td>{img_html}</td>
</tr>""")

    tabla = "\n".join(filas)
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reporte de Pruebas - Control de Alimentos I.E.I. N.° 1488</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6fb; margin: 0; padding: 26px; color: #1c2431; }}
  .wrap {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ color: #0f6f5a; margin: 0 0 6px; }}
  .sub {{ color: #5a6b7a; margin: 0 0 20px; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 18px; }}
  .card {{ background: #fff; border-radius: 12px; padding: 18px 20px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }}
  .card .num {{ font-size: 34px; font-weight: 700; }}
  .card .lbl {{ color: #5a6b7a; font-size: 13px; margin-top: 2px; }}
  .verde {{ color: #16a34a; }} .rojo {{ color: #dc2626; }} .ambar {{ color: #d97706; }}
  .estado {{ font-size: 15px; font-weight: 600; padding: 8px 14px; border-radius: 8px; margin-bottom: 18px; display: inline-block; }}
  .ok {{ background: #dcfce7; color: #166534; }} .mal {{ background: #fee2e2; color: #991b1b; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,.07); }}
  th {{ background: #0f6f5a; color: #fff; text-align: left; padding: 12px 14px; font-size: 13px; }}
  td {{ padding: 10px 14px; border-bottom: 1px solid #edf1f7; vertical-align: top; font-size: 13px; }}
  tr:nth-child(even) td {{ background: #fafbfe; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
  .badge.verde {{ background: #dcfce7; color: #166534; }}
  .badge.rojo {{ background: #fee2e2; color: #991b1b; }}
  .nombre {{ font-weight: 600; white-space: nowrap; }}
  .archivo {{ color: #5a6b7a; white-space: nowrap; }}
  .nb {{ width: 110px; }}
  .consola {{ max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #e3e8f0; }}
  .muted {{ color: #8a97a5; }}
  .meta {{ color: #8a97a5; font-size: 12px; margin-top: 16px; }}
  footer {{ text-align: center; color: #8a97a5; font-size: 12px; margin-top: 24px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Sistema de Control de Alimentos I.E.I. N.° 1488</h1>
  <p class="sub">Reporte de ejecución de pruebas funcionales &mdash; captura por cada test</p>

  <div class="grid">
    <div class="card"><div class="num verde">{aprobadas}</div><div class="lbl">Pruebas aprobadas</div></div>
    <div class="card"><div class="num {'verde' if fallidas==0 else 'rojo'}">{fallidas}</div><div class="lbl">Pruebas fallidas</div></div>
    <div class="card"><div class="num ambar">{porcentaje}%</div><div class="lbl">Efectividad</div></div>
  </div>

  <div class="estado {'ok' if fallidas==0 else 'mal'}">{'TODAS LAS PRUEBAS PASAN' if fallidas==0 else str(fallidas)+' PRUEBA(S) CON ERROR'}</div>

  <table>
    <thead>
      <tr><th>Estado</th><th>Prueba</th><th>Archivo</th><th>Captura de consola</th></tr>
    </thead>
    <tbody>
{tabla}
    </tbody>
  </table>

  <p class="meta">Generado automáticamente el {fecha} &mdash; {total} pruebas.</p>
  <footer>Proyecto de Tesis &mdash; Control de Alimentos I.E.I. N.° 1488</footer>
</div>
</body>
</html>"""

    ruta_html = os.path.join(BASE, "reporte_tests.html")
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML generado:", ruta_html)
    print(f"RESUMEN: {aprobadas} aprobadas | {fallidas} fallidas | {porcentaje}%")


if __name__ == "__main__":
    main()
