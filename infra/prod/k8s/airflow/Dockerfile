# 1. Base officielle
FROM apache/airflow:2.10.5

# 2. Switch to root pour copier et ajuster permissions
USER root
RUN mkdir -p /opt/airflow/dags /opt/airflow/scripts \
 && chown -R airflow: /opt/airflow/dags /opt/airflow/scripts

COPY ../../../dev/dags/    /opt/airflow/dags/
COPY ../../../dev/scripts/ /opt/airflow/scripts/

USER airflow
