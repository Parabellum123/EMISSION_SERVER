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
        cursor = conn.cursor()
        print("Koneksi ke database berhasil")
    except Exception as e:
        print(f"Gagal terhubung ke database: {e}")
        return

    # Ambil data dari emission_ready_segments + output_mcr_and_aux_power
    query = """
        SELECT DISTINCT m.mmsi, m.vessel_type, m.deadweight, p.mcr
        FROM emission_ready_segments m
        LEFT JOIN output_mcr_and_aux_power p ON m.mmsi = p.mmsi
        WHERE m.deadweight IS NOT NULL AND p.mcr IS NOT NULL
    """
    df = pd.read_sql(query, conn)

    if df.empty:
        print("Data kosong. Tidak ada yang bisa dihitung.")
        return

    # Mapping vessel_type mentah → kategori vessel_type_ap
    vessel_type_map = {
        "Container ship": "Container",
        "Car carrier": "Container",
        "Bulk carrier": "Container",
        "Cement carrier": "Container",
        "General cargo vessel": "Container",
        "Oil tanker": "Tanker",
        "Chemical tanker": "Tanker",
        "Chemical/Oil tanker": "Tanker",
        "LPG carrier": "Tanker"
    }

    df['vessel_type_ap'] = df['vessel_type'].map(vessel_type_map)

    # Fungsi menghitung design speed
    def calculate_design_speed(row):
        try:
            mcr = float(row['mcr'])
            dwt = float(row['deadweight'])
            vtype = row['vessel_type_ap']

            if pd.isnull(mcr) or pd.isnull(dwt) or dwt == 0:
                return None
            if vtype == "Tanker":
                return ((mcr / (2.66 * dwt**0.6)) ** (1 / 0.6))
            elif vtype == "Container":
                return ((mcr / (4.297 * dwt**0.6)) ** (1 / 0.4))
            else:
                return None
        except Exception as e:
            print(f"Error MMSI {row['mmsi']}: {e}")
            return None

    # Terapkan fungsi ke DataFrame
    df['design_speed'] = df.apply(calculate_design_speed, axis=1)

    # Filter hanya yang berhasil dihitung
    df = df[df['design_speed'].notnull()]

    # Simpan ke PostgreSQL
    try:
        engine = create_engine("postgresql+psycopg2://postgres:Achmadriadi%40123@156.67.216.241:5432/emissionprojectdb")
        df[['mmsi', 'vessel_type_ap', 'design_speed']].drop_duplicates(subset=['mmsi']).to_sql(
            'output_design_speed',
            con=engine,
            if_exists='replace',
            index=False
        )
        print("Design speed berhasil disimpan ke tabel 'output_design_speed'")
    except Exception as e:
        print(f"Gagal menyimpan ke PostgreSQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
