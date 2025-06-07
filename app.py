import streamlit as st
import requests
import re
import pandas as pd

OCR_SPACE_API_KEY = "TU_API_KEY_AQUI"  # Cambia aquí tu API Key

def ocr_space_file(file):
    """Enviar imagen a OCR.space y devolver texto extraído."""
    payload = {
        'apikey': OCR_SPACE_API_KEY,
        'language': 'spa',
        'isOverlayRequired': False,
    }
    files = {'file': (file.name, file, file.type)}
    response = requests.post('https://api.ocr.space/parse/image',
                             data=payload,
                             files=files)
    try:
        result = response.json()
    except Exception as e:
        raise Exception("No se pudo interpretar la respuesta de OCR.space como JSON.") from e
    
    if not isinstance(result, dict):
        raise Exception("Respuesta inesperada de OCR.space, no es un objeto JSON.")

    if result.get("IsErroredOnProcessing", True):
        errors = result.get("ErrorMessage", ["Error desconocido en OCR.space"])
        raise Exception("Error en OCR.space: " + "; ".join(errors))
    
    parsed_results = result.get("ParsedResults")
    if not parsed_results or len(parsed_results) == 0:
        raise Exception("No se encontraron resultados parseados en OCR.space.")
    
    return parsed_results[0].get("ParsedText", "")

def normalize_text(text):
    replacements = {
        r'[ÁÀÂÄ]': 'A',
        r'[ÉÈÊË]': 'E',
        r'[ÍÌÎÏ]': 'I',
        r'[ÓÒÔÖ]': 'O',
        r'[ÚÙÛÜ]': 'U',
        r'Ñ': 'N',
        r'[^A-Z0-9\s\.,:/\-]': ' ',  # Letras, números y signos comunes
    }
    text = text.upper()
    for wrong, right in replacements.items():
        text = re.sub(wrong, right, text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_section(text, start_marker, end_marker=None):
    if end_marker:
        pattern = re.escape(start_marker) + r'(.*?)' + re.escape(end_marker)
    else:
        pattern = re.escape(start_marker) + r'(.*)'
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ''

def extract_field(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ''

def parse_ocr_text(text):
    text = normalize_text(text)

    datos_generales = extract_section(text, "NUMERO DE GUIA", "DATOS DEL DESTINATARIO")
    datos_destinatario = extract_section(text, "DATOS DEL DESTINATARIO", "DATOS DEL TRANSPORTE")
    datos_transporte = extract_section(text, "DATOS DEL TRANSPORTE", "DESCRIPCION DEL PRODUCTO")
    descripcion_producto = extract_section(text, "DESCRIPCION DEL PRODUCTO", "VOLUMEN TRANSPORTADO")
    volumen_transportado = extract_section(text, "VOLUMEN TRANSPORTADO")

    datos = {
        "Datos Generales": {
            "Número de Guía": extract_field(r'NUMERO DE GUIA\s*([0-9]+)', datos_generales),
            "Número de Factura/Remisión": extract_field(r'NUMERO DE FACTURA/REMISION\s*([0-9]+)', datos_generales),
            "Lugar y Fecha de Expedición": extract_field(r'LUGAR Y FECHA DE EXPEDICION\s*([\w\s\-,:/]+)', datos_generales),
            "Planta o Campo Productor": extract_field(r'PLANTA O CAMPO PRODUCTOR\s*([\w\s]+)', datos_generales)
        },
        "Datos del Destinatario": {
            "Despachado a": extract_field(r'DESPACHADO A\s*([\w\s\.,]+)', datos_destinatario),
            "Dirección": extract_field(r'DIRECCION\s*([\w\s\.,\-#]+)', datos_destinatario),
            "Ciudad": extract_field(r'CIUDAD\s*([\w\s\-]+)', datos_destinatario),
            "Código ONU": extract_field(r'CODIGO ONU\s*([A-Z0-9]+)', datos_destinatario)
        },
        "Datos del Transporte": {
            "Conductor": extract_field(r'CONDUCTOR\s*([\w\s]+)', datos_transporte),
            "Cédula": extract_field(r'CEDULA\s*([0-9]+)', datos_transporte),
            "Empresa Transportadora": extract_field(r'EMPRESA TRANSPORTADORA\s*([\w\s]+)', datos_transporte),
            "Placa del Cabeza Tractora": extract_field(r'PLACA DEL CABEZA TRACTORA\s*([A-Z0-9\-]+)', datos_transporte),
            "Placa del Tanque": extract_field(r'PLACA DEL TANQUE\s*([A-Z0-9\-]+)', datos_transporte),
            "Lugar de Origen": extract_field(r'LUGAR DE ORIGEN\s*([\w\s\-]+)', datos_transporte),
            "Lugar de Destino": extract_field(r'LUGAR DE DESTINO\s*([\w\s\-]+)', datos_transporte),
            "Fecha y Hora de Salida": extract_field(r'FECHA Y HORA DE SALIDA\s*([\w\s/:\-APM]+)', datos_transporte),
            "Vigencia de la Guía": extract_field(r'VIGENCIA DE LA GUIA\s*([\w\s]+)', datos_transporte)
        },
        "Descripción del Producto": {
            "Producto": extract_field(r'PRODUCTO\s*([\w\s]+)', descripcion_producto),
            "Propietario": extract_field(r'PROPIETARIO\s*([\w\s]+)', descripcion_producto),
            "Comercializadora": extract_field(r'COMERCIALIZADORA\s*([\w\s]+)', descripcion_producto),
            "Sellos": extract_field(r'SELLOS\s*([\w\-]+)', descripcion_producto),
            "Temperatura (°F)": extract_field(r'TEMPERATURA\s*[\(°F\)]*\s*([\d\.]+[°F]*)', descripcion_producto),
            "API": extract_field(r'API\s*([\d\.]+)', descripcion_producto),
            "Salinidad (%)": extract_field(r'SALINIDAD\s*[%]*\s*([\d\.]+)', descripcion_producto),
            "PVC": extract_field(r'PVC\s*([\d\.]+)', descripcion_producto),
            "BSW (%)": extract_field(r'BSW\s*[%]*\s*([\d\.]+)', descripcion_producto),
            "Azufre (S%)": extract_field(r'AZUFRE\s*[(S%)]*\s*([\d\.]+)', descripcion_producto)
        },
        "Volumen Transportado": {
            "Barriles Brutos": extract_field(r'BARRILES BRUTOS\s*([\d\.,]+)', volumen_transportado),
            "Barriles a 60°F": extract_field(r'BARRILES A 60[F]*\s*([\d\.,]+)', volumen_transportado),
            "Barriles Netos": extract_field(r'BARRILES NETOS\s*([\d\.,]+)', volumen_transportado)
        }
    }
    return datos

def app():
    st.title("App OCR para Guías de Transporte")

    uploaded_file = st.file_uploader("Sube una imagen de la guía (jpg, png, jpeg)", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        with st.spinner("Procesando imagen con OCR.space..."):
            try:
                texto_ocr = ocr_space_file(uploaded_file)
                st.text_area("Texto OCR Extraído", texto_ocr, height=200)
                
                datos = parse_ocr_text(texto_ocr)
                for seccion, campos in datos.items():
                    st.markdown(f"### 🟩 {seccion}")
                    df = pd.DataFrame(campos.items(), columns=["Campo", "Valor"])
                    st.table(df)
            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    app()
