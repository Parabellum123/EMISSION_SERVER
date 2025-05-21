import pandas as pd
from sqlalchemy import create_engine
import sys

# PostgreSQL database connection parameters
db_user = 'postgres'
db_password = 'Achmadriadi@123'
db_host = '156.67.216.241'
db_port = '5432'
db_name = 'emissionprojectdb'

# Function to filter data based on selected MMSI
def filter_data(selected_mmsi):
    # Create database engine for PostgreSQL
    engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

    # Query to fetch data from 'emission_output_final' table
    query = """
        SELECT mmsi, start_timestamp, end_timestamp, start_latitude, start_longitude, 
               CO2, NOX, CO, NMVOC, PM, SO2 
        FROM emission_output_final
    """

    # Load data into a pandas DataFrame
    df = pd.read_sql(query, engine)

    # Filter data based on the selected MMSI
    filtered_df = df[df['mmsi'] == int(selected_mmsi)]

    # Write the filtered DataFrame to the 'select_emission' table
    filtered_df.to_sql('select_emission', con=engine, if_exists='replace', index=False)

def main(selected_mmsi):
    filter_data(selected_mmsi)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        selected_mmsi = sys.argv[1]
        main(selected_mmsi)
    else:
        print("No MMSI provided.")
