import fitz  # PyMuPDF
import re
from spellchecker import SpellChecker
import textstat
from utils.ocr import extract_text_with_ocr


# ============================================================
# EXTRACCIÓN GENERAL DE TEXTO CON ENCABEZADOS Y DETALLES
# ============================================================

def extract_text_with_headers_and_details(pdf_path):
    """
    Extrae encabezados (en negrita) y detalles de un PDF.
    Devuelve un diccionario con encabezados como claves y detalles como listas de texto.
    """
    items = {}
    current_header = None

    with fitz.open(pdf_path) as doc:
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue

                        if "bold" in span["font"].lower() and not text.startswith("-"):
                            current_header = text
                            items[current_header] = []
                        elif current_header:
                            items[current_header].append(text)

    return items


# ============================================================
# EXTRACCIÓN DE SECCIONES ESPECÍFICAS
# ============================================================

def extract_experience_items_with_details(pdf_path):
    """ Extrae encabezados y detalles de la sección 'EXPERIENCIA EN ANEIAP'. """
    items = {}
    current_item = None
    in_section = False

    with fitz.open(pdf_path) as doc:
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue

                        # Detectar inicio y fin
                        lower_text = text.lower()
                        if "experiencia en aneiap" in lower_text:
                            in_section = True
                            continue
                        elif any(k in lower_text for k in ["reconocimientos", "eventos organizados"]):
                            in_section = False
                            break

                        if not in_section:
                            continue

                        # Detectar encabezados (negrita)
                        if "bold" in span["font"].lower() and not text.startswith("-"):
                            current_item = text
                            items[current_item] = []
                        elif current_item:
                            items[current_item].append(text)

    return items


def extract_event_items_with_details(pdf_path):
    """ Extrae encabezados y detalles de la sección 'EVENTOS ORGANIZADOS'. """
    items = {}
    current_item = None
    in_section = False

    with fitz.open(pdf_path) as doc:
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue

                        lower_text = text.lower()
                        if "eventos organizados" in lower_text:
                            in_section = True
                            continue
                        elif any(k in lower_text for k in ["firma", "experiencia laboral"]):
                            in_section = False
                            break

                        if not in_section:
                            continue

                        if "bold" in span["font"].lower() and not text.startswith("-"):
                            current_item = text
                            items[current_item] = []
                        elif current_item:
                            items[current_item].append(text)

    return items


def extract_asistencia_items_with_details(pdf_path):
    """ Extrae encabezados y detalles de la sección 'Asistencia a eventos ANEIAP'. """
    items = {}
    current_item = None
    in_section = False
    excluded_terms = {"dirección de residencia:", "tiempo en aneiap:", "medios de comunicación:"}

    with fitz.open(pdf_path) as doc:
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        lower_text = text.lower()
                        if not text or lower_text in excluded_terms:
                            continue

                        if "asistencia a eventos aneiap" in lower_text:
                            in_section = True
                            continue
                        elif any(k in lower_text for k in ["actualización profesional", "firma"]):
                            in_section = False
                            break

                        if not in_section:
                            continue

                        if "bold" in span["font"].lower() and not text.startswith("-"):
                            current_item = text
                            items[current_item] = []
                        elif current_item:
                            items[current_item].append(text)

    return items


def extract_profile_section_with_details(pdf_path):
    """ Extrae la sección 'Perfil' del archivo PDF. """
    text_content = []
    in_section = False

    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                for block in page.get_text("dict")["blocks"]:
                    if "lines" not in block:
                        continue
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if not text:
                                continue

                            lower_text = text.lower()
                            if "perfil" in lower_text:
                                in_section = True
                                continue
                            elif any(k in lower_text for k in ["asistencia a eventos aneiap", "actualización profesional"]):
                                in_section = False
                                break

                            if in_section:
                                text_content.append(text)

        return " ".join(text_content).strip()
    except Exception as e:
        print(f"⚠️ Error en extract_profile_section_with_details: {e}")
        return ""


# ============================================================
# EVALUACIÓN DE PRESENTACIÓN DE LA HOJA DE VIDA
# ============================================================

def evaluate_cv_presentation_with_headers(pdf_path):
    """
    Evalúa ortografía, capitalización y coherencia general del texto de la hoja de vida.
    """
    text = extract_text_with_ocr(pdf_path)
    if not text:
        return None, "No se pudo extraer texto del PDF."

    spell = SpellChecker(language="es")

    def evaluate_spelling(text):
        """Evalúa la ortografía general (0–100)."""
        words = text.split()
        if len(words) < 2:
            return 100
        misspelled = spell.unknown(words)
        return round(((len(words) - len(misspelled)) / len(words)) * 100, 2)

    def evaluate_capitalization(text):
        """Evalúa el uso correcto de mayúsculas en oraciones."""
        sentences = re.split(r"[.!?]\s*", text.strip())
        sentences = [s for s in sentences if s]
        if not sentences:
            return 100
        correct = sum(1 for s in sentences if s and s[0].isupper())
        return round((correct / len(sentences)) * 100, 2)

    def evaluate_coherence(text):
        """Evalúa coherencia con Flesch-Kincaid adaptado."""
        try:
            score = 100 - textstat.flesch_kincaid_grade(text) * 10
            return max(0, min(100, score))
        except Exception:
            return 50

    spelling = evaluate_spelling(text)
    caps = evaluate_capitalization(text)
    coherence = evaluate_coherence(text)
    overall = round((spelling + caps + coherence) / 3, 2)

    return {
        "spelling_score": spelling,
        "capitalization_score": caps,
        "coherence_score": coherence,
        "overall_score": overall,
    }
