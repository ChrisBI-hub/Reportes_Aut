#!/usr/bin/env python3
"""
main.py — Orquestador del Reporte Mensual Organon
==================================================

Flujo completo:
  1. organon_2_1.py       → REPORTE_ADUANAL_ORGANON_{año}_{mes:02d}.xlsx
  2. oñate_extraccion.py  → REPORTE_MAESTRO_{año}_{mes:02d}.xlsx  (refs MNS)
  3. laredo.py            → PDFs en Descargas_LT/               (refs LT)
     └── analisis.py      → ANALISIS_LT_{timestamp}.xlsx
  4. union_2_1.py         → Reporte_organon.xlsx
  5. revision_profunda.py → Reporte_organon_{mes:02d}.xlsx
  6a. [Revisado]   limpieza.py → separador_pestañas.py → correo.py
  6b. [No revisado]                                  correo_revision.py

Uso:
  python main.py              # Detecta mes anterior automáticamente
  python main.py --desde 4    # Inicia desde el paso 4 (útil si algo falló)
"""

import os
import re
import sys
import importlib.util
import calendar
import argparse
from datetime import date, timedelta

# ===========================================================================
# CONFIGURACIÓN CENTRAL
# ===========================================================================

PATH_BASE = "/home/christian/Documentos/Reportes_Aut"

