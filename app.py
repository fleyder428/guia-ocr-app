import streamlit as st
import requests
from PIL import Image
import io

# Cambia aquí tu API key real o usa st.secrets["ocr_space_api_key"]
api_key = "K84668714088957"

def reducir_imagen(bytes_data, max_size_kb=1024):
    """Reduce la imagen para que pese menos de max_size_kb (1MB por defecto)"""
    image = Image.open(io.BytesIO(bytes_data))
    quality = 90
    buffer = io.BytesIO()

    while True:
        buffer.seek(0)
        buffer.truncate()
        image.save(buffer, format="JPEG", quality=quality)
        size_kb = buffer.tell() / 1024
        if size_kb <= max_size_kb or quality <= 20:
            break
        quality -= 10

    return buffer.getvalue()

def ocr_space_api(image_bytes, api_key):
    url_api = "https://api.ocr.space/parse/image"
    headers = {
        "apikey": api_key,
    }
    files = {
        'file': ('image.jpg', image_bytes),
    }
    payload = {
        'language': 'spa',
        'isOverlayRequired': False,
    }
    try:
        response = requests.post(url_api, headers=headers, files=files, data=payload)
        result = response.json()
    except Exception as e:
        st.error(f"Error al conectar con OCR.space: {e}")
        return None

    if result.get("IsErroredOnProcessing"):
        error_msgs = result.get("ErrorMessage", ["Error desconocido"])
        st.error(f"Error en OCR.space: {error_msgs[0]}")
        return None
    parsed_results = result.get("ParsedResults")
    if parsed_results:
        return parsed_results[0].get("ParsedText", "")
    else:
        st.warning("No se detectó texto en la imagen.")
        return ""

st.title("OCR.space con Streamlit - OCR + Reducción de imagen")

uploaded_file = st.file_uploader("Sube una imagen para extraer texto (PNG, JPG, etc.)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    bytes_data_raw = uploaded_file.read()

    size_kb_raw = len(bytes_data_raw) / 1024
    st.write(f"Tamaño original de la imagen: {size_kb_raw:.2f} KB")

    if size_kb_raw > 1024:
        st.info("La imagen es mayor a 1 MB, se reducirá su tamaño automáticamente...")
        bytes_data = reducir_imagen(bytes_data_raw, max_size_kb=1024)
        size_kb_new = len(bytes_data) / 1024
        st.write(f"Tamaño reducido: {size_kb_new:.2f} KB")
    else:
        bytes_data = bytes_data_raw

    with st.spinner("Procesando OCR..."):
        text = ocr_space_api(bytes_data, api_key)

    if text:
        st.subheader("Texto reconocido:")
        st.text_area("", text, height=300)
    else:
        st.error("No se pudo extraer texto de la imagen.")
