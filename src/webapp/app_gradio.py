# app_gradio.py
import os
import io
import requests
from PIL import Image
import gradio as gr

# 1) Where your FastAPI lives
API_URL = os.getenv("API_URL", "http://localhost:8000/predict")

def predict(image: Image.Image) -> str:
    """
    Convert the uploaded PIL image to JPEG bytes, POST to your API,
    and return the 'dandelion' or 'grass' prediction.
    """
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    buf.seek(0)
    files = {"file": ("image.jpg", buf, "image/jpeg")}
    resp = requests.post(API_URL, files=files)
    resp.raise_for_status()
    return resp.json().get("prediction", "Error")

# 2) Build & launch Gradio
iface = gr.Interface(
    fn=predict,
    inputs=gr.Image(type="pil"),
    outputs="text",
    title="Dandelion vs Grass Classifier",
    description="Upload a photo of a flower or grass patch and get back “dandelion” or “grass.”"
)

if __name__ == "__main__":
    # on your laptop:
    iface.launch(server_name="0.0.0.0", server_port=7860,share = True)
