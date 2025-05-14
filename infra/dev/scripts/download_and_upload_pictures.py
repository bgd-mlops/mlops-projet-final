#!/usr/bin/env python3
import sys
import os
import psycopg2
import requests
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


def download_and_upload_pictures():
    # Étape 1 : Connexion à la base "mlops_data"
    try:
        conn = psycopg2.connect(
            dbname="mlops_data",      # La base métier
            user="airflow",
            password="airflow",
            host="postgres",          # Nom du service dans Docker
            # Port interne (communication dans le réseau Docker)
            port="5432"
        )
        print("Connexion à la base 'mlops_data' réussie.")
    except Exception as e:
        print("Erreur de connexion à la base 'mlops_data':", e)
        sys.exit(1)

    cur = None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, url_source, label FROM plants_data WHERE url_s3 IS NULL")
        rows = cur.fetchall()
        print(f"{len(rows)} images à traiter.")
    except Exception as e:
        print("Erreur lors de la récupération des enregistrements:", e)
        if cur is not None:
            cur.close()
        conn.close()
        sys.exit(1)

    # Étape 2 : Connexion à Minio via boto3 dans le réseau Docker (utiliser le nom du service)
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
        conn.close()
        sys.exit(1)

    bucket_name = "images"
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
            conn.close()
            sys.exit(1)

    # Étape 3 : Traiter chaque enregistrement
    for row in rows:
        record_id, url_source, label = row
        print(f"Traitement de l'image {record_id} : {url_source}")
        try:
            response = requests.get(url_source)
            if response.status_code == 200:
                image_data = response.content
                filename = os.path.basename(url_source)
                key = f"{label}/{filename}"
                # Vérifier si l'image existe déjà dans Minio
                try:
                    s3.head_object(Bucket=bucket_name, Key=key)
                    # Si head_object réussit, cela signifie que l'image existe déjà.
                    print(
                        f"L'image {record_id} existe déjà dans le bucket '{bucket_name}'.")
                    minio_url = f"http://minio:9000/{bucket_name}/{key}"
                    # Mettre à jour la BD avec l'URL s'il n'est pas encore renseigné
                    try:
                        cur.execute(
                            "UPDATE plants_data SET url_s3 = %s WHERE id = %s", (minio_url, record_id))
                        conn.commit()
                        print(
                            f"Base mise à jour pour l'image {record_id} avec l'URL {minio_url}.")
                    except Exception as e:
                        print(
                            f"Erreur lors de la mise à jour DB pour l'image {record_id} : {e}")
                    continue  # Passer à l'image suivante
                except ClientError as ce:
                    # Si l'erreur est NotFound, l'image n'existe pas et il faut l'uploader
                    error_code = ce.response['Error']['Code']
                    if error_code != '404':
                        print(
                            f"Erreur lors de la vérification de l'image {record_id} : {ce}")
                        continue

                # L'image n'existe pas, procéder à l'upload
                try:
                    s3.put_object(Bucket=bucket_name, Key=key, Body=image_data)
                    print(f"Image {record_id} uploadée sur Minio.")
                except Exception as e:
                    print(
                        f"Erreur lors de l'upload de l'image {record_id}: {e}")
                    continue

                # Mettre à jour l'URL dans la base de données
                minio_url = f"http://minio:9000/{bucket_name}/{key}"
                try:
                    cur.execute(
                        "UPDATE plants_data SET url_s3 = %s WHERE id = %s", (minio_url, record_id))
                    conn.commit()
                    print(
                        f"Image {record_id} mise à jour dans la BD avec l'URL {minio_url}.")
                except Exception as e:
                    print(
                        f"Erreur lors de la mise à jour de la BD pour l'image {record_id}: {e}")
                    continue
            else:
                print(
                    f"Erreur de téléchargement {url_source}: code {response.status_code}")
        except Exception as ex:
            print(f"Erreur lors du traitement de {url_source}: {ex}")

    # Nettoyage des ressources
    cur.close()
    conn.close()
    print("Traitement terminé.")


if __name__ == "__main__":
    download_and_upload_pictures()
