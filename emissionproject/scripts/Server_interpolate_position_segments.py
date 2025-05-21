import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from math import cos, sin, radians
from datetime import timedelta
import psycopg2

# Koneksi ke PostgreSQL server
def connect_to_db():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )
    return conn, conn.cursor()

def interpolate_positions_from_cleaned_segments():
    conn, cursor = connect_to_db()
    engine = create_engine("postgresql+psycopg2://postgres:Achmadriadi%40123@156.67.216.241:5432/emissionprojectdb")

    query = """
    SELECT * FROM cleaned_trajectory_segments
    WHERE interpolated = TRUE
    ORDER BY mmsi, start_time
    """
    df = pd.read_sql(query, con=engine)
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])

    output_rows = []

    for _, row in df.iterrows():
        mmsi = row['mmsi']
        lat_p = row['lat_start']
        lon_p = row['lon_start']
        lat_q = row['lat_end']
        lon_q = row['lon_end']
        course_p = row.get('course_p', 0)
        course_q = row.get('course_q', 0)
        speed_p = row['speed_avg']
        speed_q = row['speed_avg']
        t_p = row['start_time']
        t_q = row['end_time']

        if speed_p < 0.5 or speed_q < 0.5:
            continue

        delta_t = (t_q - t_p).total_seconds()
        if delta_t == 0:
            continue

        t_interp = t_p + timedelta(seconds=delta_t / 2)
        delta_tp = delta_t / 2
        delta_tq = delta_t / 2

        v_p = speed_p / 3600
        v_q = speed_q / 3600

        theta_p = radians(course_p)
        theta_q = radians(course_q)

        x_ip = lon_p + v_p * cos(theta_p) * delta_tp
        y_ip = lat_p + v_p * sin(theta_p) * delta_tp
        x_iq = lon_q - v_q * cos(theta_q) * delta_tq
        y_iq = lat_q - v_q * sin(theta_q) * delta_tq

        Wp = 1 - (delta_tp / delta_t)
        Wq = 1 - (delta_tq / delta_t)

        x_final = Wp * x_ip + Wq * x_iq
        y_final = Wp * y_ip + Wq * y_iq

        output_rows.append({
            'mmsi': mmsi,
            'mid_time': t_interp,
            'interp_lat': y_final,
            'interp_lon': x_final,
            'speed_p': speed_p,
            'speed_q': speed_q,
            'course_p': course_p,
            'course_q': course_q,
            'Wp': Wp,
            'Wq': Wq,
            'interpolated': True
        })

    result_df = pd.DataFrame(output_rows)
    result_df.to_sql("interpolated_positions", con=engine, if_exists="replace", index=False)
    print("Hasil interpolasi posisi berhasil disimpan ke tabel 'interpolated_positions' di server.")
    conn.close()

if __name__ == "__main__":
    interpolate_positions_from_cleaned_segments()
