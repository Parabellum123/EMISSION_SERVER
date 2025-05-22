from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.template.loader import render_to_string
from emissionproject.scripts.calculations import run_scripts
from emissionproject.scripts.calculateselect import run_filter
import subprocess
import os
import psycopg2

def home(request):
    return render(request, 'base.html')

def run_calculation(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

  # 🔹 1. Jalankan Scraper sebelum kalkulasi
    try:
        scraper_script = os.path.join(os.path.dirname(__file__), '../baltic_scraper/baltic_scraper/spiders/vessel.py')
        subprocess.run(["python", scraper_script], check=True)
        print("Scraping selesai sebelum kalkulasi.")
    except Exception as e:
        print(f"Error menjalankan scraper: {e}")


    # Run the calculations and get the AIS data count
    ais_data_count = run_scripts(start_date_str, end_date_str)

    # Fetch the results from the database
    results = fetch_results_from_db(start_date_str, end_date_str)

    # Fetch the emission output data sorted by start_timestamp
    emission_output_data = fetch_emission_output_data()

    # Fetch the total daily emissions data for the charts
    total_daily_data = fetch_total_daily_data()

    # Fetch the candlestick data
    candlestick_data = fetch_candlestick_data()

    # Count unique MMSI values from emission_output7 table
    unique_mmsi_count = count_unique_mmsi()

    # Log the unique MMSI count
    print(f"Unique MMSI Count (in run_calculation): {unique_mmsi_count}")

    # Fetch the total emissions data from the total_emission table
    total_emissions = fetch_total_emissions()

    total_sum = sum(total_emissions.values())
    emission_percentages = {emission: (value / total_sum) * 100 for emission, value in total_emissions.items()}

    # Prepare data for charts
    exampleDates = [entry['date'] for entry in total_daily_data]
    co2_data = [entry['total_CO2'] for entry in total_daily_data]
    nox_data = [entry['total_NOX'] for entry in total_daily_data]
    co_data = [entry['total_CO'] for entry in total_daily_data]
    nmvoc_data = [entry['total_NMVOC'] for entry in total_daily_data]
    pm_data = [entry['total_PM'] for entry in total_daily_data]
    so2_data = [entry['total_SO2'] for entry in total_daily_data]

    co2_avg = sum(co2_data) / len(co2_data) if co2_data else 0
    nox_avg = sum(nox_data) / len(nox_data) if nox_data else 0
    co_avg = sum(co_data) / len(co_data) if co_data else 0
    nmvoc_avg = sum(nmvoc_data) / len(nmvoc_data) if nmvoc_data else 0
    pm_avg = sum(pm_data) / len(pm_data) if pm_data else 0
    so2_avg = sum(so2_data) / len(so2_data) if so2_data else 0

    # Fetch unique MMSI options
    mmsi_options = fetch_unique_mmsi_options()

    # Render partial templates with fetched data
    total_emissions_html = render_to_string('partials/total_emissions.html', {'results': results})
    emission_table_html = render_to_string('partials/emission_table.html', {'results': emission_output_data})
    selected_mmsi_table_html = render_to_string('partials/selected_mmsi_table.html', {'results': results})
    mmsi_options_html = render_to_string('partials/mmsi_options.html', {'mmsi_options': mmsi_options})

    return JsonResponse({
        'total_emissions_html': total_emissions_html,
        'emission_table_html': emission_table_html,
        'selected_mmsi_table_html': selected_mmsi_table_html,
        'mmsi_options_html': mmsi_options_html,
        'data_count': len(results),  # Include the data count in the response
        'ais_data_count': ais_data_count,  # Include AIS data count in the response
        'unique_mmsi_count': unique_mmsi_count,  # Include unique MMSI count in the response
        'co2_data': co2_data,
        'co2_avg': co2_avg,
        'nox_data': nox_data,
        'nox_avg': nox_avg,
        'co_data': co_data,
        'co_avg': co_avg,
        'nmvoc_data': nmvoc_data,
        'nmvoc_avg': nmvoc_avg,
        'pm_data': pm_data,
        'pm_avg': pm_avg,
        'so2_data': so2_data,
        'so2_avg': so2_avg,
        'exampleDates': exampleDates,  # Include dates for chart labels
        'total_co2': total_emissions.get('CO2', 0),
        'total_nox': total_emissions.get('NOX', 0),
        'total_co': total_emissions.get('CO', 0),
        'total_nmvoc': total_emissions.get('NMVOC', 0),
        'total_pm': total_emissions.get('PM', 0),
        'total_so2': total_emissions.get('SO2', 0),
        'emission_percentages': emission_percentages,  # Add percentages to response
        'candlestick_data': candlestick_data  # Add candlestick data to the response
    })

@require_GET
def fetch_points_data(request):
    mmsi = request.GET.get('mmsi')
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    if mmsi and mmsi != 'all':
        query = """
        SELECT mmsi, vessel_type, start_timestamp, start_latitude, start_longitude,
               CO2, NOX, CO, NMVOC, PM, SO2
        FROM emission_output7
        WHERE mmsi = %s
        ORDER BY start_timestamp ASC
        """
        cursor.execute(query, (mmsi,))
    else:
        query = """
        SELECT mmsi, vessel_type, start_timestamp, start_latitude, start_longitude,
               CO2, NOX, CO, NMVOC, PM, SO2
        FROM emission_output7
        ORDER BY start_timestamp ASC
        """
        cursor.execute(query)

    points = cursor.fetchall()

    # Fetch unique MMSI options
    mmsi_options = fetch_unique_mmsi_options()

    cursor.close()
    conn.close()

    return JsonResponse({
        'points': points,
        'mmsi_options': mmsi_options
    })

@require_GET
def filter_mmsi(request):
    mmsi = request.GET.get('mmsi')
    if mmsi:
        # Change the working directory to the one containing the script
        script_dir = os.path.join(os.path.dirname(__file__), '../scripts')
        subprocess.run(["python", os.path.join(script_dir, "calculateselect.py"), mmsi], check=True)

        # Fetch ship data
        ship_data = fetch_ship_data(mmsi)
        
        # Fetch MMSI emission data
        mmsi_emission_data = fetch_mmsi_emission_data()

        # Fetch total emissions for the selected MMSI
        mmsi_total_emissions = fetch_mmsi_total_emissions()

        # Fetch daily emissions for the selected MMSI
        mmsi_daily_emissions = fetch_mmsi_daily_emissions(mmsi)

        # Calculate average emissions for the selected MMSI
        mmsi_average_emissions = calculate_mmsi_average_emissions(mmsi)

        # Render the MMSI emission data table
        mmsi_emission_table_html = render_to_string('partials/mmsi_emission_table.html', {'results': mmsi_emission_data})
        

        return JsonResponse({
            'ship_data': ship_data,
            'mmsi_emission_table_html': mmsi_emission_table_html,
            'mmsi_total_emissions': mmsi_total_emissions,
            'mmsi_daily_emissions': mmsi_daily_emissions,
            'mmsi_average_emissions': mmsi_average_emissions  # Include average emissions in the response
        })
    else:
        return JsonResponse({'error': 'MMSI not provided'}, status=400)

def fetch_ship_data(mmsi):
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    try:
        # First, try to get the data where length is greater than width
        query = """
        SELECT mmsi, name, imo, vessel_type, length, width
        FROM tanker_20
        WHERE mmsi = %s AND length > width
        GROUP BY mmsi, name, imo, vessel_type, length, width
        LIMIT 1
        """
        cursor.execute(query, (mmsi,))
        result = cursor.fetchone()

        # If no such data is found, fallback to any available data
        if not result:
            query = """
            SELECT mmsi, name, imo, vessel_type, length, width
            FROM tanker_20
            WHERE mmsi = %s
            GROUP BY mmsi, name, imo, vessel_type, length, width
            LIMIT 1
            """
            cursor.execute(query, (mmsi,))
            result = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    return result if result else {}

def fetch_mmsi_emission_data():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT mmsi, 
           TO_CHAR(start_timestamp, 'YYYY-MM-DD HH24:MI:SS') as start_timestamp, 
           TO_CHAR(end_timestamp, 'YYYY-MM-DD HH24:MI:SS') as end_timestamp, 
           start_latitude, start_longitude, CO2, NOX, CO, NMVOC, PM, SO2
    FROM select_emission
    ORDER BY start_timestamp ASC
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

def fetch_mmsi_total_emissions():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT emission_type, mmsi_total
    FROM select_total
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

def fetch_unique_mmsi_options():
    conn = psycopg2.connect(
    dbname="emissionprojectdb",
    user="postgres",
    password="Achmadriadi@123",
    host="156.67.216.241",
    port="5432"
)


    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT DISTINCT mmsi
    FROM emission_output7
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

def count_unique_mmsi():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )
    cursor = conn.cursor()

    query = """
    SELECT COUNT(DISTINCT mmsi) as unique_mmsi_count
    FROM emission_output7
    """
    cursor.execute(query)
    result = cursor.fetchone()
    unique_mmsi_count = result[0] if result else 0

    cursor.close()
    conn.close()

    # Log the unique MMSI count
    print(f"Unique MMSI Count: {unique_mmsi_count}")

    return unique_mmsi_count

