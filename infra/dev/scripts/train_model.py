import sys
import os

# Add the project root directory to the system path so that 'model' and 'data_loader' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'ml')))

import torch
from tqdm import tqdm
import os
import io
from mlflow.tracking import MlflowClient


from ml.model import build_model
from ml.data_loader import get_dataloaders

import mlflow
import mlflow.pytorch
from airflow.decorators import task
import boto3
from datetime import datetime
from botocore.client import Config


os.environ['MLFLOW_TRACKING_URI'] = 'http://mlflow:5000'
os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://minio:9000'
os.environ['AWS_ACCESS_KEY_ID'] = 'minio'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minio123'
    
# ------------------------------------------
# Create bcket S3 to save model
def create_s3_bucket(bucket_name):
    try:
        s3 = boto3.client(
            's3',
            endpoint_url="http://minio:9000",  
            aws_access_key_id="minio",
            aws_secret_access_key="minio123",
            config=Config(signature_version='s3v4'),
            region_name="us-east-1"
        )
    except Exception as e:
        print("Erreur de connexion à Minio:", e)

    # Check if the bucket exists
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} already exists.")
    except Exception as e:
        # If the bucket doesn't exist, create it
        print(f"Bucket {bucket_name} does not exist. Creating...")
        s3.create_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} created.")


# ------------------------------------------
# Training Function
def train_model(epochs=1, lr=1e-4):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model, criterion, optimizer = build_model(lr=lr, device=device)
    train_loader, val_loader = get_dataloaders()
    best_val_acc = 0.0
    best_model_state = None

    # Setup MLflow tracking
    mlflow.set_tracking_uri("http://mlflow:5000")  
    mlflow.set_experiment("my_training_experiment")

    with mlflow.start_run(run_name=f"train_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"):
        mlflow.log_params({
            "epochs": epochs,
            "lr": lr,
            "optimizer": "Adam"
        })

        bucket_name = "mlflow-artifacts"

        create_s3_bucket(bucket_name)

        for epoch in range(epochs):
            print(f"\nEpoch {epoch+1}/{epochs}")
            model.train()
            train_loss, train_correct = 0.0, 0

            for images, labels in tqdm(train_loader, desc="Training"):
                images, labels = images.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                train_loss += loss.item() * images.size(0)
                train_correct += (outputs.argmax(1) == labels).sum().item()

            train_acc = train_correct / len(train_loader.dataset)
            train_loss /= len(train_loader.dataset)

            # Validation phase
            model.eval()
            val_loss, val_correct = 0.0, 0
            with torch.no_grad():
                for images, labels in tqdm(val_loader, desc="Validating"):
                    images, labels = images.to(device), labels.to(device)
                    outputs = model(images)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item() * images.size(0)
                    val_correct += (outputs.argmax(1) == labels).sum().item()

            val_acc = val_correct / len(val_loader.dataset)
            val_loss /= len(val_loader.dataset)

            print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
            print(f"Val   Loss: {val_loss:.4f}, Val   Acc: {val_acc:.4f}")

            mlflow.log_metrics({
                "train_loss": train_loss,
                "train_acc": train_acc,
                "val_loss": val_loss,
                "val_acc": val_acc
            }, step=epoch)

            # Save best model directly to MLflow (no disk saving)
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model_state = model.state_dict()

        # Load best model and log it to MLflow (directly to S3/MinIO)
        model.load_state_dict(best_model_state)
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

        print(f"Modèle version {registered_model.version} enregistré et promu en Production")
# ------------------------------------------
# Run standalone
if __name__ == "__main__":
    train_model()
