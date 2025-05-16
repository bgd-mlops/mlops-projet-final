import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from PIL import Image
from src.api.main import app


client = TestClient(app)

# Utility to create a fake image
def create_test_image():
    img = Image.new("RGB", (224, 224), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


@patch("src.api.main.model")
def test_predict_dandelion(mock_model):
    # Mock model output: pretend class 0 is predicted
    fake_output = MagicMock()
    fake_output.argmax.return_value.item.return_value = 0
    mock_model.return_value = fake_output
    mock_model.__call__.return_value = fake_output

    image = create_test_image()
    response = client.post("/predict", files={"file": ("test.jpg", image, "image/jpeg")})
    assert response.status_code == 200
    assert response.json() == {"prediction": "dandelion"}


@patch("src.api.main.model")
def test_predict_grass(mock_model):
    # Mock model output: pretend class 1 is predicted
    fake_output = MagicMock()
    fake_output.argmax.return_value.item.return_value = 1
    mock_model.return_value = fake_output
    mock_model.__call__.return_value = fake_output

    image = create_test_image()
    response = client.post("/predict", files={"file": ("test.jpg", image, "image/jpeg")})
    assert response.status_code == 200
    assert response.json() == {"prediction": "grass"}


def test_predict_invalid_image():
    response = client.post("/predict", files={"file": ("test.txt", b"not an image", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Image invalide"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
