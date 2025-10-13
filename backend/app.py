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

app = Flask(__name__)

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
