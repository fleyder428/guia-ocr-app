import streamlit as st
import requests
from PIL import Image
import io
import pandas as pd
import re

st.set_page_config(page_title="Extractor de Guías Mejorado", layout="centered")
st.title("🛢️ Extractor Mejorado de Guías de Transporte de Crudo")

api_key = "K84668714088957"  # Cambia tu API Key aquí

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

def find_value_after_keyword(text, keyword, multiline=False):
    # Busca la palabra clave y extrae lo que está después de ":" en la misma línea o en la siguiente si multiline
    pattern = rf"{keyword}[:\s]*([\w\s\-\./,°]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    elif multiline:
        # Buscar línea siguiente
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower() and i+1 < len(lines):
                return lines[i+1].strip()
    return ""

def extract_custom_fields(text):
    # Aquí se ajustan las palabras clave a buscar según el texto de la guía real.
    return [
        find_value_after_keyword(text, "fecha y hora de salida", True),
        find_value_after_keyword(text, "placa del cabezote", True) or find_value_after_keyword(text, "placas del cabezote", True),
        find_value_after_keyword(text, "placas del tanque", True),
        find_value_after_keyword(text, "número de guía") or find_value_after_keyword(text, "guía") or find_value_after_keyword(text, "numero de guía"),
        find_value_after_keyword(text, "empresa transportadora", True),
        find_value_after_keyword(text, "cédula", True),
        find_value_after_keyword(text, "nombre del conductor", True) or find_value_after_keyword(text, "conductor", True),
        "",  # Casilla en blanco
        find_value_after_keyword(text, "lugar de origen", True) or find_value_after_keyword(text, "origen", True),
        find_value_after_keyword(text, "lugar de destino", True) or find_value_after_keyword(text, "destino", True),
        find_value_after_keyword(text, "barriles brutos", True) or find_value_after_keyword(text, "barriles", True),
        find_value_after_keyword(text, "barriles netos", True),
        find_value_after_keyword(text, "barriles a 60", True),
        find_value_after_keyword(text, "api", True),
        find_value_after_keyword(text, "bsw", True),
        find_value_after_keyword(text, "horas de vigencia", True) or find_value_after_keyword(text, "vigencia", True),
        "", "", "", "", "", "",  # Seis casillas vacías
        find_value_after_keyword(text, "sellos", True),
    ]

uploaded_file = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption="Imagen cargada", use_container_width=True)
    image_compressed = compress_and_resize_image(uploaded_file)

    with st.spinner("🧠 Analizando imagen con OCR..."):
        text_result = extract_text_from_image(image_compressed)

    if text_result:
        st.subheader("📝 Texto extraído de la imagen (revisar para validar):")
        st.text_area("Texto OCR", text_result, height=300)

        extracted_fields = extract_custom_fields(text_result)

        field_names = [
            "Fecha y Hora de Salida", "Placa Cabeza Tractora", "Placa del Tanque", "Número de Guía",
            "Empresa Transportadora", "Cédula", "Conductor", "Casilla en blanco",
            "Lugar de Origen", "Lugar de Destino", "Barriles Brutos", "Barriles Netos", "Barriles a 60°F",
            "API", "BSW (%)", "Vigencia de Guía",
            "Casilla 1", "Casilla 2", "Casilla 3", "Casilla 4", "Casilla 5", "Casilla 6",
            "Sellos"
        ]

        df = pd.DataFrame([extracted_fields], columns=field_names)
        st.success("✅ Datos extraídos")
        st.dataframe(df, use_container_width=True)

        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        st.download_button("📥 Descargar Excel", data=excel_buffer, file_name="datos_extraidos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("No se pudo extraer texto de la imagen.")
