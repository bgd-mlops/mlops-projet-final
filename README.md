# Projet MLOps Classification

Ce dépôt contient un projet de classification d’images permettant de distinguer entre **dandelion** (pissenlit) et **grass** (herbe).

## Prérequis

- Docker et Docker Compose installés sur votre machine.

## Démarrage de l’infrastructure

1. Ouvrez un terminal et placez-vous dans le dossier du projet :

   ```bash
   cd infra/dev

2. Lancez l’infrastructure avec Docker Compose :

    ```bash
    docker-compose up -d --build

3. Démarrez la DAG "full_pipeline" dans Airflow

    Accédez aux différentes interfaces :
    - Interface Airflow : [http://localhost:8080](http://localhost:8080)
    - Web app de classification (Gradio) : [http://localhost:7860](http://localhost:7860)


### Aperçu de la webapp
![Aperçu de la webapp](images/image_webapp1.png)
![Aperçu de la webapp](images/image_webapp2.png)
### Aperçu de Airflow
![Aperçu de Airflow](images/airflow_dag.png)
### Aperçu de Mlflow
![Aperçu de Mlflow](images/image_mlflow.png)


