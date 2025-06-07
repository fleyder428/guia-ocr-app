import pytesseract
import re
from PIL import Image

def extraer_datos_clave(imagen):
    # Usar pytesseract para extraer texto de la imagen
    texto = pytesseract.image_to_string(imagen, lang='spa')

    # Diccionario con las claves en el orden requerido
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
        "", "", "", "", "", "",  # 6 casillas en blanco
        "Sellos"
    ]

    # Crear diccionario para los resultados, inicialmente vacíos o blancos donde toca
    resultados = {}
    for campo in campos:
        if campo == "":
            resultados[campo] = ""
        else:
            resultados[campo] = ""

    # Aquí podrías mejorar con expresiones regulares específicas para extraer cada dato
    # Por ahora, como ejemplo, intentaremos extraer líneas basadas en las claves (simplificado)

    for linea in texto.split('\n'):
        for campo in campos:
            if campo and campo.lower() in linea.lower():
                # Extraer texto después de la clave (ejemplo simple)
                valor = linea.split(":")[-1].strip()
                resultados[campo] = valor

    return resultados
