from celery import shared_task
import subprocess

@shared_task
def run_scraping():
    """Menjalankan script scraping vessel.py"""
    try:
        subprocess.run(
            ["python", "src/baltic_scraper/baltic_scraper/spiders/vessel.py"],
            check=True
        )
        return "Scraping berhasil dijalankan."
    except subprocess.CalledProcessError as e:
        return f"Scraping gagal dengan error: {str(e)}"

@shared_task
def run_emission_calculation(start_date, end_date):
    """Menjalankan script perhitungan emisi."""
    try:
        subprocess.run(
            ["python", "src/scripts/db_emission_calculation.py", start_date, end_date],
            check=True
        )
        return "Perhitungan emisi berhasil dijalankan."
    except subprocess.CalledProcessError as e:
        return f"Perhitungan emisi gagal dengan error: {str(e)}"
