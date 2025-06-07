import streamlit as st
import requests
import re
import pandas as pd
from io import BytesIO

# Tu API Key de OCR.space, reemplaza aquí o usa st.secrets
api_key = "K84668714088957"

def normalize_text(text):
    # Correcciones comunes de errores OCR, usando re.escape para evitar errores de regex
    replacements = {
        "LUCAR": "LUGAR",
        "GIJíA": "GUÍA",
        "TECPETROL": "TEC PETROL",
        "PETROLEL$*Á": "PETRÓLEO",
        "PETROLEEM": "PETRÓLEO",
        "CÉDU": "CÉDULA",
        "ESTAC$b'4": "ESTACIÓN",
        "R773fi1": "R77361",
        "VOLUMEN EN BARRILES": "VOLUMEN EN BARRILES",
        "EARR\\LES": "BARRILES",
        "ANÁLISIS OE LABORATOPd9J530f_": "ANÁLISIS DE LABORATORIO",
    }
    for wrong, right in replacements.items():
        text = re.sub(re.escape(wrong), right, text, flags=re.IGNORECASE)
    return text

def extract_fields(text):
    text = normalize_text(text)

    # Inicializar diccionario con las claves y valores vacíos para mantener el orden
    campos = {
        "Fecha y Hora de Salida": "",
        "Placa del Cabeza Tractora": "",
        "Placa del Tanque": "",
        "Número de Guía": "",
        "Empresa Transportadora": "",
        "Cédula": "",
        "Conductor": "",
        "Casilla en Blanco 1": "",
        "Lugar de Origen": "",
        "Lugar de Destino": "",
        "Barriles Brutos": "",
        "Barriles Netos": "",
        "Barriles a 60°F": "",
        "API": "",
        "BSW (%)": "",
        "Vigencia de la Guía": "",
        "Casilla en Blanco 2": "",
        "Casilla en Blanco 3": "",
        "Casilla en Blanco 4": "",
        "Casilla en Blanco 5": "",
        "Casilla en Blanco 6": "",
        "Sellos": ""
    }

    # Buscar con regex cada campo clave basado en posibles patrones comunes

    # Fecha y hora de salida (buscando una fecha en formato dd/mm/yyyy o similar)
    fecha_salida = re.search(r'FECHA Y HORA DE SALIDA\s*[:\-]?\s*([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4}(?:\s*-\s*[0-9]{1,2}:[0-9]{2}(?:\s*[APMapm]{2})?)?)', text, re.IGNORECASE)
    if fecha_salida:
        campos["Fecha y Hora de Salida"] = fecha_salida.group(1).strip()

    # Placa del cabeza tractora
    placa_cabeza = re.search(r'PLACAS DEL CABEZOTE\s*[:\-]?\s*([A-Z0-9\-]+)', text, re.IGNORECASE)
    if placa_cabeza:
        campos["Placa del Cabeza Tractora"] = placa_cabeza.group(1).strip()

    # Placa del tanque
    placa_tanque = re.search(r'PLACAS DEL TANQUE\s*[:\-]?\s*([A-Z0-9\-]+)', text, re.IGNORECASE)
    if placa_tanque:
        campos["Placa del Tanque"] = placa_tanque.group(1).strip()

    # Número de guía (buscando "GUÍA ÚNICA" o solo número cercano a la palabra guía)
    num_guia = re.search(r'(?:NÚMERO DE GUÍA|GUÍA|GUIA ÚNICA|GUÍ A ÚNICA|GUÍA ÚNICA|GUÍA)\s*[:\-]?\s*([0-9]{1,6})', text, re.IGNORECASE)
    if not num_guia:
        # Si no encuentra el patrón anterior, busca solo un número grande cerca de "166" (ejemplo)
        num_guia = re.search(r'\b(\d{2,6})\b', text)
    if num_guia:
        campos["Número de Guía"] = num_guia.group(1).strip()

    # Empresa transportadora
    empresa = re.search(r'EMPRESA TRANSPORTADORA\s*[:\-]?\s*([A-Z0-9\s\.]+)', text, re.IGNORECASE)
    if empresa:
        campos["Empresa Transportadora"] = empresa.group(1).strip()

    # Cédula
    cedula = re.search(r'CÉDULA\s*[:\-]?\s*([0-9]{6,12})', text, re.IGNORECASE)
    if cedula:
        campos["Cédula"] = cedula.group(1).strip()

    # Conductor
    conductor = re.search(r'NOMBRE DEL CONDUCTOR\s*[:\-]?\s*([A-Z\s]+)', text, re.IGNORECASE)
    if conductor:
        campos["Conductor"] = conductor.group(1).strip()

    # Casilla en blanco 1 (solo dejamos vacía)

    # Lugar de origen
    lugar_origen = re.search(r'LUGAR DE ORIGEN\s*[:\-]?\s*([A-Z0-9\s\.\-]+)', text, re.IGNORECASE)
    if lugar_origen:
        campos["Lugar de Origen"] = lugar_origen.group(1).strip()

    # Lugar de destino
    lugar_destino = re.search(r'LUGAR DE DESTINO\s*[:\-]?\s*([A-Z0-9\s\.\-]+)', text, re.IGNORECASE)
    if lugar_destino:
        campos["Lugar de Destino"] = lugar_destino.group(1).strip()

    # Barriles brutos
    barriles_brutos = re.search(r'BARRILES BRUTOS\s*[:\-]?\s*([\d\.,]+)', text, re.IGNORECASE)
    if barriles_brutos:
        campos["Barriles Brutos"] = barriles_brutos.group(1).strip()
    else:
        # A veces solo "BARRILES" o "VOLUMEN EN BARRILES" puede indicar brutos
        volumen = re.search(r'VOLUMEN EN BARRILES\s*[:\-]?\s*([\d\.,]+)', text, re.IGNORECASE)
        if volumen:
            campos["Barriles Brutos"] = volumen.group(1).strip()

    # Barriles netos
    barriles_netos = re.search(r'BARRILES NETOS\s*[:\-]?\s*([\d\.,]+)', text, re.IGNORECASE)
    if barriles_netos:
        campos["Barriles Netos"] = barriles_netos.group(1).strip()

    # Barriles a 60°F
    barriles_60 = re.search(r'BARRILES A 60°F\s*[:\-]?\s*([\d\.,]+)', text, re.IGNORECASE)
    if barriles_60:
        campos["Barriles a 60°F"] = barriles_60.group(1).strip()

    # API
    api = re.search(r'API\s*[:\-]?\s*([\d\.,]+)', text, re.IGNORECASE)
    if api:
        campos["API"] = api.group(1).strip()

    # BSW (%)
    bsw = re.search(r'BSW\s*[%]?\s*[:\-]?\s*([\d\.,]+)', text, re.IGNORECASE)
    if bsw:
        campos["BSW (%)"] = bsw.group(1).strip()

    # Vigencia de la guía
    vigencia = re.search(r'HORAS DE VIGENCIA\s*[:\-]?\s*([\d]+)', text, re.IGNORECASE)
    if vigencia:
        campos["Vigencia de la Guía"] = vigencia.group(1).strip() + " horas"

    # Casillas en blanco 2 a 6 (dejamos vacías)

    # Sellos (buscando números o códigos separados por guiones o espacios)
    sellos = re.search(r'SELLOS?\s*[:\-]?\s*([0-9\- ]+)', text, re.IGNORECASE)
    if sellos:
        campos["Sellos"] = sellos.group(1).strip()

    return campos

