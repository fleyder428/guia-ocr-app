import streamlit as st
import requests
import base64
import json
import io
from PIL import Image
import re

# ---- CONFIG ----
OCR_SPACE_API_KEY = 'K84668714088957'
OCR_SPACE_URL = 'https://api.ocr.space/parse/image'

# ---- FUNCIONES ----
def comprimir_imagen(imagen, calidad=30):
    imagen_io = io.BytesIO()
    imagen.save(imagen_io, format='JPEG', quality=calidad)
    imagen_io.seek(0)
    return imagen_io

def subir_a_ocr_space(imagen_bytes):
    response = requests.post(
        OCR_SPACE_URL,
        files={"file": ("imagen.jpg", imagen_bytes)},
        data={"apikey": OCR_SPACE_API_KEY, "language": "spa"}
    )
    return response.json()

def extraer_datos_guia(texto):
    def buscar(patron, default=""):
        match = re.search(patron, texto, re.IGNORECASE)
        return match.group(1).strip() if match else default

    datos = {
        "Fecha y hora de salida": buscar(r"FECHA Y HORA DE SALIDA\s*(\d{1,2}[:.]\d{2})", ""),
        "Placa del cabeza tractora": buscar(r"PLACAS DEL CABEZOTE\s*(\w+)", ""),
        "Placa del tanque": buscar(r"PLACAS DEL TANQUE\s*(\w+)", ""),
        "Número de guía": buscar(r"\b(\d{3,6})\b", ""),
        "Empresa transportadora": buscar(r"EMPRESA TRANSPORTADORA\s*([\w!¡]+)", ""),
        "Cédula": buscar(r"C[ÉE]DULA\s*(\d+)", ""),
        "Conductor": buscar(r"CONDUCTOR\s*([A-ZÁÉÍÓÚÑ\s]+)", ""),
        "Casilla vacía 1": "",
        "Lugar de origen": buscar(r"LUGAR DE ORIGEN\s*(.+)", ""),
        "Lugar de destino": buscar(r"LUGAR DE DESTINO\s*(.+)", ""),
        "Barriles brutos": buscar(r"BARRILES.*?(\d{2,4}[.,]\d{2})", ""),
        "Barriles netos": buscar(r"NETOS\s*(\d{2,4}[.,]\d{2})", ""),
        "Barriles a 60°F": buscar(r"@\s*6C?F\s*(\d{2,4}[.,]\d{2})", ""),
        "API": buscar(r"API\s*[:\-]?\s*([\d.]+)", ""),
        "BSW (%)": buscar(r"BSW.*?([\d.,]+)%", ""),
        "Vigencia de guía": buscar(r"HORAS DE VIGENCIA\s*(\d+\s*HORAS?)", ""),
        "Casilla vacía 2": "",
        "Casilla vacía 3": "",
        "Casilla vacía 4": "",
        "Casilla vacía 5": "",
        "Casilla vacía 6": "",
        "Sellos": buscar(r"SELLOS\s*[:\-]?\s*(.*)", "")
    }
    return datos

# ---- INTERFAZ ----
st.title("🧾 Extracción de Guía con OCR.space")

imagen_subida = st.file_uploader("Sube la imagen de la guía (máx. 1MB sin comprimir)", type=["jpg", "jpeg", "png"])

if imagen_subida:
    imagen = Image.open(imagen_subida).convert("RGB")
    imagen_comprimida = comprimir_imagen(imagen, calidad=30)

    with st.spinner("Analizando con OCR.space..."):
        resultado = subir_a_ocr_space(imagen_comprimida)

    if resultado.get("IsErroredOnProcessing"):
        st.error("❌ Error en el procesamiento OCR: " + ", ".join(resultado.get("ErrorMessage", [])))
    else:
        texto_crudo = resultado['ParsedResults'][0]['ParsedText']
        st.text_area("🧪 Resultado crudo del OCR:", texto_crudo, height=200)

        datos_extraidos = extraer_datos_guia(texto_crudo)
        st.success("✅ Datos extraídos:")
        for campo, valor in datos_extraidos.items():
            st.write(f"**{campo}:** {valor}")

        # Botón para exportar a Excel si se desea agregar
        # pd.DataFrame([datos_extraidos]).to_excel("guia_extraida.xlsx", index=False)
        # st.download_button("📥 Descargar Excel", data=open("guia_extraida.xlsx", "rb"), file_name="guia.xlsx")
