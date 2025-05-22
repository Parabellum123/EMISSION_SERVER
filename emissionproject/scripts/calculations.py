# scripts/calculations.py

from emissionproject.scripts import server_output_mcr_aux_power as db_MCR_Aux_power
from emissionproject.scripts import server_desing_speed as db_designspeed
from emissionproject.scripts import Server_INTERPOLATION_TRAJECTORY as db_sailing_times
from emissionproject.scripts import Server_interpolate_position_segments as db_sailing_speed
from emissionproject.scripts import Server_calculate_emissions as db_emission_calculation
from emissionproject.scripts import db_totaldaily
from emissionproject.scripts import db_totalemission
from datetime import datetime

def run_scripts(start_date_str, end_date_str):
    print("▶️ Running server_output_mcr_aux_power.py...")
    db_MCR_Aux_power.main()
    print("✅ MCR & Auxiliary Power completed.")

    print("▶️ Running server_desing_speed.py...")
    db_designspeed.main()
    print("✅ Design Speed completed.")

    print("▶️ Running Server_INTERPOLATION_TRAJECTORY.py...")
    db_sailing_times.process_and_clean_ais_data(start_date_str, end_date_str)
    print("✅ Cleaned Trajectory Segments completed.")
    
    print("▶️ Running Server_interpolate_position_segments.py...")
    db_sailing_speed.interpolate_positions_from_cleaned_segments()
    print("✅ Interpolated Positions completed.")
    
    print("▶️ Running Server_calculate_emissions.py...")
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    db_emission_calculation.calculate_emissions(start_date, end_date)
    print("✅ Emission Calculation completed.")
    
    print("▶️ Running db_totaldaily.py...")
    db_totaldaily.main()
    print("✅ Daily Totals completed.")

    print("▶️ Running db_totalemission.py...")
    db_totalemission.main()
    print("✅ Total Emission Summary completed.")
