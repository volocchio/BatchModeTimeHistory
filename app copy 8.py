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

# Load airports data
airports_df = load_airports()
airport_display_names = airports_df["display_name"].tolist()

# Aircraft model selection
aircraft_types = ["CJ", "CJ1", "CJ1+", "M2", "CJ2", "CJ2+", "CJ3", "CJ3+"]
aircraft_model = st.selectbox("Aircraft Model", aircraft_types, index=aircraft_types.index("CJ1") if "CJ1" in aircraft_types else 0, key="aircraft_model")

# Load aircraft config first
mods_available = [m for (a, m) in AIRCRAFT_CONFIG if a == aircraft_model]
if not mods_available:
    st.error(f"No modifications available for aircraft model {aircraft_model}.")
    st.stop()
def_config = "Tamarack" if "Tamarack" in mods_available else "Flatwing"
config = AIRCRAFT_CONFIG.get((aircraft_model, def_config))
if config:
    _, _, _, _, _, _, _, _, ceiling, _, _, _, _, _, _, _, _, _, bow, mzfw, mrw, mtow, max_fuel, taxi_fuel_default, reserve_fuel_default, _, _, _, _, _, _, _, _, _, _ = config
    max_payload = mzfw - bow

# Airport selection
col1, col2 = st.columns(2)
with col1:
    departure_airport = st.selectbox(
        "Departure Airport",
        airport_display_names,
        index=next((i for i, name in enumerate(airport_display_names) if "KSZT" in name), 0)
    )
with col2:
    arrival_airport = st.selectbox(
        "Arrival Airport",
        airport_display_names,
        index=next((i for i, name in enumerate(airport_display_names) if "KSAN" in name), 0)
    )

# Get airport codes from display names
dep_airport_code = airports_df[airports_df["display_name"] == departure_airport]["ident"].iloc[0]
arr_airport_code = airports_df[airports_df["display_name"] == arrival_airport]["ident"].iloc[0]

# Calculate and display range and bearing
dep_info = airports_df[airports_df["ident"] == dep_airport_code]
arr_info = airports_df[airports_df["ident"] == arr_airport_code]
if dep_info.empty or arr_info.empty:
    st.error("Invalid airport code(s). Please check selection.")
    st.stop()

dep_lat, dep_lon, elev_dep = dep_info.iloc[0][["latitude_deg", "longitude_deg", "elevation_ft"]]
arr_lat, arr_lon, elev_arr = arr_info.iloc[0][["latitude_deg", "longitude_deg", "elevation_ft"]]
distance_nm, bearing_deg = haversine_with_bearing(dep_lat, dep_lon, arr_lat, arr_lon)

# Display range and bearing
st.markdown("---")  # Add a horizontal line for separation
col1, col2 = st.columns(2)
with col1:
    st.metric("Distance", f"{distance_nm:.1f} NM")
with col2:
    st.metric("Bearing", f"{bearing_deg:.1f}°")

# Wing type selection
st.write(f"Available wing types for {aircraft_model}: {mods_available}")
wing_type = st.radio("Wing Type", ["Flatwing", "Tamarack", "Comparison between Flatwing and Tamarack"], index=0, key="wing_type")
if wing_type != "Comparison between Flatwing and Tamarack" and wing_type not in mods_available:
    st.error(f"Wing type '{wing_type}' is not available for aircraft model {aircraft_model}. Available options: {mods_available}")
    st.stop()

# Weight mode selection
weight_option = st.radio("Weight Configuration", [
    "Manual Input",
    "Max Fuel (Fill Tanks, Adjust Payload to MRW)",
    "Max Payload (Fill Payload to MZFW, Adjust Fuel to MRW)"
], index=0, key="weight_option")

# Compute defaults
if weight_option == "Max Fuel (Fill Tanks, Adjust Payload to MRW)":
    initial_fuel = float(max_fuel)
    initial_payload = float(min(max_payload, mrw - (bow + max_fuel)))
    rw = bow + initial_payload + initial_fuel
    tow = rw - taxi_fuel_default
    if tow > mtow:
        initial_fuel = mtow - (bow + initial_payload) + taxi_fuel_default
        if initial_fuel < 0:
            initial_fuel = 0
            initial_payload = mtow - bow + taxi_fuel_default
elif weight_option == "Max Payload (Fill Payload to MZFW, Adjust Fuel to MRW)":
    initial_payload = float(max_payload)
    initial_fuel = float(min(max_fuel, mrw - (bow + max_payload)))
    if initial_fuel == max_fuel:
        initial_payload = float(min(max_payload, mrw - (bow + max_fuel)))
    rw = bow + initial_payload + initial_fuel
    tow = rw - taxi_fuel_default
    if tow > mtow:
        initial_payload = mtow - (bow + initial_fuel) + taxi_fuel_default
        if initial_payload < 0:
            initial_payload = 0
            initial_fuel = mtow - bow + taxi_fuel_default
else:
    initial_payload = 0.0
    initial_fuel = 3440.0

# Prevent negative payloads
initial_payload = max(0, initial_payload)
initial_fuel = max(0, initial_fuel)

# Inputs
payload_input = st.number_input(
    "Payload (lb)",
    min_value=0,
    value=int(initial_payload),
    step=100,
    key="payload_input"
)

fuel_input = st.number_input(
    "Initial Fuel (lb)",
    min_value=0,
    value=int(initial_fuel),
    step=100,
    key="fuel_input"
)

