import pandas as pd
from datetime import datetime
from geopy.distance import geodesic
from sqlalchemy import create_engine
import psycopg2

def is_valid_coord(lat, lon):
    return -90 <= lat <= 90 and -180 <= lon <= 180

def connect_to_db():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )
    return conn, conn.cursor()

def process_and_clean_ais_data(start_date_str, end_date_str):
    conn, cursor = connect_to_db()
    engine = create_engine("postgresql+psycopg2://postgres:Achmadriadi%40123@156.67.216.241:5432/emissionprojectdb")

    query = f"""
    SELECT mmsi, received_at, lat, lon, speed, course
    FROM ais_vessel_pos
    WHERE lat IS NOT NULL AND lon IS NOT NULL AND speed IS NOT NULL
    AND received_at BETWEEN '{start_date_str}' AND '{end_date_str}'
    ORDER BY mmsi, received_at
    """
    df = pd.read_sql(query, engine)
    df['received_at'] = pd.to_datetime(df['received_at'])

    output_data = []

    for mmsi, group in df.groupby('mmsi'):
        group = group.sort_values('received_at').reset_index(drop=True)
        for i in range(len(group) - 1):
            p1, p2 = group.iloc[i], group.iloc[i + 1]
            time_diff = (p2['received_at'] - p1['received_at']).total_seconds() / 3600
            coord1, coord2 = (p1['lat'], p1['lon']), (p2['lat'], p2['lon'])

            if coord1 == coord2 or not (is_valid_coord(*coord1) and is_valid_coord(*coord2)):
                distance_nm = 0
                speed = 0
                movement_status = 'idle'
                interpolated = False
            else:
                distance_nm = geodesic(coord1, coord2).nautical
                speed = distance_nm / time_diff if time_diff > 0 else 0
                movement_status = 'moving'
                interpolated = speed >= 0.5

            output_data.append({
                'mmsi': mmsi,
                'start_time': p1['received_at'],
                'end_time': p2['received_at'],
                'lat_start': p1['lat'],
                'lon_start': p1['lon'],
                'lat_end': p2['lat'],
                'lon_end': p2['lon'],
                'speed_avg': round(speed, 3),
                'distance_nm': round(distance_nm, 4),
                'duration_hr': round(time_diff, 4),
                'movement_status': movement_status,
                'interpolated': interpolated
            })

    result_df = pd.DataFrame(output_data)

    if result_df.empty:
        print("Tidak ada data hasil yang bisa disimpan.")
    else:
        try:
            result_df.to_sql("cleaned_trajectory_segments", con=engine, if_exists='replace', index=False)
            print("Data berhasil disimpan ke tabel cleaned_trajectory_segments (di server).")
        except Exception as e:
            print(f"Gagal menyimpan ke PostgreSQL: {e}")

    conn.close()
