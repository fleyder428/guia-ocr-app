import streamlit as st
import requests
from PIL import Image
import io
import base64
import re
import pandas as pd

API_KEY = "K84668714088957"

st.set_page_config(page_title="Extractor de Guías Tecpetrol", layout="wide")
st.title("📄 Extracción de Guías de Transporte - Tecpetrol")

uploaded_file = st.file_uploader("Sube una imagen de la guía (máx. 1MB)", type=["png", "jpg", "jpeg"])

def compress_image(image, max_size_kb=1024):
    quality = 95
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=quality)
    while buffer.tell() > max_size_kb * 1024 and quality > 10:
        quality -= 5
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=quality)
    return buffer.getvalue()

def extract_data_from_text(text):
    fields = {
        "Número de Guía": re.search(r"\b(?:gu[ií]a|n[o°º]*\.*)\s*(\d{2,})", text, re.IGNORECASE),
        "Número de Factura/Remisión": re.search(r"(?:factura.*?|remisi[oó]n.*?)\s*(\d{5,7})", text, re.IGNORECASE),
        "Lugar y Fecha de Expedición": re.search(r"(CATAN|PUERTO GAIT[AÁ]N).*?META.*", text, re.IGNORECASE),
        "Planta o Campo Productor": re.search(r"CPF\s*PEN[AD]ARE?", text, re.IGNORECASE),
        "Despachado a": re.search(r"(TRAFIGURA.*?COLOMBIA)", text, re.IGNORECASE),
        "Dirección": re.search(r"DIRECCI[OÓ]N[:\s]+(.+)", text, re.IGNORECASE),
        "Ciudad": re.search(r"CIUDAD[:\s]+(.+)", text, re.IGNORECASE),
        "Código ONU": re.search(r"UN\s?[\d]{4}", text),
        "Conductor": re.search(r"([A-Z][a-z]+)\s+GARZ[ÓO]N", text),
        "Cédula": re.search(r"\b\d{6,10}\b", text),
        "Empresa Transportadora": re.search(r"\bVIG[IÍ}A\b", text),
        "Placa del Cabeza Tractora": re.search(r"PLACAS? DEL CABEZ[OÓ]TE.*?([A-Z]{3}\d{3})", text),
        "Placa del Tanque": re.search(r"R7[0-9A-Z]{3}", text),
        "Lugar de Origen": re.search(r"CPF\s*PEN[AD]ARE?", text),
        "Lugar de Destino": re.search(r"GUADUAS|PF2", text),
        "Fecha y Hora de Salida": re.search(r"(\d{2}/\d{2}/\d{4}).*?(\d{1,2}:\d{2}\s*(AM|PM)?)?", text),
        "Vigencia de la Guía": re.search(r"72\s*HORAS", text),
        "Producto": re.search(r"(PETR[ÓO]LEO)", text),
        "Propietario": re.search(r"TRAFIGURA", text),
        "Comercializadora": re.search(r"COMERCI[ÁA]L[IZ]*ADORA.*?:?\s*(TRAFIGURA.*)", text, re.IGNORECASE),
        "Sellos": re.search(r"SELLOS.*?:?\s*(\d{6}(?:[-–]\d{6})*)", text),
        "Barriles Brutos": re.search(r"BARRILES.*?(\d{2,4}[.,]?\d*)", text),
        "Barriles a 60°F": re.search(r"@ 6[0O]F.*?(\d{2,4}[.,]?\d*)", text),
        "Barriles Netos": re.search(r"NETOS.*?(\d{2,4}[.,]?\d*)", text),
    }

    def get(match): return match.group(1).strip() if match else ""

    data = [get(fields[field]) for field in fields]
    return dict(zip(fields.keys(), data))

if uploaded_file:
    image = Image.open(uploaded_file)
    compressed_image = compress_image(image)
    b64_image = base64.b64encode(compressed_image).decode()

    with st.spinner("Analizando con OCR.space..."):
        response = requests.post(
            "https://api.ocr.space/parse/image",
            data={
                "apikey": API_KEY,
                "language": "spa",
                "isOverlayRequired": False,
            },
            files={"filename": ("image.jpg", compressed_image)},
        )

    result = response.json()

    if result.get("IsErroredOnProcessing"):
        st.error("❌ Error del OCR: " + ", ".join(result.get("ErrorMessage", ["Error desconocido."])))
    else:
        text = result["ParsedResults"][0]["ParsedText"]
        st.subheader("🧪 Texto extraído:")
        st.text(text)

        extracted_data = extract_data_from_text(text)
        df = pd.DataFrame([extracted_data])

        st.subheader("✅ Datos estructurados:")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode()
        st.download_button(
            label="📥 Descargar como Excel (.csv)",
            data=csv,
            file_name="datos_extraidos.csv",
            mime="text/csv",
        )
