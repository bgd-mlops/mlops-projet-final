#!/usr/bin/env python3
import sys
import os
import logging
from dotenv import load_dotenv
import psycopg2

# ─── CHARGEMENT DU .env ─────────────────────────────────────────
load_dotenv()

# ─── CONFIGURATION DU LOGGING ─────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── VARIABLES D'ENVIRONNEMENT ────────────────────────────────
target_db   = os.getenv("TARGET_DB_NAME")
db_user     = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host     = os.getenv("DB_HOST")
db_port     = os.getenv("DB_PORT")

# Base URL pour les images
github_raw_base = os.getenv(
    "GITHUB_RAW_BASE")
labels = os.getenv("PLANT_LABELS", "dandelion,grass").split(",")
images_per_label = int(os.getenv("IMAGES_PER_LABEL", "200"))


def get_db_connection():
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


def insert_metadata():
    """
    Insère les URLs d'images dans la table plants_data si elles n'existent pas déjà.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        for label in labels:
            for i in range(images_per_label):
                url = f"{github_raw_base}/{label}/{i:08d}.jpg"
                cur.execute(
                    "SELECT 1 FROM plants_data WHERE url_source = %s", (url,)
                )
                if cur.fetchone() is None:
                    cur.execute(
                        "INSERT INTO plants_data (url_source, url_s3, label) VALUES (%s, %s, %s)",
                        (url, None, label)
                    )
                    logger.info(f"Inséré: {url}")
                else:
                    logger.debug(f"Exist: {url}")
        conn.commit()
        logger.info("Insertion des métadonnées terminée avec succès.")
    except Exception as e:
        logger.error("Erreur lors de l'insertion des métadonnées", exc_info=e)
        conn.rollback()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()
        logger.info("Connexion fermée.")

if __name__ == "__main__":
    insert_metadata()
