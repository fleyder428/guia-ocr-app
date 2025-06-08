import streamlit as st
import requests
import re
import pandas as pd
from io import BytesIO
from PIL import Image

# Configuración de la página
st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("🛢️ Extractor Inteligente de Guías de Transporte")

# Clave de API de OCR.space (reemplázala por tu clave real)
OCR_API_KEY = "K84668714088957"
OCR_URL = "https://api.ocr.space/parse/image"

# Función para llamar al OCR
def ocr_space_image(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    response = requests.post(
        OCR_URL,
        files={"filename": buffer},
        data={"apikey": OCR_API_KEY, "language": "spa", "isOverlayRequired": False}
    )
    result = response.json()
    return result["ParsedResults"][0]["ParsedText"] if "ParsedResults" in result else ""

# Función para extraer campos clave
def extraer_campos(texto):
    texto = texto.replace("\n", " ")
    campos = []

    try:
        match_fecha = re.search(r"\d{2}[/-]\d{2}[/-]\d{4}\s+\d{2}:\d{2}", texto)
        campos.append(match_fecha.group(0) if match_fecha else "")
    except:
        campos.append("")

    placas = re.findall(r"\b[A-Z]{2,3}\d{3,4}\b", texto)
    campos.append(placas[0] if len(placas) > 0 else "")
    campos.append(placas[1] if len(placas) > 1 else "")

    match_guia = re.search(r"(?:GU[IÍ]A\s*[:#]?\s*)(\d{6,})", texto)
    campos.append(match_guia.group(1) if match_guia else "")

    match_empresa = re.search(r"TRANSPORTADORA\s*:?[\s]*(\w[\w\s&]*)", texto, re.IGNORECASE)
    campos.append(match_empresa.group(1).strip() if match_empresa else "")

    match_cedula = re.search(r"\b\d{6,10}\b", texto)
    campos.append(match_cedula.group(0) if match_cedula else "")

    match_conductor = re.search(r"(?:CONDUCTOR|Nombre)\s*[:\-]?\s*([A-ZÑ ]{3,})", texto)
    campos.append(match_conductor.group(1).strip() if match_conductor else "")

    campos.append("")

    origen = re.search(r"ORIGEN\s*[:\-]?\s*([A-ZÑ ]{3,})", texto)
    campos.append(origen.group(1).strip() if origen else "")

    destino = re.search(r"DESTINO\s*[:\-]?\s*([A-ZÑ ]{3,})", texto)
    campos.append(destino.group(1).strip() if destino else "")

    brutos = re.search(r"BRUTOS\s*[:\-]?\s*(\d+[.,]?\d*)", texto)
    campos.append(brutos.group(1) if brutos else "")

    netos = re.search(r"NETOS\s*[:\-]?\s*(\d+[.,]?\d*)", texto)
    campos.append(netos.group(1) if netos else "")

    b60 = re.search(r"60\s*°?F\s*[:\-]?\s*(\d+[.,]?\d*)", texto)
    campos.append(b60.group(1) if b60 else "")

    try:
        api = re.search(r"\bAPI\b\s*[:\-]?\s*(\d+[.,]?\d*)", texto)
        campos.append(api.group(1) if api else "")
    except:
        campos.append("")

    try:
        bsw = re.search(r"BSW\s*[:\-]?\s*(\d+[.,]?\d*)", texto)
        campos.append(bsw.group(1) if bsw else "")
    except:
        campos.append("")

    vigencia = re.search(r"VIGENCIA\s*[:\-]?\s*(\d+\s*HORAS?)", texto)
    campos.append(vigencia.group(1) if vigencia else "")

    campos += [""] * 6  # Casillas vacías del 17 al 22

    try:
        sellos = re.findall(r"\b\d{6,8}\b", texto)
        sellos_unicos = sorted(set(sellos))
        campos.append(" - ".join(sellos_unicos))
    except:
        campos.append("")

    return campos

# Lista de nombres de los 23 campos esperados
columnas = [
    "Fecha y hora de salida",
    "Placa cabeza tractora",
    "Placa tanque",
    "Número de guía",
    "Empresa transportadora",
    "Cédula",
    "Conductor",
    "Casilla en blanco",
    "Lugar de origen",
    "Lugar de destino",
    "Barriles brutos",
    "Barriles netos",
    "Barriles a 60°F",
    "API",
    "BSW (%)",
    "Vigencia de guía",
    "Casilla vacía 1",
    "Casilla vacía 2",
    "Casilla vacía 3",
    "Casilla vacía 4",
    "Casilla vacía 5",
    "Casilla vacía 6",
    "Sellos"
]

# Subida de múltiples imágenes
imagenes = st.file_uploader("📷 Sube una o varias imágenes de guías", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if st.button("📤 Procesar imágenes") and imagenes:
    datos_extraidos = []
    for imagen in imagenes:
        imagen_pil = Image.open(imagen).convert("RGB")
        texto = ocr_space_image(imagen_pil)
        campos = extraer_campos(texto)
        datos_extraidos.append(campos)

    df = pd.DataFrame(datos_extraidos, columns=columnas)

    st.success("✅ Extracción completada")
    st.dataframe(df)

    buffer_excel = BytesIO()
    df.to_excel(buffer_excel, index=False)
    buffer_excel.seek(0)
    st.download_button(
        label="⬇️ Descargar Excel",
        data=buffer_excel,
        file_name="datos_extraidos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
