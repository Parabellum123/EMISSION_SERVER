import pandas as pd
import time
import re
from math import ceil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine, text
from webdriver_manager.chrome import ChromeDriverManager

# Koneksi PostgreSQL Hostinger
DB_CONNECTION_STRING = "postgresql://postgres:Achmadriadi%40123@156.67.216.241:5432/emissionprojectdb"

def connect_to_database():
    engine = create_engine(
        DB_CONNECTION_STRING,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 15}
    )
    return engine

def get_new_vessels(engine):
    query = '''
        SELECT a.mmsi, a.imo
        FROM ais_vessel a
        WHERE a.imo IS NOT NULL AND a.imo != 0 AND a.mmsi IS NOT NULL;
    '''
    df = pd.read_sql(query, engine)
    if df.empty:
        print("Tidak ada data IMO untuk di-scrape.")
        return []
    return df.to_dict(orient="records")

def setup_webdriver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--remote-debugging-port=9222')

    service = Service("/usr/local/bin/chromedriver")  # Pastikan ini path chromedriver kamu

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def clean_text(text):
    numbers = [int(n) for n in re.findall(r'\d+', text.replace(',', ''))]
    return max(numbers) if numbers else 0

def scrape_vessel_data(vessel_list, driver):
    base_url = "https://www.balticshipping.com/vessel/imo/"
    scraped_data = []

    for vessel in vessel_list:
        imo = vessel["imo"]
        mmsi = vessel["mmsi"]

        if imo is None or imo == 0:
            print(f"IMO {imo} tidak valid, dilewati.")
            continue

        url = f"{base_url}{imo}"
        print(f"Scraping data untuk IMO {imo} dari {url}")

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

                print(f"URL Loaded: {driver.current_url}")

                if "Page not found" in driver.title:
                    print(f"Halaman tidak ditemukan untuk IMO {imo}, disimpan dengan DWT = 0.")
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
                print(f"Percobaan {attempt+1} gagal untuk IMO {imo}: {e}")

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

    return scraped_data

def save_to_database(data, engine):
    if not data:
        print("Tidak ada data untuk disimpan.")
        return

    df = pd.DataFrame(data)
    print(f"Menyimpan {len(df)} baris data ke database...")

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

        print("Batch berhasil disimpan (dengan update jika duplikat).")
    except Exception as e:
        print(f"Error saat menyimpan ke database: {e}")

def main():
    engine = connect_to_database()
    vessel_list = get_new_vessels(engine)

    if not vessel_list:
        print("Tidak ada data untuk di-scrape.")
        return

    batch_size = 20
    total_batches = ceil(len(vessel_list) / batch_size)

    print(f"Total kapal: {len(vessel_list)} — diproses dalam {total_batches} batch.\n")

    for i in range(total_batches):
        batch = vessel_list[i * batch_size : (i + 1) * batch_size]
        print(f"Batch {i+1}/{total_batches} — jumlah kapal: {len(batch)}")

        driver = setup_webdriver()

        try:
            scraped_data = scrape_vessel_data(batch, driver)
            print(f"Data yang berhasil di-scrape (batch {i+1}): {len(scraped_data)}")
            save_to_database(scraped_data, engine)
        finally:
            driver.quit()

        print("Istirahat 5 detik antar batch...\n")
        time.sleep(5)

if __name__ == "__main__":
    main()
