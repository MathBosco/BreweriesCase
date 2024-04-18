from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from datetime import datetime
import pandas as pd
import sys
import os

scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'dags')
sys.path.append(scripts_dir)

from Utils import *

# Read data from Bronze Layer
def ReadBronze():
    
    # Construct a custom schema
    schema = {
        "id": str,
        "name": str,
        "brewery_type": str,
        "address_1": str,
        "address_2": str,
        "address_3": str,
        "city": str,
        "state_province": str,
        "postal_code": str,
        "country": str,
        "longitude": str,
        "latitude": str,
        "phone": str,
        "website_url": str,
        "state": str,
        "street": str
    }

    # Get actual date
    dt = datetime.now()

    # Format date
    format_dt = dt.strftime('%Y%m%d')

    # Read file with schema
    df = pd.read_json(f'datalake/bronze/{format_dt}.json', dtype=schema)

    return df
   
# Transformations to improve the quality 
def TransformationDf(ti):

    # Get output from input task
    df = ti.xcom_pull(task_ids = 'input')

    df = AddDtProcess(df)

    # Remove blank spaces
    df['country'] = df['country'].str.replace(' ', '_')
    df['state'] = df['state'].str.replace(' ', '_')

    return df

# Persist df partitioned
def PersistData(ti):

    # Get output from transform task
    df = ti.xcom_pull(task_ids = 'transform')

    # Transformed to parquet and partitioned data
    df.to_parquet('datalake/silver', partition_cols=['dt_process','country', 'state', 'city'], compression='gzip')

# Dag Orchestration
with DAG(dag_id='dagPartition', start_date= datetime(2024,4,15,7, 0, 0),  schedule_interval='@daily',  catchup = False) as dag:

    # Read data
    input = PythonOperator(
        task_id = 'input',
        python_callable = ReadBronze
    )

    # Transformations
    transform = PythonOperator(
        task_id = 'transform',
        python_callable = TransformationDf
    )   

    # Persist transformed data
    output = PythonOperator(
        task_id = 'output',
        python_callable = PersistData
    )   

    triggerDag = TriggerDagRunOperator(
        task_id='triggerDag',
        trigger_dag_id='dagAggregations',
        dag=dag
    )

    # Orchestration
    input >> transform >> output >> triggerDag