import pandas as pd
from sqlalchemy import create_engine

def main():
    user = "postgres"
    password = "Achmadriadi%40123"
    host = "156.67.216.241"
    database = "emissionprojectdb"
    port = "5432"

    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")

    # ✅ Perbaikan kutip ganda
    query = 'SELECT "CO2", "NOX", "CO", "NMVOC", "PM", "SO2" FROM emission_output_final'
    df = pd.read_sql(query, engine)

    # Hitung total emisi
    total_emissions = df.sum().round(3).reset_index()
    total_emissions.columns = ['emission_type', 'total']

    # Simpan hasil ke tabel total_emission
    total_emissions.to_sql('total_emission', engine, if_exists='replace', index=False)

    print('✅ Total emissions calculated and exported successfully.')

if __name__ == "__main__":
    main()
