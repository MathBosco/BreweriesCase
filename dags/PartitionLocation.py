from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
import pandas as pd
import logging

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

    # Read file with schema
    df = pd.read_json('datalake/bronze/20240417.json', dtype=schema)

    return df
   
# Transformations to improve the quality 
def TransformationDf(ti):

    # Get output from input task
    df = ti.xcom_pull(task_ids = 'input')

    # Get actual date
    dt = datetime.now()

    # Format date
    format_dt = dt.strftime('%Y%m%d')

    # Add colum data processed
    df = df.assign(dt_process=format_dt)

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
with DAG('dagPartition', start_date= datetime(2024,4,15),  schedule_interval = '30 * * * *', catchup = False) as dag:

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

    # Orchestration
    input >> transform >> output