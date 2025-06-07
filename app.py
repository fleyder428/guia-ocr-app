import streamlit as st
import requests
from PIL import Image
import io
import pandas as pd
import re

st.set_page_config(page_title="Extractor Flexible de Guías de Crudo", layout="centered")
st.title("🛢️ Extractor de Guías con OCR flexible y limpieza")

api_key = "K84668714088957"  # Pon tu API key aquí

def compress_and_resize_image(image_file, max_size=(2000, 2000), quality=70):
    img = Image.open(image_file)
    img = img.convert("RGB")
    img.thumbnail(max_size)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return buffer

def extract_text_from_image(image):
    url_api = "https://api.ocr.space/parse/image"
    files = {
        "filename": ("image.jpg", image, "image/jpeg")
    }
    result = requests.post(
        url_api,
        files=files,
        data={
            "apikey": api_key,
            "language": "spa",
            "isOverlayRequired": False,
        },
    )
    result_json = result.json()
    if result_json.get("IsErroredOnProcessing"):
        st.error(f"❌ Error en OCR.space: {result_json.get('ErrorMessage')}")
        return ""
    return result_json["ParsedResults"][0]["ParsedText"]

def normalize_text(text):
    # Correcciones comunes de errores OCR
    replacements = {
        "LUCAR": "LUGAR",
        "GIJíA": "GUÍA",
        "TECPETROL": "TEC PETROL",
        "PETROLEL$*Á": "PETRÓLEO",
        "PETROLEEM": "PETRÓLEO",
        "CÉDU": "CÉDULA",
        "ESTAC$b'4": "ESTACIÓN",
        "R773fi1": "R77361",
        "EARR\\LES": "BARRILES",
        "HOPAS VICENCIA": "HOPAS VICENCIA",
        "DESCRIPCION": "DESCRIPCIÓN",
        "ANÁLISIS OE LABORATOPd9J530f_": "ANÁLISIS DE LABORATORIO",
        # Agrega otros reemplazos según encuentres
    }
    for wrong, right in replacements.items():
        text = re.sub(wrong, right, text, flags=re.IGNORECASE)
    return text

def flexible_search(text, keywords, after_colon=True, multiline=True):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for kw in keywords:
            if kw.lower() in line.lower():
                parts = re.split(r"[:\-]", line, maxsplit=1)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip()
                if multiline and i + 1 < len(lines):
                    val_next = lines[i+1].strip()
                    # Si la siguiente línea no contiene otra keyword, devolverla
                    if val_next and not any(k.lower() in val_next.lower() for k in keywords):
                        return val_next
    return ""

def extract_number_from_text(text, pattern):
    match = re.search(pattern, text)
    if match:
        return match.group(0).replace(",", ".")
    return ""

def extract_fields(text):
    text = normalize_text(text)

    data = []
    # Orden personalizado:
    data.append(flexible_search(text, ["fecha y hora de salida", "fecha salida", "fecha y hora", "salida"]))
    data.append(flexible_search(text, ["placas del cabezote", "placa cabeza tractora", "placas del cabezote", "placa cabezote"]))
    data.append(flexible_search(text, ["placas del tanque", "placa tanque"]))
    data.append(flexible_search(text, ["número de guía", "numero de guia", "guía", "guia", "factura o remisión no", "factura"]))
    data.append(flexible_search(text, ["empresa transportadora", "transportadora"]))
    data.append(flexible_search(text, ["cédula", "cedula", "céd"]))
    data.append(flexible_search(text, ["nombre del conductor", "conductor"]))
    data.append("")  # Casilla en blanco
    data.append(flexible_search(text, ["lugar de origen", "origen", "lugar de expedición", "planta o campo productor", "cpf"]))
    data.append(flexible_search(text, ["lugar de destino", "destino"]))

    # Extraer barriles con búsqueda flexible
    barriles_brutos = flexible_search(text, ["barriles brutos", "volumen en barriles", "barriles"])
    if not barriles_brutos:
        barriles_brutos = extract_number_from_text(text, r"\b\d{2,4}[.,]\d{1,2}\b")
    data.append(barriles_brutos)

    barriles_netos = flexible_search(text, ["barriles netos", "netos"])
    if not barriles_netos:
        barriles_netos = extract_number_from_text(text, r"\b\d{2,4}[.,]\d{1,2}\b")
    data.append(barriles_netos)

    barriles_60 = flexible_search(text, ["barriles a 60", "barriles a 60°f"])
    if not barriles_60:
        barriles_60 = extract_number_from_text(text, r"\b\d{2,4}[.,]\d{1,2}\b")
    data.append(barriles_60)

    data.append(flexible_search(text, ["api"]))
    data.append(flexible_search(text, ["bsw", "bsw (%)"]))
    data.append(flexible_search(text, ["horas de vigencia", "vigencia"]))

    data.extend([""] * 6)  # Seis casillas en blanco

    data.append(flexible_search(text, ["sellos", "sello"]))

    return data

uploaded_file = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption="Imagen cargada", use_container_width=True)
    image_compressed = compress_and_resize_image(uploaded_file)

    with st.spinner("🧠 Analizando imagen con OCR..."):
        texto_extraido = extract_text_from_image(image_compressed)

    if texto_extraido:
        st.subheader("📝 Texto extraído (revisar):")
        st.text_area("Texto OCR", texto_extraido, height=300)

        datos_extraidos = extract_fields(texto_extraido)

        nombres_campos = [
            "Fecha y Hora de Salida", "Placa Cabeza Tractora", "Placa del Tanque", "Número de Guía",
            "Empresa Transportadora", "Cédula", "Conductor", "Casilla en blanco",
            "Lugar de Origen", "Lugar de Destino", "Barriles Brutos", "Barriles Netos", "Barriles a 60°F",
            "API", "BSW (%)", "Vigencia de Guía",
            "Casilla 1", "Casilla 2", "Casilla 3", "Casilla 4", "Casilla 5", "Casilla 6",
            "Sellos"
        ]

        df = pd.DataFrame([datos_extraidos], columns=nombres_campos)
        st.success("✅ Datos extraídos:")
        st.dataframe(df, use_container_width=True)

        buffer_excel = io.BytesIO()
        df.to_excel(buffer_excel, index=False)
        buffer_excel.seek(0)
        st.download_button("📥 Descargar Excel", data=buffer_excel, file_name="datos_guia_extraidos.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("No se pudo extraer texto de la imagen.")
