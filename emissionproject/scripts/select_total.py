import pandas as pd
from sqlalchemy import create_engine

def main():
    # PostgreSQL database connection parameters
    db_user = 'postgres'
    db_password = 'Achmadriadi@123'
    db_host = '156.67.216.241'
    db_port = '5432'
    db_name = 'emissionprojectdb'

    # Create a connection to the PostgreSQL database
    engine = create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

    # Read the emission data from the database
    query = 'SELECT CO2, NOX, CO, NMVOC, PM, SO2 FROM select_emission'
    df = pd.read_sql(query, engine)

    # Calculate the total emission for each emission type
    total_emissions = df.sum().round(3).reset_index()

    # Rename columns to match the output table format
    total_emissions.columns = ['emission_type', 'mmsi_total']

    # Export the result to a new table in the same database
    total_emissions.to_sql('select_total', engine, if_exists='replace', index=False)

    print('Total selected emissions calculated and exported successfully.')

if __name__ == "__main__":
    main()
