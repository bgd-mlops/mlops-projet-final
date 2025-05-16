import os
import io
from dotenv import load_dotenv
import logging

from fastapi import FastAPI, File, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import torch
import torchvision.transforms as T
import mlflow.pytorch

# ─── CHARGEMENT DU .env ─────────────────────────────────────────
# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

# ─── CONFIGURATION ─────────────────────────────────────────
mlflow_tracking_uri    = os.getenv("MLFLOW_TRACKING_URI")
mlflow_s3_endpoint_url = os.getenv("MLFLOW_S3_ENDPOINT_URL")
aws_access_key_id      = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key  = os.getenv("AWS_SECRET_ACCESS_KEY")
model_name             = os.getenv("MLFLOW_MODEL_NAME", "DandelionGrassModel")
model_stage            = os.getenv("MLFLOW_MODEL_STAGE", "Production")
model_uri              = f"models:/{model_name}/{model_stage}"

# Définition des variables pour MLflow et AWS
if mlflow_tracking_uri:
    os.environ["MLFLOW_TRACKING_URI"] = mlflow_tracking_uri
if mlflow_s3_endpoint_url:
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = mlflow_s3_endpoint_url
if aws_access_key_id:
    os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key_id
if aws_secret_access_key:
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_access_key

# ─── CONFIGURATION DU LOGGING ─────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── CHARGEMENT DU MODÈLE ─────────────────────────────────────
try:
    model = mlflow.pytorch.load_model(model_uri)
    model.eval()
    logger.info(f"Modèle chargé depuis: {model_uri}")
except Exception as e:
    logger.error(f"Impossible de charger le modèle {model_uri}", exc_info=e)
    raise RuntimeError(f"Impossible de charger le modèle {model_uri}: {e}")

# ─── PRÉTRAITEMENT ─────────────────────────────────────────────
transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[.485, .456, .406], std=[.229, .224, .225]),
])

# ─── APPLICATION FASTAPI ──────────────────────────────────────
app = FastAPI(title="Dandelion vs Grass")

@app.post("/predict")
async def predict(file: bytes = File(...)):
    """
    Endpoint pour la prédiction : reçoit une image en bytes,
    effectue le prétraitement, l'inférence et renvoie le label.
    """
    # Lecture de l’image
    try:
        img = Image.open(io.BytesIO(file)).convert("RGB")
        logger.debug("Image reçue et convertie en RGB")
    except Exception as e:
        logger.error("Erreur de lecture de l'image", exc_info=e)
        raise HTTPException(status_code=400, detail="Image invalide")

    # Prétraitement
    x = transform(img).unsqueeze(0)
    logger.debug("Prétraitement de l'image terminé")

    # Inference
    try:
        with torch.no_grad():
            out = model(x)
        label = "dandelion" if out.argmax(1).item() == 0 else "grass"
        logger.info(f"Prédiction réalisée : {label}")
    except Exception as e:
        logger.error("Erreur interne lors de l'inférence", exc_info=e)
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'inférence")

    return JSONResponse({"prediction": label})

@app.get("/health")
def health():
    """Vérifie l'état de l'API."""
    logger.info("Check health endpoint")
    return {"status": "ok"}
