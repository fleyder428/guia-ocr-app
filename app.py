import streamlit as st
import re
import json

st.set_page_config(page_title="Prueba de Extracción de Guía", layout="centered")
st.title("🧪 Prueba de Extracción Inteligente (Texto pegado manualmente)")

texto = st.text_area("📋 Pega aquí el texto extraído por OCR de la guía", height=400)

def extraer_datos_clave(texto):
    def buscar(patrones):
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    return {
        "Fecha y hora de salida": buscar([r"(?:salida.*?)[:\-]\s*(\S.+)", r"FECHA.*?SALIDA.*?[:\-]?\s*(\S.+)"]),
        "Placa del cabeza tractora": buscar([r"placa.*?cabeza.*?[:\-]?\s*([A-Z0-9\-]+)"]),
        "Placa del tanque": buscar([r"placa.*?tanque.*?[:\-]?\s*([A-Z0-9\-]+)"]),
        "Número de guía": buscar([r"gu[ií]a.*?[:\-]?\s*([A-Z0-9\-]+)"]),
        "Empresa transportadora": buscar([r"empresa transportadora\s*[:\-]?\s*(.*)"]),
        "Cédula": buscar([r"c[eé]dula.*?[:\-]?\s*([0-9\.]+)"]),
        "Conductor": buscar([r"(?:nombre del conductor|conductor)\s*[:\-]?\s*([A-ZÑÁÉÍÓÚ ]{5,})"]),
        "Casilla en blanco": "",
        "Lugar de origen": buscar([r"lugar de origen\s*[:\-]?\s*(.*)"]),
        "Lugar de destino": buscar([r"lugar de destino\s*[:\-]?\s*(.*)"]),
        "Barriles brutos": buscar([r"brutos\s*[:\-]?\s*([\d.,]+)"]),
        "Barriles netos": buscar([r"netos\s*[:\-]?\s*([\d.,]+)"]),
        "Barriles a 60°F": buscar([r"60\s*°\s*f\s*[:\-]?\s*([\d.,]+)"]),
        "API": buscar([r"\bAPI\b\s*[:\-]?\s*([\d.,]+)"]),
        "BSW (%)": buscar([r"\bBSW\b.*?%?\s*[:\-]?\s*([\d.,]+)"]),
        "Vigencia de guía": buscar([r"(?:horas de vigencia|vigencia)\s*[:\-]?\s*([\d]+)\s*horas?"]),
        "Casilla vacía 1": "",
        "Casilla vacía 2": "",
        "Casilla vacía 3": "",
        "Casilla vacía 4": "",
        "Casilla vacía 5": "",
        "Casilla vacía 6": "",
        "Sellos": buscar([r"(?:sello|sellos)\s*[:\-]?\s*(.*)"]),
    }

if texto.strip():
    st.subheader("📑 Datos extraídos (en orden):")
    datos = extraer_datos_clave(texto)
    st.json(datos)
    st.success("✅ Revisión completada. Verifica que los campos estén en orden.")
else:
    st.info("👈 Pega texto OCR para ver los resultados.")
