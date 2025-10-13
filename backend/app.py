from PIL import Image
import os
import google.generativeai as genai
import base64
import fitz
import requests
import numpy as np
import spacy
import pandas as pd
from collections import Counter
from io import BytesIO
from textstat import textstat
import re
import json
import pytesseract
from spellchecker import SpellChecker
from textblob import TextBlob
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageTemplate, Frame, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Image as RLImage  
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus.flowables import PageBreak
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import statsmodels.api as sm
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
from flask import Flask, request, jsonify, send_file
from utils import (
    extract_text_with_ocr,
    extract_cleaned_lines,
    calculate_similarity,
    calculate_keyword_match_percentage,
    draw_full_page_cover,
    add_background
)
from cv_analysis import (
    extract_experience_section_with_ocr,
    extract_profile_section_with_ocr,
    calculate_indicators_for_report,
    evaluate_cv_presentation
)

app = Flask(__name__)

# ============================================================
# IMPORTS DE MÓDULOS INTERNOS (DESDE app/utils/)
# ============================================================

from utils.ocr import extract_text_with_ocr
from utils.extractors import (
    extract_profile_section_with_ocr,
    extract_experience_section_with_ocr,
    extract_event_section_with_ocr,
    extract_attendance_section_with_ocr
)
from utils.indicators import calculate_all_indicators, calculate_indicators_for_report
from utils.report_generator import generate_pdf_report
from utils.evaluation import evaluate_cv_presentation
from utils.analysis import generate_extended_analysis
from utils.helpers import load_json, clean_text, extract_candidate_data

# Cargar JSONs
with open("indicators.json", encoding="utf-8") as f:
    indicators = json.load(f)

with open("advice.json", encoding="utf-8") as f:
    advice = json.load(f)

@app.route("/analizar", methods=["POST"])
def analizar():
    nombre = request.form["nombre"]
    capitulo = request.form["capitulo"]
    cargo = request.form["cargo"]
    pdf = request.files["pdf"]

    # --- Extraer texto del PDF ---
    texto = ""
    with fitz.open(stream=pdf.read(), filetype="pdf") as doc:
        for page in doc:
            texto += page.get_text()

    # --- Obtener palabras clave ---
    palabras = indicators.get(cargo, [])
    coincidencias = sum(1 for p in palabras if p.lower() in texto.lower())
    porcentaje = round((coincidencias / len(palabras)) * 100, 2) if palabras else 0

    consejo = advice.get(cargo, "Sin consejo disponible.")

    return jsonify({
        "nombre": nombre,
        "capitulo": capitulo,
        "cargo": cargo,
        "afinidad": f"{porcentaje}%",
        "coincidencias": coincidencias,
        "total_palabras": len(palabras),
        "consejo": consejo
    })

if __name__ == "__main__":
    app.run(debug=True)
