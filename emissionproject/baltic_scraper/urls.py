from django.urls import path
from .views import manual_scraping

urlpatterns = [
    path('scrape/', manual_scraping, name='manual_scraping'),
]
