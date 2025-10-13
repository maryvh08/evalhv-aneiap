import io
import re
import fitz
import pytesseract
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.utils import ImageReader


# ============================================================
# 📸 1️⃣ PREPROCESAMIENTO DE IMAGEN PARA OCR
# ============================================================
def preprocess_image(image):
    """
    Preprocesa una imagen antes de aplicar OCR.
    """
    image = image.convert("L")  # Escala de grises
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)  # Aumentar contraste
    image = ImageOps.autocontrast(image)  # Normalizar contraste
    return image


# ============================================================
# 🔍 2️⃣ EXTRACCIÓN DE TEXTO CON PyMuPDF + OCR
# ============================================================
def extract_text_with_ocr(pdf_file):
    """
    Extrae texto de un PDF utilizando PyMuPDF y OCR con preprocesamiento optimizado.
    Acepta un archivo PDF subido desde un formulario Flask.
    """
    extracted_text = []

    # Leer el PDF desde el objeto file-like (sin ruta local)
    pdf_bytes = pdf_file.read()
    pdf_file.seek(0)

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            # Intentar extraer texto directamente
            page_text = page.get_text("text").strip()

            if not page_text:
                # Si no hay texto, usar OCR
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes(output="png")))

                img = preprocess_image(img)
                img = img.filter(ImageFilter.MedianFilter())

                # Aplicar OCR
                page_text = pytesseract.image_to_string(img, config="--psm 3").strip()

            extracted_text.append(page_text)

    return "\n".join(extracted_text)


# ============================================================
# 🧹 3️⃣ LIMPIEZA DE TEXTO
# ============================================================
def extract_cleaned_lines(text):
    """
    Limpia líneas vacías, con ruido o con errores OCR.
    """
    if isinstance(text, list):
        text = "\n".join(text)

    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        if not line or not any(char.isalnum() for char in line):
            continue
        if re.fullmatch(r"\d+", line):
            continue
        if len(line) < 3:
            continue

        cleaned_lines.append(line)

    return cleaned_lines


# ============================================================
# 📊 4️⃣ SIMILITUD ENTRE TEXTOS (TF-IDF)
# ============================================================
def calculate_similarity(text1, text2):
    """Calcula la similitud entre dos textos usando TF-IDF y similitud de coseno."""
    if not isinstance(text1, str) or not isinstance(text2, str):
        return 0

    def clean_text(text):
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text).strip().lower()
        return text

    text1, text2 = clean_text(text1), clean_text(text2)
    if not text1 or not text2:
        return 0

    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(similarity * 100, 2)
    except Exception:
        return 0


# ============================================================
# 🧠 5️⃣ CÁLCULO DE COINCIDENCIAS DE PALABRAS CLAVE
# ============================================================
def calculate_keyword_match_percentage(candidate_text, position_indicators, functions_text, profile_text):
    """
    Calcula los porcentajes de coincidencia basados en las palabras clave
    del cargo y del capítulo (según el JSON de indicadores).
    """
    if not candidate_text or not isinstance(candidate_text, str):
        return (0.0, 0.0)

    if not position_indicators or not isinstance(position_indicators, dict):
        return (0.0, 0.0)

    function_keywords = []
    profile_keywords = []

    for indicator, keywords in position_indicators.items():
        if functions_text and any(indicator.lower() in func.lower() for func in functions_text.split()):
            function_keywords.extend(keywords)
        if profile_text and any(indicator.lower() in prof.lower() for prof in profile_text.split()):
            profile_keywords.extend(keywords)

    total_function_keywords = len(function_keywords)
    total_profile_keywords = len(profile_keywords)

    function_match_percentage = 0.0
    profile_match_percentage = 0.0

    if total_function_keywords > 0:
        matched_functions = sum(1 for k in function_keywords if k.lower() in candidate_text.lower())
        function_match_percentage = round((matched_functions / total_function_keywords) * 100, 2)

    if total_profile_keywords > 0:
        matched_profiles = sum(1 for k in profile_keywords if k.lower() in candidate_text.lower())
        profile_match_percentage = round((matched_profiles / total_profile_keywords) * 100, 2)

    return function_match_percentage, profile_match_percentage


# ============================================================
# 🖼️ 6️⃣ DISEÑO DE PORTADA EN PDF
# ============================================================
def draw_full_page_cover(canvas, portada_path, candidate_name, position, chapter):
    """
    Dibuja una portada a página completa con el título centrado.
    """
    page_width, page_height = letter
    img = ImageReader(portada_path)
    img_width, img_height = img.getSize()

    scale_factor = max(page_width / img_width, page_height / img_height)
    new_width = img_width * scale_factor
    new_height = img_height * scale_factor

    x_offset = (page_width - new_width) / 2
    y_offset = (page_height - new_height) / 2

    canvas.drawImage(portada_path, x_offset, y_offset, width=new_width, height=new_height)

    # Texto centrado
    title_text = f"REPORTE DE ANÁLISIS\n{candidate_name.upper()}\nCARGO: {position.upper()}\nCAPÍTULO: {chapter.upper()}"
    canvas.setFont("Helvetica-Bold", 32)
    canvas.setFillColor(colors.black)

    text_lines = title_text.split("\n")
    total_height = len(text_lines) * 40
    y_start = (page_height + total_height) / 2

    for i, line in enumerate(text_lines):
        text_width = canvas.stringWidth(line, "Helvetica-Bold", 32)
        x_pos = (page_width - text_width) / 2
        y_pos = y_start - (i * 50)
        canvas.drawString(x_pos, y_pos, line)


# ============================================================
# 🌄 7️⃣ FONDO DE PÁGINA
# ============================================================
def add_background(canvas, background_path):
    """
    Dibuja una imagen de fondo en cada página del PDF.
    """
    canvas.saveState()
    canvas.drawImage(background_path, 0, 0, width=letter[0], height=letter[1])
    canvas.restoreState()

