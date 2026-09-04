import smtplib
import os
from email.message import EmailMessage
import mimetypes
from datetime import datetime, timedelta

# --- LÓGICA DE FECHAS AUTOMÁTICA ---
# Obtenemos el primer día del mes actual y restamos un día para llegar al mes anterior
hoy = datetime.now()
primer_dia_mes_actual = hoy.replace(day=1)
fecha_mes_pasado = primer_dia_mes_actual - timedelta(days=1)

# Configuración de nombres de meses en español
meses_es = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

MES_TEXTO = meses_es[fecha_mes_pasado.month]
MES_NUMERO = fecha_mes_pasado.strftime("%m") # Ejemplo: "03" si es marzo
ANIO = fecha_mes_pasado.strftime("%Y")

# --- CONFIGURACIÓN DE CORREO ---
SMTP_SERVER = "smtp.gmail.com" 
SMTP_PORT = 465
EMAIL_USER = "reportes.bi@abcsc.mx"
EMAIL_PASS = "jwvjdrvmprzrwzxy" 

# --- LISTAS DE CONTACTOS ---
PARA = ["daniel.alvarado2@organon.com", "maria.solano@organon.com", "angela.cristina.jimenez@organon.com","brayan.perez@organon.com","andrea.huerta@organon.com","dilan.lagunas@organon.com","martha.laura.gonzalez@organon.com"]
#PARA = ["ccarbajal@abcsc.mx"]
CC = ["imedrano@abcsc.mx", "atrujillo@abcsc.mx","administracion2@abcsc.mx"]
#CCO = ["facturacion2@abcsc.mx"]
CCO = ["ccarbajal@abcsc.mx","facturacion2@abcsc.mx"]

# --- RUTAS Y ASUNTO DINÁMICOS ---
ASUNTO = f"REPORTE DE ORGANON Y UNDRA - {MES_TEXTO} {ANIO}"
# Se construye la ruta usando MES_NUMERO (ej: Reporte_organon_03.xlsx)
RUTA_ARCHIVO = f"/home/christian/Documentos/Reportes_Aut/Reporte_organon_{MES_NUMERO}.xlsx"

def enviar_correo_pro():
    if not os.path.exists(RUTA_ARCHIVO):
        print(f"❌ Error: No se encuentra el archivo {RUTA_ARCHIVO}")
        return

    msg = EmailMessage()
    msg['Subject'] = ASUNTO
    msg['From'] = EMAIL_USER
    msg['To'] = ", ".join(PARA)
    msg['Cc'] = ", ".join(CC)

    # Cuerpo del mensaje con f-string para insertar el mes y año automáticamente
    msg.set_content(f""" 
Hola, buen día.

Les adjunto el reporte de Organon generado de manera automática.

Se adjunta el Reporte Aduanal de Organon correspondiente al mes de {MES_TEXTO} {ANIO}.
El archivo ya incluye la separación por pestañas de cada referencia y la validación de datos.

Quedamos a su disposición para cualquier duda.

Saludos,
Automatización ABC
    """)

    # Adjuntar archivo
    ctype, encoding = mimetypes.guess_type(RUTA_ARCHIVO)
    maintype, subtype = (ctype or 'application/octet-stream').split('/', 1)

    with open(RUTA_ARCHIVO, 'rb') as f:
        msg.add_attachment(
            f.read(),
            maintype=maintype,
            subtype=subtype,
            filename=os.path.basename(RUTA_ARCHIVO)
        )

    todos_los_destinatarios = PARA + CC + CCO

    try:
        print(f"🔗 Conectando y enviando reporte de {MES_TEXTO}...")
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg, to_addrs=todos_los_destinatarios)
        print(f"✅ Reporte de {MES_TEXTO} enviado con éxito.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    enviar_correo_pro()