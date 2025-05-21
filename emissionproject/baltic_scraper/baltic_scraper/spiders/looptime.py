import time
from datetime import datetime
from Scrapingloop import main  # fungsi main scraping kamu

# Atur waktu tunggu (dalam detik)
# 1 hari = 86400 detik
SCRAPE_INTERVAL = 259200    # bisa kamu ubah ke 43200 (12 jam), 432000 (5 hari), dll

def loop_scraper():
    while True:
        print(f"[{datetime.now()}] ⏳ Mulai scraping harian...")
        try:
            main()  # jalankan fungsi scraping kamu
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Gagal scraping: {e}")
        
        print(f"[{datetime.now()}] 💤 Tidur {SCRAPE_INTERVAL/3600:.1f} jam...\n")
        time.sleep(SCRAPE_INTERVAL)

if __name__ == "__main__":
    loop_scraper()
