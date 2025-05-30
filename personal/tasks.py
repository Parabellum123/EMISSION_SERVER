# personal/tasks.py
from celery import shared_task
from emissionproject.scripts.calculations import run_scripts

@shared_task
def run_calculation_task(start_date, end_date):
    return run_scripts(start_date, end_date)
