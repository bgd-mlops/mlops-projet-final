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
db_user      = os.getenv("DB_USER")
db_password  = os.getenv("DB_PASSWORD")
db_host      = os.getenv("DB_HOST")
db_port      = os.getenv("DB_PORT")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS plants_data (
    id SERIAL PRIMARY KEY,
    url_source TEXT NOT NULL UNIQUE,
    url_s3    TEXT UNIQUE,
    label     VARCHAR(50) NOT NULL
);
"""

def create_plants_table():
    """
    Connecte à la base target_db et crée la table plants_data si elle n'existe pas.
    """
    conn = None
    cur = None

    # Connexion à la base
    try:
        conn = psycopg2.connect(
            dbname=target_db,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        logger.info(f"Connexion à la base '{target_db}' réussie.")
    except Exception as e:
        logger.error(f"Erreur de connexion à la base '{target_db}'", exc_info=e)
        sys.exit(1)

    try:
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()
        logger.info(f"Table 'plants_data' créée ou déjà existante dans '{target_db}'.")
    except Exception as e:
        logger.error("Erreur lors de la création de la table 'plants_data'", exc_info=e)
        sys.exit(1)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        logger.info("Fermeture de la connexion à la base")

if __name__ == "__main__":
    create_plants_table()
