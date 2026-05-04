import pandas as pd
import sqlalchemy as sa
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import os
import re
import zipfile
import io
import pdfplumber

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
USUARIO_WEB = "ABSOLUTE"
CONTRA_WEB = "Abs0lut3$"
FECHA_INI = "2025-12-01"
FECHA_FIN = "2026-01-31"

SQL_SERVER = "150.1.1.152"
SQL_DATABASE = "SIR"
SQL_USER = "ConsultaBD"
SQL_PASS = "5D$bc#kM&5W2T8J40?s%"
MES_VALIDACION = 2
ANIO_VALIDACION = 2026

PATH_DESCARGAS = "/home/christian/Documentos/Reportes_Aut/Descargas_ZIP"
ARCHIVO_EXCEL_FINAL = f"REPORTE_MAESTRO_{ANIO_VALIDACION}_{MES_VALIDACION:02d}.xlsx"

if not os.path.exists(PATH_DESCARGAS):
    os.makedirs(PATH_DESCARGAS)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SuperScraperCorresponsalias:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.datos_gastos_web = []

    def esperar_bloqueo(self):
        try:
            self.wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "blockUI")))
            self.wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "blockOverlay")))
            time.sleep(0.5)
        except: pass

    def safe_search(self, pattern, text, group=1):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(group).strip() if match else None

    def obtener_referencias_sql(self):
        try:
            logger.info("📡 Conectando a SQL Server...")
            conn_url = (f"mssql+pyodbc://{SQL_USER}:{SQL_PASS}@{SQL_SERVER}/{SQL_DATABASE}?"
                        f"driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes")
            engine = sa.create_engine(conn_url)
            query = f"""
                SELECT DISTINCT Referencia FROM [Admin].[SIR_VT_Sabana_Pedimento_ABC]
                WHERE (Importador LIKE '%ORGANON%' OR Importador LIKE '%UNDRA%')
                AND (Referencia LIKE 'MNS%')
                AND YEAR(CuentaG_FechaFactura) = {ANIO_VALIDACION}
                AND MONTH(CuentaG_FechaFactura) = {MES_VALIDACION}
            """
            with engine.connect() as conn:
                df_refs = pd.read_sql(sa.text(query), conn)
            return df_refs['Referencia'].tolist()
        except Exception as e:
            logger.error(f"❌ Error SQL: {e}")
            return None

    def configurar_driver(self):
        options = webdriver.FirefoxOptions()
        if self.headless: options.add_argument("--headless")
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", PATH_DESCARGAS)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip,application/pdf,application/xml,text/xml")
        self.driver = webdriver.Firefox(options=options)
        self.wait = WebDriverWait(self.driver, 25)

    def ejecutar_login_y_busqueda(self):
        logger.info("🔑 Iniciando sesión...")
        self.driver.get("https://portal.owcia.com/owcia/satoWeb/Login.html")
        self.wait.until(EC.presence_of_element_located((By.ID, "usuario"))).send_keys(USUARIO_WEB)
        self.driver.find_element(By.ID, "pass").send_keys(CONTRA_WEB)
        self.driver.find_element(By.CSS_SELECTOR, "input[value='Accesar']").click()
        
        btn_aduana = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Aduana')]")))
        self.driver.execute_script("arguments[0].click();", btn_aduana)
        self.esperar_bloqueo()
        time.sleep(2)
        
        frames = self.driver.find_elements(By.TAG_NAME, "iframe")
        if frames: self.driver.switch_to.frame(0)

        f_ini = self.wait.until(EC.presence_of_element_located((By.ID, "txtInicial")))
        self.driver.execute_script(f"arguments[0].value = '{FECHA_INI}';", f_ini)
        self.driver.execute_script(f"document.getElementById('txtFinal').value = '{FECHA_FIN}';")
        
        btn_buscar = self.driver.find_element(By.ID, "btnBuscar")
        self.driver.execute_script("arguments[0].click();", btn_buscar)
        self.esperar_bloqueo()
        time.sleep(4)

    def descargar_expedientes(self, referencias):
        for ref in referencias:
            logger.info(f"📦 Procesando Referencia: {ref}")
            try:
                xpath_img = f"//tr[.//a[contains(text(), '{ref}')]]//img[@title='Mostrar documentos']"
                self.driver.execute_script("arguments[0].click();", self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_img))))
                
                # Gastos
                btn_gastos = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'GASTOS COMPROBADOS')]")))
                self.driver.execute_script("arguments[0].click();", btn_gastos)
                time.sleep(2)
                
                filas_gastos = self.driver.find_elements(By.XPATH, "//table[@id='lstDocumentosGastos']/tbody/tr[@role='row' and not(contains(@class,'jqgfirstrow'))]")
                for fila in filas_gastos:
                    def gv(sel):
                        try: return fila.find_element(By.XPATH, f".//td[contains(@aria-describedby, '{sel}')]").get_attribute("title")
                        except: return ""
                    
                    self.datos_gastos_web.append({
                        "Referencia_Original": ref, 
                        "Proveedor_Web": gv("Proveedor"), 
                        "Factura": gv("NumeroFactura"), 
                        "UUID": gv("FolioFiscal").upper(), 
                        "Importe": str(gv("Importe")).replace(",", "").strip()
                    })
                    btn_desc = fila.find_element(By.XPATH, ".//td[@aria-describedby='lstDocumentosGastos_act']//img")
                    self.driver.execute_script("arguments[0].click();", btn_desc)
                    time.sleep(1.5)

                # Casawin
                btn_casawin = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Expediente aduanal (CASAWIN)')]")))
                self.driver.execute_script("arguments[0].click();", btn_casawin)
                time.sleep(2)
                try:
                    btn_zip = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//table[@id='lstDocumentos']//img[@title='Descargar']")))
                    self.driver.execute_script("arguments[0].click();", btn_zip)
                    time.sleep(3)
                except: pass

                self.driver.find_element(By.XPATH, "//span[contains(@class, 'ui-icon-closethick')]").click()
                time.sleep(1)
            except Exception as e:
                logger.error(f"❌ Error en {ref}: {e}")
                try: self.driver.execute_script("document.querySelector('.ui-icon-closethick').click();")
                except: pass

    def limpiar_copias(self):
        patron = re.compile(r'.*\(\d+\)\..*$')
        for f in os.listdir(PATH_DESCARGAS):
            if patron.match(f): os.remove(os.path.join(PATH_DESCARGAS, f))

    def analizar_archivos(self):
        logger.info("🧪 Iniciando escaneo profundo (XML + PDFs Casawin con Mercancías y Fecha Pago)...")
        
        info_xml = {} 
        resultados_pdf = []

        def procesar_xml_content(contenido):
            uuid = self.safe_search(r'UUID="([^"]+)"', contenido)
            emisor = self.safe_search(r'<cfdi:Emisor[^>]+Nombre="([^"]+)"', contenido)
            folio = self.safe_search(r'Folio="([^"]+)"', contenido)
            total = self.safe_search(r'Total="([\d\.]+)"', contenido)
            data = {"emisor": emisor if emisor else "S/D", "uuid": uuid if uuid else "S/D"}
            if uuid: info_xml[uuid.upper()] = data
            if folio: info_xml[folio.upper()] = data
            if total: info_xml[total] = data

        for x in [f for f in os.listdir(PATH_DESCARGAS) if f.lower().endswith('.xml')]:
            with open(os.path.join(PATH_DESCARGAS, x), 'r', encoding='utf-8', errors='ignore') as f:
                procesar_xml_content(f.read())

        zips = [f for f in os.listdir(PATH_DESCARGAS) if f.lower().endswith('.zip')]
        for z_name in zips:
            base = z_name.replace(".zip", "")
            partes = base.split("-")
            if len(partes) >= 2 and partes[1].endswith('0'): partes[1] = partes[1][:-1]
            target_pdf = "-".join(partes)

            try:
                with zipfile.ZipFile(os.path.join(PATH_DESCARGAS, z_name), 'r') as z:
                    pdf_in = next((f for f in z.namelist() if target_pdf in f and f.endswith('.pdf')), None)
                    
                    for f_int in z.namelist():
                        if f_int.lower().endswith('.xml'):
                            with z.open(f_int) as fx:
                                procesar_xml_content(fx.read().decode('utf-8', errors='ignore'))

                    if pdf_in:
                        with z.open(pdf_in) as f_pdf:
                            with pdfplumber.open(io.BytesIO(f_pdf.read())) as pdf:
                                texto = "\n".join([p.extract_text() or "" for p in pdf.pages])
                        
                        ref_limpia = self.safe_search(r'REF:\s*([A-Z]+\d+)', texto)
                        
                        # --- NUEVA EXTRACCIÓN: FECHA DE PAGO ---
                        # Busca la sección de PAGO y extrae la fecha dd/mm/aaaa
                        fecha_pago = self.safe_search(r'PAGO\s+(\d{2}/\d{2}/\d{4})', texto)
                        
                        patron_desc = re.compile(r'\d{3}\s+\d{8}\s+.*?\n\s*(.*?)\n', re.MULTILINE)
                        descs = patron_desc.findall(texto)
                        
                        resultados_pdf.append({
                            "Referencia_PDF": ref_limpia.upper() if ref_limpia else None,
                            "Pedimento": self.safe_search(r'NUM\. PEDIMENTO:\s*([\d\s]+)', texto).replace(" ", ""),
                            "Fecha_Pago_PDF": fecha_pago if fecha_pago else "S/D",
                            "Descripcion_Consolidada": " / ".join([d.strip() for d in descs]) if descs else "S/D"
                        })
            except Exception as e:
                logger.error(f"Error analizando ZIP {z_name}: {e}")

        if not self.datos_gastos_web: return
        df_gastos = pd.DataFrame(self.datos_gastos_web)
        df_pdf = pd.DataFrame(resultados_pdf)

        def cruce_xml(row):
            u_w, f_w, i_w = str(row['UUID']).upper(), str(row['Factura']).upper(), str(row['Importe'])
            res = info_xml.get(u_w) or info_xml.get(f_w) or info_xml.get(i_w)
            return pd.Series([res['emisor'] if res else "S/D", res['uuid'] if res else u_w])

        df_gastos[['Emisor_fac', 'UUID_Real']] = df_gastos.apply(cruce_xml, axis=1)

        if not df_pdf.empty:
            df_final = pd.merge(df_gastos, df_pdf, left_on="Referencia_Original", right_on="Referencia_PDF", how="left")
        else:
            df_final = df_gastos

        # Organizar Columnas incluyendo la Fecha de Pago
        cols = ['Referencia_Original', 'Pedimento', 'Fecha_Pago_PDF', 'Proveedor_Web', 'Emisor_fac', 'Factura', 'Importe', 'Descripcion_Consolidada', 'UUID_Real']
        df_final = df_final[[c for c in cols if c in df_final.columns]].drop_duplicates()
        df_final.rename(columns={'UUID_Real': 'UUID', 'Fecha_Pago_PDF': 'Fecha de Pago'}, inplace=True)
        
        df_final.to_excel(ARCHIVO_EXCEL_FINAL, index=False)
        logger.info(f"✅ ¡LISTO! Reporte generado con Fecha de Pago: {ARCHIVO_EXCEL_FINAL}")

    def ejecutar(self):
        refs = self.obtener_referencias_sql()
        
        if refs is None:
            logger.error("❌ No fue posible obtener referencias desde SQL.")
            return None

        if not refs:
            print("No hay Referencias de Manzanillo este mes")
            logger.info("Terminando script porque no hay referencias de Manzanillo en el periodo.")
            return False

        try:
            self.configurar_driver()
            self.ejecutar_login_y_busqueda()
            self.descargar_expedientes(refs)
            self.driver.quit()
            self.driver = None
            self.limpiar_copias()
            self.analizar_archivos()
            return True
        except Exception:
            raise
        finally:
            if self.driver is not None:
                self.driver.quit()
                self.driver = None
            logger.info("🎉 Proceso Finalizado.")

if __name__ == "__main__":
    SuperScraperCorresponsalias(headless=False).ejecutar()
