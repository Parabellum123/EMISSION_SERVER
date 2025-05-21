import sys
import os

# Add the directory containing the scripts to sys.path
script_dir = os.path.dirname(__file__)
sys.path.append(script_dir)

import select_emission
import select_daily
import select_total

def run_filter(selected_mmsi):
    print("Running select_emission.py...")
    select_emission.main(selected_mmsi)
    print("select_emission.py completed.")

    print("Running select_daily.py...")
    select_daily.main()
    print("select_daily.py completed.")

    print("Running select_total.py...")
    select_total.main()
    print("select_total.py completed.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        selected_mmsi = sys.argv[1]
        run_filter(selected_mmsi)
    else:
        print("No MMSI provided.")
