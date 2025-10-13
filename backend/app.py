from flask import Flask, request, jsonify
import fitz
import json
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
