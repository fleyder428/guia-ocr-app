import streamlit as st
import requests
import pandas as pd
import io
import re
from PIL import Image

st.set_page_config(page_title="OCR Guías Transporte", layout="wide")
st.title("📄 Extracción de Datos de Guías de Transporte de Petróleo")

api_key = "K84668714088957"

def extraer_texto_ocr(image_file):
    try:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"filename": image_file},
            data={"apikey": api_key, "OCREngine": 2},
        )
        result = response.json()
        if result.get("IsErroredOnProcessing"):
            st.error("❌ Error en OCR.space: " + str(result.get("ErrorMessage")))
            return None
        return result["ParsedResults"][0]["ParsedText"]
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        return None

def extraer_campos(texto):
    campos = {
        "Fecha y Hora de Salida": buscar_fecha_hora(texto),
        "Placa del Cabeza Tractora": buscar_placa(texto, tipo="tractora"),
        "Placa del Tanque": buscar_placa(texto, tipo="tanque"),
        "Número de Guía": buscar_numero_guia(texto),
        "Empresa Transportadora": buscar_empresa(texto),
        "Cédula": buscar_cedula(texto),
        "Conductor": buscar_conductor(texto),
        "Casilla 1": "",
        "Lugar de Origen": buscar_origen(texto),
        "Lugar de Destino": buscar_destino(texto),
        "Barriles Brutos": buscar_barriles(texto, tipo="brutos"),
        "Barriles Netos": buscar_barriles(texto, tipo="netos"),
        "Barriles a 60°F": buscar_barriles(texto, tipo="60f"),
        "API": buscar_api(texto),
        "BSW (%)": buscar_bsw(texto),
        "Vigencia de Guía": buscar_vigencia(texto),
        "Casilla 2": "",
        "Casilla 3": "",
        "Casilla 4": "",
        "Casilla 5": "",
        "Casilla 6": "",
        "Casilla 7": "",
        "Sellos": buscar_sellos(texto),
    }
    return campos

# Funciones auxiliares de extracción

def buscar_fecha_hora(texto):
    m = re.search(r"(\d{2}/\d{2}/\d{4}).*?(\d{1,2}:\d{2}\s?[APap][Mm])", texto)
    return f"{m.group(1)} {m.group(2)}" if m else ""

def buscar_placa(texto, tipo):
    placas = re.findall(r"[A-Z]{3}\d{2,4}", texto)
    if tipo == "tractora":
        return placas[0] if placas else ""
    if tipo == "tanque":
        return placas[1] if len(placas) > 1 else ""
    return ""

def buscar_numero_guia(texto):
    m = re.search(r"(?:número de )?gu[ií]a[:\s]*([\d]{3,})", texto, re.IGNORECASE)
    return m.group(1) if m else ""

def buscar_empresa(texto):
    m = re.search(r"empresa transportadora[:\s]*([\w\s\.\-]+)", texto, re.IGNORECASE)
    return m.group(1).strip() if m else ""

def buscar_cedula(texto):
    m = re.search(r"c[eé]dula[:\s]*([\d\.]+)", texto, re.IGNORECASE)
    return m.group(1).replace(".", "") if m else ""

def buscar_conductor(texto):
    m = re.search(r"conductor[:\s]*([\w\s\.\-]+)", texto, re.IGNORECASE)
    return m.group(1).strip() if m else ""

def buscar_origen(texto):
    m = re.search(r"lugar de origen[:\s]*([\w\s\-]+)", texto, re.IGNORECASE)
    return m.group(1).strip() if m else ""

def buscar_destino(texto):
    m = re.search(r"lugar de destino[:\s]*([\w\s\-]+)", texto, re.IGNORECASE)
    return m.group(1).strip() if m else ""

def buscar_barriles(texto, tipo):
    if tipo == "brutos":
        m = re.search(r"barriles brutos[:\s]*([\d\.]+)", texto, re.IGNORECASE)
    elif tipo == "netos":
        m = re.search(r"barriles netos[:\s]*([\d\.]+)", texto, re.IGNORECASE)
    elif tipo == "60f":
        m = re.search(r"60\s?[°]?F[:\s]*([\d\.]+)", texto, re.IGNORECASE)
    else:
        return ""
    return m.group(1) if m else ""

def buscar_api(texto):
    m = re.search(r"api[:\s]*([\d\.]+)", texto, re.IGNORECASE)
    return m.group(1) if m else ""

def buscar_bsw(texto):
    m = re.search(r"bsw[:\s]*([\d\.]+)%?", texto, re.IGNORECASE)
    return m.group(1) + "%" if m else ""

def buscar_vigencia(texto):
    m = re.search(r"vigencia.*?(\d{1,3})\s*(horas|hrs|h)", texto, re.IGNORECASE)
    return m.group(1) + " horas" if m else ""

def buscar_sellos(texto):
    sellos = re.findall(r"\b\d{6}\b", texto)
    return "-".join(sellos) if sellos else ""

# UI
uploaded_file = st.file_uploader("Sube una imagen de la guía", type=["png", "jpg", "jpeg"])

if uploaded_file:
    st.image(uploaded_file, caption="Imagen cargada", use_container_width=True)
    texto_extraido = extraer_texto_ocr(uploaded_file)

    if texto_extraido:
        st.subheader("🧠 Texto extraído por OCR")
        st.text_area("Texto OCR", texto_extraido, height=200)

        st.subheader("📊 Datos extraídos de la guía")
        datos = extraer_campos(texto_extraido)
        df = pd.DataFrame(list(datos.items()), columns=["Campo", "Valor"])
        st.dataframe(df, use_container_width=True)

        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, sheet_name="Datos Guía")
        st.download_button("⬇️ Descargar Excel", data=buffer.getvalue(), file_name="datos_guia.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
