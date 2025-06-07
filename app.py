import streamlit as st
from PIL import Image
import requests
import io
import pandas as pd

API_KEY = "K84668714088957"  # Tu clave API OCR.space

# Comprime la imagen si es muy grande
def comprimir_imagen(imagen, max_width=1000):
    ancho, alto = imagen.size
    if ancho > max_width:
        ratio = max_width / ancho
        nuevo_alto = int(alto * ratio)
        imagen = imagen.resize((max_width, nuevo_alto), Image.ANTIALIAS)
    buffer = io.BytesIO()
    imagen.save(buffer, format="JPEG", quality=70)
    return buffer.getvalue()

# Llama a la API de OCR.space
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

# Interfaz de Streamlit
st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("📄 Extracción Inteligente de Guías - OCR")

archivo_subido = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if archivo_subido:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Imagen cargada", use_column_width=True)

    if st.button("🔍 Extraer texto OCR"):
        with st.spinner("Procesando imagen con OCR.space..."):
            try:
                imagen_bytes = comprimir_imagen(imagen)
                texto_ocr = ocr_space_api(imagen_bytes)
                st.text_area("📝 Texto OCR detectado:", texto_ocr, height=300)

                # Guardar en Excel
                datos = {"Texto extraído": texto_ocr.replace("\n", " ")}
                df = pd.DataFrame([datos])
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Guía")
                output.seek(0)

                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=output,
                    file_name="guia_extraida.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"No se pudo procesar la imagen OCR: {e}")
