# db_totaldaily.py
# scripts/db_totaldaily.py

import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote


load_dotenv('/root/emissionfolder/.env')

def main():
    user = os.getenv("POSTGRES_USER")
    raw_password = "Achmadriadi@123"
    password = quote(raw_password)
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("POSTGRES_DB")
    port = os.getenv("POSTGRES_PORT")

    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")

    # ✅ Pakai lowercase sesuai Spark output
    query = 'SELECT end_timestamp, "CO2", "NOX", "CO", "NMVOC", "PM", "SO2" FROM emission_output_final'
    df = pd.read_sql(query, engine)

    df['end_timestamp'] = pd.to_datetime(df['end_timestamp'])
    df['date'] = df['end_timestamp'].dt.date

    daily_emissions = df.groupby('date').agg({
        'CO2': ['sum', 'first', 'last', 'max', 'min'],
        'NOX': ['sum', 'first', 'last', 'max', 'min'],
        'CO': ['sum', 'first', 'last', 'max', 'min'],
        'NMVOC': ['sum', 'first', 'last', 'max', 'min'],
        'PM': ['sum', 'first', 'last', 'max', 'min'],
        'SO2': ['sum', 'first', 'last', 'max', 'min']
    }).reset_index()

    daily_emissions.columns = ['date', 
                               'total_CO2', 'open_CO2', 'close_CO2', 'high_CO2', 'low_CO2', 
                               'total_NOX', 'open_NOX', 'close_NOX', 'high_NOX', 'low_NOX', 
                               'total_CO', 'open_CO', 'close_CO', 'high_CO', 'low_CO', 
                               'total_NMVOC', 'open_NMVOC', 'close_NMVOC', 'high_NMVOC', 'low_NMVOC', 
                               'total_PM', 'open_PM', 'close_PM', 'high_PM', 'low_PM', 
                               'total_SO2', 'open_SO2', 'close_SO2', 'high_SO2', 'low_SO2']

    daily_emissions.to_sql('total_daily', engine, if_exists='replace', index=False)

    print("✅ Total daily emissions telah disimpan ke tabel 'total_daily'.")

if __name__ == "__main__":
    main()
