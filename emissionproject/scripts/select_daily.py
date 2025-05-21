import pandas as pd
from sqlalchemy import create_engine

def main():
    user = "postgres"
    password = "Achmadriadi%40123"
    host = "156.67.216.241"
    database = "emissionprojectdb"
    port = "5432"

    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")

    df = pd.read_sql("SELECT * FROM select_emission", engine)

    df['end_timestamp'] = pd.to_datetime(df['end_timestamp'])

    daily_emissions = df.groupby([df['end_timestamp'].dt.date, 'mmsi']).agg({
        'CO2': 'sum',
        'NOX': 'sum',
        'CO': 'sum',
        'NMVOC': 'sum',
        'PM': 'sum',
        'SO2': 'sum'
    }).reset_index()

    daily_emissions.columns = ['date', 'mmsi', 'mmsitotal_CO2', 'mmsitotal_NOX', 'mmsitotal_CO', 'mmsitotal_NMVOC', 'mmsitotal_PM', 'mmsitotal_SO2']

    daily_emissions.to_sql('select_daily', engine, if_exists='replace', index=False)

    print("✅ Total selected daily emissions have been saved to 'select_daily'")

if __name__ == "__main__":
    main()
