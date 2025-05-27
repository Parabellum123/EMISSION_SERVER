import pandas as pd
from sqlalchemy import create_engine

def main():
    user = "postgres"
    password = "Achmadriadi@123"
    host = "156.67.216.241"
    database = "emissionprojectdb"
    port = "5432"

    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")

    # ✅ Pakai lowercase sesuai Spark output
    query = 'SELECT end_timestamp, co2, nox, co, nmvoc, pm, so2 FROM emission_output_final'
    df = pd.read_sql(query, engine)

    df['end_timestamp'] = pd.to_datetime(df['end_timestamp'])
    df['date'] = df['end_timestamp'].dt.date

    daily_emissions = df.groupby('date').agg({
        'co2': ['sum', 'first', 'last', 'max', 'min'],
        'nox': ['sum', 'first', 'last', 'max', 'min'],
        'co': ['sum', 'first', 'last', 'max', 'min'],
        'nmvoc': ['sum', 'first', 'last', 'max', 'min'],
        'pm': ['sum', 'first', 'last', 'max', 'min'],
        'so2': ['sum', 'first', 'last', 'max', 'min']
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
