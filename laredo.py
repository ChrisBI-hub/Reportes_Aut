"""
laredo.py
=========
Descarga el PDF "PEDIMENTO COMPLETO" de cada referencia LT
desde SLAM.Digital.
 
Estrategia de descarga:
  1. Navegar a ConsultaRefGrupo.aspx?...&ref=LT...
  2. Localizar el <a> del bloque "PEDIMENTO COMPLETO"
  3. Abrir VisorB.aspx con Selenium  ← genera el PDF en /tmp/ del servidor
  4. Extraer la URL /tmp/{id}.pdf del botón "Abrir" dentro del Visor
  5. Descargar el PDF con requests reutilizando cookies actualizadas de Selenium
 
Dependencias:
    pip install selenium sqlalchemy pyodbc pandas requests
    GeckoDriver: sudo apt install firefox-esr geckodriver
"""
 
import os
import time
import logging
import requests
import pandas as pd
import sqlalchemy as sa
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
 
# =============================================================================
# CONFIGURACIÓN GENERAL  —  modificar aquí cada mes
# =============================================================================
 
USUARIO_WEB = "ORGA26*"
CONTRA_WEB  = "ORGA26*"
URL_LOGIN   = "https://slamnldo.alvelais.mx/slamdigital4/default.aspx"
URL_BASE    = "http://slamnldo.alvelais.mx/slamdigital4"
 
MES_VALIDACION  = 2
ANIO_VALIDACION = 2026
 
SQL_SERVER   = "150.1.1.152"
SQL_DATABASE = "SIR"
SQL_USER     = "ConsultaBD"
SQL_PASS     = "5D$bc#kM&5W2T8J40?s%"
 
PATH_DESCARGAS = "/home/christian/Documentos/Reportes_Aut/Descargas_LT"
 
# =============================================================================
# SETUP
# =============================================================================
 
os.makedirs(PATH_DESCARGAS, exist_ok=True)
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
 
 
# =============================================================================
# CLASE PRINCIPAL
# =============================================================================
 
