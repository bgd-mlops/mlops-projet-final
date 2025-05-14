#!/usr/bin/env python3
import sys
import psycopg2


def create_plants_table():
    target_db = "mlops_data"

    conn = None
    cur = None

    # Tenter de se connecter à la base mlops_data
    try:
        conn = psycopg2.connect(
            dbname=target_db,
            user="airflow",
            password="airflow",
            host="postgres",   # Le nom du service dans Docker Compose
            port="5432"        # Port interne de Postgres
        )
        print(f"Connexion à la base '{target_db}' réussie.")
    except Exception as e:
        print(
            f"Erreur : Impossible de se connecter à la base '{target_db}' :", e)
        sys.exit(1)

    try:
        cur = conn.cursor()
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS plants_data (
                id SERIAL PRIMARY KEY,
                url_source TEXT NOT NULL UNIQUE,   -- Unicité sur url_source
                url_s3 TEXT UNIQUE,                -- Unicité sur url_s3
                label VARCHAR(50) NOT NULL
            );
        """
        cur.execute(create_table_sql)
        conn.commit()
        print(
            f"Table plants_data créée avec succès dans la base '{target_db}'.")
    except Exception as e:
        print("Erreur lors de la création de la table plants_data :", e)
        sys.exit(1)
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    create_plants_table()
