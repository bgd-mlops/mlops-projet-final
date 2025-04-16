from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import psycopg2
from airflow.providers.postgres.operators.postgres import PostgresOperator


def hello():
    print("Hello depuis mon premier DAG !")
    
    
def download_and_store_image():
    folder_path = "https://raw.githubusercontent.com/btphan95/greenr-airflow/master/data/dandelion/"
    
    for i in range(200):
        url = f'{folder_path}/{i:08d}.jpg'
        response = requests.get(url)
        if response.status_code == 200:
            image_data = response.content
            conn = psycopg2.connect(
                dbname="airflow",
                user="airflow",
                password="airflow",
                host="postgres",
                port="5432"
            )
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO images (name, data) VALUES (%s, %s)",
                (f"{i}.jpg", psycopg2.Binary(image_data))
            )
            conn.commit()
            cursor.close()
            conn.close()
            print("Image stockée dans la base de données avec succès.")
        else:
            print(f"Erreur de téléchargement : {response.status_code}")




with DAG(
    dag_id='hello_dag',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
) as hello_dag:
    task = PythonOperator(
        task_id='say_hello',
        python_callable=hello
    )
    
with DAG(
    dag_id="download_and_store_image",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False
) as image_dag:

    create_table = PostgresOperator(
    task_id="create_image_table",
    postgres_conn_id="airflow_db",
    sql="""
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            name TEXT,
            data BYTEA
        );
    """,
    )

    download = PythonOperator(
        task_id="download_and_store_image",
        python_callable=download_and_store_image
    )