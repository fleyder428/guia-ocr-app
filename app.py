import streamlit as st
import requests
from PIL import Image
import io
import pandas as pd
import re

st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("🛢️ Extractor Inteligente de Guías de Transporte de Crudo")

api_key = "K84668714088957"  # Cambia aquí tu API key si quieres

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
        # El nombre 'image.jpg' y el mime type 'image/jpeg' son claves para que OCR.space detecte el tipo
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

def extract_custom_fields(text):
    def find(pattern, text, default=""):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    return [
        find(r"fecha.+salida[:\s]*([\d/:\sAMP]+)", text),
        find(r"placa(?:s)?(?: del)?(?: cabezote| cabeza)?[:\s]*([A-Z0-9\-]+)", text),
        find(r"placa(?:s)?(?: del)? tanque[:\s]*([A-Z0-9\-]+)", text),
        find(r"gu[ií]a[:\s#]*([0-9]{3,})", text),
        find(r"empresa transportadora[:\s]*([\w\s]+)", text),
        find(r"c[eé]dula[:\s]*([0-9]{6,})", text),
        find(r"conductor[:\s]*([A-ZÑÁÉÍÓÚ\s]+)", text),
        "",
        find(r"origen[:\s]*([A-ZÑÁÉÍÓÚ\s]+)", text),
        find(r"destino[:\s]*([A-ZÑÁÉÍÓÚ\s]+)", text),
        find(r"barriles brutos[:\s]*([0-9.]+)", text),
        find(r"barriles netos[:\s]*([0-9.]+)", text),
        find(r"barriles.*60°[Ff][:\s]*([0-9.]+)", text),
        find(r"\bapi[:\s]*([0-9.]+)", text),
        find(r"bsw[:\s%]*([0-9.]+)", text),
        find(r"vigencia[:\s]*([0-9]+)", text),
        "", "", "", "", "", "",
        find(r"sellos?[:\s]*([\d\- ]{5,})", text)
    ]

uploaded_file = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption="Imagen cargada", use_container_width=True)
    image_compressed = compress_and_resize_image(uploaded_file)

    with st.spinner("🧠 Analizando imagen con OCR..."):
        text_result = extract_text_from_image(image_compressed)

    if text_result:
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
        st.success("✅ Datos extraídos exitosamente")
        st.dataframe(df, use_container_width=True)

        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        st.download_button("📥 Descargar Excel", data=excel_buffer, file_name="datos_extraidos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
