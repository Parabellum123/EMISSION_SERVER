import os
import sys
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, pow, lit, coalesce, to_timestamp

# 🔹 Konfigurasi PostgreSQL
DB_HOST = os.getenv("POSTGRES_HOST", "156.67.216.241")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Achmadriadi@123")
DB_NAME = os.getenv("POSTGRES_DB", "emissionprojectdb")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

# 🔹 Path ke PostgreSQL JDBC Driver (Pastikan path driver sudah sesuai)
POSTGRES_JAR_PATH = "/root/emissionfolder/myenv/jars/postgresql-42.7.5.jar"

# 🔹 URL JDBC untuk PostgreSQL
JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"
CONNECTION_PROPERTIES = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "driver": "org.postgresql.Driver"
}

# 🔹 Membuat Spark Session
def create_spark_session():
    return SparkSession.builder \
        .appName("ShipEmissionCalculator") \
        .config("spark.jars", POSTGRES_JAR_PATH) \
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
        .config("spark.hadoop.fs.file.impl.disable.cache", "true") \
        .getOrCreate()


# 🔹 Fungsi Perhitungan Emisi
def calculate_emissions(start_date, end_date):
    spark = create_spark_session()

    try:
        print(f"📦 Menghitung emisi dari {start_date} hingga {end_date}...")

        # 1️⃣ Load cleaned_trajectory_segments
        query_segment = f"""
        (SELECT * FROM cleaned_trajectory_segments
        WHERE start_time BETWEEN '{start_date}' AND '{end_date}') AS seg        """
        segments_df = spark.read.jdbc(url=JDBC_URL, table=query_segment, properties=CONNECTION_PROPERTIES)

        # 2️⃣ Load output_design_speed
        design_df = spark.read.jdbc(url=JDBC_URL, table="output_design_speed", properties=CONNECTION_PROPERTIES)

        # 3️⃣ Load output_mcr_and_aux_power
        power_df = spark.read.jdbc(url=JDBC_URL, table="output_mcr_and_aux_power", properties=CONNECTION_PROPERTIES)

        # 4️⃣ Load emission_factor_machine_type
        ef_df = spark.read.jdbc(url=JDBC_URL, table="emission_factor_machine_type", properties=CONNECTION_PROPERTIES)

        print("✅ Semua data berhasil dimuat dari PostgreSQL")

        # 5️⃣ Join semua data berdasarkan MMSI
        df = segments_df \
            .join(design_df, on="mmsi", how="left") \
            .join(power_df, on="mmsi", how="left") \
            .crossJoin(ef_df)

        # 6️⃣ Hitung load_ratio = AS / MS
        df = df.withColumn("load_ratio", col("speed_avg") / col("design_speed"))

        # 7️⃣ Hitung Emisi
        emissions = ["CO2", "NOX", "CO", "NMVOC", "PM", "SO2"]
        for gas in emissions:
            df = df.withColumn(gas,
                when(col("speed_avg") > 3,
                    (col("mcr") * pow(col("load_ratio"), 3) * col("duration_hr") * col(f"main_engine_emission_{gas}") +
                     col("auxiliary_engine_power") * col("duration_hr") * col(f"auxiliary_engine_emission_{gas}")))
                .otherwise(
                    col("auxiliary_engine_power") * col("duration_hr") * col(f"auxiliary_engine_emission_{gas}")
                )
            )

        # 8️⃣ Tangani Null
        for gas in emissions:
            df = df.withColumn(gas, coalesce(col(gas), lit(0)))

        # 9️⃣ Simpan ke PostgreSQL
        result = df.select(
            "mmsi", "vessel_type_ap", "start_time", "end_time",
            "lat_start", "lon_start", "lat_end", "lon_end",
            "speed_avg", "design_speed", "duration_hr", "load_ratio",
            "mcr", "auxiliary_engine_power", *emissions
        )

        result.write.jdbc(url=JDBC_URL, table="emission_output_final", mode="overwrite", properties=CONNECTION_PROPERTIES)
        print("✅ Emisi berhasil disimpan ke tabel 'emission_output_final'")

        print(f"✅ Total baris: {result.count()}")

    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
        sys.exit(1)
    finally:
        spark.stop()
        print("🔄 Spark session ditutup")

# 🔹 Eksekusi Program
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python calculate_emissions_postgres.py 'YYYY-MM-DD' 'YYYY-MM-DD'")
        sys.exit(1)

    start_date_str = sys.argv[1]
    end_date_str = sys.argv[2]

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        print("❌ Format tanggal harus 'YYYY-MM-DD'")
        sys.exit(1)

    calculate_emissions(start_date_str, end_date_str)
