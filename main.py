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
import shutil
import platform
import subprocess
import importlib.util
import calendar
import argparse
from datetime import date, timedelta

# ===========================================================================
# CONFIGURACIÓN CENTRAL
# ===========================================================================

PATH_BASE = "/home/christian/Documentos/Reportes_Aut"

# Archivo marcador que solo existe en la máquina local de trabajo (fuera de
# PATH_BASE, para que sobreviva a la limpieza final). Su presencia es lo
# único que habilita el borrado automático de la carpeta del proyecto.
MARCADOR_MAQUINA_LOCAL = os.path.expanduser("~/.reportes_aut_local")

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


def elegir_archivo_revisado(mes):
    """
    Cuando Claudia ya revisó el reporte, pregunta qué archivo usar:
    el generado por defecto (si no hubo errores) o uno diferente
    (si Claudia lo reenvió con modificaciones).
    """
    archivo_default = os.path.join(PATH_BASE, f"Reporte_organon_{mes:02d}.xlsx")

    print(f"\n  📄 Archivo generado por defecto: {archivo_default}")
    print("  ¿Qué archivo deseas usar para el envío final?")
    print("    1) El generado por defecto (Claudia no encontró errores)")
    print("    2) Uno diferente (Claudia lo reenvió con modificaciones)")

    opcion = input("  Selecciona una opción [1/2]: ").strip()

    if opcion == "2":
        while True:
            ruta = input("  Ingresa la ruta del archivo con las modificaciones: ").strip()
            if not os.path.isabs(ruta):
                ruta = os.path.join(PATH_BASE, ruta)
            if os.path.isfile(ruta):
                print(f"  ✅ Se usará: {ruta}")
                return ruta
            print(f"  ⚠️  No se encontró el archivo: {ruta}")

    print(f"  ✅ Se usará el archivo por defecto: {archivo_default}")
    return archivo_default

# ===========================================================================
# INSTALACIÓN DE REQUISITOS
# ===========================================================================
#
# Verifica e instala, si faltan, lo necesario para que el pipeline corra
# (driver ODBC de SQL Server, git, tkinter) y las dependencias de Python de
# requirements.txt. Es best-effort: si algo no se puede instalar solo,
# se imprime cómo instalarlo a mano y el pipeline continúa de todos modos.
#
# OJO: esto NO activa la limpieza automática de la carpeta del proyecto.
# El marcador ~/.reportes_aut_local que la habilita sigue siendo manual,
# a propósito, para que el borrado nunca se active sin que alguien lo haya
# decidido explícitamente en esa máquina.


def _comando_disponible(nombre):
    return shutil.which(nombre) is not None


def _ejecutar(cmd, **kwargs):
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def _instalar_requisitos_python():
    """Instala las dependencias de requirements.txt si no están presentes."""
    ruta_requirements = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if not os.path.isfile(ruta_requirements):
        return

    try:
        import pyodbc    # noqa: F401
        import pandas    # noqa: F401
        import openpyxl  # noqa: F401
        import selenium  # noqa: F401
        return  # las principales ya están instaladas
    except ImportError:
        pass

    print("  📦 Instalando dependencias de Python (requirements.txt)...")
    try:
        _ejecutar([sys.executable, "-m", "pip", "install", "-r", ruta_requirements])
    except Exception as e:
        print(f"  ⚠️  No se pudieron instalar automáticamente ({e}). "
              f"Instálalas a mano con:  pip install -r requirements.txt")


def _odbc_driver18_presente():
    """Usa pyodbc (ya instalado por el paso anterior) para ver si el driver nativo está registrado."""
    try:
        import pyodbc
        return "ODBC Driver 18 for SQL Server" in pyodbc.drivers()
    except Exception:
        return False


def _actualizar_apt():
    """
    `apt-get update` sin abortar todo si UN repositorio de terceros falla
    (p. ej. uno ya mal configurado en el sistema). apt sigue listando los
    demás repos igual; solo avisa en vez de levantar una excepción.
    """
    print("  $ sudo apt-get update")
    resultado = subprocess.run(["sudo", "apt-get", "update"])
    if resultado.returncode != 0:
        print("  ⚠️  'apt-get update' reportó errores en algún repositorio de terceros; "
              "se continúa con los paquetes que sí se pudieron listar.")


