import streamlit as st
import re
import pandas as pd
import io
# Función para limpiar texto OCR y normalizar espacios y caracteres básicos
def limpiar_texto(texto):
    texto = texto.replace('\n', ' ').replace('\r', ' ')
    texto = re.sub(r'\s+', ' ', texto)
    # Correcciones simples de OCR comunes (puedes ampliar esta lista)
    texto = texto.replace('PLACAS DEL CABEZOTE', 'PLACAS DEL CABEZOTE')
    texto = texto.replace('CPF PENüARE', 'CPF Pendare')
    texto = texto.replace('ESTAC$b\'4 VÀSCDNiA', 'Estación Guaduas')
    texto = texto.replace('COMERC-íALkZAüOZ4:TRAFlGüRA PETROLEEM', 'COMERCIALIZADORA: TRAFIGURA PETROLEUM')
    texto = texto.replace('BARRILES FiUTOS', 'BARRILES BRUTOS')
    texto = texto.replace('DESPAOHAOORA', 'DESPACHADORA')
    texto = texto.strip()
    return texto

# Función para extraer datos con base en etiquetas del texto
def extraer_datos(texto):
    texto = limpiar_texto(texto)

    def buscar_valor(etiqueta):
        # Busca el texto después de la etiqueta hasta el próximo grupo de mayúsculas o línea vacía
        patron = rf"{etiqueta}\s*([A-Z0-9ÁÉÍÓÚÑÜáéíóúñü \-.,:]+)"
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            valor = match.group(1).strip()
            # Limpiar valor recortando si hay texto de otra etiqueta dentro
            valor = re.split(r'\s{2,}', valor)[0]  # corta en doble espacio o más (como separación)
            return valor
        return ""

    datos = {
        "Fecha y hora de salida": buscar_valor("FECHA Y HORA DE SALIDA"),
        "Placa del cabeza tractora": buscar_valor("PLACAS DEL CABEZOTE"),
        "Placa del tanque": buscar_valor("PLACAS DEL TANQUE"),
        "Número de guía": buscar_valor("166|GUÍA ÚNICA PARA TRANSPORTAR PETRÓLEO CRUDO"),
        "Empresa transportadora": buscar_valor("EMPRESA TRANSPORTADORA"),
        "Cédula": buscar_valor("CÉDULA"),
        "Conductor": buscar_valor("NOMBRE DEL CONDUCTOR"),
        "Casilla en blanco 1": "",
        "Lugar de origen": buscar_valor("LUGAR DE ORIGEN"),
        "Lugar de destino": buscar_valor("LUGAR DE DESTINO"),
        "Barriles brutos": buscar_valor("BARRILES BRUTOS"),
        "Barriles netos": buscar_valor("BARRILES NETOS"),
        "Barriles a 60°F": "",  # No aparece explícito en el texto que diste
        "API": "",  # No aparece explícito en el texto que diste
        "BSW (%)": "",  # No aparece explícito en el texto que diste
        "Vigencia de guía": buscar_valor("HORAS DE VIGENCIA"),
        "Casilla en blanco 2": "",
        "Casilla en blanco 3": "",
        "Casilla en blanco 4": "",
        "Casilla en blanco 5": "",
        "Casilla en blanco 6": "",
        "Casilla en blanco 7": "",
        "Sellos": "",  # No aparece explícito en el texto que diste
    }

    return datos

st.set_page_config(page_title="Extractor de Guías OCR - Barlex", layout="centered")
st.title("📄 Extracción Específica de Guías OCR")

texto_ocr = st.text_area("Pega aquí el texto OCR completo que obtuviste:", height=300)

if st.button("Extraer datos del texto OCR"):
    if not texto_ocr.strip():
        st.error("Por favor pega el texto OCR para extraer datos.")
    else:
        datos_extraidos = extraer_datos(texto_ocr)
        st.success("Datos extraídos:")
        df = pd.DataFrame([datos_extraidos])
        st.dataframe(df)

        # Botón para descargar Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Guía")
        excel_buffer.seek(0)
        st.download_button("Descargar Excel", data=excel_buffer, file_name="datos_guia.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
