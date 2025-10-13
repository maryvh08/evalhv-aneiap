import json
import re
import fitz
import pytesseract
from PIL import Image
from io import BytesIO
import os

# -------------------------------
# 🔹 LECTURA DE ARCHIVOS JSON
# -------------------------------
def load_json_data(filepath):
    """
    Carga un archivo JSON y devuelve su contenido como diccionario.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"⚠️ No se encontró el archivo JSON: {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"⚠️ Error al leer el archivo JSON: {filepath}")
        return {}

# -------------------------------
# 🔹 LIMPIEZA DE TEXTO
# -------------------------------
def limpiar_texto(texto):
    """
    Limpia y normaliza un texto eliminando caracteres especiales.
    """
    texto = re.sub(r"[^\w\s.,;:!?-]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

# -------------------------------
# 🔹 EXTRACCIÓN DE TEXTO OCR
# -------------------------------
def extract_text_with_ocr(pdf_path):
    """
    Extrae texto de un PDF utilizando OCR con pytesseract y fitz (PyMuPDF).
    """
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                # Extraer texto directo
                page_text = page.get_text("text")
                if not page_text.strip():
                    # Si no hay texto, aplicar OCR
                    pix = page.get_pixmap()
                    img = Image.open(BytesIO(pix.tobytes("png")))
                    page_text = pytesseract.image_to_string(img, lang="spa")
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"⚠️ Error al procesar el PDF con OCR: {e}")
        return ""

