# src/emissionsite/urls.py
from django.contrib import admin
from django.urls import path
from personal import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('run_calculation/', views.run_calculation, name='run_calculation'),
    path('filter_mmsi/', views.filter_mmsi, name='filter_mmsi'),
    path('fetch_points_data/', views.fetch_points_data, name='fetch_points_data'),
]