MESES_ES = {
    1: "Enero",    2: "Febrero",   3: "Marzo",    4: "Abril",
    5: "Mayo",     6: "Junio",     7: "Julio",    8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

# ===========================================================================
# UTILIDADES
# ===========================================================================

def titulo(texto, nivel=1):
    if nivel == 1:
        print(f"\n{'═' * 62}")
        print(f"  {texto}")
        print(f"{'═' * 62}")
    else:
        print(f"\n  ── {texto} ──")


def detectar_periodo():
    """Retorna (mes, año) del mes inmediatamente anterior al actual."""
    hoy = date.today()
    primer_dia = hoy.replace(day=1)
    mes_anterior = primer_dia - timedelta(days=1)
    return mes_anterior.month, mes_anterior.year


def pedir_periodo():
    """Muestra el período detectado y permite al usuario corregirlo."""
    mes_auto, año_auto = detectar_periodo()
    print(f"\n  📅 Período detectado automáticamente: {MESES_ES[mes_auto]} {año_auto}")
    respuesta = input("  ¿Es correcto? [S/n]: ").strip().lower()

    if respuesta in ("", "s", "si", "sí", "y", "yes"):
        return mes_auto, año_auto

    try:
        mes = int(input("  Ingresa el mes (1-12): ").strip())
        año = int(input("  Ingresa el año (ej. 2026): ").strip())
        assert 1 <= mes <= 12
        return mes, año
    except (ValueError, AssertionError):
        print("  ⚠️  Valor inválido. Se usará el período detectado.")
        return mes_auto, año_auto


def calcular_rango_portal(mes, año):
    """
    Calcula FECHA_INI y FECHA_FIN para el portal Owcia (oñate).
    El portal muestra operaciones con ~2 meses de desfase respecto al mes de factura.
    Rango: primer día de M-2  →  último día de M-1
    """
    primer_dia_mes = date(año, mes, 1)

    # Último día del mes anterior (M-1)
    fin_m1 = primer_dia_mes - timedelta(days=1)
    # Primer día del mes M-1
    ini_m1 = fin_m1.replace(day=1)

    # Último día de M-2
    fin_m2 = ini_m1 - timedelta(days=1)
    # Primer día de M-2
    ini_m2 = fin_m2.replace(day=1)

    return ini_m2.strftime("%Y-%m-%d"), fin_m1.strftime("%Y-%m-%d")


def cargar_modulo(alias, nombre_archivo):
    """
    Importa un módulo desde su ruta sin ejecutar el bloque __main__.
    Devuelve el objeto de módulo para que se puedan parchear sus variables.
    """
    ruta = os.path.join(PATH_BASE, nombre_archivo)
    spec = importlib.util.spec_from_file_location(alias, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def exec_con_vars(nombre_archivo, substituciones: dict):
    """
    Ejecuta un script que corre lógica a nivel de módulo (sin funciones),
    inyectando las variables dinámicas ANTES de que se evalúen las f-strings.

    Se usa exclusivamente para organon_2_1.py, donde las queries SQL
    son f-strings calculadas en la raíz del módulo.
    """
    ruta = os.path.join(PATH_BASE, nombre_archivo)
    with open(ruta, "r", encoding="utf-8") as f:
        source = f.read()

    for patron, reemplazo in substituciones.items():
        source = re.sub(patron, reemplazo, source)

    # Asegurar que los archivos generados caigan en PATH_BASE
    os.chdir(PATH_BASE)
    ns = {"__name__": "__main__", "__file__": ruta}
    exec(compile(source, ruta, "exec"), ns)  # noqa: S102


def confirmar(pregunta):
    """Retorna True si el usuario responde sí."""
    r = input(f"\n  {pregunta} [s/N]: ").strip().lower()
    return r in ("s", "si", "sí", "y", "yes")

# ===========================================================================
# PASOS DEL PIPELINE
# ===========================================================================

def paso_1_extraccion_base(mes, año):
    titulo(f"PASO 1 — Extracción Base SQL  |  {MESES_ES[mes]} {año}")
    # organon_2_1.py ejecuta queries SQL a nivel de módulo (no hay función),
    # por lo que se inyectan los valores antes de ejecutar el archivo.
    exec_con_vars(
        "organon_2_1.py",
        {
            r"MES_VALIDACION\s*=\s*\d+":  f"MES_VALIDACION = {mes}",
            r"ANIO_VALIDACION\s*=\s*\d+": f"ANIO_VALIDACION = {año}",
        },
    )
    print(f"\n  ✅ Archivo generado: REPORTE_ADUANAL_ORGANON_{año}_{mes:02d}.xlsx")


def paso_2_extraccion_manzanillo(mes, año):
    titulo("PASO 2 — Corresponsalías Manzanillo  |  oñate_extraccion.py")

    fecha_ini, fecha_fin = calcular_rango_portal(mes, año)
    print(f"  📅 Rango portal: {fecha_ini}  →  {fecha_fin}")

    mod = cargar_modulo("onate_extraccion", "oñate_extraccion.py")

    # Parchear variables de configuración ANTES de instanciar la clase
    mod.MES_VALIDACION    = mes
    mod.ANIO_VALIDACION   = año
    mod.FECHA_INI         = fecha_ini
    mod.FECHA_FIN         = fecha_fin
    mod.ARCHIVO_EXCEL_FINAL = os.path.join(PATH_BASE, f"REPORTE_MAESTRO_{año}_{mes:02d}.xlsx")

    mod.SuperScraperCorresponsalias(headless=False).ejecutar()


def paso_3_laredo_y_analisis(mes, año):
    titulo("PASO 3 — Laredo: descarga PDFs + análisis")

    # 3a — Descarga de PDFs vía Selenium
    titulo("PASO 3a — Descarga PDFs  |  laredo.py", nivel=2)
    laredo = cargar_modulo("laredo", "laredo.py")
    laredo.MES_VALIDACION  = mes
    laredo.ANIO_VALIDACION = año
    laredo.LaredoExtractor().ejecutar()

    # 3b — Análisis de los PDFs descargados
    titulo("PASO 3b — Análisis PDFs  |  analisis.py", nivel=2)
    analisis = cargar_modulo("analisis", "analisis.py")
    analisis.AnalizadorLaredo().analizar_archivos()


def paso_4_union(mes, año):
    titulo("PASO 4 — Unificación de Reportes  |  union_2_1.py")

    mod = cargar_modulo("union_2_1", "union_2_1.py")

    # Rutas dinámicas que en el script original están hardcodeadas
    mod.ARCHIVO_ADUANAL = os.path.join(PATH_BASE, f"REPORTE_ADUANAL_ORGANON_{año}_{mes:02d}.xlsx")
    mod.ARCHIVO_MAESTRO = os.path.join(PATH_BASE, f"REPORTE_MAESTRO_{año}_{mes:02d}.xlsx")
    mod.ARCHIVO_SALIDA  = os.path.join(PATH_BASE, "Reporte_organon.xlsx")

    mod.unificar_reportes()
    print(f"\n  ✅ Reporte unificado: Reporte_organon.xlsx")


def paso_5_revision_profunda(mes):
    titulo("PASO 5 — Revisión Profunda  |  revision_profunda.py")

    mod = cargar_modulo("revision_profunda", "revision_profunda.py")

    mod.MES_ANALIZADO  = f"{mes:02d}"
    mod.ARCHIVO_ENTRADA = os.path.join(PATH_BASE, "Reporte_organon.xlsx")
    mod.ARCHIVO_SALIDA  = os.path.join(PATH_BASE, f"Reporte_organon_{mes:02d}.xlsx")
    mod.PATH_DESCARGAS  = os.path.join(PATH_BASE, "Descargas_ZIP")

    mod.ejecutar_revision()
    print(f"\n  ✅ Reporte revisado: Reporte_organon_{mes:02d}.xlsx")


def paso_6a_envio_revision(mes, año):
    """Envía el reporte a Claudia para revisión interna."""
    titulo("PASO 6b — Envío para revisión  |  correo_revision.py")

    mod = cargar_modulo("correo_revision", "correo_revision.py")

    mod.MES_NOMBRE   = MESES_ES[mes]
    mod.ANIO         = str(año)
    mod.RUTA_ARCHIVO = os.path.join(PATH_BASE, f"Reporte_organon_{mes:02d}.xlsx")

    mod.enviar_correo_pro()
    print("\n  📬 Correo de revisión enviado a Claudia.")
    print("  ℹ️  Cuando confirme, ejecuta nuevamente desde el paso 6.")


def paso_6b_envio_final(mes, año):
    """Limpia descargas, separa por pestañas y envía al cliente."""
    titulo("PASO 6a — Limpieza + Separación + Envío Final")

    archivo_final = os.path.join(PATH_BASE, f"Reporte_organon_{mes:02d}.xlsx")

    # Limpieza de carpetas de descargas temporales
    titulo("Limpiando carpetas temporales  |  limpieza.py", nivel=2)
    limpieza = cargar_modulo("limpieza", "limpieza.py")
    limpieza.limpiar_carpeta_descargas(os.path.join(PATH_BASE, "Descargas_ZIP"))
    limpieza.limpiar_carpeta_descargas(os.path.join(PATH_BASE, "Descargas_LT"))

    # Separación por pestañas (referencia por hoja)
    titulo("Separando por pestañas  |  separador_pestañas.py", nivel=2)
    separador = cargar_modulo("separador_pestañas", "separador_pestañas.py")
    separador.separar_por_referencias(archivo_final)

    # Envío al cliente
    titulo("Enviando correo al cliente  |  correo.py", nivel=2)
    correo = cargar_modulo("correo", "correo.py")
    correo.ASUNTO        = f"Reporte Aduanal Organon - {MESES_ES[mes]} {año}"
    correo.RUTA_ARCHIVO  = archivo_final
    correo.enviar_correo_pro()

    print(f"\n  ✅ Reporte de {MESES_ES[mes]} {año} enviado al cliente.")

# ===========================================================================
# MAIN
# ===========================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Orquestador del Reporte Mensual Organon",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--desde",
        type=int,
        choices=range(1, 7),
        default=1,
        metavar="PASO",
        help=(
            "Inicia el pipeline desde este paso (1-6).\n"
            "  1 = Extracción Base SQL\n"
            "  2 = Corresponsalías Manzanillo\n"
            "  3 = Laredo (descarga + análisis)\n"
            "  4 = Unificación\n"
            "  5 = Revisión Profunda\n"
            "  6 = Envío (revisión o final)"
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    paso_inicio = args.desde

    titulo("REPORTE MENSUAL ORGANON — AUTOMATIZACIÓN")

    mes, año = pedir_periodo()
    print(f"\n  ✅ Período: {MESES_ES[mes]} {año}  ({mes:02d}/{año})")

    if paso_inicio > 1:
        print(f"\n  ⏭️  Iniciando desde el Paso {paso_inicio}.")

    os.chdir(PATH_BASE)

    try:
        if paso_inicio <= 1:
            paso_1_extraccion_base(mes, año)

        if paso_inicio <= 2:
            paso_2_extraccion_manzanillo(mes, año)

        if paso_inicio <= 3:
            paso_3_laredo_y_analisis(mes, año)

        if paso_inicio <= 4:
            paso_4_union(mes, año)

        if paso_inicio <= 5:
            paso_5_revision_profunda(mes)

    except Exception as e:
        print(f"\n  ❌ Error en el pipeline: {e}")
        print(f"  💡 Puedes reintentar desde el paso actual con:  python main.py --desde N")
        raise

    # ── Punto de decisión: ¿Ya revisó Claudia? ──────────────────────────────
    print("\n" + "─" * 62)
    print(f"  📋 Reporte listo: Reporte_organon_{mes:02d}.xlsx")

    if confirmar("¿Ya fue revisado y aprobado por Claudia?"):
        paso_6b_envio_final(mes, año)
    else:
        paso_6a_envio_revision(mes, año)

    titulo(f"✅  PROCESO COMPLETADO — {MESES_ES[mes]} {año}")


if __name__ == "__main__":
    main()
