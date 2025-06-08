import re

def extraer_datos(texto):
    campos = []

    try:
        # 1. Fecha y hora de salida
        fecha_salida = re.search(r'(\d{2}[^\w\d]?\d{2}[^\w\d]?\d{4})', texto)
        campos.append(fecha_salida.group(1) if fecha_salida else "")

        # 2. Placa del cabeza tractora
        placa_cabeza = re.search(r'PLACAS.*?([A-Z]{3}\s?\d{3,4})', texto)
        campos.append(placa_cabeza.group(1).replace(" ", "") if placa_cabeza else "")

        # 3. Placa del tanque
        placa_tanque = re.search(r'TANQUE.*?([A-Z]{3}\s?\d{3,4})', texto)
        campos.append(placa_tanque.group(1).replace(" ", "") if placa_tanque else "")

        # 4. Número de guía
        num_guia = re.search(r'(?:FACTURA|REMISIÓN|REMISION).{0,10}?(\d{5,})', texto)
        campos.append(num_guia.group(1) if num_guia else "")

        # 5. Empresa transportadora
        empresa = re.search(r'EMPRESA TRANSPORTADORA\s*([\w\s\.&\-]+)', texto, re.IGNORECASE)
        campos.append(empresa.group(1).strip() if empresa else "")

        # 6. Cédula
        cedula = re.search(r'C[EÉ]DULA[:\s]*([0-9]{6,})', texto)
        campos.append(cedula.group(1) if cedula else "")

        # 7. Nombre del conductor
        conductor = re.search(r'NOMBRE DEL CONDUCTOR\s*(.*?)\n', texto, re.IGNORECASE)
        campos.append(conductor.group(1).strip() if conductor else "")

        # 8. Casilla vacía
        campos.append("")

        # 9. Lugar de origen
        origen = re.search(r'LUGAR DE ORIGEN\s*([A-Z\s]+)', texto)
        campos.append(origen.group(1).strip() if origen else "")

        # 10. Lugar de destino
        destino = re.search(r'LUGAR DE DESTINO\s*([A-Z\s]+)', texto)
        campos.append(destino.group(1).strip() if destino else "")

        # 11. Barriles brutos
        brutos = re.search(r'BRUTOS\s*[:\-]?\s*([\d,.]+)', texto)
        campos.append(brutos.group(1) if brutos else "")

        # 12. Barriles netos
        netos = re.search(r'NETOS\s*[:\-]?\s*([\d,.]+)', texto)
        campos.append(netos.group(1) if netos else "")

        # 13. Barriles a 60°F
        barriles_60 = re.search(r'60.?F\s*[:\-]?\s*([\d,.]+)', texto)
        campos.append(barriles_60.group(1) if barriles_60 else "")

        # 14. API
        api = re.search(r'\bAPI\b\s*[:\-]?\s*([\d.]+)', texto)
        campos.append(api.group(1) if api else "")

        # 15. BSW (%)
        bsw = re.search(r'BSW\s*\(?%?\)?[:\-]?\s*([\d.]+)', texto)
        campos.append(bsw.group(1) if bsw else "")

        # 16. Vigencia de guía (horas)
        vigencia = re.search(r'(\d{1,3})\s*HORAS', texto)
        campos.append(vigencia.group(1) if vigencia else "")

        # 17–22. Seis casillas vacías
        campos.extend([""] * 6)

        # 23. Sellos (uno o más números)
        sellos = re.findall(r'SELLO(?:S)?\s*[:\-]?\s*(\d{5,})', texto)
        campos.append(", ".join(sellos) if sellos else "")

    except Exception as e:
        campos = ["ERROR: " + str(e)]

    return campos
