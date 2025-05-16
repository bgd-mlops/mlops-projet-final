#!/usr/bin/env python3
import sys
import os
import logging
from dotenv import load_dotenv
import psycopg2
import requests
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# ─── CHARGEMENT DU .env ─────────────────────────────────────────
load_dotenv()

# ─── CONFIGURATION DU LOGGING ─────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── VARIABLES D'ENVIRONNEMENT ────────────────────────────────
# Base de données
target_db   = os.getenv("TARGET_DB_NAME")
db_user     = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host     = os.getenv("DB_HOST")
db_port     = os.getenv("DB_PORT")

# Minio / S3
s3_endpoint = os.getenv("MLFLOW_S3_ENDPOINT_URL")
aws_key     = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret  = os.getenv("AWS_SECRET_ACCESS_KEY")
bucket_name = os.getenv("BUCKET_NAME", "images")

def get_db_connection():
    """
    Retourne une connexion psycopg2 configurée pour la base target_db.
    """
    try:
        conn = psycopg2.connect(
            dbname=target_db,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.autocommit = False
        logger.info(f"Connecté à la base '{target_db}'")
        return conn
    except Exception as e:
        logger.error(f"Échec de connexion à la base '{target_db}'", exc_info=e)
        sys.exit(1)


def get_s3_client():
    """
    Retourne un client boto3 configuré pour Minio/S3.
    """
    try:
        client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            config=Config(signature_version='s3v4'),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        logger.info("Client S3 initialisé")
        return client
    except Exception as e:
        logger.error("Échec de l'initialisation du client S3", exc_info=e)
        sys.exit(1)


def ensure_bucket_exists(s3):
    """
    Vérifie si le bucket existe, sinon le crée.
    """
    try:
        s3.head_bucket(Bucket=bucket_name)
        logger.info(f"Bucket '{bucket_name}' existe déjà")
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code')
        if code in ('404', 'NoSuchBucket'):
            try:
                s3.create_bucket(Bucket=bucket_name)
                logger.info(f"Bucket '{bucket_name}' créé")
            except Exception as e2:
                logger.error(f"Impossible de créer le bucket '{bucket_name}'", exc_info=e2)
                sys.exit(1)
        else:
            logger.error(f"Erreur head_bucket pour '{bucket_name}'", exc_info=e)
            sys.exit(1)


def download_and_upload_pictures():
    """
    Télécharge les images non uploadées depuis plants_data,
    les stocke dans S3, et met à jour la base avec l'URL.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Récupérer les enregistrements sans url_s3
    try:
        cur.execute(
            "SELECT id, url_source, label FROM plants_data WHERE url_s3 IS NULL"
        )
        rows = cur.fetchall()
        logger.info(f"{len(rows)} images à traiter")
    except Exception as e:
        logger.error("Erreur récupération enregistrements", exc_info=e)
        conn.close()
        sys.exit(1)

    s3 = get_s3_client()
    ensure_bucket_exists(s3)

    for record_id, url_source, label in rows:
        logger.info(f"Traitement id={record_id}, url={url_source}")
        try:
            resp = requests.get(url_source, timeout=10)
            resp.raise_for_status()
            data = resp.content
            filename = os.path.basename(url_source)
            key = f"{label}/{filename}"

            # Vérifier et uploader
            try:
                s3.head_object(Bucket=bucket_name, Key=key)
                logger.info(f"Objet '{key}' existe déjà")
            except ClientError as ce:
                if ce.response['Error']['Code'] in ('404', 'NoSuchKey'):
                    s3.put_object(Bucket=bucket_name, Key=key, Body=data)
                    logger.info(f"Upload de '{key}' réussi")
                else:
                    logger.error(f"Erreur head_object pour '{key}'", exc_info=ce)
                    continue

            # Mettre à jour la BDD
            url_s3 = f"{s3_endpoint}/{bucket_name}/{key}"
            try:
                cur.execute(
                    "UPDATE plants_data SET url_s3 = %s WHERE id = %s",
                    (url_s3, record_id)
                )
                conn.commit()
                logger.info(f"Mise à jour BDD id={record_id} url_s3={url_s3}")
            except Exception as e:
                logger.error(f"Erreur update BDD id={record_id}", exc_info=e)
                conn.rollback()
        except Exception as e:
            logger.error(f"Erreur traitement id={record_id}", exc_info=e)
            continue

    cur.close()
    conn.close()
    logger.info("Traitement terminé")


if __name__ == "__main__":
    download_and_upload_pictures()
