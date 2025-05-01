"""
Flight Simulation App

Main entry point for the flight simulation application. Sets up the Streamlit UI, handles user inputs,
and orchestrates the simulation and display of results.
"""

import streamlit as st
import pandas as pd

from aircraft_config import AIRCRAFT_CONFIG
from utils import load_airports
from simulation import run_simulation, haversine_with_bearing, calculate_range_rings
from display import display_simulation_results


# --- Streamlit UI ---
st.title("Flight Simulation App")
st.markdown("""
This app simulates a flight between two airports using a specified aircraft model.
It calculates flight parameters such as altitude, speed, thrust, and drag over time,
and visualizes the flight profile with charts and range rings.
""")

# Initialize session state for weight configuration
if 'weight_option_prev' not in st.session_state:
    st.session_state['weight_option_prev'] = None

# Load airports data
airports_df = load_airports()
airport_ids = airports_df["ident"].tolist()

# Airport selection
col1, col2 = st.columns(2)
with col1:
    departure_airport = st.selectbox(
        "Departure Airport",
        airport_ids,
        index=airport_ids.index("KSZT") if "KSZT" in airport_ids else 0,
    )
with col2:
    arrival_airport = st.selectbox(
        "Arrival Airport",
        airport_ids,
        index=airport_ids.index("KSJT") if "KSJT" in airport_ids else 1,
    )

# Aircraft model selection
aircraft_types = ["CJ", "CJ1", "CJ1+", "M2", "CJ2", "CJ2+", "CJ3", "CJ3+"]
aircraft_model = st.selectbox(
    "Aircraft Model",
    aircraft_types,
    index=aircraft_types.index("CJ1") if "CJ1" in aircraft_types else 0,
)

# Wing type selection
mods_available = [m for (a, m) in AIRCRAFT_CONFIG if a == aircraft_model]
if not mods_available:
    st.error(f"No modifications available for aircraft model {aircraft_model}.")
    st.stop()
st.write(f"Available wing types for {aircraft_model}: {mods_available}")
wing_type = st.radio(
    "Wing Type",
    ["Flatwing", "Tamarack", "Comparison between Flatwing and Tamarack"],
    index=0
)
if wing_type != "Comparison between Flatwing and Tamarack" and wing_type not in mods_available:
    st.error(f"Wing type '{wing_type}' is not available for aircraft model {aircraft_model}. Available options: {mods_available}")
    st.stop()

# Sidebar for aircraft images (now that aircraft_model is defined)
with st.sidebar:
    st.header("Aircraft Models")
    image_path_flatwing = f"images/flatwing_{aircraft_model}.jpg"
    try:
        st.image(image_path_flatwing, caption=f"Flatwing {aircraft_model}", use_container_width=True)
    except FileNotFoundError:
        st.warning(f"Image not found: {image_path_flatwing}")
    image_path_tamarack = f"images/tamarack_{aircraft_model}.jpg"
    try:
        st.image(image_path_tamarack, caption=f"Tamarack {aircraft_model}", use_container_width=True)
    except FileNotFoundError:
        st.warning(f"Image not found: {image_path_tamarack}")

# Load aircraft config to use for max fuel/payload calculations (use Tamarack as default for config)
config = AIRCRAFT_CONFIG.get((aircraft_model, "Tamarack" if "Tamarack" in mods_available else "Flatwing"))
if config:
    _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, bow, mzfw, mrw, mtow, max_fuel, taxi_fuel_default, reserve_fuel_default, _, _, _, _, _, _, _, _, _, _ = config
    max_payload = mzfw - bow

# Taxi fuel input (moved higher to be available for weight configuration)
taxi_fuel = int(st.number_input(
    "Taxi Fuel (lb)",
    min_value=0.0,
    value=float(taxi_fuel_default),
    step=10.0,
    key="taxi_fuel_input"
))

# Radio button for takeoff flaps
flap_option = st.radio(
    "Takeoff Flaps",
    ["Flap 0", "Flaps 15"],
    index=0
)
takeoff_flap = 0 if flap_option == "Flap 0" else 1

