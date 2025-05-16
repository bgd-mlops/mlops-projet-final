#!/usr/bin/env python3
import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

import torch
from tqdm import tqdm
import mlflow
import mlflow.pytorch
from mlflow.tracking import MlflowClient
import boto3
from botocore.client import Config
from airflow.decorators import task

from ml.model import build_model
from ml.data_loader import get_dataloaders

# ─── CHARGEMENT DU .env ─────────────────────────────────────────
load_dotenv()

# ─── CONFIGURATION DU LOGGING ─────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── VARIABLES D'ENVIRONNEMENT ────────────────────────────────
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
MLFLOW_S3_ENDPOINT_URL = os.getenv("MLFLOW_S3_ENDPOINT_URL")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = os.getenv("MLFLOW_S3_BUCKET", "mlflow-artifacts")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT", "my_training_experiment")

# Ne pas hardcoder les URIs dans le code
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(EXPERIMENT_NAME)


def get_s3_client():
    """
    Initialise et retourne un client S3/MinIO configuré.
    """
    try:
        client = boto3.client(
            's3',
            endpoint_url=MLFLOW_S3_ENDPOINT_URL,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name=AWS_REGION
        )
        logger.info("Client S3 initialisé")
        return client
    except Exception as e:
        logger.error("Échec de l'initialisation du client S3", exc_info=e)
        sys.exit(1)


def ensure_bucket(client, bucket_name):
    """
    Vérifie si le bucket existe, sinon le crée.
    """
    try:
        client.head_bucket(Bucket=bucket_name)
        logger.info(f"Bucket '{bucket_name}' existe déjà")
    except Exception:
        logger.info(f"Création du bucket '{bucket_name}'")
        try:
            client.create_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' créé")
        except Exception as e:
            logger.error(f"Erreur de création du bucket '{bucket_name}'", exc_info=e)
            sys.exit(1)


def train_model(epochs: int = 10, lr: float = 1e-4):
    """
    Entraîne le modèle et le publie sur MLflow avec gestion du Model Registry.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Utilisation du device: {device}")

    # Préparation modèle et data
    model, criterion, optimizer = build_model(lr=lr, device=device)
    train_loader, val_loader = get_dataloaders()

    s3 = get_s3_client()
    ensure_bucket(s3, BUCKET_NAME)

    best_val_acc = 0.0
    best_state = None

    run_name = f"train_{datetime.now():%Y-%m-%d_%H-%M-%S}"
    with mlflow.start_run(run_name=run_name):
        mlflow.log_params({"epochs": epochs, "lr": lr, "optimizer": optimizer.__class__.__name__})

        for epoch in range(epochs):
            logger.info(f"Début de l'époque {epoch+1}/{epochs}")
            # Phase d'entraînement
            model.train()
            train_loss = 0.0
            train_correct = 0
            for imgs, labels in tqdm(train_loader, desc="Training"):
                imgs, labels = imgs.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = model(imgs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                train_loss += loss.item() * imgs.size(0)
                train_correct += (outputs.argmax(1) == labels).sum().item()

            # Phase de validation
            val_loss = 0.0
            val_correct = 0
            model.eval()
            with torch.no_grad():
                for imgs, labels in tqdm(val_loader, desc="Validating"):
                    imgs, labels = imgs.to(device), labels.to(device)
                    outputs = model(imgs)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item() * imgs.size(0)
                    val_correct += (outputs.argmax(1) == labels).sum().item()

            # Calcul métriques
            n_train = len(train_loader.dataset)
            n_val = len(val_loader.dataset)
            train_loss /= n_train
            train_acc = train_correct / n_train
            val_loss /= n_val
            val_acc = val_correct / n_val

            logger.info(f"Train loss: {train_loss:.4f}, acc: {train_acc:.4f}")
            logger.info(f"Val   loss: {val_loss:.4f}, acc: {val_acc:.4f}")

            mlflow.log_metrics(
                {"train_loss": train_loss, "train_acc": train_acc,
                 "val_loss": val_loss, "val_acc": val_acc},
                step=epoch
            )

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_state = model.state_dict()

        # Logging du meilleur modèle
        model.load_state_dict(best_state)
        scripted = torch.jit.script(model)
        mlflow.pytorch.log_model(
            pytorch_model=scripted,
            artifact_path="model",
            code_paths=None  
        )
        run_id = mlflow.active_run().info.run_id
        logged_model_uri = f"runs:/{run_id}/model"

        # 3. Enregistrer dans le Model Registry
        model_name = "DandelionGrassModel"
        registered_model = mlflow.register_model(
            logged_model_uri,
            name=model_name
        )

        # 4. Promouvoir la version en Production
        client = MlflowClient()
        client.transition_model_version_stage(
            name=model_name,
            version=registered_model.version,
            stage="Production",
            archive_existing_versions=True
        )
        logger.info(f"Modèle promu en Production")


if __name__ == "__main__":
    train_model()
