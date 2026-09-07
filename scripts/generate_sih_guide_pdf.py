"""
SatQuery AI - Simplified Team Presentation & SIH Evaluator Defense Guide
Generates an easy-to-understand, beautifully styled PDF for team handover and hackathon judging.
"""
import sys
import os
import pathlib

# Fix Windows console encoding if needed
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic page numbers and running headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#334155"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(45, 752, "SatQuery AI — Simplified Team Guide & SIH Evaluator Q&A")
            self.setFont("Helvetica", 8)
            self.drawRightString(612 - 45, 752, "SIH 2026 (Problem SIH26167)")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(45, 746, 612 - 45, 746)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(45, 40, 612 - 45, 40)

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(45, 28, "SatQuery AI Team Documentation | Ready for SIH Evaluation")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 45, 28, page_text)
        self.restoreState()


def build_simplified_pdf(filename="SatQuery_AI_Simplified_Guide.pdf"):
    pdf_path = os.path.abspath(filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=48,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()

    # Color Palette
    C_PRIMARY = colors.HexColor("#0F172A")    # Slate 900
    C_BLUE = colors.HexColor("#1D4ED8")       # Vibrant Blue
    C_TEAL = colors.HexColor("#0D9488")       # Teal
    C_AMBER = colors.HexColor("#D97706")      # Amber
    C_BG_LIGHT = colors.HexColor("#F8FAFC")   # Slate 50
    C_BG_BLUE = colors.HexColor("#EFF6FF")    # Blue 50
    C_BG_GREEN = colors.HexColor("#F0FDF4")   # Green 50
    C_BORDER = colors.HexColor("#CBD5E1")     # Slate 300
    C_TEXT = colors.HexColor("#1E293B")       # Slate 800

    # Typography
    t_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=C_PRIMARY,
        spaceAfter=4
    )

    t_subtitle = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=C_BLUE,
        spaceAfter=10
    )

    h1 = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=C_PRIMARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2 = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=C_BLUE,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=C_TEXT,
        spaceAfter=4
    )

    body_bold = ParagraphStyle('BB', parent=body, fontName='Helvetica-Bold')

    q_title = ParagraphStyle(
        'QTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13.5,
        textColor=C_BLUE,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    a_text = ParagraphStyle(
        'AText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=C_TEXT,
        spaceAfter=6
    )

    story = []

    # =========================================================================
    # HEADER / TITLE
    # =========================================================================
    story.append(Paragraph("🛰️ SatQuery AI — Simple Team Guide & SIH Defense", t_title))
    story.append(Paragraph("<b>Smart India Hackathon 2026 (SIH26167)</b> | <i>Vision-Language Remote Sensing Assistant</i>", t_subtitle))
    story.append(HRFlowable(width="100%", thickness=2, color=C_BLUE, spaceBefore=0, spaceAfter=8))

    # Executive Overview Callout Box
    overview_table = [
        [Paragraph(
            "<b>💡 In One Sentence:</b> SatQuery AI is like <b>'ChatGPT for Satellite Images'</b>. "
            "Instead of complex GIS software (QGIS/ArcGIS), users can ask plain English questions like "
            "<i>'Where are new buildings built?'</i> or <i>'Find all airplanes'</i>, and the system gives instant "
            "text answers along with highlighted visual evidence (heatmaps & bounding boxes).",
            body
        )]
    ]
    t_ov = Table(overview_table, colWidths=[522])
    t_ov.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_BG_BLUE),
        ('BOX', (0,0), (-1,-1), 1, C_BLUE),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(t_ov)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 1: 4 MAIN FEATURES (SIMPLE EXPLANATION)
    # =========================================================================
    story.append(Paragraph("1. The 4 Superpowers of SatQuery AI (Features)", h1))

    features_data = [
        ["Feature / Task", "What It Does (In Simple Words)", "Example User Query"],
        [
            Paragraph("<b>1. RS-VQA</b><br/>(Satellite Q&A)", body),
            Paragraph("Answers semantic questions about what is visible in a satellite photo (land use, terrain type, facility identification).", body),
            Paragraph("<i>'What type of infrastructure is visible in this area?'</i>", body)
        ],
        [
            Paragraph("<b>2. Visual Grounding</b><br/>(Target Finder)", body),
            Paragraph("Finds specific objects and <b>draws bounding boxes</b> with exact geo-coordinates (latitude/longitude + pixel points).", body),
            Paragraph("<i>'Locate and detect all aircraft and runways'</i>", body)
        ],
        [
            Paragraph("<b>3. Change Detection</b><br/>(Before vs After)", body),
            Paragraph("Takes 2 images of the same place from different dates (T1 and T2), aligns them, and <b>highlights new construction or deforestation</b> in red/yellow heatmap with % change.", body),
            Paragraph("<i>'What changed between 2023 and 2025 images?'</i>", body)
        ],
        [
            Paragraph("<b>4. Optical + SAR Fusion</b><br/>(All-Weather Radar)", body),
            Paragraph("Combines normal satellite photos with radar imagery (SAR) to <b>see through clouds, smoke, rain, and at night</b> (e.g. disaster flood mapping).", body),
            Paragraph("<i>'Inspect flood penetration through cloud cover'</i>", body)
        ],
    ]
    t_feat = Table(features_data, colWidths=[105, 235, 182])
    t_feat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_feat)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 2: HOW THE BACKEND WORKS (STEP-BY-STEP)
    # =========================================================================
    story.append(Paragraph("2. How the Backend Works in 5 Simple Steps (Pipeline)", h1))

    steps_data = [
        ["Step", "Stage", "What Happens Behind the Scenes?"],
        ["1", "Upload & Ingestion", "User uploads GeoTIFF/PNG. The system automatically inspects CRS (Coordinate System), spatial resolution, and band count."],
        ["2", "Smart Query Router", "The NLP Router reads the user's question and decides which specialist tool to trigger (VQA, Grounding, Change Detection, or Fusion)."],
        ["3", "Geospatial Alignment", "If comparing two images (T1 vs T2), our Sub-Pixel ECC/ORB algorithm aligns the images perfectly so they overlap pixel-to-pixel."],
        ["4", "AI Model Execution", "The chosen AI adapter runs and produces the answer + generates visual evidence (saved in /storage/evidence/)."],
        ["5", "Confidence Scoring", "A calibrated confidence score (e.g. 92% High) is calculated based on model certainty, image quality, and spatial alignment."]
    ]
    t_steps = Table(steps_data, colWidths=[30, 120, 372])
    t_steps.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ]))
    story.append(t_steps)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 3: TECH STACK & FOLDER MAP (FOR TEAM HANDOVER)
    # =========================================================================
    story.append(Paragraph("3. Technology Stack & Key Folders", h1))

    tech_box = [
        [
            Paragraph("<b>Backend:</b> FastAPI (Python Async REST API)<br/>"
                      "<b>Database:</b> SQLite (Local dev) / PostgreSQL (Docker prod)<br/>"
                      "<b>Tasks:</b> Celery + Redis (Background AI jobs)", body),
            Paragraph("<b>Geospatial:</b> Rasterio (GeoTIFF) + OpenCV (Alignment)<br/>"
                      "<b>AI Models:</b> PyTorch (GeoCLIP, GroundingDINO, ChangeFormer)<br/>"
                      "<b>Testing:</b> Pytest (20/20 Automated Tests Passing)", body)
        ]
    ]
    t_tech = Table(tech_box, colWidths=[260, 262])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 6))

    # Page Break for Q&A section
    story.append(PageBreak())

    # =========================================================================
    # SECTION 4: SIH EVALUATOR DEFENSE & QUESTIONS (HIGH IMPACT)
    # =========================================================================
    story.append(Paragraph("4. SIH Evaluator Defense: Top Questions & Winning Answers", h1))
    story.append(Paragraph(
        "SIH judges (ISRO scientists, defense tech experts, AI professors) will test your engineering depth. "
        "Here is exactly what they will ask and how your team should answer simply and confidently:",
        body
    ))
    story.append(Spacer(1, 4))

    sih_qa = [
        (
            "Q1: Why not just use ChatGPT (GPT-4o) or Google Gemini directly?",
            "<b>Answer:</b> Generic commercial LLMs fail at remote sensing for 4 big reasons:<br/>"
            "1. <b>File Formats:</b> Commercial LLMs only accept standard JPEG/PNG photos. They cannot read multi-band 16-bit GeoTIFFs or raw satellite sensors.<br/>"
            "2. <b>Spatial Coordinates:</b> Generic LLMs hallucinate coordinates. SatQuery uses specialized Grounding models that compute exact latitude/longitude.<br/>"
            "3. <b>Radar / SAR:</b> LLMs think radar speckle noise is a corrupted photo. SatQuery does physical radar decibel scaling (dB) to inspect soil moisture & dielectric properties.<br/>"
            "4. <b>Data Sovereignty:</b> Defense and space agencies cannot send classified satellite rasters to third-party public cloud APIs. SatQuery runs 100% on-premise air-gapped."
        ),
        (
            "Q2: What if the two images (T1 vs T2) are slightly rotated or shifted?",
            "<b>Answer:</b> We built an automatic <b>Sub-Pixel Coregistration Engine</b> (<code>app/geospatial/registration.py</code>). Before comparing images, it uses ECC (Enhanced Correlation Coefficient) and ORB feature points to shift, rotate, and scale image T2 so it aligns with T1 down to the sub-pixel level."
        ),
        (
            "Q3: How do you calculate the Confidence Score? Is it just raw AI probability?",
            "<b>Answer:</b> No! Raw AI probability is often overconfident. We use a <b>Multi-Factor Calibrated Score</b>:<br/>"
            "<code>Confidence = (Vision Model % * 40%) + (Geospatial Overlap IoU * 30%) + (Alignment Quality * 15%) + (Sensor Agreement * 15%) - Resolution Penalty</code>.<br/>"
            "If images don't align or resolution is poor, the confidence score automatically drops."
        ),
        (
            "Q4: Satellite images are huge (multi-gigabytes). How do you prevent server crashes?",
            "<b>Answer:</b><br/>"
            "1. <b>Windowed Tiling:</b> Rasterio reads small chunks (tiles) as needed, instead of loading a 5GB file into RAM all at once.<br/>"
            "2. <b>Asynchronous Queue:</b> Heavy model tasks run in the background via Celery + Redis, keeping the FastAPI server instant and responsive."
        ),
        (
            "Q5: How is your system explainable and auditable for military/government use?",
            "<b>Answer:</b> Every analysis generates two verifiable proofs:<br/>"
            "• <b>Visual Evidence:</b> Pixel change heatmaps and bounding box overlay images saved on disk.<br/>"
            "• <b>Execution Trace:</b> Step-by-step database log showing which tool was chosen, why it was chosen, and how long each step took."
        )
    ]

    for q, a in sih_qa:
        story.append(Paragraph(q, q_title))
        story.append(Paragraph(a, a_text))
        story.append(Spacer(1, 2))

    # =========================================================================
    # SECTION 5: QUICK COMMANDS CHEATSHEET
    # =========================================================================
    story.append(Spacer(1, 4))
    story.append(Paragraph("5. Ready-to-Run Presentation Commands", h1))

    cmd_table = [
        ["Action to Show Judges", "Command to Run in Terminal"],
        ["Run All 20 Automated Tests", ".\\venv\\Scripts\\pytest.exe tests/ -v"],
        ["Run Live End-to-End Demo Script", ".\\venv\\Scripts\\python.exe scripts/verify_live_pipeline.py"],
        ["Start Local API Server", ".\\venv\\Scripts\\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"],
        ["Open Interactive Swagger UI", "http://localhost:8000/docs"],
    ]
    t_cmd = Table(cmd_table, colWidths=[160, 362])
    t_cmd.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C_BG_LIGHT]),
        ('PADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_cmd)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated simplified PDF at: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    out_name = "SatQuery_AI_Technical_Guide_and_SIH_Defense.pdf"
    if len(sys.argv) > 1:
        out_name = sys.argv[1]
    build_simplified_pdf(out_name)
