import pandas as pd
from sqlalchemy import create_engine

def main():
    user = "postgres"
    password = "Achmadriadi%40123"
    host = "156.67.216.241"
    database = "emissionprojectdb"
    port = "5432"

    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")

    # ✅ Perhatikan kutip ganda untuk kolom huruf kapital
    query = 'SELECT "end_time", "CO2", "NOX", "CO", "NMVOC", "PM", "SO2" FROM emission_output_final'
    df = pd.read_sql(query, engine)

    # Konversi end_time ke datetime (bukan end_timestamp)
    df['end_time'] = pd.to_datetime(df['end_time'])

    # Grup per tanggal dan hitung statistik harian
    daily_emissions = df.groupby(df['end_time'].dt.date).agg({
        'CO2': ['sum', 'first', 'last', 'max', 'min'],
        'NOX': ['sum', 'first', 'last', 'max', 'min'],
        'CO': ['sum', 'first', 'last', 'max', 'min'],
        'NMVOC': ['sum', 'first', 'last', 'max', 'min'],
        'PM': ['sum', 'first', 'last', 'max', 'min'],
        'SO2': ['sum', 'first', 'last', 'max', 'min']
    }).reset_index()

    # Flatten kolom hasil agregasi
    daily_emissions.columns = ['date', 
                               'total_CO2', 'open_CO2', 'close_CO2', 'high_CO2', 'low_CO2', 
                               'total_NOX', 'open_NOX', 'close_NOX', 'high_NOX', 'low_NOX', 
                               'total_CO', 'open_CO', 'close_CO', 'high_CO', 'low_CO', 
                               'total_NMVOC', 'open_NMVOC', 'close_NMVOC', 'high_NMVOC', 'low_NMVOC', 
                               'total_PM', 'open_PM', 'close_PM', 'high_PM', 'low_PM', 
                               'total_SO2', 'open_SO2', 'close_SO2', 'high_SO2', 'low_SO2']

    # Simpan ke tabel total_daily
    daily_emissions.to_sql('total_daily', engine, if_exists='replace', index=False)

    print("✅ Total daily emissions telah disimpan ke tabel 'total_daily'.")

if __name__ == "__main__":
    main()
