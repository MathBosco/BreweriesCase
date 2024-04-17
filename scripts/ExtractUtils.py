from datetime import datetime
import pandas as pd
import requests

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

# Validate Data quality
def ValidateData(ti):
    df = ti.xcom_pull(task_ids = 'extractApi')

    size = len(df)

    print("Df Rows: " + str(size))

    # Verify the number of rows 
    if (size > 0):
        return 'persistData'
    return 'exceptionData'

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
