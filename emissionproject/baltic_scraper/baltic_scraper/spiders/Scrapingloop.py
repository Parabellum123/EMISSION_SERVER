import pandas as pd
import time
import random
import re
from math import ceil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine, text

# Koneksi ke database
DB_CONNECTION_STRING = "postgresql://postgres:Achmadriadi%40123@156.67.216.241:5432/emissionprojectdb"

def connect_to_database():
    engine = create_engine(
        DB_CONNECTION_STRING,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 15}
    )
    return engine

# Fungsi ambil data dari scraping_pending
def get_pending_vessels(engine):
    query = '''
        SELECT imo, mmsi
        FROM scraping_pending
        WHERE imo IS NOT NULL AND imo != 0;
    '''
    df = pd.read_sql(query, engine)
    return df.to_dict(orient="records")

# Fungsi pengecekan apakah sudah pernah di-scrape
def already_scraped(imo, engine):
    query = text("SELECT 1 FROM scraping_data WHERE imo_number = :imo LIMIT 1")
    with engine.connect() as conn:
        result = conn.execute(query, {"imo": imo}).fetchone()
    return result is not None

# Setup Selenium Chrome Headless
def setup_webdriver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--window-size=1920,1080')
    service = Service("/usr/local/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

# Ekstrak angka dari string
def clean_text(text):
    numbers = [int(n) for n in re.findall(r'\d+', text.replace(',', ''))]
    return max(numbers) if numbers else 0

# Scraping
def scrape_vessel_data(vessel_list, driver, engine):
    base_url = "https://www.balticshipping.com/vessel/imo/"
    scraped_data = []

    for vessel in vessel_list:
        imo = vessel["imo"]
        mmsi = vessel["mmsi"]

        if already_scraped(imo, engine):
            print(f"⏩ IMO {imo} sudah pernah di-scrape. Lewati.")
            continue

        url = f"{base_url}{imo}"
        print(f"🌐 Scraping IMO {imo}: {url}")

        retries = 3
        vessel_name = "-"
        deadweight = 0
        engine_type = "-"
        engine_model = "-"
        engine_power = 0
        vessel_type = "-"
        length = 0
        breadth = 0

        for attempt in range(retries):
            try:
                driver.get(url)
                time.sleep(2)

                if "Page not found" in driver.title:
                    print(f"⚠️ Halaman tidak ditemukan untuk IMO {imo}, simpan dengan DWT = 0.")
                    break

                try:
                    vessel_name = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                    ).text.strip()
                except:
                    vessel_name = "-"

                try:
                    table_rows = driver.find_elements(By.XPATH, "//table[@class='table ship-info']//tr")
                    for row in table_rows:
                        header = row.find_element(By.TAG_NAME, "th").text.strip()
                        value = row.find_element(By.TAG_NAME, "td").text.strip()
                        if "Deadweight" in header:
                            deadweight = clean_text(value)
                        elif "Engine type" in header:
                            engine_type = value
                        elif "Engine model" in header:
                            engine_model = value
                        elif "Engine power" in header or "Engine output" in header:
                            engine_power = clean_text(value)
                        elif "Vessel type" in header:
                            vessel_type = value
                        elif "Length" in header:
                            length = clean_text(value)
                        elif "Breadth" in header:
                            breadth = clean_text(value)
                except:
                    pass
                break

            except Exception as e:
                print(f"❌ Gagal attempt {attempt+1} untuk IMO {imo}: {e}")

        scraped_data.append({
            "mmsi": mmsi,
            "imo_number": imo,
            "vessel_name": vessel_name,
            "deadweight": deadweight,
            "engine_type": engine_type,
            "engine_model": engine_model,
            "engine_power": engine_power,
            "vessel_type": vessel_type,
            "length": length,
            "breadth": breadth
        })

        delay = random.uniform(2, 5)
        print(f"🕒 Delay {delay:.1f} detik...")
        time.sleep(delay)

    return scraped_data

# Simpan hasil ke database
def save_to_database(data, engine):
    if not data:
        print("Tidak ada data baru untuk disimpan.")
        return

    df = pd.DataFrame(data)
    print(f"💾 Menyimpan {len(df)} data ke scraping_data...")

    df["length"] = pd.to_numeric(df["length"], errors="coerce").fillna(0)
    df["breadth"] = pd.to_numeric(df["breadth"], errors="coerce").fillna(0)

    try:
        with engine.begin() as conn:
            for _, row in df.iterrows():
                query = text("""
                    INSERT INTO scraping_data (
                        mmsi, imo_number, vessel_name, deadweight,
                        engine_type, engine_model, engine_power,
                        vessel_type, length, breadth
                    )
                    VALUES (
                        :mmsi, :imo_number, :vessel_name, :deadweight,
                        :engine_type, :engine_model, :engine_power,
                        :vessel_type, :length, :breadth
                    )
                    ON CONFLICT (imo_number) DO UPDATE SET
                        vessel_name = EXCLUDED.vessel_name,
                        deadweight = EXCLUDED.deadweight,
                        engine_type = EXCLUDED.engine_type,
                        engine_model = EXCLUDED.engine_model,
                        engine_power = EXCLUDED.engine_power,
                        vessel_type = EXCLUDED.vessel_type,
                        length = EXCLUDED.length,
                        breadth = EXCLUDED.breadth;
                """)
                conn.execute(query, row.to_dict())
        print("✅ Data berhasil disimpan.")
    except Exception as e:
        print(f"❌ Error saat menyimpan data: {e}")

# Main
def main():
    engine = connect_to_database()
    vessel_list = get_pending_vessels(engine)

    if not vessel_list:
        print("🔍 Tidak ada data IMO baru di scraping_pending.")
        return

    print(f"🚢 Total kapal dari pending: {len(vessel_list)}")

    driver = setup_webdriver()
    try:
        scraped_data = scrape_vessel_data(vessel_list, driver, engine)
        save_to_database(scraped_data, engine)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
