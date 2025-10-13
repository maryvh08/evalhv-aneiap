# backend/app/main.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil, os
from ats.extractors import extract_text_with_ocr  # importa tus funciones adaptadas
from ats.report import generate_pdf_report  # función que envuelve tu lógica y devuelve path
import uuid

app = FastAPI(title="EvalHV ANEIAP API")

# Habilitar CORS para el frontend alojado en GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # mejor: especificar el dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze(
    candidate_name: str = Form(...),
    chapter: str = Form(...),
    position: str = Form(...),
    file: UploadFile = File(...)
):
    # Guardar PDF temporalmente
    file_id = str(uuid.uuid4())[:8]
    pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(pdf_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    try:
        # Aquí llamas a la función que integra tu ATS: extrae secciones, calcula %, genera reporte y retorna path del PDF
        report_path = generate_pdf_report(
            pdf_path,
            position=position,
            candidate_name=candidate_name,
            chapter=chapter,
            indicators_path="app/indicators.json",
            advice_path="app/advice.json"
        )

        # Devuelves archivo como respuesta o su URL
        return FileResponse(report_path, filename=os.path.basename(report_path), media_type="application/pdf")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        # opcional: eliminar el archivo de entrada si quieres ahorrar disco
        try:
            os.remove(pdf_path)
        except:
            pass

