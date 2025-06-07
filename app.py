import streamlit as st
import requests
import re
import pandas as pd
from io import BytesIO

API_KEY = "tu_api_key_aqui"

def ocr_space_file_bytes(file_bytes, filename, api_key):
    payload = {
        'apikey': api_key,
        'language': 'spa',
        'isOverlayRequired': False,
    }
    files = {'file': (filename, file_bytes)}
    r = requests.post('https://api.ocr.space/parse/image', data=payload, files=files)
    result = r.json()
    if result.get("IsErroredOnProcessing"):
        raise Exception(f"Error en OCR.space: {result.get('ErrorMessage')}")
    parsed_results = result.get("ParsedResults")
    if parsed_results:
        return parsed_results[0].get("ParsedText", "")
    return ""

def normalize_text(text):
    # Reemplazos comunes para corregir errores de OCR en español y formatos específicos
    replacements = {
        r"PLANT[OA]": "PLANTA",
        r"LUCAR": "LUGAR",
        r"LUCAR DE ORIGEN": "LUGAR DE ORIGEN",
        r"LUCAR DE DESTINO": "LUGAR DE DESTINO",
        r"PETROLEI]M": "PETROLEO",
        r"PETROLEL\$*\*Á": "PETROLEO",
        r"GUILLERMO GRANAnos": "GUILLERMO GRANADOS",
        r"PLACAS DEL CABEZOTE": "PLACAS DEL CABEZA TRACTORA",
        r"BARRILES BRUTOS": "BARRILES BRUTOS",
        r"BARRILES NETOS": "BARRILES NETOS",
        r"BARRILES A 60°F": "BARRILES A 60°F",
        r"VOLUMEN EN SARRLES": "VOLUMEN EN BARRILES",
        r"TS CASANARE SAS": "TS CASANARE SAS",
        r"CPF PENOARE": "CPF PENDARE",
        r"ESTAC\$b'4 VASCONIA": "ESTACION VASCONIA",
        r"ANÁLISIS DE LABORATORIO": "ANÁLISIS DE LABORATORIO",
        r"FACTURA O REMISIÓN NO": "FACTURA O REMISIÓN NO",
        r"CÉDU": "CÉDULA",
        r"DE DESTINO": "LUGAR DE DESTINO",
        r"DE ORIGEN": "LUGAR DE ORIGEN",
        r"\s+": " ",  # espacios multiples a uno solo
    }
    # Aplica todos los reemplazos
    for wrong, right in replacements.items():
        text = re.sub(wrong, right, text, flags=re.IGNORECASE)
    # Quitar caracteres no ASCII que suelen fallar
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = text.strip()
    return text

