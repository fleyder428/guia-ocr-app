import streamlit as st
from PIL import Image
import io
import requests
from utils import extraer_datos_clave, generar_excel

API_KEY = "K84668714088957"  # Tu API Key OCR.space

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
    st.image(imagen, caption="Imagen cargada", use_column_width=True)

    if st.button("🔍 Extraer datos y generar Excel"):
        with st.spinner("Procesando imagen con OCR.space..."):
            try:
                buf = io.BytesIO()
                imagen.save(buf, format='JPEG')
                bytes_imagen = buf.getvalue()

                texto_ocr = ocr_space_api(bytes_imagen)
                datos = extraer_datos_clave(texto_ocr)

                st.success("✅ Datos extraídos:")
                st.dataframe([datos])

                excel_bytes = generar_excel(datos)

                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=excel_bytes,
                    file_name="guia_extraida.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"No se pudo procesar la imagen OCR: {e}")
