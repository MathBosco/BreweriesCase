from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
import pandas as pd
import requests
import sys
import os

scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'dags')
sys.path.append(scripts_dir)

from Utils import AddDtProcess

# Extract data from Api
# Retun a df with the request data
def ExtractApi():

    # Url from API
    url = "https://api.openbrewerydb.org/breweries"

    print("Requesto to: " + url)

    # Request data 
    response = requests.get(url)

    # Convert Request to Json
    data = response.json()

    # Convert json to df
    df = pd.DataFrame.from_dict(data)
    
    return df

# Persist data on bronze layer
def PersistData(ti):
    df = ti.xcom_pull(task_ids = 'extractApi')

    # Get actual date
    dt = datetime.now()

    # format date
    format_dt = dt.strftime('%Y%m%d')

    # Build file name with actual date 
    fileName = str(format_dt) + ".json"

    path = "datalake/bronze/" + fileName

    print("Persisting Brewery... \n Path: " + path)

    # Persist df
    df.to_json(path, index=False)


# Dag Orchestration
with DAG('dagExtract', start_date= datetime(2024,4,15,6, 0, 0),  schedule_interval='@daily', catchup = False) as dag:

    # Extract data from Brewery API
    extractApi = PythonOperator(
        task_id = 'extractApi',
        python_callable = ExtractApi
    )

    
    # Persist data on bronze layer 
    persistData = PythonOperator(
        task_id = 'persistData',
        python_callable = PersistData
    )

    # Define a tarefa que desencadeará a execução da DAG d2
    triggerDag = TriggerDagRunOperator(
        task_id='triggerDag',
        trigger_dag_id='dagPartition',
        dag=dag
    )

    # Orchestration
    extractApi >> persistData >> triggerDag