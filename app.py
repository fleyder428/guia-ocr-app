import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from PIL import Image

# ===== CONFIGURACIÓN GENERAL =====
st.set_page_config(page_title="🧾 Guías OCR Personalizadas")
st.title("🧾 Cargar Guía y Extraer Datos")

# ===== DATOS DE USUARIO =====
api_key = st.secrets["ocr_space_api_key"]  # Usa secrets.toml o reemplaza directamente aquí
url_api = 'https://api.ocr.space/parse/image'

# ===== SUBIR IMAGEN =====
imagen = st.file_uploader("📤 Sube una imagen JPG o PNG de la guía", type=["jpg", "jpeg", "png"])

# ===== FUNCIONES =====
def enviar_ocr_space(imagen_bytes):
    response = requests.post(
        url_api,
        files={"filename": imagen_bytes},
        data={
            "apikey": api_key,
            "language": "spa",
            "isTable": "false",
            "OCREngine": "2"
        }
    )
    result = response.json()
    return result['ParsedResults'][0]['ParsedText'] if 'ParsedResults' in result else ""

def extraer_campos(texto):
    campos = {
        "Fecha y hora de salida": "",
        "Placa cabeza tractora": "",
        "Placa del tanque": "",
        "Número de guía": "",
        "Empresa transportadora": "",
        "Cédula": "",
        "Conductor": "",
        "Casilla en blanco 1": "",
        "Lugar de origen": "",
        "Lugar de destino": "",
        "Barriles brutos": "",
        "Barriles netos": "",
        "Barriles a 60°F": "",
        "API": "",
        "BSW (%)": "",
        "Vigencia de guía": "",
        "Casilla en blanco 2": "",
        "Casilla en blanco 3": "",
        "Casilla en blanco 4": "",
        "Casilla en blanco 5": "",
        "Casilla en blanco 6": "",
        "Casilla en blanco 7": "",
        "Sellos": ""
    }

    texto = texto.replace("\n", " ").replace(":", " ").replace(",", ".")
    palabras = texto.split()

    # Ejemplos de extracción robusta (puedes mejorarlo por regex luego)
    for i, palabra in enumerate(palabras):
        if palabra.startswith("GWU"):
            campos["Placa cabeza tractora"] = palabra
        elif palabra.startswith("R7"):
            campos["Placa del tanque"] = palabra
        elif palabra.lower().startswith("vigia"):
            campos["Empresa transportadora"] = palabra
        elif "CAMILO" in palabra.upper():
            campos["Conductor"] = " ".join(palabras[i:i+3])
        elif palabra.lower() == "pendare":
            campos["Lugar de origen"] = "CPF PENDARE"
        elif "guaduas" in palabra.lower():
            campos["Lugar de destino"] = "ESTACIÓN GUADUAS"
        elif palabra.lower() == "brutos":
            campos["Barriles brutos"] = palabras[i+1]
        elif palabra == "netos":
            campos["Barriles netos"] = palabras[i+1]
        elif palabra == "60°F" or palabra == "60f":
            campos["Barriles a 60°F"] = palabras[i-1]
        elif palabra.lower() == "api":
            campos["API"] = palabras[i+1]
        elif palabra.lower() == "bsw":
            campos["BSW (%)"] = palabras[i+1]
        elif palabra == "HORAS":
            campos["Vigencia de guía"] = palabras[i-1] + " HORAS"
        elif palabra.isdigit() and len(palabra) == 7:
            campos["Número de guía"] = palabra
        elif len(palabra) == 8 and palabra.isdigit():
            campos["Cédula"] = palabra
        elif palabra.lower().startswith("2089"):
            campos["Sellos"] = palabra

    return campos

# ===== PROCESAR =====
if imagen:
    st.image(imagen, caption="Guía cargada", use_column_width=True)

    # Convertir imagen a bytes
    imagen_bytes = imagen.read()

    with st.spinner("🧠 Aplicando OCR..."):
        texto_ocr = enviar_ocr_space(imagen_bytes)

    if texto_ocr:
        campos = extraer_campos(texto_ocr)
        df = pd.DataFrame([campos])
        st.success("✅ Extracción completa")
        st.dataframe(df)

        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        st.download_button(
            label="📥 Descargar Excel",
            data=output.getvalue(),
            file_name="guia_extraida.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("❌ No se pudo procesar el OCR. Verifica la imagen o tu API key.")
