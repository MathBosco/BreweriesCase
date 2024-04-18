from datetime import datetime
import pandas as pd

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