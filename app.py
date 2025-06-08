import streamlit as st
import requests
import re
import pandas as pd
from io import BytesIO

# OCR.space API config
OCR_API_KEY = "TU_API_KEY"
OCR_URL = "https://api.ocr.space/parse/image"

# Campos esperados en orden
CAMPOS_GUIA = [
    "Fecha y hora de salida",
    "Placa del cabeza tractora",
    "Placa del tanque",
    "Número de guía",
    "Empresa transportadora",
    "Cédula",
    "Conductor",
    "Casilla en blanco 1",
    "Lugar de origen",
    "Lugar de destino",
    "Barriles brutos",
    "Barriles netos",
    "Barriles a 60°F",
    "API",
    "BSW (%)",
    "Vigencia de guía",
    "Casilla en blanco 2",
    "Casilla en blanco 3",
    "Casilla en blanco 4",
    "Casilla en blanco 5",
    "Casilla en blanco 6",
    "Casilla en blanco 7",
    "Sellos"
]

def extraer_datos(texto):
    campos = []

    try:
        salida = re.search(r"(\d{2}[\/\-]\d{2}[\/\-]\d{4})", texto)
        campos.append(salida.group(1) if salida else "")
    except: campos.append("")

    try:
        placa_cabeza = re.findall(r"[A-Z]{3}\d{3,4}", texto)
        campos.append(placa_cabeza[0] if len(placa_cabeza) > 0 else "")
    except: campos.append("")

    try:
        campos.append(placa_cabeza[1] if len(placa_cabeza) > 1 else "")
    except: campos.append("")

    try:
        guia = re.search(r"FACTURA.*?(\d{5,})", texto, re.IGNORECASE)
        campos.append(guia.group(1) if guia else "")
    except: campos.append("")

    try:
        empresa = re.search(r"EMPRESA TRANSPORTADORA\s*\n?([A-Z \-]+)", texto)
        campos.append(empresa.group(1).strip() if empresa else "")
    except: campos.append("")

    try:
        cedula = re.search(r"C[EÉ]DULA\s*\n?(\d{6,})", texto)
        campos.append(cedula.group(1) if cedula else "")
    except: campos.append("")

    try:
        conductor = re.search(r"NOMBRE DEL CONDUCTOR\s*\n?([A-Z\s]+)", texto)
        campos.append(conductor.group(1).strip() if conductor else "")
    except: campos.append("")

    campos.append("")  # Casilla en blanco 1

    try:
        origen = re.search(r"LUGAR DE ORIGEN\s*\n?([A-Z \-]+)", texto)
        campos.append(origen.group(1).strip() if origen else "")
    except: campos.append("")

    try:
        destino = re.search(r"LUGAR DE DESTINO\s*\n?([A-Z \-]+)", texto)
        campos.append(destino.group(1).strip() if destino else "")
    except: campos.append("")

    try:
        brutos = re.findall(r"(\d{2,3}[\.,]\d{2})", texto)
        campos.append(brutos[0] if len(brutos) > 0 else "")
    except: campos.append("")

    try:
        campos.append(brutos[1] if len(brutos) > 1 else "")
    except: campos.append("")

    try:
        campos.append(brutos[2] if len(brutos) > 2 else "")
    except: campos.append("")

    try:
        api = re.search(r"API\s*[:\-]?\s*(\d+[\.,]?\d*)", texto)
        campos.append(api.group(1) if api else "")
    except: campos.append("")

    try:
        bsw = re.search(r"BSW\s*[:\-]?\s*(\d+[\.,]?\d*)", texto)
        campos.append(bsw.group(1) if bsw else "")
    except: campos.append("")

    try:
        vigencia = re.search(r"(\d{2,3}\s*HORAS)", texto)
        campos.append(vigencia.group(1) if vigencia else "")
    except: campos.append("")

    # Casillas en blanco 2 a 7
    for _ in range(6):
        campos.append("")

    try:
        sellos = re.search(r"SE[L|1]{2}O\s*[:\-]?\s*(\w+)", texto)
        campos.append(sellos.group(1) if sellos else "")
    except: campos.append("")

    return campos

def ocr_espacio(img_bytes):
    result = requests.post(
        OCR_URL,
        files={"filename": img_bytes},
        data={"apikey": OCR_API_KEY, "language": "spa", "isOverlayRequired": False}
    )
    result.raise_for_status()
    return result.json()["ParsedResults"][0]["ParsedText"]

st.title("Extractor de Datos de Guías de Transporte")

imagenes = st.file_uploader("Sube una o varias imágenes", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

if imagenes:
    tabla = []
    for imagen in imagenes:
        st.image(imagen, caption="Guía cargada", use_column_width=True)
        texto = ocr_espacio(imagen.read())
        datos = extraer_datos(texto)
        tabla.append(datos)

    df = pd.DataFrame(tabla, columns=CAMPOS_GUIA)
    st.dataframe(df)

    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button("Descargar Excel", data=output.getvalue(), file_name="guias_extraidas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
