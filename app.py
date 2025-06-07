import streamlit as st
from PIL import Image
import requests
import io
import pandas as pd

API_KEY = "K84668714088957"  # Tu clave API OCR.space

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

st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("📄 Extracción Inteligente de Guías - OCR")

archivo_subido = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if archivo_subido:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Imagen cargada", use_container_width=True)

    if st.button("🔍 Extraer texto OCR"):
        with st.spinner("Procesando imagen con OCR.space..."):
            try:
                buf = io.BytesIO()

                # Comprimir imagen para que pese menos de 1MB
                calidad = 30
                imagen.save(buf, format='JPEG', quality=calidad)

                while buf.getbuffer().nbytes > 1024 * 1024 and calidad > 10:
                    buf.seek(0)
                    buf.truncate()
                    calidad -= 5
                    imagen.save(buf, format='JPEG', quality=calidad)

                bytes_imagen = buf.getvalue()

                texto_ocr = ocr_space_api(bytes_imagen)
                st.text_area("Texto OCR detectado:", texto_ocr, height=300)

            except Exception as e:
                st.error(f"No se pudo procesar la imagen OCR: {e}")
