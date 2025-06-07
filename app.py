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

def extraer_datos_clave(texto):
    campos = {
        "Fecha y hora de salida": "",
        "Placa del cabeza tractora": "",
        "Placa del tanque": "",
        "Número de guía": "",
        "Empresa transportadora": "",
        "Cédula": "",
        "Conductor": "",
        "Casilla en blanco": "",
        "Lugar de origen": "",
        "Lugar de destino": "",
        "Barriles brutos": "",
        "Barriles netos": "",
        "Barriles a 60°F": "",
        "API": "",
        "BSW (%)": "",
        "Vigencia de guía": "",
        "Casilla vacía 1": "",
        "Casilla vacía 2": "",
        "Casilla vacía 3": "",
        "Casilla vacía 4": "",
        "Casilla vacía 5": "",
        "Casilla vacía 6": "",
        "Sellos": "",
    }

    lineas = texto.splitlines()

    for linea in lineas:
        linea = linea.strip()
        if "Fecha y hora de salida" in linea:
            campos["Fecha y hora de salida"] = linea.split(":")[-1].strip()
        elif "Placa cabeza tractora" in linea or "Placa del cabeza tractora" in linea:
            campos["Placa del cabeza tractora"] = linea.split(":")[-1].strip()
        elif "Placa tanque" in linea or "Placa del tanque" in linea:
            campos["Placa del tanque"] = linea.split(":")[-1].strip()
        elif "Número de guía" in linea or "No. de guía" in linea:
            campos["Número de guía"] = linea.split(":")[-1].strip()
        elif "Empresa transportadora" in linea:
            campos["Empresa transportadora"] = linea.split(":")[-1].strip()
        elif "Cédula" in linea:
            campos["Cédula"] = linea.split(":")[-1].strip()
        elif "Conductor" in linea:
            campos["Conductor"] = linea.split(":")[-1].strip()
        elif "Lugar de origen" in linea:
            campos["Lugar de origen"] = linea.split(":")[-1].strip()
        elif "Lugar de destino" in linea:
            campos["Lugar de destino"] = linea.split(":")[-1].strip()
        elif "Barriles brutos" in linea:
            campos["Barriles brutos"] = linea.split(":")[-1].strip()
        elif "Barriles netos" in linea:
            campos["Barriles netos"] = linea.split(":")[-1].strip()
        elif "Barriles a 60°F" in linea:
            campos["Barriles a 60°F"] = linea.split(":")[-1].strip()
        elif "API" in linea:
            campos["API"] = linea.split(":")[-1].strip()
        elif "BSW" in linea:
            campos["BSW (%)"] = linea.split(":")[-1].strip()
        elif "Vigencia de guía" in linea:
            campos["Vigencia de guía"] = linea.split(":")[-1].strip()
        elif "Sellos" in linea:
            campos["Sellos"] = linea.split(":")[-1].strip()

    return campos

st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("📄 Extracción Inteligente de Guías - OCR")

archivo_subido = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if archivo_subido:
    imagen = Image.open(archivo_subido)
    st.image(imagen, caption="Imagen cargada", use_column_width=True)

    if st.button("🔍 Extraer datos clave"):
        with st.spinner("Procesando imagen con OCR.space y extrayendo datos..."):
            try:
                buf = io.BytesIO()
                imagen.save(buf, format='JPEG')
                bytes_imagen = buf.getvalue()

                texto_ocr = ocr_space_api(bytes_imagen)
                campos = extraer_datos_clave(texto_ocr)

                df = pd.DataFrame([campos])
                st.success("✅ Datos extraídos:")
                st.dataframe(df)

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
