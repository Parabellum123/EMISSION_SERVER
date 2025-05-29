from django.urls import path
from emissionfolder.personal import check_status
from .views import run_calculation, update_vessel
from django.contrib import admin
from django.urls import path, include



urlpatterns = [
    path('run_calculation/', run_calculation, name='run_calculation'),
    path('update_vessel/', update_vessel, name='update_vessel'),
    path('admin/', admin.site.urls),
    path('', include('personal.urls')),  # <- tambahkan ini kalau belum ada
]
