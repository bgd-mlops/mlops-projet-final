#!/usr/bin/env python3
import sys
import os
import logging
from dotenv import load_dotenv
import psycopg2
from pathlib import Path



# ─── CHARGEMENT DU .env ─────────────────────────────────────────
load_dotenv()


# ─── CONFIGURATION DU LOGGING ─────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── VARIABLES D'ENVIRONNEMENT ────────────────────────────────
airflow_db   = os.getenv("AIRFLOW_DB_NAME")
target_db    = os.getenv("TARGET_DB_NAME")
db_user      = os.getenv("DB_USER")
db_password  = os.getenv("DB_PASSWORD")
db_host      = os.getenv("DB_HOST")
db_port      = os.getenv("DB_PORT")

def create_mlops_db():
    """
    Connecte à la base de maintenance (airflow_db) et crée la base métier (target_db)
    si elle n'existe pas.
    """
    # Connexion à la base de maintenance
    try:
        conn = psycopg2.connect(
            dbname=airflow_db,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        logger.info(f"Connexion à la base '{airflow_db}' réussie")
    except Exception as e:
        logger.error(f"Impossible de se connecter à la base '{airflow_db}'", exc_info=e)
        sys.exit(1)

    # Activer autocommit pour la création de la nouvelle base
    conn.autocommit = True
    cur = conn.cursor()

    # Vérifier l'existence de la base target_db
    try:
        cur.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (target_db,)
        )
        exists = cur.fetchone()
        if exists:
            logger.info(f"La base de données '{target_db}' existe déjà.")
        else:
            cur.execute(f"CREATE DATABASE {target_db};")
            logger.info(f"La base de données '{target_db}' a été créée avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la vérification/création de '{target_db}'", exc_info=e)
        cur.close()
        conn.close()
        sys.exit(1)

    # Fermeture des connexions
    cur.close()
    conn.close()
    logger.info("Opération terminée")

if __name__ == "__main__":
    create_mlops_db()
