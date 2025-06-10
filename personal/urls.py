#/root/emissionfolder/personal/urls.py
from django.urls import path
from emissionfolder.personal import check_status
from .views import run_calculation, update_vessel
from django.contrib import admin
from django.urls import path, include
from personal.views import get_mmsi_count_by_ship_type
from emissionfolder.personal import views
from personal.views import filter_results_by_ship_type



urlpatterns = [
    path('run_calculation/', run_calculation, name='run_calculation'),
    path('update_vessel/', update_vessel, name='update_vessel'),
    path('admin/', admin.site.urls),
    path('', include('personal.urls')),  # <- tambahkan ini kalau belum ada
    path('get_mmsi_count/', get_mmsi_count_by_ship_type, name='get_mmsi_count_by_ship_type'),
    path('filter_by_ship_type/', filter_results_by_ship_type, name='filter_results_by_ship_type'),
]

