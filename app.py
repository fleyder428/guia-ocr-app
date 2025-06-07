import streamlit as st
import requests
from PIL import Image
import io
import os
from datetime import datetime
import pandas as pd

# API Key (puedes mover a secrets.toml si deseas ocultarla)
api_key = "K84668714088957"

# Función para comprimir imágenes que superan 1 MB
def reducir_tamano_imagen(imagen_pil):
    buffer = io.BytesIO()
    calidad = 95
    while True:
        buffer.seek(0)
        imagen_pil.save(buffer, format="JPEG", quality=calidad)
        if buffer.tell() <= 1024 * 1024 or calidad <= 20:
            break
        calidad -= 5
    buffer.seek(0)
    return buffer

# Enviar imagen a OCR.space
def enviar_a_ocr(imagen):
    imagen_pil = Image.open(imagen).convert("RGB")
    imagen_bytes = reducir_tamano_imagen(imagen_pil)

    response = requests.post(
        "https://api.ocr.space/parse/image",
        files={"filename": imagen_bytes},
        data={"apikey": api_key, "language": "spa"},
    )
    result = response.json()
    if result.get("IsErroredOnProcessing"):
        return None, result.get("ErrorMessage", "Error desconocido")
    return result["ParsedResults"][0]["ParsedText"], None

# Función de extracción estructurada
def extraer_datos(texto):
    datos = {
        "Datos Generales": {
            "Número de Guía": extraer_por_patron(texto, r"Número de Gu[ií]a[:\s]*([0-9]{3,})"),
            "Número de Factura/Remisión": extraer_por_patron(texto, r"(Factura|Remisión)[^\d]*([0-9]{5,})"),
            "Lugar y Fecha de Expedición": extraer_por_patron(texto, r"(?i)LUGAR Y FECHA DE EXPEDICIÓN[:\s]*(.*)"),
            "Planta o Campo Productor": extraer_por_patron(texto, r"PLANTA O CAMPO PRODUCTOR[:\s]*(.*)")
        },
        "Datos del Destinatario": {
            "Despachado a": extraer_por_patron(texto, r"DESPACHADO A[:\s]*(.*)"),
            "Dirección": extraer_por_patron(texto, r"DIRECCIÓN[:\s]*(.*)"),
            "Ciudad": extraer_por_patron(texto, r"CIUDAD[:\s]*(.*)"),
            "Código ONU": extraer_por_patron(texto, r"CÓDIGO[:\s]*([A-Z]{2,4}\s*\d{3,5})")
        },
        "Datos del Transporte": {
            "Conductor": extraer_por_patron(texto, r"NOMBRE DEL CONDUCTOR[:\s]*(.*)"),
            "Cédula": extraer_por_patron(texto, r"C[EÉ]DULA[:\s]*([0-9]{6,})"),
            "Empresa Transportadora": extraer_por_patron(texto, r"EMPRESA TRANSPORTADORA[:\s]*(.*)"),
            "Placa del Cabeza Tractora": extraer_por_patron(texto, r"CABEZOTE[:\s]*([A-Z]{3}\d{3})"),
            "Placa del Tanque": extraer_por_patron(texto, r"TANQUE[:\s]*([A-Z]{1,3}\d{3,5})"),
            "Lugar de Origen": extraer_por_patron(texto, r"LUGAR DE ORIGEN[:\s]*(.*)"),
            "Lugar de Destino": extraer_por_patron(texto, r"LUGAR DE DESTINO[:\s]*(.*)"),
            "Fecha y Hora de Salida": extraer_por_patron(texto, r"SALIDA[:\s]*(\d{2}/\d{2}/\d{4}.*)"),
            "Vigencia de la Guía": extraer_por_patron(texto, r"VIGENCIA.*?(\d{1,3})\s*horas", flags=re.IGNORECASE)
        },
        "Descripción del Producto": {
            "Producto": extraer_por_patron(texto, r"DESCRIPCI[ÓO]N DEL PRODUCTO[:\s]*(.*)"),
            "Sellos": extraer_por_patron(texto, r"SELLO[S]?[:\s]*(\d{4,}-?\d*)"),
            "API": extraer_por_patron(texto, r"A\.?P\.?I\.?[:\s]*([\d.]+)"),
            "BSW (%)": extraer_por_patron(texto, r"B\.?S\.?W\.?[:\s]*([\d.]+)%?")
        },
        "Volumen Transportado": {
            "Barriles Brutos": extraer_por_patron(texto, r"BRUTO[S]?[:\s]*([\d.]+)"),
            "Barriles Netos": extraer_por_patron(texto, r"NETO[S]?[:\s]*([\d.]+)"),
            "Barriles a 60°F": extraer_por_patron(texto, r"60.?F[:\s]*([\d.]+)")
        }
    }
    return datos

# Utilidad para extraer con regex
import re
def extraer_por_patron(texto, patron, flags=0):
    match = re.search(patron, texto, flags)
    return match.group(1).strip() if match else ""

# Mostrar datos en forma de tablas por sección
def mostrar_datos_estructurados(datos):
    for seccion, campos in datos.items():
        st.markdown(f"### 🟩 {seccion}")
        df = pd.DataFrame(list(campos.items()), columns=["Campo", "Valor"])
        st.table(df)

# Crear DataFrame para Excel
def crear_dataframe_para_excel(datos):
    filas = []
    for seccion, campos in datos.items():
        for campo, valor in campos.items():
            filas.append({"Sección": seccion, "Campo": campo, "Valor": valor})
    return pd.DataFrame(filas)

# INTERFAZ DE LA APP
st.set_page_config(page_title="OCR Guías de Petróleo", layout="centered")
st.title("📄 Extracción de Datos de Guías de Transporte de Crudo")

imagen_subida = st.file_uploader("📤 Sube una imagen o escaneo de la guía", type=["jpg", "jpeg", "png", "pdf"])

if imagen_subida:
    st.image(imagen_subida, caption="Imagen cargada", use_column_width=True)
    texto, error = enviar_a_ocr(imagen_subida)
    if error:
        st.error(f"❌ Error en OCR.space: {error}")
    elif texto:
        datos = extraer_datos(texto)
        mostrar_datos_estructurados(datos)

        df_excel = crear_dataframe_para_excel(datos)
        buffer_excel = io.BytesIO()
        df_excel.to_excel(buffer_excel, index=False, sheet_name="Datos OCR", engine="openpyxl")
        buffer_excel.seek(0)

        st.download_button(
            label="⬇️ Descargar Excel",
            data=buffer_excel,
            file_name="datos_guia_ocr.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ No se pudo extraer texto de la imagen.")