def extract_fields(text):
    text = normalize_text(text)

    datos = {
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
        "Vigencia de Guía": "",
        "Casilla en Blanco 2": "",
        "Casilla en Blanco 3": "",
        "Casilla en Blanco 4": "",
        "Casilla en Blanco 5": "",
        "Casilla en Blanco 6": "",
        "Casilla en Blanco 7": "",
        "Sellos": "",
    }

    # FECHA Y HORA DE SALIDA: busca fechas en varios formatos dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd y hora
    fecha_hora = re.search(
        r"FECHA Y HORA DE SALIDA\s*[:\-]?\s*([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4}(?:\s+[\d]{1,2}[:h][\d]{2}(?:[:][\d]{2})?\s*[APMapm\.]{0,4})?)", text)
    if fecha_hora:
        datos["Fecha y Hora de Salida"] = fecha_hora.group(1).strip()
    else:
        # Alternativa: solo fecha y hora en líneas cercanas
        alt_fecha = re.search(r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})", text)
        alt_hora = re.search(r"(\d{1,2}[:h]\d{2}(?::\d{2})?\s*[APMapm\.]{0,4})", text)
        if alt_fecha:
            datos["Fecha y Hora de Salida"] = alt_fecha.group(1)
            if alt_hora:
                datos["Fecha y Hora de Salida"] += " " + alt_hora.group(1)

    # PLACA DEL CABEZA TRACTORA: patrón flexible, mayúsculas, números, guiones
    placa_ct = re.search(r"PLACAS DEL CABEZA TRACTORA\s*[:\-]?\s*([A-Z0-9\-]{4,10})", text)
    if placa_ct:
        datos["Placa del Cabeza Tractora"] = placa_ct.group(1).strip()

    # PLACA DEL TANQUE
    placa_tanque = re.search(r"PLACAS DEL TANQUE\s*[:\-]?\s*([A-Z0-9\-]{4,10})", text)
    if placa_tanque:
        datos["Placa del Tanque"] = placa_tanque.group(1).strip()

    # NÚMERO DE GUÍA - busca números cercanos a "GUÍA"
    num_guia = re.search(r"GUÍA.*?(\d{3,10})", text, re.IGNORECASE)
    if num_guia:
        datos["Número de Guía"] = num_guia.group(1).strip()

    # EMPRESA TRANSPORTADORA: letras y espacios
    empresa = re.search(r"EMPRESA TRANSPORTADORA\s*[:\-]?\s*([A-Z0-9\s\.]+)", text)
    if empresa:
        datos["Empresa Transportadora"] = empresa.group(1).strip()

    # CÉDULA (números con puntos o sin)
    cedula = re.search(r"CÉDULA\s*[:\-]?\s*([\d\.]+)", text)
    if cedula:
        datos["Cédula"] = cedula.group(1).strip()

    # CONDUCTOR - letras y espacios
    conductor = re.search(r"NOMBRE DEL CONDUCTOR\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s]+)", text)
    if conductor:
        datos["Conductor"] = conductor.group(1).strip()

    # Casilla en blanco 1 (vacío)
    datos["Casilla en Blanco 1"] = ""

    # LUGAR DE ORIGEN
    origen = re.search(r"LUGAR DE ORIGEN\s*[:\-]?\s*([A-Z0-9\s\.,\-]+)", text)
    if origen:
        datos["Lugar de Origen"] = origen.group(1).strip()

    # LUGAR DE DESTINO
    destino = re.search(r"LUGAR DE DESTINO\s*[:\-]?\s*([A-Z0-9\s\.,\-]+)", text)
    if destino:
        datos["Lugar de Destino"] = destino.group(1).strip()

    # BARRILES BRUTOS
    barriles_brutos = re.search(r"BARRILES BRUTOS\s*[:\-]?\s*([\d,\.]+)", text, re.IGNORECASE)
    if barriles_brutos:
        datos["Barriles Brutos"] = barriles_brutos.group(1).replace(",", ".").strip()

    # BARRILES NETOS
    barriles_netos = re.search(r"BARRILES NETOS\s*[:\-]?\s*([\d,\.]+)", text, re.IGNORECASE)
    if barriles_netos:
        datos["Barriles Netos"] = barriles_netos.group(1).replace(",", ".").strip()

    # BARRILES A 60°F
    barriles_60 = re.search(r"BARRILES A 60°F\s*[:\-]?\s*([\d,\.]+)", text, re.IGNORECASE)
    if barriles_60:
        datos["Barriles a 60°F"] = barriles_60.group(1).replace(",", ".").strip()

    # API
    api = re.search(r"API\s*[:\-]?\s*([\d,\.]+)", text, re.IGNORECASE)
    if api:
        datos["API"] = api.group(1).replace(",", ".").strip()

    # BSW (%)
    bsw = re.search(r"BSW\s*%?\s*[:\-]?\s*([\d,\.]+)", text, re.IGNORECASE)
    if bsw:
        datos["BSW (%)"] = bsw.group(1).replace(",", ".").strip()

    # VIGENCIA DE GUÍA (horas)
    vigencia = re.search(r"HORAS DE VIGENCIA\s*[:\-]?\s*(\d+)", text, re.IGNORECASE)
    if vigencia:
        datos["Vigencia de Guía"] = vigencia.group(1).strip()

    # Casillas en blanco 2 a 7 (vacías)
    for i in range(2, 8):
        datos[f"Casilla en Blanco {i}"] = ""

    # SELLOS
    sellos = re.search(r"SELLOS\s*[:\-]?\s*([A-Z0-9\s\-]+)", text)
    if sellos:
        datos["Sellos"] = sellos.group(1).strip()

    return datos

def main():
    st.title("Extracción OCR y Exportación a Excel - Guías de Transporte")

    uploaded_file = st.file_uploader("Sube la imagen o PDF de la guía", type=["jpg", "jpeg", "png", "pdf"])
    if uploaded_file is not None:
        try:
            # Leer bytes
            file_bytes = uploaded_file.read()
            filename = uploaded_file.name

            with st.spinner("Procesando OCR..."):
                texto_extraido = ocr_space_file_bytes(file_bytes, filename, API_KEY)

            st.subheader("Texto extraído (normalizado):")
            st.text_area("", normalize_text(texto_extraido), height=300)

            datos_extraidos = extract_fields(texto_extraido)
            df = pd.DataFrame([datos_extraidos])

            st.subheader("Datos extraídos:")
            st.dataframe(df)

            # Botón para descargar Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Datos')
                writer.save()
            output.seek(0)

            st.download_button(
                label="Descargar datos en Excel",
                data=output,
                file_name="datos_guia.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