def _instalar_requisitos_linux():
    if not _comando_disponible("apt-get"):
        print("  ⚠️  No se detectó 'apt-get'. Instala manualmente: git, python3-tk "
              "y 'ODBC Driver 18 for SQL Server'.")
        return

    faltantes = []
    if not _comando_disponible("git"):
        faltantes.append("git")
    try:
        import tkinter  # noqa: F401
    except ImportError:
        faltantes.append("python3-tk")
    if not _comando_disponible("odbcinst"):
        faltantes.append("unixodbc-dev")

    if faltantes:
        print(f"  📦 Instalando paquetes del sistema faltantes: {', '.join(faltantes)}")
        _actualizar_apt()
        try:
            _ejecutar(["sudo", "apt-get", "install", "-y"] + faltantes)
        except Exception as e:
            print(f"  ⚠️  No se pudieron instalar automáticamente ({e}). Instálalos a mano.")

    if _odbc_driver18_presente():
        print("  ✅ ODBC Driver 18 for SQL Server ya está instalado.")
        return

    print("  📦 Instalando 'ODBC Driver 18 for SQL Server' (repositorio oficial de Microsoft)...")
    try:
        _ejecutar(["sudo", "apt-get", "install", "-y", "curl", "gnupg2", "apt-transport-https"])

        lista_repo = subprocess.run(
            ["curl", "-sSL", "https://packages.microsoft.com/config/debian/12/prod.list"],
            capture_output=True, check=True,
        )
        texto_lista = lista_repo.stdout.decode()

        clave = subprocess.run(
            ["curl", "-sSL", "https://packages.microsoft.com/keys/microsoft.asc"],
            capture_output=True, check=True,
        )

        # El prod.list trae su propio `signed-by=<ruta>`. La clave tiene que
        # quedar EXACTAMENTE en esa ruta o apt no la encuentra — eso fue lo
        # que falló antes: la clave se copió a /etc/apt/trusted.gpg.d, pero
        # el repo pedía /usr/share/keyrings/microsoft-prod.gpg.
        rutas_keyring = {"/etc/apt/trusted.gpg.d/microsoft.asc"}
        rutas_keyring.update(re.findall(r"signed-by=([^\]\s]+)", texto_lista))

        for ruta_keyring in rutas_keyring:
            subprocess.run(["sudo", "mkdir", "-p", os.path.dirname(ruta_keyring)], check=True)
            subprocess.run(["sudo", "tee", ruta_keyring], input=clave.stdout,
                            capture_output=True, check=True)

        subprocess.run(["sudo", "tee", "/etc/apt/sources.list.d/mssql-release.list"],
                        input=lista_repo.stdout, capture_output=True, check=True)

        _actualizar_apt()
        env = os.environ.copy()
        env["ACCEPT_EULA"] = "Y"
        _ejecutar(["sudo", "-E", "apt-get", "install", "-y", "msodbcsql18"], env=env)
        print("  ✅ ODBC Driver 18 for SQL Server instalado.")
    except Exception as e:
        print(f"  ⚠️  No se pudo instalar el driver ODBC automáticamente ({e}).")
        print("     Instálalo a mano siguiendo: "
              "https://learn.microsoft.com/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server")


def _instalar_requisitos_windows():
    pendientes = []

    if not _comando_disponible("git"):
        if _comando_disponible("winget"):
            try:
                _ejecutar(["winget", "install", "--id", "Git.Git", "-e", "--silent"])
            except Exception:
                pendientes.append("Git — https://git-scm.com/download/win")
        else:
            pendientes.append("Git — https://git-scm.com/download/win")

    if not _odbc_driver18_presente():
        if _comando_disponible("winget"):
            try:
                _ejecutar([
                    "winget", "install", "--id", "Microsoft.msodbcsql.18", "-e", "--silent",
                    "--accept-package-agreements", "--accept-source-agreements",
                ])
            except Exception:
                pendientes.append(
                    "ODBC Driver 18 for SQL Server — "
                    "https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server"
                )
        else:
            pendientes.append(
                "ODBC Driver 18 for SQL Server — "
                "https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server"
            )

    if pendientes:
        print("  ⚠️  No se pudieron instalar automáticamente estos requisitos; instálalos a mano:")
        for item in pendientes:
            print(f"     - {item}")


def instalar_requisitos_sistema():
    """
    Verifica e instala (si faltan) lo necesario para correr el pipeline:
    git, tkinter, el driver ODBC 18 de SQL Server y las dependencias de
    Python. No requiere privilegios especiales salvo los que pida 'sudo'
    o el instalador del sistema (Windows) de forma normal e interactiva.
    """
    titulo("VERIFICANDO REQUISITOS DEL SISTEMA")
    sistema = platform.system()

    if sistema == "Linux":
        _instalar_requisitos_linux()
    elif sistema == "Windows":
        _instalar_requisitos_windows()
    else:
        print(f"  ⚠️  Sistema operativo no reconocido ({sistema}); omite verificación automática.")

    _instalar_requisitos_python()

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

    resultado = mod.SuperScraperCorresponsalias(headless=False).ejecutar()
    if resultado is False:
        print("  ℹ️  El pipeline continuará sin archivo de corresponsalías Manzanillo.")
    elif resultado is None:
        print("  ⚠️  No se pudo consultar Manzanillo por SQL. El pipeline seguirá, pero revisa la conectividad si esperabas datos.")


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


def paso_6b_envio_final(mes, año, archivo_final):
    """Limpia descargas, separa por pestañas y envía al cliente."""
    titulo("PASO 6a — Limpieza + Separación + Envío Final")

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

