import pandas as pd
import numpy as np
import os
import re
import zipfile
import io
import pdfplumber
import warnings
from openpyxl import load_workbook

warnings.filterwarnings('ignore')

# --- CONFIGURACIÓN ---
MES_ANALIZADO = "02"
PATH_DESCARGAS = "/home/christian/Documentos/Reportes_Aut/Descargas_ZIP"
ARCHIVO_ENTRADA = "/home/christian/Documentos/Reportes_Aut/Reporte_organon.xlsx"
ARCHIVO_SALIDA = f"/home/christian/Documentos/Reportes_Aut/Reporte_organon_{MES_ANALIZADO}.xlsx"

def extraer_datos_completos(ruta_pdf):
    """Busca Proveedor, Fecha y Mercancía dentro del PDF"""
    datos = {"proveedor": None, "fecha": None, "mercancia": None}
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            texto = "\n".join([p.extract_text() or "" for p in pdf.pages])
            
            # 1. Buscar Fecha de Pago
            fecha_match = re.search(r'PAGO\s+(\d{2}/\d{2}/\d{4})', texto)
            if fecha_match: datos["fecha"] = fecha_match.group(1)
            
            # 2. Buscar Mercancía (Descripción)
            patron_desc = re.compile(r'\d{3}\s+\d{8}\s+.*?\n\s*(.*?)\n', re.MULTILINE)
            descs = patron_desc.findall(texto)
            if descs: datos["mercancia"] = " / ".join([d.strip() for d in descs])
            
            # 3. Buscar Proveedor
            prov_match = re.search(r'PROVEEDOR:\s*(.*)', texto, re.IGNORECASE)
            if prov_match: datos["proveedor"] = prov_match.group(1).strip()
            
            return datos
    except: return datos

def ejecutar_revision():
    print(f"🛠️ Iniciando revisión quirúrgica para MNS y LT (Mes: {MES_ANALIZADO})...")
    
    if not os.path.exists(ARCHIVO_ENTRADA):
        print(f"❌ No se encontró el archivo base: {ARCHIVO_ENTRADA}")
        return

    df = pd.read_excel(ARCHIVO_ENTRADA)

    def tiene_error(fila):
        ref = str(fila['Referencia']).strip().upper()
        if not (ref.startswith('MNS') or ref.startswith('LT')):
            return False
            
        columnas_criticas = ['Proveedor', 'Fecha de Pago', 'Mercancía', 'No Factura']
        for col in columnas_criticas:
            if col in df.columns:
                val = str(fila[col]).strip().upper()
                if val in ['S/D', 'NAN', '', 'NONE']:
                    return True
        return False

    indices_reparar = df[df.apply(tiene_error, axis=1)].index

    if len(indices_reparar) == 0:
        print("✅ No se detectaron campos faltantes en referencias MNS o LT.")
    else:
        print(f"🔍 Detectadas {len(indices_reparar)} filas por reparar. Buscando en ZIPs...")

        for idx in indices_reparar:
            referencia_target = str(df.at[idx, 'Referencia']).strip().upper()
            uuid_target = str(df.at[idx].get('UUID de la Factura', 'NAN')).upper().strip()
            factura_target = str(df.at[idx].get('No Factura', 'NAN')).strip()
            encontrado = False

            for archivo in os.listdir(PATH_DESCARGAS):
                if archivo.endswith('.zip'):
                    try:
                        with zipfile.ZipFile(os.path.join(PATH_DESCARGAS, archivo), 'r') as z:
                            for nombre_interno in z.namelist():
                                if (referencia_target in nombre_interno.upper()) or \
                                   (uuid_target != 'NAN' and uuid_target in nombre_interno.upper()) or \
                                   (factura_target != 'NAN' and factura_target in nombre_interno):
                                    
                                    if nombre_interno.lower().endswith('.pdf'):
                                        with z.open(nombre_interno) as f_pdf:
                                            nuevos_datos = extraer_datos_completos(io.BytesIO(f_pdf.read()))
                                            
                                            if str(df.at[idx, 'Proveedor']).upper() in ['S/D', 'NAN'] and nuevos_datos["proveedor"]:
                                                df.at[idx, 'Proveedor'] = nuevos_datos["proveedor"]
                                            
                                            if str(df.at[idx, 'Fecha de Pago']).upper() in ['S/D', 'NAN'] and nuevos_datos["fecha"]:
                                                df.at[idx, 'Fecha de Pago'] = nuevos_datos["fecha"]
                                                
                                            if str(df.at[idx, 'Mercancía']).upper() in ['S/D', 'NAN', ''] and nuevos_datos["mercancia"]:
                                                df.at[idx, 'Mercancía'] = nuevos_datos["mercancia"]
                                            
                                            encontrado = True
                                            print(f"   ✨ Reparada Referencia: {referencia_target}")
                                            break
                    except: continue
                if encontrado: break

    # --- GUARDADO Y ELIMINACIÓN DEL ANTERIOR ---
    try:
        df.to_excel(ARCHIVO_SALIDA, sheet_name='RESUMEN_TOTAL', index=False)
        print(f"💾 Guardando reporte finalizado en: {ARCHIVO_SALIDA}")
        
        # Eliminamos el archivo de entrada original
        if os.path.exists(ARCHIVO_ENTRADA):
            os.remove(ARCHIVO_ENTRADA)
            print(f"🗑️ Archivo temporal '{os.path.basename(ARCHIVO_ENTRADA)}' eliminado.")
            
    except Exception as e:
        print(f"❌ Error al guardar o eliminar archivos: {e}")

    print("✨ Proceso de revisión y limpieza completado.")

if __name__ == "__main__":
    ejecutar_revision()