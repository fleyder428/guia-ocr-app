import streamlit as st
import requests
import re
import pandas as pd

# --- CONFIGURACIÓN ---
API_KEY = st.secrets["api_key"]  # Asegúrate que tu api_key esté en .streamlit/secrets.toml

# Función para llamar a OCR.space y obtener texto
def ocr_space_api(file_bytes, api_key):
    url_ocr_space = 'https://api.ocr.space/parse/image'
    headers = {
        'apikey': api_key,
    }
    files = {
        'file': ('image.jpg', file_bytes),
    }
    data = {
        'language': 'spa',
        'isOverlayRequired': False,
    }
    
    response = requests.post(url_ocr_space, files=files, data=data, headers=headers)
    
    try:
        result = response.json()
    except Exception as e:
        return f"Error: No se pudo interpretar la respuesta JSON: {e}"
    
    if 'ParsedResults' in result and result['ParsedResults']:
        parsed_text = result['ParsedResults'][0].get('ParsedText', '')
        return parsed_text
    else:
        error_message = result.get('ErrorMessage') or result.get('ErrorDetails') or 'Error desconocido en OCR'
        return f"Error en OCR.space: {error_message}"

# Normaliza texto para facilitar búsqueda
def normalize_text(text):
    replacements = {
        r'[ÁÀÂÄ]': 'A',
        r'[ÉÈÊË]': 'E',
        r'[ÍÌÎÏ]': 'I',
        r'[ÓÒÔÖ]': 'O',
        r'[ÚÙÛÜ]': 'U',
        r'Ñ': 'N',
        r'[^A-Z0-9\s]': ' ',  # elimina caracteres especiales, dejando espacios y números
    }
    text = text.upper()
    for wrong, right in replacements.items():
        text = re.sub(wrong, right, text)
    # Reemplazar múltiples espacios por uno solo
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Extrae campos en el orden requerido
def extract_fields(text):
    text = normalize_text(text)
    
    # Definir expresiones regulares para cada campo, adaptarlas a la estructura que tengas
    campos = {
        "FECHA_Y_HORA_DE_SALIDA": r'FECHA Y HORA DE SALIDA\s*([0-9/:\-\sAPM]+)',
        "PLACA_CABEZA_TRACTORA": r'PLACAS DEL CABEZOTE?\s*([A-Z0-9\-]+)',
        "PLACA_TANQUE": r'PLACAS DEL TANQUE\s*([A-Z0-9\-]+)',
        "NUMERO_DE_GUIA": r'GUIA\s*UNICA\s*PARA\s*TRANSPORTAR.*?(\d{3,})',
        "EMPRESA_TRANSPORTADORA": r'EMPRESA TRANSPORTADORA\s*([A-Z\s]+)',
        "CEDULA": r'C[ÉE]DULA\s*([0-9]+)',
        "CONDUCTOR": r'NOMBRE DEL CONDUCTOR\s*([A-Z\s]+)',
        "CASILLA_EN_BLANCO_1": '',
        "LUGAR_DE_ORIGEN": r'LUGAR DE ORIGEN\s*([A-Z\s]+)',
        "LUGAR_DE_DESTINO": r'LUGAR DE DESTINO\s*([A-Z\s]+)',
        "BARRILES_BRUTOS": r'BARRILES BRUTOS?\s*([0-9.,]+)',
        "BARRILES_NETOS": r'BARRILES NETOS?\s*([0-9.,]+)',
        "BARRILES_A_60F": r'BARRILES A 60[F]?\s*([0-9.,]+)',
        "API": r'API\s*([0-9.,]+)',
        "BSW": r'BSW\s*[%]?\s*([0-9.,]+)',
        "VIGENCIA_DE_GUIA": r'HORAS DE VIGENCIA\s*([0-9]+)',
        # Seis casillas en blanco
        "CASILLA_EN_BLANCO_2": '',
        "CASILLA_EN_BLANCO_3": '',
        "CASILLA_EN_BLANCO_4": '',
        "CASILLA_EN_BLANCO_5": '',
        "CASILLA_EN_BLANCO_6": '',
        "CASILLA_EN_BLANCO_7": '',
        "SELLOS": r'SELLOS\s*([0-9\-]+)'
    }
    
    resultados = {}
    for campo, patron in campos.items():
        if patron == '':
            # Casilla en blanco
            resultados[campo] = ''
        else:
            match = re.search(patron, text)
            if match:
                resultados[campo] = match.group(1).strip()
            else:
                resultados[campo] = ''
    
    return resultados

# Crear DataFrame para Excel con orden definido
def resultados_a_dataframe(resultados):
    campos_orden = [
        "FECHA_Y_HORA_DE_SALIDA",
        "PLACA_CABEZA_TRACTORA",
        "PLACA_TANQUE",
        "NUMERO_DE_GUIA",
        "EMPRESA_TRANSPORTADORA",
        "CEDULA",
        "CONDUCTOR",
        "CASILLA_EN_BLANCO_1",
        "LUGAR_DE_ORIGEN",
        "LUGAR_DE_DESTINO",
        "BARRILES_BRUTOS",
        "BARRILES_NETOS",
        "BARRILES_A_60F",
        "API",
        "BSW",
        "VIGENCIA_DE_GUIA",
        "CASILLA_EN_BLANCO_2",
        "CASILLA_EN_BLANCO_3",
        "CASILLA_EN_BLANCO_4",
        "CASILLA_EN_BLANCO_5",
        "CASILLA_EN_BLANCO_6",
        "CASILLA_EN_BLANCO_7",
        "SELLOS"
    ]
    df = pd.DataFrame([{campo: resultados.get(campo, '') for campo in campos_orden}])
    return df

# --- STREAMLIT APP ---
st.title("Extractor OCR para Guías de Transporte de Petróleo Crudo")

uploaded_file = st.file_uploader("Sube la imagen de la guía", type=['png','jpg','jpeg','tif','tiff','bmp'])

if uploaded_file:
    st.image(uploaded_file, caption='Imagen cargada', use_container_width=True)
    
    file_bytes = uploaded_file.read()
    
    with st.spinner('Procesando OCR...'):
        texto_extraido = ocr_space_api(file_bytes, API_KEY)
    
    if texto_extraido.startswith("Error"):
        st.error(texto_extraido)
    else:
        st.success("Texto extraído correctamente")
        st.text_area("Texto extraído", texto_extraido, height=300)
        
        datos_extraidos = extract_fields(texto_extraido)
        df_resultados = resultados_a_dataframe(datos_extraidos)
        
        st.write("Datos extraídos en orden personalizado:")
        st.dataframe(df_resultados)
        
        # Botón para descargar Excel
        excel_bytes = df_resultados.to_excel(index=False, engine='openpyxl')
        st.download_button(
            label="Descargar datos en Excel",
            data=excel_bytes,
            file_name="datos_ocr_guia.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
