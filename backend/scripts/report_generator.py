from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from .extractors import extract_experience_section_with_ocr
from .indicators import calculate_indicators_for_report

def generate_report(pdf_path, candidate, cargo, capitulo, indicators_json, advice_json, output_filename):
    styles = getSampleStyleSheet()
    pdf = SimpleDocTemplate(output_filename, pagesize=letter)
    story = []

    # Portada
    title_style = ParagraphStyle('Title', parent=styles['Title'], alignment=TA_CENTER, fontSize=20)
    story.append(Spacer(1, 100))
    story.append(Paragraph("Evaluador Hoja de Vida ANEIAP", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate}", styles['Normal']))
    story.append(Paragraph(f"<b>Cargo:</b> {cargo}", styles['Normal']))
    story.append(Paragraph(f"<b>Capítulo:</b> {capitulo}", styles['Normal']))
    story.append(PageBreak())

    # Extracción de experiencia
    experiencia = extract_experience_section_with_ocr(pdf_path)
    lines = experiencia.split("\n")

    # Cálculo de indicadores
    indicadores = calculate_indicators_for_report(lines, indicators_json.get(cargo, {}))

    # Tabla de resultados
    data = [["Indicador", "Porcentaje", "Coincidencias"]]
    for ind, vals in indicadores.items():
        data.append([ind, f"{vals['percentage']:.1f}%", vals['relevant_lines']])
    table = Table(data, colWidths=[200, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D62AD")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(Paragraph("<b>Resultados de Concordancia</b>", styles['Heading2']))
    story.append(Spacer(1, 10))
    story.append(table)
    story.append(PageBreak())

    # Conclusión general
    promedio = sum(v["percentage"] for v in indicadores.values()) / len(indicadores)
    if promedio >= 75:
        conclusion = "El candidato presenta un alto nivel de afinidad con las funciones del cargo."
    elif promedio >= 50:
        conclusion = "El candidato presenta afinidad media con el cargo, se recomienda fortalecer su experiencia."
    else:
        conclusion = "El candidato presenta baja afinidad con el cargo, debe adquirir más experiencia relacionada."

    story.append(Paragraph("<b>Conclusión General</b>", styles['Heading2']))
    story.append(Paragraph(conclusion, styles['Normal']))
    story.append(PageBreak())

    # Consejos personalizados
    consejos = advice_json.get(cargo, [])
    story.append(Paragraph("<b>Consejos personalizados</b>", styles['Heading2']))
    for consejo in consejos:
        story.append(Paragraph(f"• {consejo}", styles['Normal']))

    pdf.build(story)
    return output_filename
