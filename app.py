import streamlit as st
import requests
import pandas as pd
import re
from PIL import Image
from io import BytesIO

# --- Comprime imágenes al vuelo ---
def comprimir_imagen(image_file, max_size_kb=1000):
    imagen = Image.open(image_file)
    output = BytesIO()

    # Redimensionar si es muy grande (ancho máximo 1024 px)
    max_ancho = 1024
    if imagen.width > max_ancho:
        ratio = max_ancho / float(imagen.width)
        nuevo_alto = int((float(imagen.height) * float(ratio)))
        imagen = imagen.resize((max_ancho, nuevo_alto))

    # Guardar como JPEG optimizado
    imagen = imagen.convert("RGB")  # Para asegurar compatibilidad JPEG
    calidad = 85  # Puedes ajustar esto (85 es buena compresión sin perder mucho detalle)

    imagen.save(output, format="JPEG", optimize=True, quality=calidad)
    output.seek(0)
    return output

# --- Función OCR.space con compresión integrada ---
def ocr_space_file(uploaded_file, api_key='K84668714088957', language='spa'):
    # Comprimir si es imagen
    if uploaded_file.type.startswith("image/"):
        archivo_procesado = comprimir_imagen(uploaded_file)
        filename = "comprimido.jpg"
    else:
        archivo_procesado = uploaded_file
        filename = uploaded_file.name

    result = requests.post(
        'https://api.ocr.space/parse/image',
        files={'filename': (filename, archivo_procesado)},
        data={'apikey': api_key, 'language': language},
    )
    return result.json()

# --- Función para extraer los campos del texto OCR ---
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

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Extractor de Guías - OCR", layout="centered")
st.title("📦 Extracción de Guías con OCR.space")

uploaded_file = st.file_uploader("Sube una imagen o PDF escaneado de la guía", type=["jpg", "jpeg", "png", "pdf"])

# Entrada de texto manual opcional
st.subheader("✍️ O pega aquí texto OCR manual (para pruebas):")
input_text = st.text_area("Texto OCR", height=300)

# BOTÓN de procesamiento
if st.button("🔍 Procesar"):
    texto = ""

    if uploaded_file:
        st.info("⏳ Enviando a OCR.space con compresión automática...")
        result = ocr_space_file(uploaded_file)
        st.write("🧪 Resultado crudo del OCR:", result)

        try:
            texto = result['ParsedResults'][0]['ParsedText']
        except (KeyError, IndexError):
            st.error("❌ No se pudo leer texto OCR. Verifica la imagen.")
    elif input_text.strip():
        texto = input_text.strip()
    else:
        st.warning("⚠️ Debes subir una imagen o pegar texto OCR.")

    if texto:
        st.success("✅ Texto OCR recibido correctamente.")
        st.text_area("📄 Texto detectado por OCR", value=texto, height=250)

        datos = extraer_datos_guia(texto)
        df = pd.DataFrame([datos])
        st.subheader("📋 Datos extraídos:")
        st.dataframe(df)

        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("⬇️ Descargar Excel", data=output.getvalue(), file_name="datos_guia.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("❌ No se detectó texto válido para procesar.")