# Radio button for weight configuration
weight_option = st.radio(
    "Weight Configuration",
    ["Manual Input", "Max Fuel (Fill Tanks, Adjust Payload to MRW)", "Max Payload (Fill Payload to MZFW, Adjust Fuel to MRW)"],
    index=0,
    key="weight_option"
)

# Radio button for winds and temps aloft source
winds_temps_source = st.radio(
    "Winds and Temps Aloft Source",
    ["Current Conditions", "Summer Average", "Winter Average"],
    index=0
)

# Compute initial payload and fuel values based on weight option
if weight_option == "Max Fuel (Fill Tanks, Adjust Payload to MRW)":
    initial_fuel = float(max_fuel)
    initial_payload = float(min(max_payload, mrw - (bow + max_fuel)))
    # Check TOW = (bow + payload + fuel) - taxi_fuel <= MTOW
    rw = bow + initial_payload + initial_fuel
    tow = rw - taxi_fuel
    if tow > mtow:
        # Reduce fuel to meet MTOW
        initial_fuel = mtow - (bow + initial_payload) + taxi_fuel
        if initial_fuel < 0:
            initial_fuel = 0
            initial_payload = mtow - bow + taxi_fuel
elif weight_option == "Max Payload (Fill Payload to MZFW, Adjust Fuel to MRW)":
    initial_payload = float(max_payload)
    initial_fuel = float(min(max_fuel, mrw - (bow + max_payload)))
    if initial_fuel == max_fuel:
        initial_payload = float(min(max_payload, mrw - (bow + max_fuel)))
    # Check TOW = (bow + payload + fuel) - taxi_fuel <= MTOW
    rw = bow + initial_payload + initial_fuel
    tow = rw - taxi_fuel
    if tow > mtow:
        # Reduce payload to meet MTOW
        initial_payload = mtow - (bow + initial_fuel) + taxi_fuel
        if initial_payload < 0:
            initial_payload = 0
            initial_fuel = mtow - bow + taxi_fuel
else:
    initial_payload = 0.0
    initial_fuel = 3440.0

# Initialize session state for payload and fuel on first run
if 'payload_input' not in st.session_state:
    st.session_state.payload_input = initial_payload
if 'fuel_input' not in st.session_state:
    st.session_state.fuel_input = initial_fuel

# Update session state when weight configuration changes
if st.session_state.weight_option_prev != weight_option:
    st.session_state.payload_input = initial_payload
    st.session_state.fuel_input = initial_fuel
    st.session_state.weight_option_prev = weight_option

# User input fields for payload, fuel, and reserve fuel
payload_input = int(st.number_input(
    "Payload (lb)",
    min_value=0.0,
    step=100.0,
    key="payload_input"
))
fuel_input = int(st.number_input(
    "Initial Fuel (lb)",
    min_value=0.0,
    step=100.0,
    key="fuel_input"
))
reserve_fuel = int(st.number_input(
    "Reserve Fuel (lb)",
    min_value=0.0,
    value=float(reserve_fuel_default),
    step=10.0,
    key="reserve_fuel_input"
))

cruise_altitude = st.number_input("Cruise Altitude (ft)", min_value=0, value=41000, step=1000)
isa_dev = int(st.number_input("ISA Deviation (C)", value=0.0, step=1.0))
v1_cut_enabled = st.checkbox("Enable V1 Cut Simulation (Single Engine)", value=False)

