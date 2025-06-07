import streamlit as st
from PIL import Image
import requests
import io
import pandas as pd
import re

API_KEY = "K84668714088957"  # Reemplaza con tu clave de OCR.space

# --- Función para enviar imagen a OCR.space ---
def ocr_space_api(imagen_bytes):
    url_api = "https://api.ocr.space/parse/image"
    archivos = {
        'filename': ('imagen.jpg', imagen_bytes, 'image/jpeg'),
    }
    datos = {
        'apikey': API_KEY,
        'language': 'spa',
        'isOverlayRequired': False
    }
    respuesta = requests.post(url_api, files=archivos, data=datos)
    resultado = respuesta.json()
    if resultado.get("IsErroredOnProcessing"):
        raise Exception(resultado.get("ErrorMessage", ["Error desconocido en OCR"])[0])
    texto = resultado['ParsedResults'][0]['ParsedText']
    return texto

# --- Función para extraer datos del texto OCR ---
def extraer_datos_clave(texto):
    def buscar_patron(patrones):
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    return {
        "Fecha y hora de salida": buscar_patron([r"(?:salida.*?)[:\-]\s*(\S.+)", r"FECHA.*?SALIDA.*?[:\-]?\s*(\S.+)"]),
        "Placa del cabeza tractora": buscar_patron([r"placa.*?cabeza.*?[:\-]?\s*([A-Z0-9\-]+)"]),
        "Placa del tanque": buscar_patron([r"placa.*?tanque.*?[:\-]?\s*([A-Z0-9\-]+)"]),
        "Número de guía": buscar_patron([r"gu[ií]a.*?[:\-]?\s*([A-Z0-9\-]+)"]),
        "Empresa transportadora": buscar_patron([r"empresa transportadora\s*[:\-]?\s*(.*)"]),
        "Cédula": buscar_patron([r"c[eé]dula.*?[:\-]?\s*([0-9\.]+)"]),
        "Conductor": buscar_patron([r"(?:nombre del conductor|conductor)\s*[:\-]?\s*([A-ZÑÁÉÍÓÚ ]{5,})"]),
        "Casilla en blanco": "",
        "Lugar de origen": buscar_patron([r"lugar de origen\s*[:\-]?\s*(.*)"]),
        "Lugar de destino": buscar_patron([r"lugar de destino\s*[:\-]?\s*(.*)"]),
        "Barriles brutos": buscar_patron([r"brutos\s*[:\-]?\s*([\d.,]+)"]),
        "Barriles netos": buscar_patron([r"netos\s*[:\-]?\s*([\d.,]+)"]),
        "Barriles a 60°F": buscar_patron([r"60\s*°\s*f\s*[:\-]?\s*([\d.,]+)"]),
        "API": buscar_patron([r"\bAPI\b\s*[:\-]?\s*([\d.,]+)"]),
        "BSW (%)": buscar_patron([r"\bBSW\b.*?%?\s*[:\-]?\s*([\d.,]+)"]),
        "Vigencia de guía": buscar_patron([r"(?:horas de vigencia|vigencia)\s*[:\-]?\s*([\d]+)\s*horas?"]),
        "Casilla vacía 1": "",
        "Casilla vacía 2": "",
        "Casilla vacía 3": "",
        "Casilla vacía 4": "",
        "Casilla vacía 5": "",
        "Casilla vacía 6": "",
        "Sellos": buscar_patron([r"(?:sello|sellos)\s*[:\-]?\s*(.*)"]),
    }

# --- INTERFAZ CON STREAMLIT ---
st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("📄 Extracción Inteligente de Guías - OCR")

archivo_subido = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if archivo_subido:
    imagen = Image.open(archivo_subido)

    # Reducción de tamaño si supera 1MB
    buf_original = io.BytesIO()
    imagen.save(buf_original, format='JPEG', quality=70, optimize=True)
    imagen_bytes = buf_original.getvalue()

    if len(imagen_bytes) > 1024 * 1024:
        escala = 1024 * 1024 / len(imagen_bytes)
        nueva_ancho = int(imagen.width * escala**0.5)
        nueva_alto = int(imagen.height * escala**0.5)
        imagen = imagen.resize((nueva_ancho, nueva_alto), Image.Resampling.LANCZOS)
        buf_reducido = io.BytesIO()
        imagen.save(buf_reducido, format='JPEG', quality=70)
        imagen_bytes = buf_reducido.getvalue()

    st.image(imagen, caption="Imagen cargada", use_container_width=True)

    with st.spinner("Procesando imagen con OCR..."):
        try:
            texto_ocr = ocr_space_api(imagen_bytes)

            st.subheader("📝 Texto completo del OCR")
            st.text_area("Texto detectado por OCR", texto_ocr, height=400)

            if st.button("📥 Extraer datos estructurados"):
                datos = extraer_datos_clave(texto_ocr)
                st.subheader("📋 Datos extraídos")
                st.json(datos)

        except Exception as e:
            st.error(f"No se pudo procesar la imagen OCR: {e}")
