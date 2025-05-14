# src/api/main.py
import os
import io

from fastapi import FastAPI, File, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import torch
import torchvision.transforms as T
import mlflow.pytorch

# ─── CONFIGURATION ─────────────────────────────────────────
# (MLflow va déduire le tracking URI, l’endpoint S3 et les creds AWS
#  à partir des vars d’environnement)
os.environ.setdefault("MLFLOW_TRACKING_URI",    "http://mlflow:5000")
os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", "http://minio:9000")
os.environ.setdefault("AWS_ACCESS_KEY_ID",      "minio")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY",  "minio123")

# Nom et stage du modèle à charger (via env vars si vous voulez changer en dev/test)
MODEL_NAME  = os.getenv("MLFLOW_MODEL_NAME",  "DandelionGrassModel")
MODEL_STAGE = os.getenv("MLFLOW_MODEL_STAGE", "Production")
MODEL_URI   = f"models:/{MODEL_NAME}/{MODEL_STAGE}"

# ─── CHARGEMENT DU MODÈLE ───────────────────────────────────
try:
    model = mlflow.pytorch.load_model(MODEL_URI)
    model.eval()
    print(f" Modèle chargé depuis « {MODEL_URI} »")
except Exception as e:
    # On plante immédiatement si la version n’est pas dispo
    raise RuntimeError(f"Impossible de charger le modèle {MODEL_URI}: {e}")

# ─── PRÉTRAITEMENT ───────────────────────────────────────────
transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[.485, .456, .406], std=[.229, .224, .225]),
])

# ─── APPLICATION FASTAPI ────────────────────────────────────
app = FastAPI(title="Dandelion vs Grass")

@app.post("/predict")
async def predict(file: bytes = File(...)):
    # Lecture de l’image
    try:
        img = Image.open(io.BytesIO(file)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Image invalide")

    # Inference
    x = transform(img).unsqueeze(0)
    with torch.no_grad():
        out = model(x)
        label = "dandelion" if out.argmax(1).item() == 0 else "grass"

    return JSONResponse({"prediction": label})

@app.get("/health")
def health():
    return {"status": "ok"}