def ocr_space_file(filename, api_key):
    """Envía archivo a OCR.space y devuelve texto extraído"""
    with open(filename, 'rb') as f:
        payload = {
            'apikey': api_key,
            'language': 'spa',
            'isOverlayRequired': False,
        }
        files = {'file': (filename, f)}
        r = requests.post('https://api.ocr.space/parse/image', data=payload, files=files)
    result = r.json()
    if result.get("IsErroredOnProcessing"):
        raise Exception(f"Error en OCR.space: {result.get('ErrorMessage')}")
    parsed_results = result.get("ParsedResults")
    if parsed_results:
        return parsed_results[0].get("ParsedText", "")
    return ""

def main():
    st.title("OCR para Guías de Transporte de Crudo - Extracción de Datos")

    uploaded_file = st.file_uploader("Sube una imagen o PDF de la guía", type=["png", "jpg", "jpeg", "pdf"])

    if uploaded_file:
        # Guardar archivo temporal para enviarlo a OCR.space
        with open("temp_upload", "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            texto = ocr_space_file("temp_upload", api_key)
            st.text_area("Texto extraído por OCR:", texto, height=300)

            datos = extract_fields(texto)

            st.write("Datos extraídos:")
            df = pd.DataFrame(list(datos.items()), columns=["Campo", "Valor"])
            st.dataframe(df)

            # Exportar a Excel
            towrite = BytesIO()
            df.to_excel(towrite, index=False, sheet_name="Datos")
            towrite.seek(0)
            st.download_button(
                label="Descargar Excel",
                data=towrite,
                file_name="datos_guia.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
