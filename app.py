import streamlit as st
from PIL import Image
import requests
import io
import pandas as pd
import re

API_KEY = "K84668714088957"  # Tu clave API de OCR.space

# 🔍 Función que envía la imagen a OCR.space
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

# 🔎 Extrae datos clave del texto OCR con casillas en blanco y orden requerido
def extraer_datos_clave(texto):
    def buscar_patron(patrones):
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                valor = match.group(1).strip()
                valor = re.sub(r"[\n\r\t]+", "", valor)
                return valor
        return ""

    datos = {
        "Fecha y hora de salida": buscar_patron([r"(?:salida.*?)[:\-]\s*(\S.+)", r"FECHA.*?SALIDA.*?[:\-]?\s*(\S.+)"]),
        "Placa del cabeza tractora": buscar_patron([r"placa.*?cabeza.*?[:\-]?\s*([A-Z0-9\-]+)"]),
        "Placa del tanque": buscar_patron([r"placa.*?tanque.*?[:\-]?\s*([A-Z0-9\-]+)"]),
        "Número de guía": buscar_patron([r"gu[ií]a.*?[:\-]?\s*([A-Z0-9\-]+)"]),
        "Empresa transportadora": buscar_patron([r"empresa transportadora\s*[:\-]?\s*(.*)"]),
        "Cédula": buscar_patron([r"c[eé]dula.*?[:\-]?\s*([0-9\.]+)"]),
        "Conductor": buscar_patron([r"(?:nombre del conductor|conductor)\s*[:\-]?\s*([A-ZÑÁÉÍÓÚ ]{5,})"]),
        # Casilla en blanco tras Conductor
        "Casilla en blanco 1": "",
        "Lugar de origen": buscar_patron([r"lugar de origen\s*[:\-]?\s*(.*)"]),
        "Lugar de destino": buscar_patron([r"lugar de destino\s*[:\-]?\s*(.*)"]),
        "Barriles brutos": buscar_patron([r"brutos\s*[:\-]?\s*([\d.,]+)"]),
        "Barriles netos": buscar_patron([r"netos\s*[:\-]?\s*([\d.,]+)"]),
        "Barriles a 60°F": buscar_patron([r"60\s*°\s*f\s*[:\-]?\s*([\d.,]+)"]),
        "API": buscar_patron([r"\bAPI\b\s*[:\-]?\s*([\d.,]+)"]),
        "BSW (%)": buscar_patron([r"\bBSW\b.*?%?\s*[:\-]?\s*([\d.,]+)"]),
        "Vigencia de guía": buscar_patron([r"(?:horas de vigencia|vigencia)\s*[:\-]?\s*([\d]+)\s*horas?"]),
        # Seis casillas en blanco después de Vigencia de guía
        "Casilla en blanco 2": "",
        "Casilla en blanco 3": "",
        "Casilla en blanco 4": "",
        "Casilla en blanco 5": "",
        "Casilla en blanco 6": "",
        "Casilla en blanco 7": "",
        "Sellos": buscar_patron([r"(?:sello|sellos)\s*[:\-]?\s*(.*)"]),
    }

    # Por si alguno quedó None
    for clave in datos:
        if datos[clave] is None:
            datos[clave] = ""

    return datos


# 🎯 Streamlit UI
st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("📄 Extracción Inteligente de Guías - OCR")

archivo_subido = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if archivo_subido:
    imagen = Image.open(archivo_subido)

    # Reducir tamaño si pasa de 1MB
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

    if st.button("🔍 Extraer datos"):
        with st.spinner("Procesando con OCR.space..."):
            try:
                texto_ocr = ocr_space_api(imagen_bytes)
                datos = extraer_datos_clave(texto_ocr)

                columnas_ordenadas = [
                    "Fecha y hora de salida",
                    "Placa del cabeza tractora",
                    "Placa del tanque",
                    "Número de guía",
                    "Empresa transportadora",
                    "Cédula",
                    "Conductor",
                    "Casilla en blanco 1",
                    "Lugar de origen",
                    "Lugar de destino",
                    "Barriles brutos",
                    "Barriles netos",
                    "Barriles a 60°F",
                    "API",
                    "BSW (%)",
                    "Vigencia de guía",
                    "Casilla en blanco 2",
                    "Casilla en blanco 3",
                    "Casilla en blanco 4",
                    "Casilla en blanco 5",
                    "Casilla en blanco 6",
                    "Casilla en blanco 7",
                    "Sellos"
                ]

                df = pd.DataFrame([datos])
                df = df.reindex(columns=columnas_ordenadas, fill_value="")

                st.success("✅ Datos extraídos correctamente")
                st.dataframe(df)

                # Exportar a Excel
                excel = io.BytesIO()
                with pd.ExcelWriter(excel, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Guía")
                excel.seek(0)

                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=excel,
                    file_name="guia_extraida.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"No se pudo procesar la imagen OCR: {e}")
