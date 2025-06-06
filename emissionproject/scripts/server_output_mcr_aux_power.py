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
        FROM emission_ready_segments_view
    """)
    vessel_data = cursor.fetchall()

    cursor.close()
    conn.close()

    # Konversi ke DataFrame
    df = pd.DataFrame(vessel_data, columns=['mmsi', 'vessel_type', 'length', 'breadth', 'engine_power'])

    # Mapping vessel type ke kategori utama
    vessel_type_map = {
        "Container ship": "Cargo",
        "Car carrier": "Cargo",
        "Bulk carrier": "Cargo",
        "Cement carrier": "Cargo",
        "General cargo vessel": "Cargo",
        "Oil tanker": "Tanker",
        "Chemical tanker": "Tanker",
        "Chemical/Oil tanker": "Tanker",
        "LPG carrier": "Tanker",
        "Passenger vessel": "Passenger",
        "RO-RO": "Passenger",
        "Tug boat": "Rest",
        "Crew boat": "Rest",
        "Offshore supply vessel": "Rest",
        "Other": "Rest",
        "Barge": "Rest"
    }

    # Buat kolom kategori utama
    df['vessel_main_type'] = df['vessel_type'].map(vessel_type_map).fillna("Rest")

    # Filter hanya Cargo dan Tanker
    df_filtered = df[df['vessel_main_type'].isin(['Cargo', 'Tanker'])].copy()

    # Fungsi perhitungan MCR & Aux Power
    def calculate_mcr_and_aux_power(engine_power, vessel_type_main, length, breadth):
        if not length or not breadth:
            return (None, None)

        lw = length * breadth

        # Validasi batasan berdasarkan scatter
        if vessel_type_main == "Cargo" and (lw < 500 or lw > 12000):
            return (None, None)
        if vessel_type_main == "Tanker" and (lw < 300 or lw > 2500):
            return (None, None)


        if vessel_type_main == "Tanker":
            mcr = 3.32e-4 * (lw)**2 + 0.27 * lw + 57.20
        elif vessel_type_main == "Cargo":
            mcr = 7.52e-5 * (lw)**2 + 0.59 * lw - 41.48
        else:
            return (None, None)

        ratio = next((r[1] for r in ratio_data if r[0] == vessel_type_main), 0.22)
        aux_power = mcr * ratio
        return (round(mcr, 2), round(aux_power, 2))

    # Terapkan fungsi ke setiap baris
    df_filtered[['mcr', 'auxiliary_engine_power']] = df_filtered.apply(
        lambda row: pd.Series(calculate_mcr_and_aux_power(
            row['engine_power'],
            row['vessel_main_type'],
            row['length'],
            row['breadth']
        )), axis=1
    )

    # Simpan ke PostgreSQL
    try:
        engine = create_engine("postgresql+psycopg2://postgres:Achmadriadi%40123@156.67.216.241:5432/emissionprojectdb")
        df_filtered[['mmsi', 'vessel_type', 'mcr', 'auxiliary_engine_power']].to_sql(
            'output_mcr_and_aux_power', con=engine, if_exists='replace', index=False
        )
        print("✅ Data MCR dan Auxiliary Power berhasil disimpan ke PostgreSQL (tanpa Passenger dan Rest).")
    except Exception as e:
        print(f"❌ Gagal menyimpan ke PostgreSQL: {e}")

if __name__ == "__main__":
    main()
