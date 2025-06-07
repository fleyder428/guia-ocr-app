import streamlit as st
from PIL import Image
import pytesseract

st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("📄 Extracción Inteligente de Guías - OCR")

archivo_subido = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if archivo_subido:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Imagen cargada", use_column_width=True)

    if st.button("🔍 Extraer texto OCR"):
        with st.spinner("Procesando imagen..."):
            try:
                texto = pytesseract.image_to_string(imagen, lang='spa')
                st.text_area("Texto OCR detectado:", texto, height=300)
            except Exception as e:
                st.error(f"No se pudo procesar la imagen OCR: {e}")
