"""
analisis_laredo_pdf.py
======================
Analiza los PDFs "PEDIMENTO SIMPLIFICADO" descargados por laredo.py
y genera un Excel con los campos extraídos.
 
Dependencias:
    pip install pdfplumber pandas openpyxl
"""
 
import os
import re
import logging
import pdfplumber
import pandas as pd
from datetime import datetime
 
# =============================================================================
# CONFIGURACIÓN
# =============================================================================
 
PATH_DESCARGAS = "/home/christian/Documentos/Reportes_Aut/Descargas_LT"
PATH_REPORTES  = os.path.dirname(os.path.abspath(__file__))  # mismo directorio del script
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
 
 
# =============================================================================
# CLASE PRINCIPAL
# =============================================================================
 
class AnalizadorLaredo:
 
    def __init__(self):
        self.resultados = []
 
    # -------------------------------------------------------------------------
    # HELPER
    # -------------------------------------------------------------------------
 
    def buscar(self, patron: str, texto: str, grupo: int = 1) -> str:
        """Devuelve el grupo capturado o 'S/D' si no hay coincidencia."""
        m = re.search(patron, texto, re.IGNORECASE | re.DOTALL)
        return m.group(grupo).strip() if m else "S/D"
 
    # -------------------------------------------------------------------------
    # EXTRACCIÓN DE CAMPOS
    # -------------------------------------------------------------------------
 
    def extraer_datos(self, texto: str, nombre_archivo: str) -> dict:
        """
        Campos extraídos y sus patrones (basados en el texto real del PDF):
 
        FECHAS
        ──────
        ENTRADA: 28/01/2026        →  r'ENTRADA:\s*(\d{2}/\d{2}/\d{4})'
        PAGO: 28/01/2026           →  r'PAGO:\s*(\d{2}/\d{2}/\d{4})'
                                       (el regex anterior fallaba porque buscaba
                                        PAGO\s+fecha sin los dos puntos)
 
        PEDIMENTO / ADUANA
        ──────────────────
        PEDIMENTO: 6000306         →  r'PEDIMENTO:\s*(\d+)'
        ADUANA: 240                →  r'ADUANA:\s*(\d+)'
        PATENTE: 3813              →  r'PATENTE:\s*(\d+)'
 
        PAGO
        ────
        IMPORTE PAGADO: $ 91,504.00  →  r'IMPORTE PAGADO:\s*\$\s*([\d,\.]+)'
        FECHA DE PAGO: 28/01/2026    →  r'FECHA DE PAGO:\s*(\d{2}/\d{2}/\d{4})'
                                        (confirmación / segunda aparición)
 
        REFERENCIA
        ──────────
        Nombre del archivo: LT2691769_PEDIMENTO_SIMPLIFICADO.pdf
        Se extrae directamente del nombre (más fiable que buscar en el texto).
        """
 
        # — Referencia desde nombre de archivo —
        ref_match = re.match(r"([A-Z]+\d+)", nombre_archivo, re.IGNORECASE)
        referencia = ref_match.group(1).upper() if ref_match else nombre_archivo.replace(".pdf", "")
 
        # — Fechas —
        fecha_entrada = self.buscar(r'ENTRADA:\s*(\d{2}/\d{2}/\d{4})', texto)
        # CORRECCIÓN: el texto real es "PAGO: dd/mm/aaaa" (con dos puntos)
        fecha_pago    = self.buscar(r'\bPAGO:\s*(\d{2}/\d{2}/\d{4})', texto)
        # Segunda fuente de fecha de pago (sección de depósito referenciado)
        if fecha_pago == "S/D":
            fecha_pago = self.buscar(r'FECHA DE PAGO:\s*(\d{2}/\d{2}/\d{4})', texto)
 
        # — Pedimento / aduana —
        pedimento = self.buscar(r'PEDIMENTO:\s*(\d[\d\s]*)', texto)
        pedimento = pedimento.replace(" ", "")   # quitar espacios internos si los hay
        aduana    = self.buscar(r'ADUANA:\s*(\d+)', texto)
        patente   = self.buscar(r'PATENTE:\s*(\d+)', texto)
 
        # — Importe —
        importe = self.buscar(r'IMPORTE PAGADO:\s*\$\s*([\d,\.]+)', texto)
 
        # — Descripción de mercancías —
        # Estructura real del PDF (PEDIMENTO COMPLETO):
        #   Línea A:  "1 30049099 99 0 0 6 45039.000 ..."  → SEC + FRACCION(8 dígitos) + datos
        #   Línea B:  "OLMETEC PLUS 20/12.5 MG 30TAB..."   → DESCRIPCIÓN
        # El patrón captura la línea B: texto alfabético inmediatamente
        # después de la línea de fracción arancelaria.
        patron_desc = re.compile(
            r'^\d+\s+\d{8}\s+[\d\s\.\,A-Z]+\n'   # línea SEC + FRACCION + datos numéricos
            r'([A-ZÁÉÍÓÚÑ][^\n]{3,})',             # línea siguiente con texto = descripción
            re.MULTILINE
        )
        descs = [d.strip() for d in patron_desc.findall(texto)
                 if not re.match(r'^[\d\s\.\,]+$', d)]   # descartar si solo tiene números
        descripcion = " / ".join(descs) if descs else "S/D"
 
        return {
            "Referencia":          referencia,
            "Pedimento":           pedimento,
            "Aduana":              aduana,
            "Patente":             patente,
            "Fecha Entrada":       fecha_entrada,
            "Fecha Pago":          fecha_pago,
            "Importe Pagado":      importe,
            "Descripcion":         descripcion,
            "Archivo":             nombre_archivo,
        }
 
    # -------------------------------------------------------------------------
    # LOOP PRINCIPAL
    # -------------------------------------------------------------------------
 
    def analizar_archivos(self):
        logger.info("🧪 Iniciando análisis de PDFs...")
 
        archivos = sorted(f for f in os.listdir(PATH_DESCARGAS) if f.lower().endswith(".pdf"))
 
        if not archivos:
            logger.warning("⚠️  No se encontraron PDFs en la carpeta de descargas.")
            return None
 
        logger.info(f"📂 {len(archivos)} archivo(s) encontrado(s).")
 
        for archivo in archivos:
            ruta = os.path.join(PATH_DESCARGAS, archivo)
            logger.info(f"📄 Analizando: {archivo}")
 
            try:
                with pdfplumber.open(ruta) as pdf:
                    texto = "\n".join(p.extract_text() or "" for p in pdf.pages)
 
                datos = self.extraer_datos(texto, archivo)
                self.resultados.append(datos)
 
                # Log rápido de los campos clave
                logger.info(
                    f"   ✔ Pedimento: {datos['Pedimento']} | "
                    f"Fecha Pago: {datos['Fecha Pago']} | "
                    f"Importe: {datos['Importe Pagado']}"
                )
 
            except Exception as e:
                logger.error(f"❌ Error analizando {archivo}: {e}")
 
        return self.generar_excel()
 
    # -------------------------------------------------------------------------
    # GENERAR EXCEL
    # -------------------------------------------------------------------------
 
    def generar_excel(self):
        if not self.resultados:
            logger.error("No se extrajeron datos de ningún PDF.")
            return None
 
        df = pd.DataFrame(self.resultados, columns=[
            "Referencia", "Pedimento", "Aduana", "Patente",
            "Fecha Entrada", "Fecha Pago", "Importe Pagado",
            "Descripcion", "Archivo"
        ])
 
        timestamp    = datetime.now().strftime("%Y%m%d_%H%M")
        nombre_excel = f"ANALISIS_LT_{timestamp}.xlsx"
        ruta_final   = os.path.join(PATH_REPORTES, nombre_excel)
 
        with pd.ExcelWriter(ruta_final, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Pedimentos")
 
            # Autoajustar ancho de columnas
            ws = writer.sheets["Pedimentos"]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
 
        logger.info(f"✅ Reporte generado: {ruta_final}")
        logger.info(f"   Filas: {len(df)} | Columnas: {len(df.columns)}")
        return df
 
 
# =============================================================================
if __name__ == "__main__":
    AnalizadorLaredo().analizar_archivos()
 
    AnalizadorLaredo().analizar_archivos()