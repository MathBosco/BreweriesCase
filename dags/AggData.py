from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd

# Read data from Silver Layer
def ReadSilver():

    # Get actual date
    dt = datetime.now()

    # Format date
    format_dt = dt.strftime('%Y%m%d')

    # Read file with schema
    df = pd.read_parquet(f'datalake/silver/dt_process={format_dt}/')

    return df

# Aggregate Brewery by type
def GroupByType(ti):
    # Get output from input task
    df = ti.xcom_pull(task_ids = 'input')

    # Group by for count the brewery types
    vw_type = df.groupby('brewery_type')['id'].count().reset_index()

    # Rename Columns
    vw_type.columns = ['brewery_type', 'number']

    # Order Values
    vw_type = vw_type.sort_values(by='number', ascending=False)

    vw_type = AddDtProcess(vw_type)

    # Persist view on gold layer
    vw_type.to_parquet('datalake/gold/vwByType', partition_cols=['dt_process'], compression='gzip')

def GroupByLocation(ti):
    # Get output from input task
    df = ti.xcom_pull(task_ids = 'input')

    # Group by for count the brewery types
    vw_location = df.groupby(['country', 'state', 'city'])['id'].count().reset_index()

    # Rename Columns
    vw_location.columns = ['country', 'state', 'city', 'number']

    # Order Values
    vw_location = vw_location.sort_values(by='number', ascending=False)

    vw_location = AddDtProcess(vw_location)

    print(vw_location)

    # Persist view on gold layer
    vw_location.to_parquet('datalake/gold/vwByLocation', partition_cols=['dt_process'], compression='gzip')

# Function to add column 'Data processed'
def AddDtProcess(dataframe):
    df = dataframe

    # Get actual date
    dt = datetime.now()

    # Format date
    format_dt = dt.strftime('%Y%m%d')

    # Add colum data processed
    df = df.assign(dt_process=format_dt)

    return df

with DAG('dagAggregations', start_date= datetime(2024,4,15,6, 0, 0),  schedule_interval='@daily', catchup = False) as dag:

    # Read data
    input = PythonOperator(
        task_id = 'input',
        python_callable = ReadSilver
    )

    # Aggregate Brewery by type
    vwType = PythonOperator(
        task_id = 'vwType',
        python_callable = GroupByType
    )   

    # Aggregate Brewery by location
    vwCountry = PythonOperator(
        task_id = 'vwCountry',
        python_callable = GroupByLocation
    )   


    # Orchestration
    input >> [vwCountry,vwType]