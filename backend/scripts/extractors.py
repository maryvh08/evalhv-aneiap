# extractors.py
import re
from collections import Counter
from typing import Dict, List, Tuple, Optional

# Importar funciones de utils (asegúrate de que utils.py esté en el mismo paquete)
from .utils import extract_text_with_ocr, extract_cleaned_lines


# ---------------------------
#  EXTRACTORES PARA FORMATO SIMPLIFICADO
# ---------------------------

def extract_profile_section_with_ocr(pdf_path: str) -> str:
    """
    Extrae la sección 'Perfil' de un PDF (OCR fallback).
    Retorna cadena limpia o '' si no se encuentra.
    """
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return ""

    start_keyword = "perfil"
    end_keywords = ["asistencia a eventos", "actualización profesional", "asistencia eventos", "experiencia en aneiap"]

    start_idx = text.lower().find(start_keyword)
    if start_idx == -1:
        return ""

    end_idx = len(text)
    for kw in end_keywords:
        idx = text.lower().find(kw, start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    candidate_profile_text = text[start_idx:end_idx].strip()
    cleaned = re.sub(r"[^\w\s.,;:()\-]", "", candidate_profile_text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def extract_experience_section_with_ocr(pdf_path: str) -> Optional[str]:
    """
    Extrae la sección 'EXPERIENCIA EN ANEIAP'. Retorna texto limpió o None si no existe.
    """
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return None

    start_keyword = "experiencia en aneiap"
    end_keywords = [
        "eventos organizados",
        "reconocimientos individuales",
        "reconocimientos grupales",
        "reconocimientos",
        "asistencia a eventos"
    ]

    start_idx = text.lower().find(start_keyword)
    if start_idx == -1:
        return None

    end_idx = len(text)
    for kw in end_keywords:
        idx = text.lower().find(kw, start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    experience_text = text[start_idx:end_idx].strip()
    lines = experience_text.split("\n")
    exclude = {
        "a nivel capitular", "a nivel nacional", "a nivel seccional",
        "trabajo capitular", "trabajo nacional"
    }

    cleaned_lines = []
    for line in lines:
        ln = line.strip()
        ln_clean = re.sub(r"[^\w\s]", "", ln)
        normalized = re.sub(r"\s+", " ", ln_clean).strip().lower()
        if not normalized:
            continue
        if normalized in exclude or normalized == start_keyword.lower():
            continue
        cleaned_lines.append(ln.strip())

    return "\n".join(cleaned_lines)


def extract_event_section_with_ocr(pdf_path: str) -> Optional[str]:
    """
    Extrae la sección 'EVENTOS ORGANIZADOS'. Retorna texto o None.
    """
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return None

    start_keyword = "eventos organizados"
    end_keywords = ["experiencia laboral", "firma", "reconocimientos", "asistencia a eventos"]

    start_idx = text.lower().find(start_keyword)
    if start_idx == -1:
        return None

    end_idx = len(text)
    for kw in end_keywords:
        idx = text.lower().find(kw, start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    org_text = text[start_idx:end_idx].strip()
    lines = org_text.split("\n")
    exclude = {"a nivel capitular", "a nivel nacional", "a nivel seccional"}

    cleaned = []
    for line in lines:
        ln = line.strip()
        ln_clean = re.sub(r"[^\w\s]", "", ln)
        normalized = re.sub(r"\s+", " ", ln_clean).strip().lower()
        if not normalized or normalized == start_keyword.lower():
            continue
        if normalized in exclude:
            continue
        cleaned.append(ln.strip())

    return "\n".join(cleaned)


def extract_attendance_section_with_ocr(pdf_path: str) -> Optional[str]:
    """
    Extrae la sección 'ASISTENCIA A EVENTOS ANEIAP'. Retorna texto o None.
    """
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return None

    start_keyword = "asistencia a eventos aneiap"
    end_keywords = ["actualización profesional", "experiencia en aneiap", "eventos organizados", "reconocimientos"]

    start_idx = text.lower().find(start_keyword)
    if start_idx == -1:
        # Intentar variante sin "aneiap"
        start_idx = text.lower().find("asistencia a eventos")
        if start_idx == -1:
            return None

    end_idx = len(text)
    for kw in end_keywords:
        idx = text.lower().find(kw, start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    att_text = text[start_idx:end_idx].strip()
    lines = att_text.split("\n")
    exclude = {"a nivel capitular", "a nivel nacional", "a nivel seccional", "capitular", "seccional", "nacional"}

    cleaned = []
    for line in lines:
        ln = line.strip()
        ln_clean = re.sub(r"[^\w\s]", "", ln)
        normalized = re.sub(r"\s+", " ", ln_clean).strip().lower()
        if not normalized or normalized == start_keyword.lower():
            continue
        if normalized in exclude:
            continue
        cleaned.append(ln.strip())

    return "\n".join(cleaned)


# ---------------------------
#  FORMAT DESCRIPTIVO (encabezados en negrita + detalles)
# ---------------------------

def extract_text_with_headers_and_details(pdf_path: str) -> Dict[str, List[str]]:
    """
    Extrae encabezados (negrita si está presente) y detalles.
    Retorna dict {header: [detail_lines...]}.
    Nota: depende de que extract_text_with_ocr devuelva texto con suficiente info;
    si quieres distinguir negrita estrictamente, hay que usar fitz.get_text('dict') (más abajo).
    """
    # Implementación robusta usando el texto general: busca líneas en MAYÚSCULAS o con patrón de título.
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return {}

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    items = {}
    current_header = None

    for ln in lines:
        # heurística de header: línea en mayúsculas o que termina con ':' o con formato de título corto
        if ln.isupper() or ln.endswith(":") or (len(ln.split()) <= 6 and ln[0].isalpha() and ln[0].isupper()):
            current_header = ln.rstrip(":").strip()
            items.setdefault(current_header, [])
        else:
            if current_header:
                items[current_header].append(ln)
            else:
                # Si no hay header todavía, agregar a un header genérico
                items.setdefault("GENERAL", []).append(ln)

    return items


def extract_experience_items_with_details(pdf_path: str) -> Dict[str, List[str]]:
    """
    Extrae encabezados y detalles SOLO de la sección 'EXPERIENCIA EN ANEIAP'.
    Usa extract_text_with_headers_and_details y filtra por la sección.
    """
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return {}

    # localizar la sección y luego aplicar la función de encabezados a ese fragmento
    start_kw = "experiencia en aneiap"
    start_idx = text.lower().find(start_kw)
    if start_idx == -1:
        return {}

    # delimitar fin de sección
    end_keywords = ["reconocimientos", "eventos organizados", "asistencia a eventos", "experiencia laboral"]
    end_idx = len(text)
    for kw in end_keywords:
        idx = text.lower().find(kw, start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    subtext = text[start_idx:end_idx]
    # ahora parsear encabezados
    lines = [ln.strip() for ln in subtext.split("\n") if ln.strip()]
    items = {}
    current = None
    for ln in lines:
        # Considerar negrita/encabezado: mayúsculas o pocas palabras, o termina con ':'
        if ln.isupper() or ln.endswith(":") or (len(ln.split()) <= 6 and ln[0].isalpha() and ln[0].isupper()):
            current = ln.rstrip(":").strip()
            items.setdefault(current, [])
        else:
            if current:
                items[current].append(ln)
    return items


def extract_event_items_with_details(pdf_path: str) -> Dict[str, List[str]]:
    """
    Extrae encabezados y detalles de 'EVENTOS ORGANIZADOS'.
    """
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return {}

    start_kw = "eventos organizados"
    start_idx = text.lower().find(start_kw)
    if start_idx == -1:
        return {}

    end_keywords = ["firma", "experiencia laboral", "asistencia a eventos"]
    end_idx = len(text)
    for kw in end_keywords:
        idx = text.lower().find(kw, start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    subtext = text[start_idx:end_idx]
    lines = [ln.strip() for ln in subtext.split("\n") if ln.strip()]
    items = {}
    current = None
    for ln in lines:
        if ln.isupper() or ln.endswith(":") or (len(ln.split()) <= 7 and ln[0].isalpha() and ln[0].isupper()):
            current = ln.rstrip(":").strip()
            items.setdefault(current, [])
        else:
            if current:
                items[current].append(ln)
    return items


def extract_asistencia_items_with_details(pdf_path: str) -> Dict[str, List[str]]:
    """
    Extrae encabezados y detalles de 'Asistencia a eventos ANEIAP'.
    Excluye campos irrelevantes como 'Dirección de residencia:'.
    """
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return {}

    start_kw = "asistencia a eventos aneiap"
    start_idx = text.lower().find(start_kw)
    if start_idx == -1:
        start_idx = text.lower().find("asistencia a eventos")
        if start_idx == -1:
            return {}

    end_keywords = ["actualización profesional", "firma", "experiencia en aneiap"]
    end_idx = len(text)
    for kw in end_keywords:
        idx = text.lower().find(kw, start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    subtext = text[start_idx:end_idx]
    lines = [ln.strip() for ln in subtext.split("\n") if ln.strip()]
    excluded_terms = {"dirección de residencia:", "tiempo en aneiap:", "medios de comunicación:"}

    items = {}
    current = None
    for ln in lines:
        if ln.lower() in excluded_terms:
            continue
        if ln.isupper() or ln.endswith(":") or (len(ln.split()) <= 7 and ln[0].isalpha() and ln[0].isupper()):
            current = ln.rstrip(":").strip()
            items.setdefault(current, [])
        else:
            if current:
                items[current].append(ln)
    return items


# ---------------------------
#  PRESENTACIÓN (resumen limpio)
# ---------------------------
def extract_profile_section_with_details(pdf_path: str) -> str:
    """
    Extrae la sección 'Perfil' retornando texto continuo (detalles).
    """
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return ""

    start_kw = "perfil"
    start_idx = text.lower().find(start_kw)
    if start_idx == -1:
        return ""

    end_keywords = ["asistencia a eventos aneiap", "actualización profesional", "asistencia a eventos"]
    end_idx = len(text)
    for kw in end_keywords:
        idx = text.lower().find(kw, start_idx)
        if idx != -1:
            end_idx = min(end_idx, idx)

    candidate_profile_text = text[start_idx:end_idx].strip()
    cleaned = re.sub(r"\s+", " ", candidate_profile_text)
    cleaned = re.sub(r"[^\w\s.,;:()\-]", "", cleaned).strip()
    return cleaned


def evaluate_cv_presentation_with_headers(pdf_path: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Evalúa la presentación de la HV usando encabezados y detalles.
    Retorna dict con métricas por sección o (None, mensaje_error).
    """
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return None, "No se pudo extraer texto del archivo PDF."

    # Simple wrapper: reusar funciones de evaluación del main.
    # Para mantener la dependencia mínima, devolvemos métricas simples:
    words = re.findall(r"\b\w+\b", text)
    if not words:
        return None, "Documento vacío o sin texto válido."

    # ortografía (simplificada): proporción de palabras con solo letras (no es real spelling)
    total = len(words)
    alpha_count = sum(1 for w in words if w.isalpha())
    spelling_score = round((alpha_count / total) * 100, 2)

    # capitalización: proporción oraciones que empiezan en mayúscula
    sentences = [s.strip() for s in re.split(r'[.!?]\s*', text) if s.strip()]
    caps = sum(1 for s in sentences if s and s[0].isupper())
    capitalization_score = round((caps / len(sentences)) * 100, 2) if sentences else 100.0

    # coherencia: usar longitud media de oraciones como proxy
    sentence_lengths = [len(s.split()) for s in sentences] if sentences else [0]
    avg_len = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
    coherence_score = max(0, min(100, 100 - abs(avg_len - 12) * 5))  # heurística

    overall = round((spelling_score + capitalization_score + coherence_score) / 3, 2)

    return {
        "spelling_score": spelling_score,
        "capitalization_score": capitalization_score,
        "coherence_score": coherence_score,
        "overall_score": overall,
    }, None


# ---------------------------
#  INDICADORES (funciones auxiliares ya definidas en main)
# ---------------------------
def calculate_all_indicators(lines: List[str], position_indicators: Dict[str, List[str]]) -> Dict[str, float]:
    """
    Calcula el porcentaje por indicador sobre la lista de líneas (EXPERIENCIA).
    """
    total_lines = len(lines)
    if total_lines == 0:
        return {indicator: 0.0 for indicator in position_indicators}

    results = {}
    for indicator, keywords in position_indicators.items():
        relevant = sum(1 for line in lines if any(kw.lower() in line.lower() for kw in keywords))
        results[indicator] = round((relevant / total_lines) * 100, 2)
    return results


def calculate_indicators_for_report(lines: List[str], position_indicators: Dict[str, List[str]]):
    """
    Devuelve dict con {'indicator': {'percentage': X, 'relevant_lines': Y}}
    """
    total_lines = len(lines)
    if total_lines == 0:
        return {indicator: {"percentage": 0.0, "relevant_lines": 0} for indicator in position_indicators}

    results = {}
    for indicator, keywords in position_indicators.items():
        relevant_count = sum(1 for line in lines if any(kw.lower() in line.lower() for kw in keywords))
        percentage = round((relevant_count / total_lines) * 100, 2)
        results[indicator] = {"percentage": percentage, "relevant_lines": relevant_count}
    return results