class LaredoExtractor:
 
    def __init__(self):
        self.driver  = None
        self.wait    = None
        self.uid     = None
        self.perfil  = None
        self.session = requests.Session()
 
    # -------------------------------------------------------------------------
    # DRIVER
    # -------------------------------------------------------------------------
 
    def configurar_driver(self):
        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", PATH_DESCARGAS)
        options.set_preference(
            "browser.helperApps.neverAsk.saveToDisk",
            "application/pdf,application/zip,application/octet-stream"
        )
        options.set_preference("pdfjs.disabled", True)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        self.driver = webdriver.Firefox(options=options)
        self.wait   = WebDriverWait(self.driver, 35)
        logger.info("🦊 Firefox iniciado.")
 
    # -------------------------------------------------------------------------
    # FASE 1 — SQL
    # -------------------------------------------------------------------------
 
    def obtener_referencias_desde_sql(self) -> list[str]:
        try:
            logger.info(f"📡 Consultando SQL — periodo: {MES_VALIDACION}/{ANIO_VALIDACION}")
            conn_url = (
                f"mssql+pyodbc://{SQL_USER}:{SQL_PASS}@{SQL_SERVER}/{SQL_DATABASE}?"
                f"driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
            )
            engine = sa.create_engine(conn_url)
            query  = f"""
                SELECT DISTINCT Referencia FROM [Admin].[SIR_VT_Sabana_Pedimento_ABC]
                WHERE (Importador LIKE '%ORGANON%' OR Importador LIKE '%UNDRA%')
                  AND (Referencia LIKE 'MNS%' OR Referencia LIKE 'LT%')
                  AND YEAR(CuentaG_FechaFactura)  = {ANIO_VALIDACION}
                  AND MONTH(CuentaG_FechaFactura) = {MES_VALIDACION}
            """
            with engine.connect() as conn:
                df = pd.read_sql(sa.text(query), conn)
 
            lista = df["Referencia"].tolist()
            logger.info(f"✅ {len(lista)} referencia(s) encontrada(s): {lista}")
            return lista
 
        except Exception as e:
            logger.error(f"❌ Error SQL: {e}")
            return []
 
    # -------------------------------------------------------------------------
    # FASE 2 — LOGIN + PARÁMETROS DE SESIÓN
    # -------------------------------------------------------------------------
 
    def ejecutar_login(self):
        logger.info("🔑 Iniciando sesión en SLAM.Digital...")
        self.driver.get(URL_LOGIN)
        self.wait.until(EC.presence_of_element_located((By.ID, "uname"))).send_keys(USUARIO_WEB)
        campo_pass = self.driver.find_element(By.ID, "unamep")
        campo_pass.send_keys(CONTRA_WEB)
        campo_pass.send_keys(Keys.ENTER)
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "navbar-brand")))
        logger.info("✅ Login exitoso.")
 
    def leer_parametros_sesion(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, "txtarg4")))
        except Exception:
            self.driver.get(f"{URL_BASE}/Defaultb.aspx")
            self.wait.until(EC.presence_of_element_located((By.ID, "txtarg4")))
 
        self.uid    = self.driver.find_element(By.ID, "txtarg4").get_attribute("value")
        self.perfil = self.driver.find_element(By.ID, "txtarg7").get_attribute("value")
        logger.info(f"🔑 Sesión — uid: {self.uid} | perfil: {self.perfil}")
 
    def sincronizar_cookies(self):
        """
        Vuelca las cookies actuales del navegador a la sesión de requests.
        Se llama justo antes de cada descarga para que las cookies estén frescas.
        """
        self.session.cookies.clear()
        for cookie in self.driver.get_cookies():
            self.session.cookies.set(cookie["name"], cookie["value"])
 
    # -------------------------------------------------------------------------
    # FASE 3 — PROCESAR UNA REFERENCIA
    # -------------------------------------------------------------------------
 
    def obtener_visor_href(self, ref: str) -> str | None:
        """
        Navega a la página de resultados de la referencia y localiza
        el href a VisorB.aspx del bloque 'PEDIMENTO COMPLETO'.
        """
        token   = "AutoScriptABC1234"
        url_ref = (
            f"{URL_BASE}/ConsultaRefGrupo.aspx"
            f"?token={token}&ref={ref}&p={self.perfil}&uid={self.uid}"
        )
        logger.info(f"   [{ref}] Cargando página de resultados...")
        self.driver.get(url_ref)
 
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[normalize-space()='PEDIMENTO COMPLETO']")
                )
            )
        except Exception:
            logger.warning(f"   [{ref}] ⚠ 'PEDIMENTO COMPLETO' no apareció.")
            return None
 
        try:
            enlace = self.driver.find_element(
                By.XPATH,
                "//span[normalize-space()='PEDIMENTO COMPLETO']"
                "/ancestor::div[contains(@class,'G000')]"
                "//a[contains(@href,'VisorB.aspx')]"
            )
            href = enlace.get_attribute("href")
            logger.info(f"   [{ref}] VisorB href: {href}")
            return href
        except Exception:
            logger.error(f"   [{ref}] ❌ No se encontró el enlace VisorB.")
            return None
 
    def abrir_visor_y_obtener_url_pdf(self, ref: str, visor_href: str) -> str | None:
        """
        Abre VisorB.aspx en una nueva pestaña.
        Esto obliga al servidor a generar el PDF en /tmp/.
        Luego extrae la URL del botón 'Abrir' (el enlace directo al PDF).
 
        HTML del botón Abrir:
            <a href="http://.../slamdigital4/tmp/{id}.pdf" target="_blank" class="btn btn-info">
                <span>Abrir</span>
            </a>
        """
        # Abre VisorB en nueva pestaña para no perder la página de referencia
        self.driver.execute_script("window.open(arguments[0], '_visor');", visor_href)
 
        # Cambiar foco a la nueva pestaña
        self.driver.switch_to.window(self.driver.window_handles[-1])
 
        try:
            # Esperar a que aparezca el botón "Abrir" con la URL del PDF
            btn_abrir = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(@class,'btn-info') and .//span[text()='Abrir']]")
                )
            )
            url_pdf = btn_abrir.get_attribute("href")
            logger.info(f"   [{ref}] PDF generado en: {url_pdf}")
            return url_pdf
 
        except Exception:
            logger.error(f"   [{ref}] ❌ No se encontró el botón 'Abrir' en VisorB.")
            return None
 
        finally:
            # Cerrar la pestaña del visor y volver a la pestaña principal
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
 
    def descargar_pdf(self, ref: str, url_pdf: str) -> bool:
        """
        Descarga el PDF con requests usando las cookies actuales del navegador.
        Guarda como {ref}_PEDIMENTO_COMPLETO.pdf
        """
        destino = os.path.join(PATH_DESCARGAS, f"{ref}_PEDIMENTO_COMPLETO.pdf")
 
        # Sincronizar cookies justo antes de descargar
        self.sincronizar_cookies()
 
        try:
            logger.info(f"   [{ref}] Descargando PDF...")
            resp = self.session.get(url_pdf, timeout=60, stream=True)
            resp.raise_for_status()
 
            # Verificar que la respuesta realmente es un PDF
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" not in content_type and "octet" not in content_type:
                logger.error(
                    f"   [{ref}] ❌ Respuesta inesperada ({content_type}). "
                    f"Posible redirección al login — las cookies pueden haber expirado."
                )
                return False
 
            with open(destino, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
 
            tamanio_kb = os.path.getsize(destino) / 1024
            logger.info(f"   [{ref}] ✅ Guardado: {destino} ({tamanio_kb:.1f} KB)")
            return True
 
        except Exception as e:
            logger.error(f"   [{ref}] ❌ Error al descargar: {e}")
            return False
 
    def procesar_referencia(self, ref: str):
        try:
            # Paso A: obtener href de VisorB desde la página de resultados
            visor_href = self.obtener_visor_href(ref)
            if not visor_href:
                logger.warning(f"   [{ref}] Sin enlace VisorB. Se omite.")
                return
 
            # Paso B: abrir VisorB → el servidor genera el PDF → extraer URL
            url_pdf = self.abrir_visor_y_obtener_url_pdf(ref, visor_href)
            if not url_pdf:
                logger.warning(f"   [{ref}] Sin URL de PDF. Se omite.")
                return
 
            # Paso C: descargar el PDF con requests + cookies frescas
            self.descargar_pdf(ref, url_pdf)
 
        except Exception as e:
            logger.error(f"⚠️  Error procesando [{ref}]: {e}")
            # Cerrar pestañas extra si quedaron abiertas
            while len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            time.sleep(2)
 
    # -------------------------------------------------------------------------
    # EJECUCIÓN MAESTRA
    # -------------------------------------------------------------------------
 
    def ejecutar(self):
        referencias = self.obtener_referencias_desde_sql()
        if not referencias:
            logger.warning("⚠️  Sin referencias para el periodo. Abortando.")
            return
 
        self.configurar_driver()
 
        try:
            self.ejecutar_login()
            self.leer_parametros_sesion()
 
            total = len(referencias)
            for i, ref in enumerate(referencias, start=1):
                logger.info(f"\n{'='*55}")
                logger.info(f"  [{i}/{total}]  {ref}")
                logger.info(f"{'='*55}")
                self.procesar_referencia(ref)
 
            logger.info("\n🎉 Todas las referencias procesadas.")
 
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🏁 Firefox cerrado.")
 
 
# =============================================================================
if __name__ == "__main__":
    LaredoExtractor().ejecutar()