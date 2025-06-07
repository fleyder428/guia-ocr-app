import streamlit as st
import requests
import pandas as pd
import re
from collections import OrderedDict
from io import BytesIO

st.set_page_config(page_title="Extractor OCR Guías", layout="wide")
st.title("🧾 OCR + Extracción Automática de Guías de Transporte")

OCR_API_KEY = "K84668714088957"  # tu clave API personal de OCR.space

def llamar_ocr_space(image_bytes):
    url = 'https://api.ocr.space/parse/image'
    response = requests.post(
        url,
        files={'filename': image_bytes},
        data={'apikey': OCR_API_KEY, 'language': 'spa', 'isOverlayRequired': False},
    )
    result = response.json()
    texto = result['ParsedResults'][0]['ParsedText'] if result.get("ParsedResults") else ''
    return texto

def extraer_datos_guia(texto):
    datos = OrderedDict()

    # ========== DATOS GENERALES ==========
    datos['Número de Guía'] = re.search(r'Número de Guía\s+(\d+)', texto).group(1) if re.search(r'Número de Guía\s+(\d+)', texto) else ''
    datos['Número de Factura/Remisión'] = re.search(r'Número de Factura/Remisión\s+(\d+)', texto).group(1) if re.search(r'Número de Factura/Remisión\s+(\d+)', texto) else ''
    datos['Lugar y Fecha de Expedición'] = re.search(r'Lugar y Fecha de Expedición\s+(.+)', texto).group(1).strip() if re.search(r'Lugar y Fecha de Expedición\s+(.+)', texto) else ''
    datos['Planta o Campo Productor'] = re.search(r'Planta o Campo Productor\s+(.+)', texto).group(1).strip() if re.search(r'Planta o Campo Productor\s+(.+)', texto) else ''

    # ========== DESTINATARIO ==========
    datos['Despachado a'] = re.search(r'Despachado a\s+(.+)', texto).group(1).strip() if re.search(r'Despachado a\s+(.+)', texto) else ''
    datos['Dirección'] = re.search(r'Dirección\s+(.+)', texto).group(1).strip() if re.search(r'Dirección\s+(.+)', texto) else ''
    datos['Ciudad'] = re.search(r'Ciudad\s+(.+)', texto).group(1).strip() if re.search(r'Ciudad\s+(.+)', texto) else ''
    datos['Código ONU'] = re.search(r'Código ONU\s+(.+)', texto).group(1).strip() if re.search(r'Código ONU\s+(.+)', texto) else ''

    # ========== TRANSPORTE ==========
    datos['Conductor'] = re.search(r'Conductor\s+(.+)', texto).group(1).strip() if re.search(r'Conductor\s+(.+)', texto) else ''
    datos['Cédula'] = re.search(r'Cédula\s+(\d+)', texto).group(1) if re.search(r'Cédula\s+(\d+)', texto) else ''
    datos['Empresa Transportadora'] = re.search(r'Empresa Transportadora\s+(.+)', texto).group(1).strip() if re.search(r'Empresa Transportadora\s+(.+)', texto) else ''
    datos['Placa del Cabeza Tractora'] = re.search(r'Placa del Cabeza Tractora\s+(\w+)', texto).group(1) if re.search(r'Placa del Cabeza Tractora\s+(\w+)', texto) else ''
    datos['Placa del Tanque'] = re.search(r'Placa del Tanque\s+(\w+)', texto).group(1) if re.search(r'Placa del Tanque\s+(\w+)', texto) else ''
    datos['Lugar de Origen'] = re.search(r'Lugar de Origen\s+(.+)', texto).group(1).strip() if re.search(r'Lugar de Origen\s+(.+)', texto) else ''
    datos['Lugar de Destino'] = re.search(r'Lugar de Destino\s+(.+)', texto).group(1).strip() if re.search(r'Lugar de Destino\s+(.+)', texto) else ''
    datos['Fecha y Hora de Salida'] = re.search(r'Fecha y Hora de Salida\s+(.+)', texto).group(1).strip() if re.search(r'Fecha y Hora de Salida\s+(.+)', texto) else ''
    datos['Vigencia de la Guía'] = re.search(r'Vigencia de la Guía\s+(.+)', texto).group(1).strip() if re.search(r'Vigencia de la Guía\s+(.+)', texto) else ''

    # ========== PRODUCTO ==========
    datos['Producto'] = re.search(r'Producto\s+(.+)', texto).group(1).strip() if re.search(r'Producto\s+(.+)', texto) else ''
    datos['Propietario'] = re.search(r'Propietario\s+(.+)', texto).group(1).strip() if re.search(r'Propietario\s+(.+)', texto) else ''
    datos['Comercializadora'] = re.search(r'Comercializadora\s+(.+)', texto).group(1).strip() if re.search(r'Comercializadora\s+(.+)', texto) else ''
    datos['Sellos'] = re.search(r'Sellos\s+([0-9\-]+)', texto).group(1).strip() if re.search(r'Sellos\s+([0-9\-]+)', texto) else ''
    datos['Temperatura (°F)'] = re.search(r'Temperatura \(°F\)\s+([\d\.]+)', texto).group(1) if re.search(r'Temperatura \(°F\)\s+([\d\.]+)', texto) else ''
    datos['API'] = re.search(r'API\s+([\d\.]+)', texto).group(1) if re.search(r'API\s+([\d\.]+)', texto) else ''
    datos['Salinidad (%)'] = re.search(r'Salinidad \(%\)\s+([\d\.]+)', texto).group(1) if re.search(r'Salinidad \(%\)\s+([\d\.]+)', texto) else ''
    datos['PVC'] = re.search(r'PVC\s+([\d\.]+)', texto).group(1) if re.search(r'PVC\s+([\d\.]+)', texto) else ''
    datos['BSW (%)'] = re.search(r'BSW \(%\)\s+([\d\.]+)', texto).group(1) if re.search(r'BSW \(%\)\s+([\d\.]+)', texto) else ''
    datos['Azufre (S%)'] = re.search(r'Azufre \(S%\)\s+([\d\.]+)', texto).group(1) if re.search(r'Azufre \(S%\)\s+([\d\.]+)', texto) else ''

    # ========== VOLUMEN ==========
    datos['Barriles Brutos'] = re.search(r'Barriles Brutos\s+([\d\.]+)', texto).group(1) if re.search(r'Barriles Brutos\s+([\d\.]+)', texto) else ''
    datos['Barriles a 60°F'] = re.search(r'Barriles a 60°F\s+([\d\.]+)', texto).group(1) if re.search(r'Barriles a 60°F\s+([\d\.]+)', texto) else ''
    datos['Barriles Netos'] = re.search(r'Barriles Netos\s+([\d\.]+)', texto).group(1) if re.search(r'Barriles Netos\s+([\d\.]+)', texto) else ''

    return datos

uploaded_image = st.file_uploader("📷 Sube una imagen de guía escaneada:", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_image and st.button("🔍 Analizar y Extraer"):
    st.info("⏳ Ejecutando OCR, por favor espera...")
    texto_ocr = llamar_ocr_space(uploaded_image)

    if texto_ocr.strip() == "":
        st.error("No se pudo leer texto OCR. Verifica que la imagen esté clara.")
    else:
        st.subheader("📋 Texto OCR Detectado:")
        st.text_area("Resultado OCR:", texto_ocr, height=200)

        datos = extraer_datos_guia(texto_ocr)
        st.subheader("✅ Datos extraídos:")
        st.json(datos)

        df = pd.DataFrame([datos])
        st.dataframe(df)

        excel = BytesIO()
        df.to_excel(excel, index=False, engine="openpyxl")
        st.download_button("⬇️ Descargar Excel", data=excel.getvalue(), file_name="guia_extraida.xlsx")