reserve_fuel = st.number_input(
    "Reserve Fuel (lb)",
    min_value=0,
    value=int(reserve_fuel_default),
    step=10,
    key="reserve_fuel_input"
)

taxi_fuel = st.number_input(
    "Taxi Fuel (lb)",
    min_value=0,
    value=int(taxi_fuel_default),
    step=10
)

cruise_altitude = st.number_input(
    "Cruise Altitude (ft)",
    min_value=0,
    max_value=int(ceiling),
    value=int(ceiling),
    step=1000,
    key="cruise_altitude"
)

# Other settings
flap_option = st.radio("Takeoff Flaps", ["Flap 0", "Flaps 15"], index=0)
takeoff_flap = 0 if flap_option == "Flap 0" else 1
winds_temps_source = st.radio("Winds and Temps Aloft Source", ["Current Conditions", "Summer Average", "Winter Average"], index=0)
isa_dev = int(st.number_input("ISA Deviation (C)", value=0.0, step=1.0))
v1_cut_enabled = st.checkbox("Enable V1 Cut Simulation (Single Engine)", value=False)

# Sidebar for aircraft images
with st.sidebar:
    st.header("Aircraft Models")
    image_path_flatwing = f"images/flatwing_{aircraft_model}.jpg"
    image_path_tamarack = f"images/tamarack_{aircraft_model}.jpg"
    try:
        st.image(image_path_flatwing, caption=f"Flatwing {aircraft_model}", use_container_width=True)
    except FileNotFoundError:
        st.warning(f"Image not found: {image_path_flatwing}")
    try:
        st.image(image_path_tamarack, caption=f"Tamarack {aircraft_model}", use_container_width=True)
    except FileNotFoundError:
        st.warning(f"Image not found: {image_path_tamarack}")

if st.button("Run Simulation 🚀"):
    dep_info = airports_df[airports_df["ident"] == dep_airport_code]
    arr_info = airports_df[airports_df["ident"] == arr_airport_code]
    if dep_info.empty or arr_info.empty:
        st.error("Invalid airport code(s). Please check selection.")
        st.stop()

    dep_lat, dep_lon, elev_dep = dep_info.iloc[0][["latitude_deg", "longitude_deg", "elevation_ft"]]
    arr_lat, arr_lon, elev_arr = arr_info.iloc[0][["latitude_deg", "longitude_deg", "elevation_ft"]]
    config = AIRCRAFT_CONFIG.get((aircraft_model, def_config))
    if not config:
        st.error("Invalid aircraft config!")
        st.stop()

    tamarack_data = pd.DataFrame()
    tamarack_results = {}
    flatwing_data = pd.DataFrame()
    flatwing_results = {}

    if wing_type == "Comparison between Flatwing and Tamarack":
        if "Tamarack" in mods_available:
            tamarack_data, tamarack_results, dep_lat, dep_lon, arr_lat, arr_lon = run_simulation(
                dep_airport_code, arr_airport_code, aircraft_model, "Tamarack", takeoff_flap,
                payload_input, fuel_input, taxi_fuel, reserve_fuel, cruise_altitude,
                winds_temps_source, v1_cut_enabled)
        if "Flatwing" in mods_available:
            flatwing_data, flatwing_results, dep_lat, dep_lon, arr_lat, arr_lon = run_simulation(
                dep_airport_code, arr_airport_code, aircraft_model, "Flatwing", takeoff_flap,
                payload_input, fuel_input, taxi_fuel, reserve_fuel, cruise_altitude,
                winds_temps_source, v1_cut_enabled)
    elif wing_type == "Tamarack":
        tamarack_data, tamarack_results, dep_lat, dep_lon, arr_lat, arr_lon = run_simulation(
            dep_airport_code, arr_airport_code, aircraft_model, "Tamarack", takeoff_flap,
            payload_input, fuel_input, taxi_fuel, reserve_fuel, cruise_altitude,
            winds_temps_source, v1_cut_enabled)
    elif wing_type == "Flatwing":
        flatwing_data, flatwing_results, dep_lat, dep_lon, arr_lat, arr_lon = run_simulation(
            dep_airport_code, arr_airport_code, aircraft_model, "Flatwing", takeoff_flap,
            payload_input, fuel_input, taxi_fuel, reserve_fuel, cruise_altitude,
            winds_temps_source, v1_cut_enabled)

    if v1_cut_enabled:
        if not tamarack_data.empty:
            end_idx = tamarack_data[tamarack_data['Segment'] == 3].index[-1] if not tamarack_data[tamarack_data['Segment'] == 3].empty else 0
            tamarack_data = tamarack_data.iloc[:end_idx + 1]
        if not flatwing_data.empty:
            end_idx = flatwing_data[flatwing_data['Segment'] == 3].index[-1] if not flatwing_data[flatwing_data['Segment'] == 3].empty else 0
            flatwing_data = flatwing_data.iloc[:end_idx + 1]

    # Display the map first
    display_simulation_results(
        tamarack_data, tamarack_results,
        flatwing_data, flatwing_results,
        v1_cut_enabled,
        dep_lat, dep_lon, arr_lat, arr_lon,
        distance_nm, bearing_deg,
        winds_temps_source,
        cruise_altitude,
        dep_airport_code, arr_airport_code,
        calculate_range_rings,
        fuel_input
    )

    # Ensure V-speeds are not printed prematurely by run_simulation
    # (This is handled by moving V-speed display logic to display_simulation_results if needed)