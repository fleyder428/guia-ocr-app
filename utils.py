def extraer_datos_clave(texto):
    datos = {
        "Fecha y hora de salida": "",
        "Placa del cabeza tractora": "",
        "Placa del tanque": "",
        "Número de guía": "",
        "Empresa transportadora": "",
        "Cédula": "",
        "Conductor": "",
        "Casilla en blanco": "",
        "Lugar de origen": "",
        "Lugar de destino": "",
        "Barriles brutos": "",
        "Barriles netos": "",
        "Barriles a 60°F": "",
        "API": "",
        "BSW (%)": "",
        "Vigencia de guía": "",
        "Casilla en blanco 1": "",
        "Casilla en blanco 2": "",
        "Casilla en blanco 3": "",
        "Casilla en blanco 4": "",
        "Casilla en blanco 5": "",
        "Casilla en blanco 6": "",
        "Sellos": ""
    }

    lineas = texto.splitlines()

    for i, linea in enumerate(lineas):
        linea_lower = linea.lower()

        if "fecha y hora de salida" in linea_lower:
            if ":" in linea:
                datos["Fecha y hora de salida"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Fecha y hora de salida"] = lineas[i+1].strip()

        elif "placas del cabezote" in linea_lower or "placas del cabeza tractora" in linea_lower:
            if ":" in linea:
                datos["Placa del cabeza tractora"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Placa del cabeza tractora"] = lineas[i+1].strip()

        elif "placas del tanque" in linea_lower:
            if ":" in linea:
                datos["Placa del tanque"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Placa del tanque"] = lineas[i+1].strip()

        elif "número de guía" in linea_lower or "factura o remisión no" in linea_lower:
            if ":" in linea:
                datos["Número de guía"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Número de guía"] = lineas[i+1].strip()

        elif "empresa transportadora" in linea_lower:
            if ":" in linea:
                datos["Empresa transportadora"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Empresa transportadora"] = lineas[i+1].strip()

        elif "cédula" in linea_lower:
            if ":" in linea:
                datos["Cédula"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Cédula"] = lineas[i+1].strip()

        elif "nombre del conductor" in linea_lower or "conductor" in linea_lower:
            if ":" in linea:
                datos["Conductor"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Conductor"] = lineas[i+1].strip()

        elif "lugar de origen" in linea_lower:
            if ":" in linea:
                datos["Lugar de origen"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Lugar de origen"] = lineas[i+1].strip()

        elif "lugar de destino" in linea_lower or "lucar de destino" in linea_lower:
            if ":" in linea:
                datos["Lugar de destino"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Lugar de destino"] = lineas[i+1].strip()

        elif "barriles brutos" in linea_lower or ("barriles" in linea_lower and "brutos" in linea_lower):
            if ":" in linea:
                datos["Barriles brutos"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Barriles brutos"] = lineas[i+1].strip()

        elif "barriles netos" in linea_lower or ("barriles" in linea_lower and "netos" in linea_lower):
            if ":" in linea:
                datos["Barriles netos"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Barriles netos"] = lineas[i+1].strip()

        elif "barriles a 60" in linea_lower:
            if ":" in linea:
                datos["Barriles a 60°F"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Barriles a 60°F"] = lineas[i+1].strip()

        elif "api" in linea_lower:
            if ":" in linea:
                datos["API"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["API"] = lineas[i+1].strip()

        elif "bsw" in linea_lower:
            if ":" in linea:
                datos["BSW (%)"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["BSW (%)"] = lineas[i+1].strip()

        elif "horas de vigencia" in linea_lower or "vigencia" in linea_lower:
            if ":" in linea:
                datos["Vigencia de guía"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Vigencia de guía"] = lineas[i+1].strip()

        elif "sellos" in linea_lower:
            if ":" in linea:
                datos["Sellos"] = linea.split(":",1)[1].strip()
            elif i+1 < len(lineas):
                datos["Sellos"] = lineas[i+1].strip()

    return datos


def generar_excel(datos):
    import io
    import pandas as pd

    df = pd.DataFrame([datos])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Guía")
    output.seek(0)
    return output
