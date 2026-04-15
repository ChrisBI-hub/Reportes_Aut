import smtplib
import os
import mimetypes
from email.message import EmailMessage
from datetime import datetime, timedelta

# --- LÓGICA DE FECHAS AUTOMÁTICA ---
# Calculamos el mes pasado basándonos en la fecha actual
hoy = datetime.now()
# Retrocedemos al mes anterior (yendo al día 1 del actual y restando un día)
fecha_mes_pasado = hoy.replace(day=1) - timedelta(days=1)

# Diccionario para nombres en español
meses_es = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

MES_NOMBRE = meses_es[fecha_mes_pasado.month]
MES_DIGITOS = fecha_mes_pasado.strftime("%m")  # Ejemplo: "03"
ANIO = fecha_mes_pasado.strftime("%Y")

# --- CONFIGURACIÓN DE CORREO ---
SMTP_SERVER = "smtp.gmail.com" 
SMTP_PORT = 465
EMAIL_USER = "reportes.bi@abcsc.mx"
EMAIL_PASS = "jwvjdrvmprzrwzxy" 

# --- CONFIGURACIÓN DEL REPORTE (DINÁMICA) ---
# Ahora la ruta se construye sola: /.../Reporte_organon_03.xlsx
RUTA_ARCHIVO = f"/home/christian/Documentos/Reportes_Aut/Reporte_organon_{MES_DIGITOS}.xlsx"

# --- DESTINATARIOS ---
PARA = ["facturacion2@abcsc.mx"]
CC = ["ymontoya@abcsc.mx"]
CCO = ["administracion2@abcsc.mx", "ccarbajal@abcsc.mx"]

ASUNTO = f"Reporte Aduanal Organon - {MES_NOMBRE} {ANIO}"

def enviar_correo_pro():
    # 1. Validar existencia del archivo
    if not os.path.exists(RUTA_ARCHIVO):
        print(f"❌ Error: No se encuentra el archivo {RUTA_ARCHIVO}")
        return

    # 2. Crear el objeto del mensaje
    msg = EmailMessage()
    msg['Subject'] = ASUNTO
    msg['From'] = EMAIL_USER
    msg['To'] = ", ".join(PARA)
    msg['Cc'] = ", ".join(CC)
    
    # Cuerpo del mensaje dinámico
    cuerpo_texto = f"""
Hola, buen día.

Te envío el archivo de Organon correspondiente a {MES_NOMBRE} {ANIO} para tu revisión, Claudia. 
Por favor, confírmame su recepción. En cuanto tengas comentarios sobre modificaciones o posibles errores, házmelo saber. 
Estaré en completa disposición de hacer los cambios necesarios antes de enviarlo al cliente.

Saludos,
Equipo de Automatización ABC
    """
    msg.set_content(cuerpo_texto)

    # 3. Adjuntar archivo
    print(f"📎 Adjuntando: {os.path.basename(RUTA_ARCHIVO)}...")
    ctype, encoding = mimetypes.guess_type(RUTA_ARCHIVO)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)

    with open(RUTA_ARCHIVO, 'rb') as f:
        msg.add_attachment(
            f.read(),
            maintype=maintype,
            subtype=subtype,
            filename=os.path.basename(RUTA_ARCHIVO)
        )

    # 4. Enviar correo
    destinatarios_reales = PARA + CC + CCO

    try:
        print(f"🔗 Conectando a {SMTP_SERVER} para enviar reporte de {MES_NOMBRE}...")
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg, to_addrs=destinatarios_reales)
            
        print(f"✅ ¡Reporte de {MES_NOMBRE} enviado con éxito!")
        print(f"📩 Destinatarios: {len(PARA)} principal(es), {len(CC)} en copia y {len(CCO)} ocultos.")
        
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")

if __name__ == "__main__":
    enviar_correo_pro()