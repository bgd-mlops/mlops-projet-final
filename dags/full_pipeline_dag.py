#!/usr/bin/env python3
import subprocess
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def run_python_script(script_path):
    """
    Exécute un script Python localisé à script_path,
    par exemple : /opt/airflow/scripts/insert_metadata.py
    """
    command = ["python3", script_path]
    # subprocess.run lance la commande et check=True lève une exception si returncode != 0
    subprocess.run(command, check=True)


with DAG(
    dag_id='full_pipeline',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    description="Pipeline complet exécutant deux scripts Python"
) as dag:

    # Tâche 1 : créer mlops db
    create_db_task = PythonOperator(
        task_id='run_create_db_task',
        python_callable=run_python_script,
        # chemin absolu dans le container
        op_args=["/opt/airflow/scripts/create_mlops_db.py"],
    )

    # Tâche 2 : créer plants table
    create_table_task = PythonOperator(
        task_id='run_create_table_task',
        python_callable=run_python_script,
        # chemin absolu dans le container
        op_args=["/opt/airflow/scripts/create_plants_table.py"],
    )

    # Tâche 3 : insérer les métadonnées
    insert_metadata_task = PythonOperator(
        task_id='run_insert_metadata',
        python_callable=run_python_script,
        # chemin absolu dans le container
        op_args=["/opt/airflow/scripts/insert_metadata.py"],
    )

    # Tâche 4 : télécharger / uploader les images
    download_upload_pictures_task = PythonOperator(
        task_id='run_download_and_upload_pictures',
        python_callable=run_python_script,
        op_args=["/opt/airflow/scripts/download_and_upload_pictures.py"],
    )

    # Orchestration : d'abord insérer les métadonnées, puis traiter les images
    create_db_task >> create_table_task >> insert_metadata_task >> download_upload_pictures_task
