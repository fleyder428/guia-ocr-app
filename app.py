import streamlit as st
import pandas as pd
from utils import extraer_datos_clave
from PIL import Image
import io

st.set_page_config(page_title="Extractor de Guías", layout="centered")
st.title("📄 Extracción Inteligente de Guías - OCR")

uploaded_file = st.file_uploader("📤 Sube una imagen de la guía", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Imagen cargada", use_column_width=True)

    if st.button("🔍 Extraer datos"):
        with st.spinner("Procesando imagen..."):
            datos = extraer_datos_clave(image)

            # Mostrar resultados
            df = pd.DataFrame([datos])
            st.success("✅ Datos extraídos:")
            st.dataframe(df)

            # Exportar a Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="Guía")
                writer.close()
            output.seek(0)

            st.download_button(
                label="⬇️ Descargar Excel",
                data=output,
                file_name="guia_extraida.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
