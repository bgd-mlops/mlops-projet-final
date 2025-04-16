# mlops_classification_project

# Lancer dockercompose 1ere fois
docker-compose up --build

# Lancer dockercompose ensuite
docker-compose up -d

# Stopper docker compose
docker-compose down

# Connexion à la bdd psql de airflow (dans un autre terminal)
docker exec -it mlops_classification_project-postgres-1 psql -U airflow -d airflow
--> CREATE DATABASE mlops_data;

# Connexion à la bdd psql de mlops_data = bdd métier : contient la table plants_data
docker exec -it mlops_classification_project-postgres-1 psql -U airflow -d mlops_data

docker exec -it mlops_classification_project-postgres-1 psql -U airflow -d mlops_data -f /tmp/create_plants_data.sql
--> exécute le script sql de création de la table

# Accéder à Airflow
curl http://localhost:8080

# Supprimer DB mlops_data
docker exec -it mlops_classification_project-postgres-1 psql -U airflow -d airflow
airflow=# DROP DATABASE mlops_data;