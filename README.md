# SatQuery AI — Backend Architecture & API Guide
### Smart India Hackathon 2026 (Problem Statement SIH26167)
**Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis**

---

## 🛰️ 1. Architecture Overview

SatQuery AI is an agentic Earth-observation copilot designed around strict geospatial validation, multi-modal alignment, specialist tool routing, explainable visual evidence, and calibrated confidence scoring:

```
NATURAL LANGUAGE QUERY + SATELLITE RASTERS (Optical / SAR / Bi-temporal)
                      ↓
           QUERY UNDERSTANDING & INTENT CLASSIFICATION
                      ↓
       GEOSPATIAL VALIDATION (CRS, Extent IoU, Resolution, Modality)
                      ↓
   SUB-PIXEL COREGISTRATION & PREPROCESSING (ECC / ORB / dB scaling)
                      ↓
           DETERMINISTIC AGENT EXECUTION POLICY CHECK
                      ↓
             SPECIALIST TOOL & MODEL SELECTION
  ┌───────────────────┬───────────────────┬───────────────────┬───────────────────┐
  │      RS-VQA       │  Visual Grounding │  Temporal Change  │ Optical-SAR Fusion│
  │     (GeoCLIP)     │  (GroundingDINO)  │   (ChangeFormer)  │  (Cross-Attn Net) │
  └───────────────────┴───────────────────┴───────────────────┴───────────────────┘
                      ↓
             VISUAL EVIDENCE AGGREGATION
   (Bounding Box Overlays, Change Mask Heatmaps, Side-by-Side Splits)
                      ↓
          CALIBRATED MULTI-FACTOR CONFIDENCE
                      ↓
         AUDITABLE RESPONSE WITH EXECUTION TRACE
```

---

## 🚀 2. Quickstart & Installation

### Option A: Local Python Setup (Zero-Config Demo Mode)
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Generate sample datasets (Optical, SAR, T1, T2)
python scripts/generate_sample_data.py

# Run FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation will be available at: **`http://localhost:8000/docs`**

### Option B: Docker Compose (Full Stack with Postgres & Redis)
```bash
cd backend
docker compose up --build
```

---

## 🧪 3. Running Automated Tests

```bash
cd backend
pytest tests/ -v
```

---

## 📡 4. Core API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check for DB, Storage, Model Registry & Device |
| `POST` | `/api/v1/auth/register` | Register new analyst account |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT Bearer token |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile |
| `POST` | `/api/v1/uploads` | Upload GeoTIFF/PNG with automatic metadata inspection |
| `GET` | `/api/v1/uploads` | List recent uploaded imagery |
| `GET` | `/api/v1/uploads/{id}/metadata` | Fetch granular raster CRS, bounds, and bands |
| `POST` | `/api/v1/queries` | Intent analysis and plan generation preview |
| `POST` | `/api/v1/analysis` | Execute synchronous or asynchronous analysis |
| `GET` | `/api/v1/analysis/{id}` | Fetch full analysis result, evidence, and execution trace |
| `POST` | `/api/v1/jobs` | Submit async background analysis job |
| `GET` | `/api/v1/jobs/{id}` | Poll background job status and progress |
| `GET` | `/api/v1/tools` | List registered specialist tools and contracts |
| `GET` | `/api/v1/models` | List loaded model adapters and hardware deployment status |
| `GET` | `/api/v1/history` | Chronological audit trail of past analyses |

---

## 🤖 5. Specialist Model Adapters & Placement

To plug in real PyTorch / HuggingFace checkpoints:
- **RS-VQA**: Place model weights under `storage/models/vqa/` and configure in `app/models/vqa_model.py`.
- **Visual Grounding**: Place checkpoints in `storage/models/grounding/` (e.g. Grounding DINO) in `app/models/grounding_model.py`.
- **Change Detection**: Place checkpoints in `storage/models/change/` (e.g. ChangeFormer / BIT) in `app/models/change_model.py`.
- **Optical + SAR Fusion**: Place checkpoints in `storage/models/fusion/` in `app/models/fusion_model.py`.

Toggle `DEMO_MODE=false` in `.env` when weights are mounted to enable GPU inference.