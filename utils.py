import requests
from io import BytesIO

def extraer_datos_clave(imagen):
    # Convertir imagen PIL a bytes para enviar a OCR.Space
    buffered = BytesIO()
    imagen.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    # Tu API key de OCR.Space
    API_KEY = "K84668714088957"  # <-- ya colocada aquí

    # Configurar petición POST a OCR.Space
    payload = {
        'isOverlayRequired': False,
        'apikey': API_KEY,
        'language': 'spa',
    }

    files = {
        'filename': ('image.png', img_bytes)
    }

    response = requests.post('https://api.ocr.space/parse/image',
                             data=payload,
                             files=files)

    result = response.json()

    if result.get('IsErroredOnProcessing'):
        return {"Error": "No se pudo procesar la imagen OCR"}

    texto = result['ParsedResults'][0]['ParsedText']

    campos = [
        "Fecha y hora de salida",
        "Placa del cabeza tractora",
        "Placa del tanque",
        "Número de guía",
        "Empresa transportadora",
        "Cédula",
        "Conductor",
        "Casilla en blanco",
        "Lugar de origen",
        "Lugar de destino",
        "Barriles brutos",
        "Barriles netos",
        "Barriles a 60°F",
        "API",
        "BSW (%)",
        "Vigencia de guía",
        "", "", "", "", "", "",
        "Sellos"
    ]

    resultados = {}
    for campo in campos:
        if campo == "":
            resultados[campo] = ""
        else:
            resultados[campo] = ""

    for linea in texto.split('\n'):
        for campo in campos:
            if campo and campo.lower() in linea.lower():
                partes = linea.split(":")
                if len(partes) > 1:
                    valor = partes[1].strip()
                    resultados[campo] = valor

    return resultados
