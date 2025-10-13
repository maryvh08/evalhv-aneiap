# ============================================================
# APP PRINCIPAL DE LA ATS ANEIAP - VERSIÓN FLASK
# ============================================================

from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
import os
import tempfile
from datetime import datetime

# ============================================================
# IMPORTS DE MÓDULOS INTERNOS
# ============================================================
from utils.ocr import extract_text_with_ocr
from utils.extractors import (
    extract_profile_section_with_ocr,
    extract_experience_section_with_ocr,
    extract_event_section_with_ocr,
    extract_attendance_section_with_ocr
)
from utils.indicators import calculate_all_indicators, calculate_indicators_for_report
from utils.report_generator import analyze_and_generate_descriptive_report
from utils.evaluation import evaluate_cv_presentation
from utils.analysis import generate_extended_analysis
from utils.helpers import load_json, clean_text, extract_candidate_data

# ============================================================
# CONFIGURACIÓN DE LA APLICACIÓN FLASK
# ============================================================

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ============================================================
# RUTA PRINCIPAL (FORMULARIO)
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")  # formulario principal


# ============================================================
# RUTA DE ANÁLISIS (PROCESA EL PDF Y GENERA EL REPORTE)
# ============================================================

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # ------------------------------
        # 1️⃣  Capturar datos del formulario
        # ------------------------------
        candidate_name = request.form.get("candidate_name")
        chapter = request.form.get("chapter")
        position = request.form.get("position")
        pdf_file = request.files.get("pdf")

        if not all([candidate_name, chapter, position, pdf_file]):
            return jsonify({"error": "Faltan campos obligatorios."}), 400

        # ------------------------------
        # 2️⃣  Guardar archivo temporalmente
        # ------------------------------
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, pdf_file.filename)
        pdf_file.save(pdf_path)

        # ------------------------------
        # 3️⃣  Extraer texto del PDF
        # ------------------------------
        extracted_text = extract_text_with_ocr(pdf_path)
        clean_extracted_text = clean_text(extracted_text)

        # ------------------------------
        # 4️⃣  Extraer secciones específicas
        # ------------------------------
        profile_text = extract_profile_section_with_ocr(clean_extracted_text)
        experience_text = extract_experience_section_with_ocr(clean_extracted_text)
        event_text = extract_event_section_with_ocr(clean_extracted_text)
        attendance_text = extract_attendance_section_with_ocr(clean_extracted_text)

        # ------------------------------
        # 5️⃣  Calcular indicadores
        # ------------------------------
        indicators_results = calculate_all_indicators(
            {
                "Perfil": profile_text,
                "Experiencia": experience_text,
                "Eventos": event_text,
                "Asistencia": attendance_text,
            },
            position,
            chapter
        )

        indicator_percentages = calculate_indicators_for_report(indicators_results)

        # ------------------------------
        # 6️⃣  Evaluar presentación del CV
        # ------------------------------
        presentation_scores = evaluate_cv_presentation(clean_extracted_text)

        # ------------------------------
        # 7️⃣  Generar análisis extendido
        # ------------------------------
        extended_analysis = generate_extended_analysis(
            indicators_results, profile_text, experience_text
        )

        # ------------------------------
        # 8️⃣  Generar reporte PDF
        # ------------------------------
        output_filename = f"Reporte_{candidate_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_filename)

        analyze_and_generate_descriptive_report(
            candidate_name=candidate_name,
            position=position,
            chapter=chapter,
            pdf_path=pdf_path,
            indicator_percentages=indicator_percentages,
            presentation_scores=presentation_scores,
            extended_analysis=extended_analysis,
            output_path=output_path
        )

        # ------------------------------
        # 9️⃣  Retornar éxito y enlace de descarga
        # ------------------------------
        return render_template("result.html",
                               candidate_name=candidate_name,
                               position=position,
                               chapter=chapter,
                               report_path=url_for("download", filename=output_filename))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# RUTA DE DESCARGA DEL REPORTE
# ============================================================

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "Archivo no encontrado."}), 404


# ============================================================
# INICIO DEL SERVIDOR LOCAL
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
