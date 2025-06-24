# /root/emissionfolder/emissionsite/urls.py
from django.contrib import admin
from django.urls import path
from personal import views
from personal.views import get_mmsi_count_by_ship_type
from personal.views import filter_results_by_ship_type



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('run_calculation/', views.run_calculation, name='run_calculation'),
    path('filter_mmsi/', views.filter_mmsi, name='filter_mmsi'),
    path('fetch_points_data/', views.fetch_points_data, name='fetch_points_data'),
    path('update_vessel/', views.update_vessel, name='update_vessel'),  # ✅ Tambahkan ini
    path('get_mmsi_count/', get_mmsi_count_by_ship_type, name='get_mmsi_count_by_ship_type'),
    path('filter_by_ship_type/', filter_results_by_ship_type, name='filter_results_by_ship_type'),
    path('flag-statistics/', views.flag_statistics, name='flag_statistics')
]

