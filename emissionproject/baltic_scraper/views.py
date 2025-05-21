from django.shortcuts import render
from django.http import JsonResponse
from .tasks import run_scraping
from .models import VesselData  # Model database untuk menyimpan data kapal

def manual_scraping(request):
    """Menjalankan scraping secara manual dari Django"""
    task = run_scraping.delay()  # Menjalankan scraping sebagai background task
    return JsonResponse({"message": "Scraping dimulai!", "task_id": task.id})

def vessel_list(request):
    """Menampilkan daftar kapal yang sudah di-scrape"""
    vessels = VesselData.objects.filter(deadweight__gt=0)  # Hanya kapal dengan DWT valid
    return render(request, 'vessel_list.html', {'vessels': vessels})

def get_scraped_data(request):
    """Membaca data dari vessels_data.json dan mengembalikannya sebagai JSON"""
    import json
    from pathlib import Path

    json_file_path = Path("src/baltic_scraper/baltic_scraper/spiders/vessels_data.json")
    
    if not json_file_path.exists():
        return JsonResponse({"error": "Data belum tersedia"}, status=404)

    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return JsonResponse(data, safe=False)
