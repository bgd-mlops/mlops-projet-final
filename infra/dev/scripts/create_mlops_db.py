#!/usr/bin/env python3
import sys
import psycopg2


def create_mlops_db():
    airflow_db = "airflow"  # La base de maintenance dans ton docker-compose
    target_db = "mlops_data"    # La base métier que tu veux créer

    # Tenter de se connecter à la base de maintenance "airflow"
    try:
        conn = psycopg2.connect(
            dbname=airflow_db,
            user="airflow",
            password="airflow",
            host="postgres",   # Nom du service dans Docker Compose
            port="5432"        # Port interne de Postgres
        )
        print(f"connexion à bdd {airflow_db} réussie")
    except Exception as e:
        print(
            f"Erreur : la base '{airflow_db}' n'existe pas ou n'est pas accessible.")
        print("Détails :", e)
        sys.exit(1)

    # Activer autocommit pour la création de la nouvelle base
    conn.autocommit = True
    cur = conn.cursor()

    # Vérifier si la base target_db existe déjà
    cur.execute(
        "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (target_db,))
    exists = cur.fetchone()

    if exists:
        print(f"La base de données '{target_db}' existe déjà.")
    else:
        try:
            cur.execute(f"CREATE DATABASE {target_db};")
            print(f"La base de données '{target_db}' a été créée avec succès.")
        except Exception as e:
            print(
                f"Erreur lors de la création de la base de données '{target_db}':", e)
            sys.exit(1)

    cur.close()
    conn.close()


if __name__ == "__main__":
    create_mlops_db()
