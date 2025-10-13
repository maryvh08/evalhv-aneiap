from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from .extractors import extract_experience_section_with_ocr
from .indicators import calculate_indicators_for_report
from .helpers import load_json_data, limpiar_texto

def generar_portada(pdf, story, candidato, cargo, capitulo, imagen_portada):
    """Genera la portada del reporte"""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TituloPortada', parent=styles['Title'], fontSize=22, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitulo', parent=styles['Normal'], fontSize=14, alignment=TA_CENTER)
    
    story.append(Spacer(1, 80))
    story.append(Paragraph("📘 Reporte de Evaluación ANEIAP", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<b>Candidato:</b> {candidato}", subtitle_style))
    story.append(Paragraph(f"<b>Cargo al que aspira:</b> {cargo}", subtitle_style))
    story.append(Paragraph(f"<b>Capítulo:</b> {capitulo}", subtitle_style))
    story.append(PageBreak())
    return story

def generar_tabla_concordancia(story, indicadores):
    """Agrega una tabla con los resultados de concordancia"""
    data = [["Indicador", "Porcentaje", "Coincidencias"]]
    for indicador, valores in indicadores.items():
        data.append([
            indicador,
            f"{valores['percentage']:.1f}%",
            str(valores['relevant_lines'])
        ])

    table = Table(data, colWidths=[200, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D62AD")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(Paragraph("<b>Resultados de Concordancia</b>", getSampleStyleSheet()['Heading2']))
    story.append(Spacer(1, 10))
    story.append(table)
    story.append(PageBreak())
    return story

def interpretar_resultados_globales(indicadores):
    """Genera interpretación textual según los resultados obtenidos"""
    promedio = sum(v["percentage"] for v in indicadores.values()) / len(indicadores)
    if promedio >= 75:
        return "El candidato presenta un alto nivel de afinidad con las funciones del cargo. Es un perfil altamente recomendado."
    elif promedio >= 50:
        return "El candidato presenta un nivel medio de afinidad. Muestra potencial para el cargo, aunque podría reforzar algunos aspectos."
    else:
        return "El candidato presenta baja afinidad con el cargo. Se recomienda adquirir más experiencia relacionada antes de postularse nuevamente."

def agregar_consejos_presentacion(story, cargo, consejos_json):
    """Agrega los consejos correspondientes al cargo"""
    story.append(Paragraph("<b>Consejos personalizados</b>", getSampleStyleSheet()['Heading2']))
    story.append(Spacer(1, 10))
    for consejo in consejos_json.get(cargo, []):
        story.append(Paragraph(f"• {consejo}", getSampleStyleSheet()['Normal']))
    return story

def generar_reporte_simplificado(pdf_path, candidato, cargo, capitulo, indicadores_json, consejos_json, output_filename):
    """Función principal para generar el reporte completo"""
    story = []
    pdf = SimpleDocTemplate(output_filename, pagesize=letter)

    # 1️⃣ Portada
    story = generar_portada(pdf, story, candidato, cargo, capitulo, None)

    # 2️⃣ Extracción de experiencia
    experiencia_texto = extract_experience_section_with_ocr(pdf_path)
    lines = experiencia_texto.split("\n")

    # 3️⃣ Cálculo de indicadores
    indicadores = calculate_indicators_for_report(lines, indicadores_json.get(cargo, {}))

    # 4️⃣ Tabla de resultados
    story = generar_tabla_concordancia(story, indicadores)

    # 5️⃣ Interpretación
    interpretacion = interpretar_resultados_globales(indicadores)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Conclusión General</b>", getSampleStyleSheet()['Heading2']))
    story.append(Paragraph(interpretacion, getSampleStyleSheet()['Normal']))
    story.append(PageBreak())

    # 6️⃣ Consejos personalizados
    story = agregar_consejos_presentacion(story, cargo, consejos_json)

    pdf.build(story)
    return output_filename

