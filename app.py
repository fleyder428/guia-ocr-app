import streamlit as st
import requests
from PIL import Image
import io
import pandas as pd
import re

st.set_page_config(page_title="Extractor de Guías de Crudo Adaptado", layout="centered")
st.title("🛢️ Extractor Adaptado de Guías con OCR Flexible")

api_key = "K84668714088957"  # Pon tu API Key aquí

def compress_and_resize_image(image_file, max_size=(2000, 2000), quality=70):
    img = Image.open(image_file)
    img = img.convert("RGB")
    img.thumbnail(max_size)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return buffer

def extract_text_from_image(image):
    url_api = "https://api.ocr.space/parse/image"
    files = {
        "filename": ("image.jpg", image, "image/jpeg")
    }
    result = requests.post(
        url_api,
        files=files,
        data={
            "apikey": api_key,
            "language": "spa",
            "isOverlayRequired": False,
        },
    )
    result_json = result.json()
    if result_json.get("IsErroredOnProcessing"):
        st.error(f"❌ Error en OCR.space: {result_json.get('ErrorMessage')}")
        return ""
    return result_json["ParsedResults"][0]["ParsedText"]

def search_flexible(text, keywords, multiline=False):
    """
    Busca palabras clave similares en el texto para extraer el valor.
    keywords: lista de palabras clave posibles (strings)
    multiline: si True busca en línea siguiente si no encuentra en la misma línea.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for kw in keywords:
            if kw.lower() in line.lower():
                # Intenta extraer después de ":" en la misma línea
                parts = re.split(r"[:\-]", line, maxsplit=1)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip()
                # Si no hay ":" o nada después, intenta línea siguiente si multiline=True
                if multiline and i + 1 < len(lines):
                    return lines[i + 1].strip()
    return ""

def extract_fields(text):
    # Lista de posibles keywords para cada campo (más flexibles)
    fields_keywords = [
        ["fecha y hora de salida", "fecha salida", "fecha y hora", "salida"],  # Fecha y hora de salida
        ["placa del cabezote", "placas del cabezote", "placa cabeza tractora", "placa cabeza", "placa tractora"],  # Placa cabeza tractora
        ["placas del tanque", "placa tanque"],  # Placa tanque
        ["número de guía", "numero de guia", "guía", "guia", "número guia"],  # Número de guía
        ["empresa transportadora", "transportadora"],  # Empresa transportadora
        ["cédula", "cedula"],  # Cédula
        ["nombre del conductor", "conductor"],  # Conductor
        [],  # Casilla en blanco
        ["lugar de origen", "origen"],  # Lugar de origen
        ["lugar de destino", "destino"],  # Lugar de destino
        ["barriles brutos", "barriles", "volumen en barriles", "volumen en sarrles"],  # Barriles brutos (flexible)
        ["barriles netos", "netos"],  # Barriles netos
        ["barriles a 60", "barriles a 60°f"],  # Barriles a 60°F
        ["api"],  # API
        ["bsw", "bsw (%)"],  # BSW
        ["horas de vigencia", "vigencia"],  # Vigencia de guía
        [], [], [], [], [], [],  # Seis casillas en blanco
        ["sellos", "sello"],  # Sellos
    ]

    extracted = []
    for kw_list in fields_keywords:
        if len(kw_list) == 0:
            # Casilla en blanco
            extracted.append("")
        else:
            val = search_flexible(text, kw_list, multiline=True)
            extracted.append(val)
    return extracted

uploaded_file = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption="Imagen cargada", use_container_width=True)
    image_compressed = compress_and_resize_image(uploaded_file)

    with st.spinner("🧠 Analizando imagen con OCR..."):
        texto_extraido = extract_text_from_image(image_compressed)

    if texto_extraido:
        st.subheader("📝 Texto extraído (verifica para ajustes):")
        st.text_area("Texto OCR", texto_extraido, height=300)

        datos_extraidos = extract_fields(texto_extraido)

        nombres_campos = [
            "Fecha y Hora de Salida", "Placa Cabeza Tractora", "Placa del Tanque", "Número de Guía",
            "Empresa Transportadora", "Cédula", "Conductor", "Casilla en blanco",
            "Lugar de Origen", "Lugar de Destino", "Barriles Brutos", "Barriles Netos", "Barriles a 60°F",
            "API", "BSW (%)", "Vigencia de Guía",
            "Casilla 1", "Casilla 2", "Casilla 3", "Casilla 4", "Casilla 5", "Casilla 6",
            "Sellos"
        ]

        df = pd.DataFrame([datos_extraidos], columns=nombres_campos)
        st.success("✅ Datos extraídos:")
        st.dataframe(df, use_container_width=True)

        buffer_excel = io.BytesIO()
        df.to_excel(buffer_excel, index=False)
        buffer_excel.seek(0)
        st.download_button("📥 Descargar Excel", data=buffer_excel, file_name="datos_guia_extraidos.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("No se pudo extraer texto de la imagen.")
