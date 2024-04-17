from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from scripts.ExtractUtils import *

# Dag Orchestration
with DAG('dagExtract', start_date= datetime(2024,4,15),  schedule_interval = '30 * * * *', catchup = False) as dag:

    # Extract data from Brewery API
    extractApi = PythonOperator(
        task_id = 'extractApi',
        python_callable = ExtractApi
    )

    # Verify the data quality 
    validateData = BranchPythonOperator(
        task_id = 'validateData',
        python_callable = ValidateData
    )

    # Persist data on bronze layer 
    persistData = PythonOperator(
        task_id = 'persistData',
        python_callable = PersistData
    )

    # If the data quality's not good, shows a message
    exceptionData = BashOperator(
        task_id = 'exceptionData',
        bash_command = 'Error to extract blank dataframe'
    )

    # Orchestration
    extractApi >> validateData >> [persistData,exceptionData]