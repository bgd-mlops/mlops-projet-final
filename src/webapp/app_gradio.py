import os
import io
import logging
from dotenv import load_dotenv
import requests
from PIL import Image
import gradio as gr

# ─── CHARGEMENT DU .env ─────────────────────────────────────────
load_dotenv()

# ─── CONFIGURATION DU LOGGING ─────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── CONFIGURATION DE L'API ────────────────────────────────────
API_URL = os.getenv("API_URL", "http://localhost:8000/predict")
logger.info(f"API URL définie sur: {API_URL}")


def predict(image: Image.Image) -> str:
    """
    Convertit l'image PIL en bytes JPEG, envoie à l'API FastAPI
    et renvoie la prédiction 'dandelion' ou 'grass'.
    """
    try:
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        buf.seek(0)
        files = {"file": ("image.jpg", buf, "image/jpeg")}
        logger.debug("Envoi de la requête à l'API...")
        resp = requests.post(API_URL, files=files)
        resp.raise_for_status()
        prediction = resp.json().get("prediction", "Error")
        logger.info(f"Prédiction reçue: {prediction}")
        return prediction
    except requests.exceptions.RequestException as e:
        logger.error("Erreur lors de l'appel à l'API", exc_info=e)
        return "Error: impossible de joindre l'API"
    except Exception as e:
        logger.error("Erreur inattendue dans la fonction predict", exc_info=e)
        return "Error: exception inattendue"


iface = gr.Interface(
    fn=predict,
    inputs=gr.Image(type="pil"),
    outputs="text",
    title="Dandelion vs Grass Classifier",
    description=(
        "Upload a photo of a flower or grass patch and get back “dandelion” or “grass.”"
    )
)

if __name__ == "__main__":
    logger.info("Lancement de l'interface Gradio")
    iface.launch(server_name="0.0.0.0", server_port=7860, share=True)
