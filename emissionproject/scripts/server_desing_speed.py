import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine

# Fungsi koneksi ke PostgreSQL
def connect_to_db():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )
    return conn

def main():
    try:
        conn = connect_to_db()
        print("Koneksi ke database berhasil")
    except Exception as e:
        print(f"Gagal terhubung ke database: {e}")
        return

    # --- Metode 1: Design speed dari MCR & DWT ---
    query1 = """
        SELECT DISTINCT m.mmsi, m.vessel_type, m.deadweight, p.mcr
        FROM emission_ready_segments_view m
        INNER JOIN output_mcr_and_aux_power p ON m.mmsi = p.mmsi
        WHERE m.deadweight IS NOT NULL AND p.mcr IS NOT NULL
    """
    df1 = pd.read_sql(query1, conn)

    vessel_type_map = {
        "Container ship": "Cargo",
        "Car carrier": "Cargo",
        "Bulk carrier": "Cargo",
        "Cement carrier": "Cargo",
        "General cargo vessel": "Cargo",
        "Oil tanker": "Tanker",
        "Chemical tanker": "Tanker",
        "Chemical/Oil tanker": "Tanker",
        "LPG carrier": "Tanker"
    }
    df1['vessel_type_ap'] = df1['vessel_type'].map(vessel_type_map)

    def calculate_design_speed(row):
        try:
            mcr = float(row['mcr'])
            dwt = float(row['deadweight'])
            vtype = row['vessel_type_ap']
            if pd.isnull(mcr) or pd.isnull(dwt) or dwt == 0:
                return None
            if vtype == "Tanker":
                return ((mcr / (2.66 * dwt**0.6)) ** (1 / 0.6))
            elif vtype == "Cargo":
                return ((mcr / (4.297 * dwt**0.6)) ** (1 / 0.4))
            else:
                return None
        except Exception as e:
            print(f"Error MMSI {row['mmsi']}: {e}")
            return None

    df1['design_speed_mcr'] = df1.apply(calculate_design_speed, axis=1)

    # --- Metode 2: Design speed dari 0.94 × max speed ---
    query2 = """
        SELECT mmsi, MAX(speed) AS max_speed
        FROM ais_vessel_pos
        WHERE speed IS NOT NULL
        GROUP BY mmsi
    """
    df2 = pd.read_sql(query2, conn)
    df2['design_speed_max'] = df2['max_speed'] / 0.94

    # Gabungkan kedua hasil berdasarkan mmsi
    df_final = pd.merge(df1[['mmsi', 'vessel_type_ap', 'design_speed_mcr']], df2[['mmsi', 'design_speed_max']], on='mmsi', how='outer')
    df_final['design_speed'] = df_final[['design_speed_mcr', 'design_speed_max']].max(axis=1)

    # Filter: hanya baris yang design_speed_mcr ≠ 0 dan design_speed_max ≠ 0
    df_final = df_final[
        (df_final['design_speed_mcr'].notnull()) & (df_final['design_speed_mcr'] != 0) &
        (df_final['design_speed_max'].notnull()) & (df_final['design_speed_max'] != 0)
    ]

    # Simpan ke PostgreSQL
    try:
        engine = create_engine("postgresql+psycopg2://postgres:Achmadriadi%40123@156.67.216.241:5432/emissionprojectdb")
        df_final.drop_duplicates(subset=['mmsi']).to_sql(
            'output_design_speed',
            con=engine,
            if_exists='replace',
            index=False
        )
        print("Design speed (dua metode) berhasil disimpan ke tabel 'output_design_speed'")
    except Exception as e:
        print(f"Gagal menyimpan ke PostgreSQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
