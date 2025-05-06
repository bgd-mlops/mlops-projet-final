#!/usr/bin/env python3
import torch
import boto3
import io
import os
from botocore.client import Config
from botocore.exceptions import ClientError
from datetime import datetime
import sys

def save_model_s3():
    cur = None
    try:
        s3 = boto3.client(
            's3',
            endpoint_url="http://minio:9000",  # Utilise le nom du service Minio dans Docker
            aws_access_key_id="minio",
            aws_secret_access_key="minio123",
            config=Config(signature_version='s3v4'),
            region_name="us-east-1"
        )
    except Exception as e:
        print("Erreur de connexion à Minio:", e)
        cur.close()

    bucket_name = "models"

    # Vérification de l'existence du bucket et création si nécessaire
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' existe déjà.")
    except ClientError as e:
        print(
            f"Bucket '{bucket_name}' n'existe pas, tentative de création...", e)
        try:
            s3.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' créé avec succès.")
        except Exception as e2:
            print(f"Erreur lors de la création du bucket '{bucket_name}':", e2)
            cur.close()

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    model_key = f"models/best_model_{timestamp}.pt"
    model_path = "./models/best_model.pt"

    # récupération du modele
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Local file {model_path} does not exist")
    try:
        s3.upload_file(model_path, bucket_name, model_key)
        print(f"✅ Uploaded {model_path} to s3://{bucket_name}/{model_key}")
    except ClientError as e:
            print(f"Failed to upload to S3: {e}")
            raise

if __name__ == "__main__":
    save_model_s3()