def es_maquina_local():
    """
    True solo si existe el archivo marcador fuera del repo (ver
    MARCADOR_MAQUINA_LOCAL). Evita que la limpieza automática borre la
    carpeta del proyecto en cualquier entorno que no sea la máquina de
    trabajo local (ej. CI, contenedores, otra copia del repo).
    """
    return os.path.isfile(MARCADOR_MAQUINA_LOCAL)


def mostrar_aviso_limpieza():
    """Muestra una ventana emergente confirmando que la limpieza terminó."""
    mensaje = "Reporte completado, limpieza local completa, revisar reportes.bi@abcsc.mx"
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Reporte Mensual Organon", mensaje)
        root.destroy()
    except Exception:
        # Si no hay entorno gráfico disponible, al menos deja constancia en consola.
        print(f"\n  🪟 {mensaje}")


def detectar_ruta_proyecto():
    """
    Detecta la raíz real del repositorio git en ESTA máquina, en lugar de
    confiar en PATH_BASE (que es fijo y no coincide con la ruta de clonado
    en cada equipo, sobre todo en Windows). Equivale a lo que reporta
    `git rev-parse --show-toplevel` ejecutado desde la carpeta del proyecto
    en la terminal (ej. la terminal integrada de VS Code).

    Devuelve None si no se puede detectar (por ejemplo, si git no está
    disponible o la carpeta ya no es un repositorio git).
    """
    try:
        resultado = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            check=True,
        )
        ruta = resultado.stdout.strip()
        return os.path.normpath(ruta) if ruta else None
    except Exception:
        return None


def limpieza_local_final():
    """
    Elimina la carpeta raíz del proyecto SOLO en la máquina local de
    trabajo, para liberar espacio en disco una vez que el reporte ya fue
    respaldado. No hace nada si no se detecta el marcador de máquina local
    (ver es_maquina_local).

    La ruta a eliminar se detecta vía git (ver detectar_ruta_proyecto) para
    que funcione igual sin importar en qué carpeta/unidad esté clonado el
    repositorio en cada máquina (ej. Windows vs. Linux). Si git no logra
    detectarla, se usa PATH_BASE como respaldo.
    """
    if not es_maquina_local():
        print("\n  ℹ️  No se detectó marcador de máquina local "
              f"({MARCADOR_MAQUINA_LOCAL}): se omite la limpieza de la carpeta del proyecto.")
        return

    ruta_proyecto = detectar_ruta_proyecto() or PATH_BASE

    # Verificación de cordura: la ruta debe existir y contener este mismo
    # main.py, para no borrar por error una carpeta distinta.
    if not ruta_proyecto or not os.path.isfile(os.path.join(ruta_proyecto, "main.py")):
        print(f"\n  ⚠️  No se pudo confirmar la ruta del proyecto ({ruta_proyecto!r}). "
              "Se omite la limpieza por seguridad.")
        return

    titulo("LIMPIEZA LOCAL — Eliminando carpeta del proyecto")
    print(f"  🗑️  Eliminando: {ruta_proyecto}")

    # Salir de la carpeta antes de borrarla, para no eliminar el directorio
    # de trabajo mientras está en uso por este mismo proceso.
    os.chdir(os.path.dirname(ruta_proyecto) or "/")
    shutil.rmtree(ruta_proyecto)

    print("  ✅ Carpeta del proyecto eliminada.")
    mostrar_aviso_limpieza()


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

    instalar_requisitos_sistema()

    mes, año = pedir_periodo()
    print(f"\n  ✅ Período: {MESES_ES[mes]} {año}  ({mes:02d}/{año})")

    if paso_inicio > 1:
        print(f"\n  ⏭️  Iniciando desde el Paso {paso_inicio}.")

    os.chdir(PATH_BASE)

    # La limpieza local (ver limpieza_local_final) se ejecuta siempre al
    # final, sin importar si el pipeline terminó bien o falló en cualquier
    # paso (incluido el envío de correo). Esto evita que máquinas con
    # versiones viejas o errores a medias se queden con carpetas desactualizadas
    # tras el `git pull`: siempre arrancan de cero en la siguiente corrida.
    try:
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

            # ── Punto de decisión: ¿Ya revisó Claudia? ───────────────────────
            print("\n" + "─" * 62)
            print(f"  📋 Reporte listo: Reporte_organon_{mes:02d}.xlsx")

            if confirmar("¿Ya fue revisado y aprobado por Claudia?"):
                archivo_final = elegir_archivo_revisado(mes)
                paso_6b_envio_final(mes, año, archivo_final)
            else:
                paso_6a_envio_revision(mes, año)

            titulo(f"✅  PROCESO COMPLETADO — {MESES_ES[mes]} {año}")

        except Exception as e:
            print(f"\n  ❌ Error en el pipeline: {e}")
            print(f"  💡 Puedes reintentar desde el paso actual con:  python main.py --desde N")
            raise
    finally:
        limpieza_local_final()


if __name__ == "__main__":
    main()
