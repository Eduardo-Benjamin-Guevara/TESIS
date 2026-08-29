"""Servicio de exportación de reportes en CSV y Excel."""
import csv
import io
from copy import copy

from openpyxl import Workbook


def exportar_csv(filas: list[dict]) -> bytes:
    """Convierte una lista de diccionarios a CSV (bytes)."""
    if not filas:
        return ("\ufeff").encode("utf-8")
    buffer = io.StringIO()
    columnas = list(filas[0].keys())
    escritor = csv.DictWriter(buffer, fieldnames=columnas)
    escritor.writeheader()
    escritor.writerows(filas)
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def exportar_excel(nombre_hoja: str, filas: list[dict]) -> bytes:
    """Convierte una lista de diccionarios a un archivo Excel (bytes)."""
    libro = Workbook()
    hoja = libro.active
    hoja.title = (nombre_hoja or "Reporte")[:31]
    if filas:
        columnas = list(filas[0].keys())
        hoja.append(columnas)
        for fila in filas:
            hoja.append([fila[c] for c in columnas])
        for celda in hoja[1]:
            fuente = copy(celda.font)
            fuente.bold = True
            celda.font = fuente
        # ajustar ancho aproximado de columnas
        for i, c in enumerate(columnas, start=1):
            maxlen = max(len(str(c)), max(len(str(fila[c])) for fila in filas))
            hoja.column_dimensions[_letra_columna(i)].width = min(maxlen + 2, 40)
    buffer = io.BytesIO()
    libro.save(buffer)
    return buffer.getvalue()


def _letra_columna(indice: int) -> str:
    letra = ""
    n = indice
    while n:
        n, resto = divmod(n - 1, 26)
        letra = chr(65 + resto) + letra
    return letra