import streamlit as st
from PIL import Image
import requests
import io
import pandas as pd
import re

API_KEY = "K84668714088957"  # Tu clave API OCR.space

def ocr_space_api(imagen_bytes):
    url_api = "https://api.ocr.space/parse/image"
    archivos = {'filename': ('imagen.jpg', imagen_bytes, 'image/jpeg')}
    datos = {'apikey': API_KEY, 'language': 'spa', 'isOverlayRequired': False}
    try:
        respuesta = requests.post(url_api, files=archivos, data=datos, timeout=30)
        resultado = respuesta.json()
    except requests.exceptions.Timeout:
        raise Exception("Timeout en la petición a OCR.space")
    except Exception as e:
        raise Exception(f"Error en la petición OCR: {e}")

    if resultado.get("IsErroredOnProcessing"):
        raise Exception(resultado.get("ErrorMessage", ["Error desconocido en OCR"])[0])

    texto = resultado['ParsedResults'][0]['ParsedText']
    return texto

def extraer_datos_clave(texto):
    def buscar(patron):
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            valor = match.group(1).strip()
            valor = re.sub(r"[\n\r\t]+", " ", valor)
            return valor
        return ""

    datos = {
        "Fecha y hora de salida": buscar(r"Fecha y Hora de Salida\s*[:\t]*([\d/]+(?: -? ?\d{1,2}:\d{2} [APMapm]{2})?)"),
        "Placa del cabeza tractora": buscar(r"Placa del Cabeza Tractora\s*[:\t]*([A-Z0-9\-]+)"),
        "Placa del tanque": buscar(r"Placa del Tanque\s*[:\t]*([A-Z0-9\-]+)"),
        "Número de guía": buscar(r"Número de Guía\s*[:\t]*([A-Z0-9\-]+)"),
        "Empresa transportadora": buscar(r"Empresa Transportadora\s*[:\t]*(.+)"),
        "Cédula": buscar(r"Cédula\s*[:\t]*([0-9]+)"),
        "Conductor": buscar(r"Conductor\s*[:\t]*([A-ZÑÁÉÍÓÚa-zñáéíóú ]+)"),
        "Casilla en blanco 1": "",
        "Lugar de origen": buscar(r"Lugar de Origen\s*[:\t]*(.+)"),
        "Lugar de destino": buscar(r"Lugar de Destino\s*[:\t]*(.+)"),
        "Barriles brutos": buscar(r"Barriles Brutos\s*[:\t]*([\d.,]+)"),
        "Barriles netos": buscar(r"Barriles Netos\s*[:\t]*([\d.,]+)"),
        "Barriles a 60°F": buscar(r"Barriles a 60°F\s*[:\t]*([\d.,]+)"),
        "API": buscar(r"API\s*[:\t]*([\d.,]+)"),
        "BSW (%)": buscar(r"BSW\s*\(%\)?\s*[:\t]*([\d.,]+)"),
        "Vigencia de guía": buscar(r"Vigencia de la Guía\s*[:\t]*([\d]+) horas"),
        "Casilla en blanco 2": "",
        "Casilla en blanco 3": "",
        "Casilla en blanco 4": "",
        "Casilla en blanco 5": "",
        "Casilla en blanco 6": "",
        "Casilla en blanco 7": "",
        "Sellos": buscar(r"Sellos\s*[:\t]*(.+)")
    }
    return datos

st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("📄 Extracción Inteligente de Guías - OCR")

# --- Subida de imagen y OCR ---
archivo_subido = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if archivo_subido:
    imagen = Image.open(archivo_subido)

    # Reducir tamaño si > 500 KB para evitar errores
    buf_original = io.BytesIO()
    imagen.save(buf_original, format='JPEG', quality=50, optimize=True)
    imagen_bytes = buf_original.getvalue()

    if len(imagen_bytes) > 500 * 1024:
        escala = (500 * 1024) / len(imagen_bytes)
        escala = min(escala, 1)
        nueva_ancho = int(imagen.width * escala**0.5)
        nueva_alto = int(imagen.height * escala**0.5)
        imagen = imagen.resize((nueva_ancho, nueva_alto), Image.Resampling.LANCZOS)
        buf_reducido = io.BytesIO()
        imagen.save(buf_reducido, format='JPEG', quality=50)
        imagen_bytes = buf_reducido.getvalue()

    st.image(imagen, caption="Imagen cargada", use_container_width=True)

    if st.button("🔍 Extraer datos de imagen"):
        with st.spinner("Procesando con OCR.space..."):
            try:
                texto_ocr = ocr_space_api(imagen_bytes)
                datos = extraer_datos_clave(texto_ocr)

                columnas_ordenadas = [
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

                df = pd.DataFrame([datos])
                df = df.reindex(columns=columnas_ordenadas, fill_value="")

                st.success("✅ Datos extraídos correctamente")
                st.dataframe(df)

                excel = io.BytesIO()
                with pd.ExcelWriter(excel, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Guía")
                excel.seek(0)

                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=excel,
                    file_name="guia_extraida.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error al procesar OCR: {e}")

# --- Opción para pegar texto OCR manualmente ---
st.markdown("---")
st.subheader("Opción 2: Pegar texto OCR directamente")

texto_ocr_manual = st.text_area(
    "📋 Pega aquí el texto OCR extraído previamente de la guía",
    height=300,
)

if st.button("🔍 Extraer datos del texto OCR pegado", key="extraer_texto"):
    if texto_ocr_manual.strip():
        try:
            datos = extraer_datos_clave(texto_ocr_manual)

            columnas_ordenadas = [
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

            df = pd.DataFrame([datos])
            df = df.reindex(columns=columnas_ordenadas, fill_value="")

            st.success("✅ Datos extraídos correctamente desde texto OCR pegado")
            st.dataframe(df)

            excel = io.BytesIO()
            with pd.ExcelWriter(excel, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Guía")
            excel.seek(0)

            st.download_button(
                label="⬇️ Descargar Excel",
                data=excel,
                file_name="guia_extraida_desde_texto.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Error al extraer datos: {e}")
    else:
        st.warning("Por favor, pega primero el texto OCR para extraer.")