def fetch_results_from_db(start_date_str, end_date_str):
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT mmsi, vessel_type, start_timestamp, start_latitude, start_longitude,
           end_timestamp, CO2, NOX, CO, NMVOC, PM, SO2
    FROM emission_output7
    WHERE start_timestamp BETWEEN %s AND %s
    """
    cursor.execute(query, (start_date_str, end_date_str))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

def fetch_emission_output_data():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT mmsi, vessel_type, 
           TO_CHAR(start_timestamp, 'YYYY-MM-DD HH24:MI:SS') as start_timestamp, 
           TO_CHAR(end_timestamp, 'YYYY-MM-DD HH24:MI:SS') as end_timestamp, 
           CO2, NOX, CO, NMVOC, PM, SO2
    FROM emission_output7
    ORDER BY start_timestamp ASC
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

def fetch_total_daily_data():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT date, total_CO2, open_CO2, close_CO2, high_CO2, low_CO2,
           total_NOX, open_NOX, close_NOX, high_NOX, low_NOX,
           total_CO, open_CO, close_CO, high_CO, low_CO,
           total_NMVOC, open_NMVOC, close_NMVOC, high_NMVOC, low_NMVOC,
           total_PM, open_PM, close_PM, high_PM, low_PM,
           total_SO2, open_SO2, close_SO2, high_SO2, low_SO2
    FROM total_daily
    ORDER BY date ASC
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

def fetch_total_emissions():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT emission_type, total
    FROM total_emission
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    # Convert results to a dictionary
    total_emissions = {entry['emission_type']: entry['total'] for entry in results}

    return total_emissions

def fetch_mmsi_daily_emissions(mmsi):
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT date, mmsitotal_CO2, mmsitotal_NOX, mmsitotal_CO, mmsitotal_NMVOC, mmsitotal_PM, mmsitotal_SO2
    FROM select_daily
    WHERE mmsi = %s
    ORDER BY date ASC
    """
    cursor.execute(query, (mmsi,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results

def calculate_mmsi_average_emissions(mmsi):
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT 
        AVG(CO2) as avg_co2, 
        AVG(NOX) as avg_nox, 
        AVG(CO) as avg_co, 
        AVG(NMVOC) as avg_nmvoc, 
        AVG(PM) as avg_pm, 
        AVG(SO2) as avg_so2
    FROM select_emission
    WHERE mmsi = %s
    """
    cursor.execute(query, (mmsi,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result

def fetch_candlestick_data():
    conn = psycopg2.connect(
        dbname="emissionprojectdb",
        user="postgres",
        password="Achmadriadi@123",
        host="156.67.216.241",
        port="5432"
    )

    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT date, 
           total_CO2, open_CO2, close_CO2, high_CO2, low_CO2, 
           total_NOX, open_NOX, close_NOX, high_NOX, low_NOX, 
           total_CO, open_CO, close_CO, high_CO, low_CO, 
           total_NMVOC, open_NMVOC, close_NMVOC, high_NMVOC, low_NMVOC, 
           total_PM, open_PM, close_PM, high_PM, low_PM, 
           total_SO2, open_SO2, close_SO2, high_SO2, low_SO2
    FROM total_daily
    ORDER BY date ASC
    """
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results