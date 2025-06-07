import streamlit as st
import requests

def ocr_space_api(image_bytes, api_key):
    """Enviar imagen a OCR.space y devolver texto reconocido."""
    url_api = "https://api.ocr.space/parse/image"
    headers = {
        "apikey": api_key,
    }
    files = {
        'file': ('image.png', image_bytes),
    }
    payload = {
        'language': 'spa',  # español
        'isOverlayRequired': False,
    }
    response = requests.post(url_api, headers=headers, files=files, data=payload)
    result = response.json()
    if result.get("IsErroredOnProcessing"):
        st.error("Error en OCR.space: " + result.get("ErrorMessage", ["Error desconocido"])[0])
        return None
    parsed_results = result.get("ParsedResults")
    if parsed_results:
        return parsed_results[0].get("ParsedText", "")
    else:
        return ""

st.title("OCR.space con Streamlit")

# Obtener API key
try:
    api_key = st.secrets["ocr_space_api_key"]
except KeyError:
    st.warning("No se encontró la clave 'ocr_space_api_key' en secrets.toml. Usando clave fija para pruebas.")
    api_key = "TU_API_KEY_REAL_AQUI"  # Cambia esto con tu clave para pruebas locales

uploaded_file = st.file_uploader("Sube una imagen para extraer texto (PNG, JPG, etc.)", type=["png", "jpg", "jpeg"])

if uploaded_file and api_key:
    bytes_data = uploaded_file.read()
    with st.spinner("Procesando OCR..."):
        text = ocr_space_api(bytes_data, api_key)
    if text:
        st.subheader("Texto reconocido:")
        st.text_area("", text, height=300)
    else:
        st.error("No se pudo extraer texto de la imagen.")
