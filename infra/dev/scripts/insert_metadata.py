#!/usr/bin/env python3
import sys
import psycopg2


def insert_metadata():
    conn = None
    cur = None

    # Tentative de connexion à la base métier "mlops_data"
    try:
        conn = psycopg2.connect(
            # Base métier (assure-toi qu'elle est correcte)
            dbname="mlops_data",
            user="airflow",
            password="airflow",
            host="postgres",          # Nom du service dans Docker Compose
            port="5432"               # Port interne de Postgres
        )
        print("Connexion à la base 'mlops_data' réussie.")
    except Exception as e:
        print("Erreur : Impossible de se connecter à la base 'mlops_data' :", e)
        sys.exit(1)

    try:
        cur = conn.cursor()
        labels = ["dandelion", "grass"]
        for label in labels:
            for i in range(200):
                url = f"https://raw.githubusercontent.com/btphan95/greenr-airflow/refs/heads/master/data/{label}/{i:08d}.jpg"
                # Vérification si l'URL est déjà présente
                cur.execute(
                    "SELECT 1 FROM plants_data WHERE url_source = %s", (url,))
                if cur.fetchone() is None:
                    cur.execute(
                        "INSERT INTO plants_data (url_source, url_s3, label) VALUES (%s, %s, %s)",
                        (url, None, label)
                    )
                    print(f"Insertion de {url} effectuée.")
                else:
                    print(
                        f"Données pour {url} existent déjà, insertion ignorée.")
        conn.commit()
        print("Insertion des métadonnées terminée avec succès.")
    except Exception as e:
        print("Erreur lors de l'insertion des métadonnées :", e)
        sys.exit(1)
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    insert_metadata()
