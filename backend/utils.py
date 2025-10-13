import io
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader


# ============================================================
# 🔹 PREPROCESAMIENTO DE IMÁGENES PARA OCR
# ============================================================
def preprocess_image(image):
    """
    Preprocesa una imagen antes de aplicar OCR.
    Mejora contraste, elimina ruido y convierte a blanco y negro.
    """
    image = image.convert("L")  # Escala de grises
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)  # Mejora contraste
    image = ImageOps.autocontrast(image)
    return image


# ============================================================
# 🔹 EXTRACCIÓN DE TEXTO DESDE PDF (OCR + TEXTO EMBEBIDO)
# ============================================================
def extract_text_with_ocr(pdf_path):
    """
    Extrae texto de un PDF utilizando PyMuPDF y OCR si es necesario.
    """
    extracted_text = []

    with fitz.open(pdf_path) as doc:
        for page in doc:
            # Intentar obtener texto directo
            page_text = page.get_text("text").strip()
            if not page_text:  # Si no hay texto, usar OCR
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes(output="png")))
                img = preprocess_image(img)
                page_text = pytesseract.image_to_string(img, config="--psm 3").strip()

            extracted_text.append(page_text)

    return "\n".join(extracted_text)


# ============================================================
# 🔹 LIMPIEZA DE TEXTO EXTRAÍDO
# ============================================================
def extract_cleaned_lines(text):
    """
    Limpia el texto extraído eliminando líneas vacías, errores de OCR,
    números de página y caracteres no alfanuméricos.
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
# 🔹 CÁLCULO DE SIMILITUD ENTRE TEXTOS
# ============================================================
def calculate_similarity(text1, text2):
    """
    Calcula la similitud entre dos textos con TF-IDF + Cosine Similarity.
    Retorna el porcentaje de similitud (0 a 100).
    """
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
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="spanish")
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(similarity * 100, 2)
    except Exception:
        return 0


# ============================================================
# 🔹 CÁLCULO DE COINCIDENCIA POR PALABRAS CLAVE
# ============================================================
def calculate_keyword_match_percentage(candidate_text, position_indicators, functions_text, profile_text):
    """
    Calcula coincidencia por palabras clave para 'Funciones' y 'Perfil del cargo'.
    Retorna: (porcentaje_funciones, porcentaje_perfil)
    """
    if not candidate_text or not isinstance(candidate_text, str):
        return (0.0, 0.0)

    if not position_indicators or not isinstance(position_indicators, dict):
        return (0.0, 0.0)

    function_keywords = []
    profile_keywords = []

    for indicator, keywords in position_indicators.items():
        if functions_text and indicator.lower() in functions_text.lower():
            function_keywords.extend(keywords)
        if profile_text and indicator.lower() in profile_text.lower():
            profile_keywords.extend(keywords)

    def keyword_match_score(keywords, text):
        if not keywords:
            return 0.0
        found = sum(1 for kw in keywords if kw.lower() in text.lower())
        return round((found / len(keywords)) * 100, 2)

    func_match = keyword_match_score(function_keywords, candidate_text)
    profile_match = keyword_match_score(profile_keywords, candidate_text)

    return func_match, profile_match


# ============================================================
# 🔹 PORTADA DEL REPORTE
# ============================================================
def draw_full_page_cover(canvas, portada_path, candidate_name, position, chapter):
    """
    Dibuja una portada con imagen a página completa y texto centrado.
    """
    page_width, page_height = letter
    img = ImageReader(portada_path)
    img_width, img_height = img.getSize()
    scale = max(page_width / img_width, page_height / img_height)
    new_w, new_h = img_width * scale, img_height * scale
    x_offset = (page_width - new_w) / 2
    y_offset = (page_height - new_h) / 2
    canvas.drawImage(portada_path, x_offset, y_offset, width=new_w, height=new_h)

    canvas.setFont("Helvetica-Bold", 36)
    canvas.setFillColor(colors.black)
    lines = [
        "REPORTE DE ANÁLISIS",
        candidate_name.upper(),
        f"CARGO: {position.upper()}",
        f"CAPÍTULO: {chapter.upper()}",
    ]
    total_height = len(lines) * 40
    start_y = (page_height + total_height) / 2 - 100
    for i, line in enumerate(lines):
        line_width = canvas.stringWidth(line, "Helvetica-Bold", 36)
        x = (page_width - line_width) / 2
        y = start_y - (i * 45)
        canvas.drawString(x, y, line)


# ============================================================
# 🔹 FONDO DE PÁGINAS
# ============================================================
def add_background(canvas, background_path):
    """
    Dibuja una imagen de fondo en cada página del PDF.
    """
    canvas.saveState()
    canvas.drawImage(background_path, 0, 0, width=letter[0], height=letter[1])
    canvas.restoreState()
