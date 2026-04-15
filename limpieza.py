import os
import shutil
import logging

# --- CONFIGURACIÓN DE LAS RUTAS ---
PATH_DESCARGAS_ZIP = "/home/christian/Documentos/Reportes_Aut/Descargas_ZIP"
PATH_DESCARGAS_LT = "/home/christian/Documentos/Reportes_Aut/Descargas_LT"

# Configurar logging para ver qué está pasando
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def limpiar_carpeta_descargas(ruta):
    if not os.path.exists(ruta):
        logger.warning(f"⚠️ La ruta no existe: {ruta}")
        return

    logger.info(f"🧹 Iniciando limpieza de: {ruta}")
    
    contador = 0
    for nombre_archivo in os.listdir(ruta):
        ruta_completa = os.path.join(ruta, nombre_archivo)
        try:
            # Si es un archivo o un enlace simbólico, se elimina
            if os.path.isfile(ruta_completa) or os.path.islink(ruta_completa):
                os.unlink(ruta_completa)
                contador += 1
            # Si es una carpeta, se elimina con todo su contenido
            elif os.path.isdir(ruta_completa):
                shutil.rmtree(ruta_completa)
                contador += 1
        except Exception as e:
            logger.error(f"❌ No se pudo eliminar {ruta_completa}. Motivo: {e}")

    logger.info(f"✨ Limpieza completada en {ruta}. Se eliminaron {contador} elementos.")

if __name__ == "__main__":
    # Ejecutamos la limpieza para ambas carpetas
    limpiar_carpeta_descargas(PATH_DESCARGAS_ZIP)
    limpiar_carpeta_descargas(PATH_DESCARGAS_LT)