#!/usr/bin/env python3
import psycopg2


def insert_metadata():
    conn = None
    cur = None
    try:
        # Connexion à la base métier "mlops_data"
        conn = psycopg2.connect(
            dbname="mlops_data",
            user="airflow",
            password="airflow",
            host="localhost",   # ou "postgres" si exécuté dans un container Docker
            port="5433"
        )
        cur = conn.cursor()

        labels = ["dandelion", "grass"]
        for label in labels:
            for i in range(200):
                url = f"https://raw.githubusercontent.com/btphan95/greenr-airflow/refs/heads/master/data/{label}/{i:08d}.jpg"
                cur.execute(
                    "INSERT INTO plants_data (url_source, url_s3, label) VALUES (%s, %s, %s)",
                    (url, None, label)
                )
        conn.commit()
        print("Insertion des métadonnées terminée avec succès.")
    except Exception as e:
        print("Erreur lors de l'insertion :", e)
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    insert_metadata()
