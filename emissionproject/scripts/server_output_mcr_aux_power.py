import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Koneksi PostgreSQL
def connect_to_db():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )
    return conn, conn.cursor()

def main():
    conn, cursor = connect_to_db()

    # Ambil rasio auxiliary/main power
    cursor.execute("SELECT * FROM auxiliary_to_main_power_ratio")
    ratio_data = cursor.fetchall()

    # Ambil data dari emission_ready_segments
    cursor.execute("""
        SELECT DISTINCT mmsi, vessel_type, length, breadth, engine_power
        FROM emission_ready_segments
    """)
    vessel_data = cursor.fetchall()

    cursor.close()
    conn.close()

    # Konversi ke DataFrame
    df = pd.DataFrame(vessel_data, columns=['mmsi', 'vessel_type', 'length', 'breadth', 'engine_power'])

    # Mapping vessel type ke kategori utama
    vessel_type_map = {
        "Container ship": "Container",
        "Car carrier": "Container",
        "Bulk carrier": "Container",
        "Cement carrier": "Container",
        "General cargo vessel": "Container",
        "Oil tanker": "Tanker",
        "Chemical tanker": "Tanker",
        "Chemical/Oil tanker": "Tanker",
        "LPG carrier": "Tanker",
        "Passenger vessel": "Passenger",
        "RO-RO": "Ro-ro",
        "Tug boat": "Rest",
        "Crew boat": "Rest",
        "Offshore supply vessel": "Rest",
        "Other": "Rest",
        "Barge": "Rest"
    }

    # Fungsi perhitungan
    def calculate_mcr_and_aux_power(engine_power, vessel_type_raw, length, breadth):
        vessel_type = vessel_type_map.get(vessel_type_raw, "Rest")

        # Jika power sudah ada dari scraping
        if engine_power and engine_power > 0:
            mcr = engine_power
        else:
            if not length or not breadth:
                return (None, None)

            lw = length * breadth

            if vessel_type == "Tanker":
                mcr = 3.32e-5 * (lw)**2 + 0.27 * lw + 57.20
            elif vessel_type == "Container":
                mcr = 7.52e-5 * (lw)**2 + 0.59 * lw - 41.48
            else:
                mcr = 2000  # default fallback

        ratio = next((r[1] for r in ratio_data if r[0] == vessel_type), 0.22)
        aux_power = mcr * ratio
        return (round(mcr, 2), round(aux_power, 2))

    # Terapkan fungsi ke setiap baris
    df[['mcr', 'auxiliary_engine_power']] = df.apply(
        lambda row: pd.Series(calculate_mcr_and_aux_power(
            row['engine_power'],
            row['vessel_type'],
            row['length'],
            row['breadth']
        )), axis=1
    )

    # Simpan ke PostgreSQL
    try:
        engine = create_engine("postgresql+psycopg2://postgres:Achmadriadi%40123@156.67.216.241:5432/emissionprojectdb")
        df[['mmsi', 'vessel_type', 'mcr', 'auxiliary_engine_power']].to_sql(
            'output_mcr_and_aux_power', con=engine, if_exists='replace', index=False
        )
        print("Data MCR dan Auxiliary Power berhasil disimpan ke PostgreSQL.")
    except Exception as e:
        print(f"Gagal menyimpan ke PostgreSQL: {e}")

if __name__ == "__main__":
    main()
