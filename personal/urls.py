from django.urls import path
from .views import run_calculation

urlpatterns = [
    path('run_calculation/', run_calculation, name='run_calculation'),
]
