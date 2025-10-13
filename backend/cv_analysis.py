# ============================================================
# 🔹 FUNCIONES DE EXTRACCIÓN DE SECCIONES
# ============================================================

def extract_profile_section_with_ocr(pdf_path):
    """
    Extrae la sección 'Perfil' de la hoja de vida ANEIAP.
    """
    text = extract_text_with_ocr(pdf_path)

    if not text.strip():
        print("⚠️ No se pudo extraer texto del PDF.")
        return ""

    start_keyword = "Perfil"
    end_keywords = ["Asistencia a eventos", "Actualización profesional"]

    start_idx = text.lower().find(start_keyword.lower())
    if start_idx == -1:
        print("⚠️ No se encontró la sección 'Perfil'.")
        return ""

    end_idx = len(text)
    for keyword in end_keywords:
        idx = text.lower().find(keyword.lower(), start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    section = text[start_idx:end_idx].strip()
    section = re.sub(r"[^\w\s.,;:()\-]", "", section)
    section = re.sub(r"\s+", " ", section)

    return section


def extract_experience_section_with_ocr(pdf_path):
    """
    Extrae la sección 'EXPERIENCIA EN ANEIAP' de la hoja de vida.
    """
    text = extract_text_with_ocr(pdf_path)

    start_keyword = "EXPERIENCIA EN ANEIAP"
    end_keywords = [
        "EVENTOS ORGANIZADOS",
        "Reconocimientos individuales",
        "Reconocimientos grupales",
        "Reconocimientos"
    ]

    start_idx = text.lower().find(start_keyword.lower())
    if start_idx == -1:
        return ""

    end_idx = len(text)
    for keyword in end_keywords:
        idx = text.lower().find(keyword.lower(), start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    section = text[start_idx:end_idx].strip()

    exclude_lines = [
        "a nivel capitular", "a nivel nacional", "a nivel seccional",
        "reconocimientos individuales", "reconocimientos grupales",
        "trabajo capitular", "trabajo nacional", "nacional 2024", "nacional 20212023"
    ]

    lines = section.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        line = re.sub(r"[^\w\s]", "", line)
        normalized = re.sub(r"\s+", " ", line).lower()
        if (
            normalized and
            normalized not in exclude_lines and
            normalized != start_keyword.lower() and
            normalized not in [kw.lower() for kw in end_keywords]
        ):
            cleaned.append(line)

    return "\n".join(cleaned)


def extract_event_section_with_ocr(pdf_path):
    """
    Extrae la sección 'EVENTOS ORGANIZADOS' de la hoja de vida.
    """
    text = extract_text_with_ocr(pdf_path)
    if not text.strip():
        return ""

    start_keyword = "EVENTOS ORGANIZADOS"
    end_keywords = ["EXPERIENCIA LABORAL", "FIRMA"]

    start_idx = text.lower().find(start_keyword.lower())
    if start_idx == -1:
        return ""

    end_idx = len(text)
    for keyword in end_keywords:
        idx = text.lower().find(keyword.lower(), start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    section = text[start_idx:end_idx].strip()

    exclude_lines = [
        "a nivel capitular", "a nivel nacional", "a nivel seccional",
        "reconocimientos individuales", "reconocimientos grupales",
        "trabajo capitular", "trabajo nacional"
    ]

    lines = section.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        line = re.sub(r"[^\w\s]", "", line)
        normalized = re.sub(r"\s+", " ", line).lower()
        if (
            normalized and
            normalized not in exclude_lines and
            normalized != start_keyword.lower() and
            normalized not in [kw.lower() for kw in end_keywords]
        ):
            cleaned.append(line)

    return "\n".join(cleaned)


def extract_attendance_section_with_ocr(pdf_path):
    """
    Extrae la sección 'ASISTENCIA A EVENTOS ANEIAP' de la hoja de vida.
    """
    text = extract_text_with_ocr(pdf_path)
    start_keyword = "ASISTENCIA A EVENTOS ANEIAP"
    end_keywords = [
        "ACTUALIZACIÓN PROFESIONAL", "EXPERIENCIA EN ANEIAP",
        "EVENTOS ORGANIZADOS", "RECONOCIMIENTOS"
    ]

    start_idx = text.lower().find(start_keyword.lower())
    if start_idx == -1:
        return ""

    end_idx = len(text)
    for keyword in end_keywords:
        idx = text.lower().find(keyword.lower(), start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    section = text[start_idx:end_idx].strip()

    exclude_lines = [
        "a nivel capitular", "a nivel nacional", "a nivel seccional",
        "capitular", "seccional", "nacional"
    ]

    lines = section.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        line = re.sub(r"[^\w\s]", "", line)
        normalized = re.sub(r"\s+", " ", line).lower()
        if (
            normalized and
            normalized not in exclude_lines and
            normalized != start_keyword.lower() and
            normalized not in [kw.lower() for kw in end_keywords]
        ):
            cleaned.append(line)

    return "\n".join(cleaned)


# ============================================================
# 🔹 FUNCIÓN DE EVALUACIÓN DE PRESENTACIÓN GENERAL
# ============================================================

def evaluate_cv_presentation(pdf_path):
    """
    Evalúa la presentación general de la hoja de vida (redacción, claridad, coherencia).
    """
    text = extract_text_with_ocr(pdf_path)

    if not text.strip():
        return {"clean_text": "", "message": "No se pudo extraer el texto del PDF."}

    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        line = re.sub(r"[^\w\s.,;:!?-]", "", line)
        line = re.sub(r"\s+", " ", line)
        if line:
            cleaned.append(line)

    if not cleaned:
        return {"clean_text": "", "message": "El documento no contiene texto procesable."}

    return {"clean_text": "\n".join(cleaned), "message": "Texto procesado correctamente."}


# ============================================================
# 🔹 FUNCIONES DE CÁLCULO DE INDICADORES
# ============================================================

def calculate_all_indicators(lines, position_indicators):
    """
    Calcula los porcentajes de coincidencia por indicador del cargo.
    """
    total_lines = len(lines)
    if total_lines == 0:
        return {indicator: 0 for indicator in position_indicators}

    results = {}
    for indicator, keywords in position_indicators.items():
        matches = sum(any(k.lower() in line.lower() for k in keywords) for line in lines)
        results[indicator] = (matches / total_lines) * 100

    return results


def calculate_indicators_for_report(lines, position_indicators):
    """
    Calcula porcentajes y cantidad de líneas relevantes por indicador.
    """
    total_lines = len(lines)
    if total_lines == 0:
        return {indicator: {"percentage": 0, "relevant_lines": 0} for indicator in position_indicators}

    results = {}
    for indicator, keywords in position_indicators.items():
        matches = sum(any(k.lower() in line.lower() for k in keywords) for line in lines)
        percentage = (matches / total_lines) * 100
        results[indicator] = {"percentage": percentage, "relevant_lines": matches}

    return results
