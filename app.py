import streamlit as st
import requests
from PIL import Image
import io
import re
import pandas as pd

api_key = "K84668714088957"  # Pon aquí tu API key

def reducir_imagen(bytes_data, max_size_kb=1024):
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
    headers = {"apikey": api_key}
    files = {'file': ('image.jpg', image_bytes)}
    payload = {'language': 'spa', 'isOverlayRequired': False}
    response = requests.post(url_api, headers=headers, files=files, data=payload)
    result = response.json()
    if result.get("IsErroredOnProcessing"):
        st.error("Error en OCR.space: " + result.get("ErrorMessage", ["Error desconocido"])[0])
        return None
    parsed_results = result.get("ParsedResults")
    if parsed_results:
        return parsed_results[0].get("ParsedText", "")
    return ""

def extraer_campos(texto):
    # Define aquí tus patrones de extracción
    patrones = {
        "Empresa": r"(TECPETROL COLOMBIA S\.A\.S)",
        "NIT": r"NIT\.?\s*([\d\.\-]+)",
        "Número de guía": r"FACTURA O REMISIÓN NO\s*(\d+)",
        "Conductor": r"FIRMA DEL CLIENTE\s*[\d\s]*([A-Z\s]+)",
        "Placas cabezote": r"PLACAS DEL CABEZOTE\s*([A-Z0-9\-]+)",
        "Placas tanque": r"PLACAS DEL TANQUE\s*([A-Z0-9\-]+)",
        "Fecha y hora de salida": r"FECHA Y HORA DE SALIDA\s*([\d]+)",
        "Barriles netos": r"NETO S\s*([\d\.]+)",
        "B.S.W.": r"B\.S\.W\.\s*([\d\.]+)",
        # Puedes añadir más campos aquí siguiendo el mismo patrón
    }
    resultados = {}
    for campo, patron in patrones.items():
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            resultados[campo] = match.group(1).strip()
        else:
            resultados[campo] = "No encontrado"
    return resultados

st.title("Extracción de Datos Clave de Guías Petroleras con OCR.space")

uploaded_file = st.file_uploader("Sube una imagen de la guía (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

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
        texto = ocr_space_api(bytes_data, api_key)

    if texto:
        st.subheader("Texto extraído de la imagen:")
        st.text_area("", texto, height=300)

        campos = extraer_campos(texto)

        st.subheader("Datos extraídos:")
        df = pd.DataFrame(list(campos.items()), columns=["Campo", "Valor"])
        st.table(df)

        # Botón para exportar a Excel
        excel_data = df.to_excel(index=False)
        st.download_button(
            label="Descargar datos en Excel",
            data=df.to_excel(index=False).encode('utf-8'),
            file_name="datos_guia_petrolera.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("No se pudo extraer texto de la imagen.")
