#!/usr/bin/env python3
import os
import psycopg2
import requests
import boto3
from botocore.client import Config


def download_and_upload_pictures():
    # Connexion à la base mlops_data depuis l'hôte local
    try:
        conn = psycopg2.connect(
            dbname="mlops_data",
            user="airflow",
            password="airflow",
            host="localhost",   # depuis ton venv, on utilise localhost
            # port mappé dans docker-compose (ex: "5433:5432")
            port="5433"
        )
    except Exception as e:
        print("Erreur de connexion à la base:", e)
        return

    cur = conn.cursor()
    # Récupérer les enregistrements où url_s3 est NULL
    cur.execute(
        "SELECT id, url_source, label FROM plants_data WHERE url_s3 IS NULL")
    rows = cur.fetchall()
    print(f"{len(rows)} images à traiter.")

    # Connexion à Minio via boto3 en utilisant localhost
    s3 = boto3.client(
        's3',
        endpoint_url="http://localhost:9000",  # accès via le port mappé sur localhost
        aws_access_key_id="minio",
        aws_secret_access_key="minio123",
        config=Config(signature_version='s3v4'),
        region_name="us-east-1"  # région arbitraire
    )
    bucket_name = "images"

    # Vérifier si le bucket existe, sinon le créer
    try:
        s3.head_bucket(Bucket=bucket_name)
    except Exception as e:
        print(f"Bucket '{bucket_name}' n'existe pas, création...", e)
        s3.create_bucket(Bucket=bucket_name)

    # Pour chaque enregistrement, télécharger l'image et uploader vers Minio
    for row in rows:
        record_id, url_source, label = row
        print(f"Traitement de l'image {record_id} : {url_source}")
        try:
            response = requests.get(url_source)
            if response.status_code == 200:
                image_data = response.content
                # Construit le nom de fichier à partir de l'URL
                filename = os.path.basename(url_source)
                # Organiser par dossier en fonction du label
                key = f"{label}/{filename}"
                # Upload sur Minio
                s3.put_object(Bucket=bucket_name, Key=key, Body=image_data)
                # Construire l'URL d'accès à l'image stockée (selon ta configuration Minio)
                minio_url = f"http://localhost:9000/{bucket_name}/{key}"
                # Mettre à jour la table plants_data avec l'URL de l'image dans Minio
                cur.execute(
                    "UPDATE plants_data SET url_s3 = %s WHERE id = %s", (minio_url, record_id))
                conn.commit()
                print(f"Image {record_id} uploadée vers {minio_url}")
            else:
                print(
                    f"Erreur de téléchargement {url_source}: code {response.status_code}")
        except Exception as ex:
            print(f"Erreur lors du traitement de {url_source}: {ex}")

    cur.close()
    conn.close()
    print("Traitement terminé.")


if __name__ == "__main__":
    download_and_upload_pictures()