# --- Run Simulation ---
if st.button("Run Simulation 🚀"):
    dep_info = airports_df[airports_df["ident"] == departure_airport]
    arr_info = airports_df[airports_df["ident"] == arrival_airport]

    if dep_info.empty or arr_info.empty:
        st.error("Invalid airport code(s). Please check selection.")
        st.stop()

    dep_lat, dep_lon, elev_dep = dep_info.iloc[0][["latitude_deg", "longitude_deg", "elevation_ft"]]
    arr_lat, arr_lon, elev_arr = arr_info.iloc[0][["latitude_deg", "longitude_deg", "elevation_ft"]]

    config = AIRCRAFT_CONFIG.get((aircraft_model, "Tamarack" if "Tamarack" in mods_available else "Flatwing"))
    if not config:
        st.error("Invalid aircraft config!")
        st.stop()

    distance_nm, bearing_deg = haversine_with_bearing(dep_lat, dep_lon, arr_lat, arr_lon)

    # Initialize simulation results
    tamarack_data = pd.DataFrame()
    tamarack_results = {}
    flatwing_data = pd.DataFrame()
    flatwing_results = {}
    dep_latitude = dep_lat
    dep_longitude = dep_lon
    arr_latitude = arr_lat
    arr_longitude = arr_lon

    # Run simulation based on wing type selection
    if wing_type == "Comparison between Flatwing and Tamarack":
        # Run for both Tamarack and Flatwing
        if "Tamarack" in mods_available:
            tamarack_data, tamarack_results, dep_latitude, dep_longitude, arr_latitude, arr_longitude = run_simulation(
                departure_airport,
                arrival_airport,
                aircraft_model,
                "Tamarack",
                takeoff_flap,
                payload_input,
                fuel_input,
                taxi_fuel,
                reserve_fuel,
                cruise_altitude,
                winds_temps_source,
                v1_cut_enabled,
            )
        if "Flatwing" in mods_available:
            flatwing_data, flatwing_results, _, _, _, _ = run_simulation(
                departure_airport,
                arrival_airport,
                aircraft_model,
                "Flatwing",
                takeoff_flap,
                payload_input,
                fuel_input,
                taxi_fuel,
                reserve_fuel,
                cruise_altitude,
                winds_temps_source,
                v1_cut_enabled,
            )
    elif wing_type == "Tamarack":
        # Run only for Tamarack
        tamarack_data, tamarack_results, dep_latitude, dep_longitude, arr_latitude, arr_longitude = run_simulation(
            departure_airport,
            arrival_airport,
            aircraft_model,
            "Tamarack",
            takeoff_flap,
            payload_input,
            fuel_input,
            taxi_fuel,
            reserve_fuel,
            cruise_altitude,
            winds_temps_source,
            v1_cut_enabled,
        )
    elif wing_type == "Flatwing":
        # Run only for Flatwing
        flatwing_data, flatwing_results, dep_latitude, dep_longitude, arr_latitude, arr_longitude = run_simulation(
            departure_airport,
            arrival_airport,
            aircraft_model,
            "Flatwing",
            takeoff_flap,
            payload_input,
            fuel_input,
            taxi_fuel,
            reserve_fuel,
            cruise_altitude,
            winds_temps_source,
            v1_cut_enabled,
        )

    # Filter sim_data to stop at the end of segment 3 if V1 cut is enabled
    if v1_cut_enabled:
        if not tamarack_data.empty:
            end_segment_3_idx = tamarack_data[tamarack_data['Segment'] == 3].index[-1] if not tamarack_data[tamarack_data['Segment'] == 3].empty else 0
            tamarack_data = tamarack_data.iloc[:end_segment_3_idx + 1]
        if not flatwing_data.empty:
            end_segment_3_idx = flatwing_data[flatwing_data['Segment'] == 3].index[-1] if not flatwing_data[flatwing_data['Segment'] == 3].empty else 0
            flatwing_data = flatwing_data.iloc[:end_segment_3_idx + 1]

    # Display the results
    display_simulation_results(
        tamarack_data,
        tamarack_results,
        flatwing_data,
        flatwing_results,
        v1_cut_enabled,
        dep_latitude,
        dep_longitude,
        arr_latitude,
        arr_longitude,
        distance_nm,
        bearing_deg,
        winds_temps_source,
        cruise_altitude,
        departure_airport,
        arrival_airport,
        calculate_range_rings
    )