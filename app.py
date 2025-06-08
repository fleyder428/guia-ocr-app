import streamlit as st
import requests
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("🛢️ Extractor de Datos de Guías (23 Campos)")
st.write("Sube una imagen de una guía y extraeremos todos los campos importantes automáticamente.")

# --- Subida de archivo ---
uploaded_file = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

# --- API Key de OCR.space ---
OCR_API_KEY = "K84668714088957"

# --- Función para enviar imagen a OCR.space y obtener texto ---
def ocr_space_image(image_file):
    response = requests.post(
        "https://api.ocr.space/parse/image",
        files={"filename": image_file},
        data={"apikey": OCR_API_KEY, "language": "spa", "OCREngine": 2},
    )
    result = response.json()
    return result["ParsedResults"][0]["ParsedText"] if result.get("ParsedResults") else ""

# --- Función para extraer los 23 campos ordenadamente ---
def extraer_campos(texto):
    texto = texto.replace("\n", " ")
    campos = []

    # Campo 1: Fecha y hora de salida
    match_fecha = re.search(r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}", texto)
    campos.append(match_fecha.group(0) if match_fecha else "")

    # Campo 2: Placa cabeza tractora (primera placa encontrada)
    placas = re.findall(r"\b[A-Z]{2,3}\d{3,4}\b", texto)
    campos.append(placas[0] if len(placas) > 0 else "")

    # Campo 3: Placa del tanque (segunda placa encontrada)
    campos.append(placas[1] if len(placas) > 1 else "")

    # Campo 4: Número de guía
    match_guia = re.search(r"(?:GU[IÍ]A\s*[:#]?\s*)(\d{6,})", texto)
    campos.append(match_guia.group(1) if match_guia else "")

    # Campo 5: Empresa transportadora
    match_empresa = re.search(r"TRANSPORTADORA\s*:?[\s]*(\w[\w\s&]*)", texto)
    campos.append(match_empresa.group(1).strip() if match_empresa else "")

    # Campo 6: Cédula
    match_cedula = re.search(r"\b(\d{6,10})\b", texto)
    campos.append(match_cedula.group(1) if match_cedula else "")

    # Campo 7: Conductor
    match_conductor = re.search(r"(?:CONDUCTOR|Nombre)\s*[:\-]?\s*([A-ZÑ ]{3,})", texto)
    campos.append(match_conductor.group(1).strip() if match_conductor else "")

    # Campo 8: Casilla vacía
    campos.append("")

    # Campo 9: Lugar de origen
    origen = re.search(r"ORIGEN\s*[:\-]?\s*([A-ZÑ ]{3,})", texto)
    campos.append(origen.group(1).strip() if origen else "")

    # Campo 10: Lugar de destino
    destino = re.search(r"DESTINO\s*[:\-]?\s*([A-ZÑ ]{3,})", texto)
    campos.append(destino.group(1).strip() if destino else "")

    # Campo 11: Barriles brutos
    brutos = re.search(r"BRUTOS\s*[:\-]?\s*(\d+[,\.]?\d*)", texto)
    campos.append(brutos.group(1) if brutos else "")

    # Campo 12: Barriles netos
    netos = re.search(r"NETOS\s*[:\-]?\s*(\d+[,\.]?\d*)", texto)
    campos.append(netos.group(1) if netos else "")

    # Campo 13: Barriles a 60°F
    b60 = re.search(r"60\s*°?F\s*[:\-]?\s*(\d+[,\.]?\d*)", texto)
    campos.append(b60.group(1) if b60 else "")

    # Campo 14: API
    api = re.search(r"\bAPI\b\s*[:\-]?\s*(\d+[,\.]?\d*)", texto)
    campos.append(api.group(1) if api else "")

    # Campo 15: BSW
    bsw = re.search(r"BSW\s*[:\-]?\s*(\d+[,\.]?\d*)", texto)
    campos.append(bsw.group(1) if bsw else "")

    # Campo 16: Vigencia
    vigencia = re.search(r"VIGENCIA\s*[:\-]?\s*(\d+\s*HORAS?)", texto)
    campos.append(vigencia.group(1) if vigencia else "")

    # Campos 17-22: vacíos
    campos += [""] * 6

    # Campo 23: Sellos
    sellos = re.findall(r"\b\d{6}\b", texto)
    sellos_unicos = sorted(set(sellos))  # elimina duplicados y ordena
    campos.append(" - ".join(sellos_unicos))

    return campos

# --- Interfaz principal ---
if uploaded_file:
    st.info("⏳ Procesando imagen...")
    texto_extraido = ocr_space_image(uploaded_file)

    if texto_extraido:
        datos = extraer_campos(texto_extraido)
        columnas = [
            "Fecha y hora de salida", "Placa del cabeza tractora", "Placa del tanque",
            "Número de guía", "Empresa transportadora", "Cédula", "Conductor", "Casilla en blanco",
            "Lugar de origen", "Lugar de destino", "Barriles brutos", "Barriles netos", "Barriles a 60°F",
            "API", "BSW (%)", "Vigencia de guía", "Casilla en blanco 1", "Casilla en blanco 2",
            "Casilla en blanco 3", "Casilla en blanco 4", "Casilla en blanco 5", "Casilla en blanco 6",
            "Sellos"
        ]
        df = pd.DataFrame([datos], columns=columnas)

        st.success("✅ Datos extraídos con éxito:")
        st.dataframe(df)

        # --- Descargar Excel ---
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        st.download_button("📥 Descargar Excel", data=output, file_name="guia_extraida.xlsx", mime="application/vnd.ms-excel")
    else:
        st.error("❌ No se pudo extraer texto de la imagen.")
