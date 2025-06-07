import streamlit as st
import requests
import pandas as pd
import re
from io import BytesIO

# Función para usar OCR.space
def ocr_space_file(uploaded_file, api_key='K84668714088957', language='spa'):
    url_api = 'https://api.ocr.space/parse/image'
    result = requests.post(
        url_api,
        files={'filename': uploaded_file},
        data={'apikey': api_key, 'language': language},
    )
    return result.json()

# Función para extraer los campos del texto OCR
def extraer_datos_guia(texto):
    def buscar(patron):
        match = re.search(patron, texto, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    datos = {
        "Fecha y hora de salida": buscar(r"Fecha y Hora de Salida\s*[:\-]?\s*(.*)"),
        "Placa del cabeza tractora": buscar(r"Placa del Cabeza Tractora\s*[:\-]?\s*(.*)"),
        "Placa del tanque": buscar(r"Placa del Tanque\s*[:\-]?\s*(.*)"),
        "Número de guía": buscar(r"Número de Gu[ií]a\s*[:\-]?\s*(\d+)"),
        "Empresa transportadora": buscar(r"Empresa Transportadora\s*[:\-]?\s*(.*)"),
        "Cédula": buscar(r"C[eé]dula\s*[:\-]?\s*(\d{5,})"),
        "Conductor": buscar(r"Conductor\s*[:\-]?\s*(.*)"),
        "Casilla vacía 1": "",
        "Lugar de origen": buscar(r"Lugar de Origen\s*[:\-]?\s*(.*)"),
        "Lugar de destino": buscar(r"Lugar de Destino\s*[:\-]?\s*(.*)"),
        "Barriles brutos": buscar(r"Barriles Brutos\s*[:\-]?\s*([\d.,]+)"),
        "Barriles netos": buscar(r"Barriles Netos\s*[:\-]?\s*([\d.,]+)"),
        "Barriles a 60°F": buscar(r"Barriles a 60.?F\s*[:\-]?\s*([\d.,]+)"),
        "API": buscar(r"API\s*[:\-]?\s*([\d.]+)"),
        "BSW \(%\)": buscar(r"BSW\s*\(%\)\s*[:\-]?\s*([\d.,]+%)"),
        "Vigencia de guía": buscar(r"Vigencia de la Gu[ií]a\s*[:\-]?\s*(.*)"),
        "Casilla vacía 2": "",
        "Casilla vacía 3": "",
        "Casilla vacía 4": "",
        "Casilla vacía 5": "",
        "Casilla vacía 6": "",
        "Sellos": buscar(r"Sellos\s*[:\-]?\s*(.*)")
    }
    return datos

# INTERFAZ STREAMLIT
st.set_page_config(page_title="Extractor de Guías - OCR", layout="centered")
st.title("📦 Extracción de Guías con OCR.space")

uploaded_file = st.file_uploader("Sube una imagen o PDF escaneado de la guía", type=["jpg", "jpeg", "png", "pdf"])

# Prueba manual con texto
st.subheader("✍️ O ingresa manualmente el texto OCR (para pruebas):")
input_text = st.text_area("Pega aquí el texto OCR si ya lo tienes", height=300)

# BOTÓN para ejecutar OCR o procesar texto
if st.button("🔍 Procesar"):
    texto = ""

    # Si hay imagen, la procesamos con OCR
    if uploaded_file:
        st.info("⏳ Analizando con OCR.space...")
        result = ocr_space_file(uploaded_file)

        # DEBUG opcional: mostrar respuesta completa
        st.write("🧪 Resultado crudo del OCR:", result)

        try:
            texto = result['ParsedResults'][0]['ParsedText']
        except (KeyError, IndexError):
            st.error("❌ No se pudo leer texto OCR. Verifica que la imagen esté clara.")
    elif input_text.strip():
        texto = input_text.strip()
    else:
        st.warning("⚠️ Debes subir una imagen o pegar texto OCR manualmente.")

    if texto:
        st.success("✅ Texto OCR recibido correctamente.")
        st.text_area("📄 Texto detectado por OCR", value=texto, height=250)

        # Extraer campos
        datos = extraer_datos_guia(texto)
        df = pd.DataFrame([datos])
        st.subheader("📋 Datos extraídos:")
        st.dataframe(df)

        # Descargar como Excel
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("⬇️ Descargar Excel", data=output.getvalue(), file_name="datos_guia.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("❌ No se detectó texto válido para procesar.")
