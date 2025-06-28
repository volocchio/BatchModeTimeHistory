import streamlit as st
import plotly.graph_objects as go


def display_simulation_results(
    tamarack_data, tamarack_results, flatwing_data, flatwing_results, v1_cut_enabled,
    dep_latitude, dep_longitude, arr_latitude, arr_longitude, distance_nm, bearing_deg, winds_temps_source, cruise_alt,
    departure_airport, arrival_airport, calculate_range_rings, initial_fuel
):
    """
    Display the simulation results, including V-speeds, final metrics, range rings, and charts for one or both models.

    Args:
        tamarack_data, tamarack_results: Simulation data and results for the Tamarack model.
        flatwing_data, flatwing_results: Simulation data and results for the Flatwing model.
        v1_cut_enabled: Boolean indicating if V1 cut simulation is enabled.
        dep_latitude, dep_longitude: Coordinates of the departure airport.
        arr_latitude, arr_longitude: Coordinates of the arrival airport.
        distance_nm: Distance between airports in nautical miles.
        bearing_deg: Bearing between airports in degrees.
        winds_temps_source: Source for winds aloft data.
        cruise_alt: Cruise altitude for wind calculations.
        departure_airport: ICAO code of the departure airport.
        arrival_airport: ICAO code of the arrival airport.
        calculate_range_rings: Function to calculate range rings (imported from simulation.py).
        initial_fuel: Initial fuel value.
    """

    # Plot the flight path with range rings on a map using Plotly
    st.write("**Flight Path with Range Rings**")
    fig = go.Figure()

    # Add the flight path as a line
    fig.add_trace(
        go.Scattergeo(
            lat=[dep_latitude, arr_latitude],
            lon=[dep_longitude, arr_longitude],
            mode='lines',
            line=dict(width=2, color='red'),
            name='Flight Path'
        )
    )

    # Add markers for departure and arrival airports
    fig.add_trace(
        go.Scattergeo(
            lat=[dep_latitude, arr_latitude],
            lon=[dep_longitude, arr_longitude],
            mode='markers+text',
            marker=dict(size=10, color='blue', symbol='circle'),
            text=[departure_airport, arrival_airport],
            textposition="top center",
            name='Airports'
        )
    )

    # Calculate range rings for both models if available
    winds_temps_data = {
        "Current Conditions": {
            18000: (310, 30, -20),  # FL180
            30000: (310, 40, -35),  # FL300
            39000: (310, 50, -45),  # FL390
        },
        "Summer Average": {
            18000: (270, 15, -10),
            30000: (270, 20, -25),
            39000: (270, 25, -30),
        },
        "Winter Average": {
            18000: (320, 35, -25),
            30000: (320, 45, -40),
            39000: (320, 55, -50),
        }
    }
    selected_winds_temps = winds_temps_data[winds_temps_source]

    # Initialize range rings
    tamarack_reserve_fuel_ring = None
    tamarack_max_range_ring = None
    flatwing_reserve_fuel_ring = None
    flatwing_max_range_ring = None
    flatwing_fuel_exhaustion = None

    # Tamarack range rings
    if not tamarack_data.empty and not tamarack_results.get("error"):
        tamarack_reserve_fuel_ring, tamarack_max_range_ring = calculate_range_rings(
            dep_latitude,
            dep_longitude,
            distance_nm,
            tamarack_results.get("Total Time (sec)", 0),
            tamarack_results.get("Cruise VKTAS (knots)", 0),
            tamarack_results.get("Fuel Start (lb)", 0),
            tamarack_results.get("Fuel Burned (lb)", 0),
            100,  # taxi_fuel
            600,  # reserve_fuel
            tamarack_results.get("Cruise Fuel Rate (lb/hr)", 0),
            cruise_alt,
            selected_winds_temps
        )

    # Flatwing range rings
    if not flatwing_data.empty and not flatwing_results.get("error"):
        flatwing_reserve_fuel_ring, flatwing_max_range_ring = calculate_range_rings(
            dep_latitude,
            dep_longitude,
            distance_nm,
            flatwing_results.get("Total Time (sec)", 0),
            flatwing_results.get("Cruise VKTAS (knots)", 0),
            flatwing_results.get("Fuel Start (lb)", 0),
            flatwing_results.get("Fuel Burned (lb)", 0),
            100,  # taxi_fuel
            600,  # reserve_fuel
            flatwing_results.get("Cruise Fuel Rate (lb/hr)", 0),
            cruise_alt,
            selected_winds_temps
        )

    # Add Tamarack range rings if available
    if tamarack_reserve_fuel_ring:
        fig.add_trace(
            go.Scattergeo(
                lat=tamarack_reserve_fuel_ring[0],
                lon=tamarack_reserve_fuel_ring[1],
                mode='lines',
                line=dict(width=1, color='orange', dash='dot'),
                name='Tamarack Reserve Fuel Ring'
            )
        )
        fig.add_trace(
            go.Scattergeo(
                lat=tamarack_max_range_ring[0],
                lon=tamarack_max_range_ring[1],
                mode='lines',
                line=dict(width=1, color='orange', dash='solid'),
                name='Tamarack Max Range Ring'
            )
        )

    # Add Flatwing range rings if available
    if flatwing_reserve_fuel_ring:
        fig.add_trace(
            go.Scattergeo(
                lat=flatwing_reserve_fuel_ring[0],
                lon=flatwing_reserve_fuel_ring[1],
                mode='lines',
                line=dict(width=1, color='purple', dash='dot'),
                name='Flatwing Reserve Fuel Ring'
            )
        )
        fig.add_trace(
            go.Scattergeo(
                lat=flatwing_max_range_ring[0],
                lon=flatwing_max_range_ring[1],
                mode='lines',
                line=dict(width=1, color='purple', dash='solid'),
                name='Flatwing Max Range Ring'
            )
        )

    # Add Flatwing fuel exhaustion point if applicable
    if flatwing_fuel_exhaustion:
        fig.add_trace(
            go.Scattergeo(
                lat=[flatwing_fuel_exhaustion[0]],
                lon=[flatwing_fuel_exhaustion[1]],
                mode='markers+text',
                marker=dict(size=10, color='black', symbol='x'),
                text=['Flatwing Fuel Exhausted'],
                textposition="bottom center",
                name='Flatwing Fuel Exhausted'
            )
        )

    # Update the layout for the map with dynamic bounds
    center_lat = (dep_latitude + arr_latitude) / 2
    center_lon = (dep_longitude + arr_longitude) / 2
    lat_diff = abs(dep_latitude - arr_latitude)
    lon_diff = abs(dep_longitude - arr_longitude)
    # Add padding to ensure the map fills the space nicely
    padding = max(lat_diff, lon_diff) * 0.5  # 50% padding on the larger dimension
    lat_min = min(dep_latitude, arr_latitude) - padding
    lat_max = max(dep_latitude, arr_latitude) + padding
    lon_min = min(dep_longitude, arr_longitude) - padding
    lon_max = max(dep_longitude, arr_longitude) + padding
    # Ensure the map has a minimum aspect ratio to avoid distortion
    lat_range = lat_max - lat_min
    lon_range = lon_max - lon_min
    aspect_ratio = 1.0  # Target aspect ratio (width/height)
    if lat_range / lon_range < aspect_ratio:
        # Extend latitude range to match the desired aspect ratio
        lat_mid = (lat_max + lat_min) / 2
        lat_range_needed = lon_range * aspect_ratio
        lat_min = lat_mid - lat_range_needed / 2
        lat_max = lat_mid + lat_range_needed / 2
    else:
        # Extend longitude range to match the desired aspect ratio
        lon_mid = (lon_max + lon_min) / 2
        lon_range_needed = lat_range / aspect_ratio
        lon_min = lon_mid - lon_range_needed / 2
        lon_max = lon_mid + lon_range_needed / 2

    fig.update_layout(
        geo=dict(
            scope='north america',
            projection_type='mercator',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            showcountries=True,
            countrycolor='rgb(150, 150, 150)',
            showsubunits=True,
            subunitcolor='rgb(200, 200, 200)',
            showocean=True,
            oceancolor='rgb(200, 230, 255)',
            showlakes=True,
            lakecolor='rgb(200, 230, 255)',
            showrivers=True,
            rivercolor='rgb(200, 230, 255)',
            center=dict(lat=center_lat, lon=center_lon),
            lataxis=dict(range=[lat_min, lat_max]),
            lonaxis=dict(range=[lon_min, lon_max]),
        ),
        showlegend=True,
        height=500,
        margin={"r":0,"t":0,"l":0,"b":0}
    )

    st.plotly_chart(fig, use_container_width=True)
    # Display distance and bearing
    st.success(f"Distance: {distance_nm:.1f} NM | Bearing: {bearing_deg:.1f}°")

    # Create two columns for side-by-side display
    col1, col2 = st.columns(2)
    
    # Tamarack column
    with col1:
        st.subheader("Tamarack")
        
        # Takeoff Section
        if tamarack_results:
            st.write("**Takeoff**")
            if "Takeoff V-Speeds" in tamarack_results:
                v_speeds = tamarack_results["Takeoff V-Speeds"]
                if v_speeds:
                    st.write("*V-Speeds*")
                    st.write(f"Weight: {v_speeds.get('Weight', 'N/A')} lb")
                    st.write(f"VR: {v_speeds.get('VR', 'N/A')} kts")
                    st.write(f"V1: {v_speeds.get('V1', 'N/A')} kts")
                    st.write(f"V2: {v_speeds.get('V2', 'N/A')} kts")
                    st.write(f"V3: {v_speeds.get('V3', 'N/A')} kts")
            st.write("*Performance*")
            st.write(f"Start Weight: {tamarack_results.get('Takeoff Start Weight (lb)', 'N/A')} lb")
            st.write(f"End Weight: {tamarack_results.get('Takeoff End Weight (lb)', 'N/A')} lb")
            st.write(f"Roll Distance: {tamarack_results.get('Takeoff Roll Dist (ft)', 'N/A')} ft")
            st.write(f"Dist to 35 ft: {tamarack_results.get('Dist to 35 ft (ft)', 'N/A')} ft")
            st.write(f"Seg 1 Grad: {tamarack_results.get('Segment 1 Gradient (%)', 'N/A')} %")
            st.write(f"Dist to 400 ft: {tamarack_results.get('Dist to 400 ft (ft)', 'N/A')} ft")
            st.write(f"Seg 2 Grad: {tamarack_results.get('Segment 2 Gradient (%)', 'N/A')} %")
            st.write(f"Dist to 1500 ft: {tamarack_results.get('Dist to 1500 ft (ft)', 'N/A')} ft")
            st.write(f"Seg 3 Grad: {tamarack_results.get('Segment 3 Gradient (%)', 'N/A')} %")
            st.write("---")
            
            # Add V1 cut information
            if tamarack_results.get("V1 Cut", False):
                st.write("**V1 Cut**")
                st.write("*Single Engine Operation*")
                st.write("---")
            else:
                # Climb Section
                st.write("**Climb**")
                st.write(f"Start Weight: {tamarack_results.get('Climb Start Weight (lb)', 'N/A')} lb")
                st.write(f"End Weight: {tamarack_results.get('Climb End Weight (lb)', 'N/A')} lb")
                st.write(f"Time: {tamarack_results.get('Climb Time (min)', 'N/A')} min")
                st.write(f"Distance: {tamarack_results.get('Climb Dist (NM)', 'N/A')} NM")
                st.write(f"Fuel: {tamarack_results.get('Climb Fuel (lb)', 'N/A')} lb")
                st.write("---")
                
                # Cruise Section
                st.write("**Cruise**")
                st.write(f"Start Weight: {tamarack_results.get('Cruise Start Weight (lb)', 'N/A')} lb")
                st.write(f"End Weight: {tamarack_results.get('Cruise End Weight (lb)', 'N/A')} lb")
                st.write(f"Time: {tamarack_results.get('Cruise Time (min)', 'N/A')} min")
                st.write(f"Distance: {tamarack_results.get('Cruise Dist (NM)', 'N/A')} NM")
                st.write(f"Fuel: {tamarack_results.get('Cruise Fuel (lb)', 'N/A')} lb")
                st.write(f"VKTAS: {tamarack_results.get('Cruise VKTAS (knots)', 'N/A')} kts")
                
                cruise_time = tamarack_results.get('Cruise Time (min)', None)
                cruise_fuel = tamarack_results.get('Cruise Fuel (lb)', None)
                if cruise_time is not None and cruise_time > 0:
                    fuel_rate = cruise_fuel / (cruise_time / 60)
                    st.write(f"Fuel Rate: {fuel_rate:.1f} lb/hr")
                st.write("---")
                
                # Descent Section
                st.write("**Descent**")
                st.write(f"Start Weight: {tamarack_results.get('Descent Start Weight (lb)', 'N/A')} lb")
                st.write(f"End Weight: {tamarack_results.get('Descent End Weight (lb)', 'N/A')} lb")
                st.write(f"Time: {tamarack_results.get('Descent Time (min)', 'N/A')} min")
                st.write(f"Distance: {tamarack_results.get('Descent Dist (NM)', 'N/A')} NM")
                st.write(f"Fuel: {tamarack_results.get('Descent Fuel (lb)', 'N/A')} lb")
                st.write("---")
                
                # Landing Section
                st.write("**Landing**")
                landing_start_weight = tamarack_results.get('Landing Start Weight (lb)', None)
                if landing_start_weight is not None:
                    st.write(f"Start Weight: {landing_start_weight} lb")
                
                dist_land_35 = tamarack_results.get('Landing - Dist from 35 ft to Stop (ft)', None)
                ground_roll = tamarack_results.get('Landing - Ground Roll (ft)', None)
                
                if dist_land_35 is not None:
                    st.write(f"Total Distance: {dist_land_35} ft")
                if ground_roll is not None:
                    st.write(f"Ground Roll: {ground_roll} ft")
                
                descent_fuel_burned = tamarack_results.get('Descent Fuel (lb)', None)
                if descent_fuel_burned is not None and landing_start_weight is not None:
                    final_weight = landing_start_weight - descent_fuel_burned
                    st.write(f"Final Weight: {int(final_weight)} lb")
                st.write("---")
                
                # Total Flight Section
                st.write("**Total Flight**")
                st.write(f"Time: {tamarack_results.get('Total Time (min)', 'N/A')} min")
                st.write(f"Distance: {tamarack_results.get('Total Dist (NM)', 'N/A')} NM")
                st.write(f"Fuel Burned: {tamarack_results.get('Total Fuel Burned (lb)', 'N/A')} lb")
                st.write(f"Fuel Start: {tamarack_results.get('Fuel Start (lb)', 'N/A')} lb")
                st.write(f"Fuel End: {tamarack_results.get('Fuel End (lb)', 'N/A')} lb")
                st.write("---")

    # Flatwing column
    with col2:
        st.subheader("Flatwing")
        
        # Takeoff Section
        if flatwing_results:
            st.write("**Takeoff**")
            if "Takeoff V-Speeds" in flatwing_results:
                v_speeds = flatwing_results["Takeoff V-Speeds"]
                if v_speeds:
                    st.write("*V-Speeds*")
                    st.write(f"Weight: {v_speeds.get('Weight', 'N/A')} lb")
                    st.write(f"VR: {v_speeds.get('VR', 'N/A')} kts")
                    st.write(f"V1: {v_speeds.get('V1', 'N/A')} kts")
                    st.write(f"V2: {v_speeds.get('V2', 'N/A')} kts")
                    st.write(f"V3: {v_speeds.get('V3', 'N/A')} kts")
            st.write("*Performance*")
            st.write(f"Start Weight: {flatwing_results.get('Takeoff Start Weight (lb)', 'N/A')} lb")
            st.write(f"End Weight: {flatwing_results.get('Takeoff End Weight (lb)', 'N/A')} lb")
            st.write(f"Roll Distance: {flatwing_results.get('Takeoff Roll Dist (ft)', 'N/A')} ft")
            st.write(f"Dist to 35 ft: {flatwing_results.get('Dist to 35 ft (ft)', 'N/A')} ft")
            st.write(f"Seg 1 Grad: {flatwing_results.get('Segment 1 Gradient (%)', 'N/A')} %")
            st.write(f"Dist to 400 ft: {flatwing_results.get('Dist to 400 ft (ft)', 'N/A')} ft")
            st.write(f"Seg 2 Grad: {flatwing_results.get('Segment 2 Gradient (%)', 'N/A')} %")
            st.write(f"Dist to 1500 ft: {flatwing_results.get('Dist to 1500 ft (ft)', 'N/A')} ft")
            st.write(f"Seg 3 Grad: {flatwing_results.get('Segment 3 Gradient (%)', 'N/A')} %")
            st.write("---")
            
            # Add V1 cut information
            if flatwing_results.get("V1 Cut", False):
                st.write("**V1 Cut**")
                st.write("*Single Engine Operation*")
                st.write("---")
            else:
                # Climb Section
                st.write("**Climb**")
                st.write(f"Start Weight: {flatwing_results.get('Climb Start Weight (lb)', 'N/A')} lb")
                st.write(f"End Weight: {flatwing_results.get('Climb End Weight (lb)', 'N/A')} lb")
                st.write(f"Time: {flatwing_results.get('Climb Time (min)', 'N/A')} min")
                st.write(f"Distance: {flatwing_results.get('Climb Dist (NM)', 'N/A')} NM")
                st.write(f"Fuel: {flatwing_results.get('Climb Fuel (lb)', 'N/A')} lb")
                st.write("---")
                
                # Cruise Section
                st.write("**Cruise**")
                st.write(f"Start Weight: {flatwing_results.get('Cruise Start Weight (lb)', 'N/A')} lb")
                st.write(f"End Weight: {flatwing_results.get('Cruise End Weight (lb)', 'N/A')} lb")
                st.write(f"Time: {flatwing_results.get('Cruise Time (min)', 'N/A')} min")
                st.write(f"Distance: {flatwing_results.get('Cruise Dist (NM)', 'N/A')} NM")
                st.write(f"Fuel: {flatwing_results.get('Cruise Fuel (lb)', 'N/A')} lb")
                st.write(f"VKTAS: {flatwing_results.get('Cruise VKTAS (knots)', 'N/A')} kts")
                
                cruise_time = flatwing_results.get('Cruise Time (min)', None)
                cruise_fuel = flatwing_results.get('Cruise Fuel (lb)', None)
                if cruise_time is not None and cruise_time > 0:
                    fuel_rate = cruise_fuel / (cruise_time / 60)
                    st.write(f"Fuel Rate: {fuel_rate:.1f} lb/hr")
                st.write("---")
                
                # Descent Section
                st.write("**Descent**")
                st.write(f"Start Weight: {flatwing_results.get('Descent Start Weight (lb)', 'N/A')} lb")
                st.write(f"End Weight: {flatwing_results.get('Descent End Weight (lb)', 'N/A')} lb")
                st.write(f"Time: {flatwing_results.get('Descent Time (min)', 'N/A')} min")
                st.write(f"Distance: {flatwing_results.get('Descent Dist (NM)', 'N/A')} NM")
                st.write(f"Fuel: {flatwing_results.get('Descent Fuel (lb)', 'N/A')} lb")
                st.write("---")
                
                # Landing Section
                st.write("**Landing**")
                landing_start_weight = flatwing_results.get('Landing Start Weight (lb)', None)
                if landing_start_weight is not None:
                    st.write(f"Start Weight: {landing_start_weight} lb")
                
                dist_land_35 = flatwing_results.get('Landing - Dist from 35 ft to Stop (ft)', None)
                ground_roll = flatwing_results.get('Landing - Ground Roll (ft)', None)
                
                if dist_land_35 is not None:
                    st.write(f"Total Distance: {dist_land_35} ft")
                if ground_roll is not None:
                    st.write(f"Ground Roll: {ground_roll} ft")
                
                descent_fuel_burned = flatwing_results.get('Descent Fuel (lb)', None)
                if descent_fuel_burned is not None and landing_start_weight is not None:
                    final_weight = landing_start_weight - descent_fuel_burned
                    st.write(f"Final Weight: {int(final_weight)} lb")
                st.write("---")
                
                # Total Flight Section
                st.write("**Total Flight**")
                st.write(f"Time: {flatwing_results.get('Total Time (min)', 'N/A')} min")
                st.write(f"Distance: {flatwing_results.get('Total Dist (NM)', 'N/A')} NM")
                st.write(f"Fuel Burned: {flatwing_results.get('Total Fuel Burned (lb)', 'N/A')} lb")
                st.write(f"Fuel Start: {flatwing_results.get('Fuel Start (lb)', 'N/A')} lb")
                st.write(f"Fuel End: {flatwing_results.get('Fuel End (lb)', 'N/A')} lb")
                st.write("---")

    # Check for exceedances or errors
    if tamarack_results.get("exceedances"):
        for msg in tamarack_results["exceedances"]:
            st.error(msg)
    elif tamarack_results.get("error"):
        st.error(tamarack_results["error"])
    
    if flatwing_results.get("exceedances"):
        for msg in flatwing_results["exceedances"]:
            st.error(msg)
    elif flatwing_results.get("error"):
        st.error(flatwing_results["error"])

    # Display graphs comparing both models if both have data
    if not tamarack_data.empty and not flatwing_data.empty:
        st.subheader("Flight Profile Visualizations (Tamarack vs. Flatwing)")

        try:
            # Altitude and Mach vs. Distance with secondary Y-axis for Mach
            st.write("**Altitude and Mach vs. Distance**")
            fig_alt_mach = go.Figure()
            # Tamarack Altitude
            fig_alt_mach.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['Altitude (ft)'],
                    name='Altitude (ft) - Tamarack',
                    line=dict(color='blue')
                )
            )
            # Flatwing Altitude
            fig_alt_mach.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['Altitude (ft)'],
                    name='Altitude (ft) - Flatwing',
                    line=dict(color='purple')
                )
            )
            # Tamarack Mach
            fig_alt_mach.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['Mach'],
                    name='Mach - Tamarack',
                    yaxis='y2',
                    line=dict(color='orange')
                )
            )
            # Flatwing Mach
            fig_alt_mach.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['Mach'],
                    name='Mach - Flatwing',
                    yaxis='y2',
                    line=dict(color='red')
                )
            )
            fig_alt_mach.update_layout(
                xaxis=dict(
                    title='Distance (NM)',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    gridwidth=1
                ),
                yaxis=dict(title='Altitude (ft)'),
                yaxis2=dict(
                    title='Mach',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.1, y=1.1, orientation='h')
            )
            st.plotly_chart(fig_alt_mach)

            # Speed (KTAS and KIAS) vs. Distance
            st.write("**Speed (KTAS and KIAS) vs. Distance**")
            fig_speed = go.Figure()
            # Tamarack VKTAS
            fig_speed.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['VKTAS (kts)'],
                    name='VKTAS - Tamarack',
                    line=dict(color='blue')
                )
            )
            # Flatwing VKTAS
            fig_speed.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['VKTAS (kts)'],
                    name='VKTAS - Flatwing',
                    line=dict(color='purple')
                )
            )
            # Tamarack VKIAS
            fig_speed.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['VKIAS (kts)'],
                    name='VKIAS - Tamarack',
                    line=dict(color='blue', dash='dot')
                )
            )
            # Flatwing VKIAS
            fig_speed.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['VKIAS (kts)'],
                    name='VKIAS - Flatwing',
                    line=dict(color='purple', dash='dot')
                )
            )
            fig_speed.update_layout(
                title='Speed vs. Distance',
                xaxis_title='Distance (NM)',
                yaxis_title='Speed (kts)',
                legend_title='Speed Type'
            )
            st.plotly_chart(fig_speed)

            # Add VKTAS vs. Time chart
            st.write("**Speed (KTAS) vs. Time**")
            fig_speed_time = go.Figure()
            # Tamarack VKTAS
            fig_speed_time.add_trace(
                go.Scatter(
                    x=tamarack_data['Time (hr)'],
                    y=tamarack_data['VKTAS (kts)'],
                    name='VKTAS - Tamarack',
                    line=dict(color='blue')
                )
            )
            # Flatwing VKTAS
            fig_speed_time.add_trace(
                go.Scatter(
                    x=flatwing_data['Time (hr)'],
                    y=flatwing_data['VKTAS (kts)'],
                    name='VKTAS - Flatwing',
                    line=dict(color='purple')
                )
            )
            fig_speed_time.update_layout(
                title='Speed vs. Time',
                xaxis_title='Time (hr)',
                yaxis_title='Speed (kts)',
                legend_title='Speed Type'
            )
            st.plotly_chart(fig_speed_time)

            # Rate of Climb (ROC) and Gradient vs. Distance
            st.write("**Rate of Climb (ROC) and Gradient vs. Distance**")
            fig_roc = go.Figure()
            # Tamarack ROC
            fig_roc.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['ROC (fpm)'],
                    name='ROC (fpm) - Tamarack',
                    line=dict(color='blue')
                )
            )
            # Flatwing ROC
            fig_roc.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['ROC (fpm)'],
                    name='ROC (fpm) - Flatwing',
                    line=dict(color='purple')
                )
            )
            # Tamarack Gradient
            fig_roc.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['Gradient (%)'],
                    name='Gradient (%) - Tamarack',
                    yaxis='y2',
                    line=dict(color='orange')
                )
            )
            # Flatwing Gradient
            fig_roc.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['Gradient (%)'],
                    name='Gradient (%) - Flatwing',
                    yaxis='y2',
                    line=dict(color='red')
                )
            )
            fig_roc.update_layout(
                xaxis=dict(
                    title='Distance (NM)',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    gridwidth=1
                ),
                yaxis=dict(title='ROC (fpm)'),
                yaxis2=dict(
                    title='Gradient (%)',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.1, y=1.1, orientation='h')
            )
            st.plotly_chart(fig_roc)

        except ValueError as e:
            st.warning(f"Error rendering charts: {e}")
            st.write("Displaying raw data instead:")
            st.write("Tamarack Data:")
            st.dataframe(tamarack_data)
            st.write("Flatwing Data:")
            st.dataframe(flatwing_data)

    # Display graphs for Tamarack only if Flatwing data is empty
    elif not tamarack_data.empty:
        st.subheader("Flight Profile Visualizations - Tamarack")
        try:
            # Altitude and Mach vs. Distance with secondary Y-axis for Mach
            st.write("**Altitude and Mach vs. Distance**")
            fig_alt_mach = go.Figure()
            fig_alt_mach.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['Altitude (ft)'],
                    name='Altitude (ft) - Tamarack',
                    line=dict(color='blue')
                )
            )
            fig_alt_mach.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['Mach'],
                    name='Mach - Tamarack',
                    yaxis='y2',
                    line=dict(color='orange')
                )
            )
            fig_alt_mach.update_layout(
                xaxis=dict(
                    title='Distance (NM)',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    gridwidth=1
                ),
                yaxis=dict(title='Altitude (ft)'),
                yaxis2=dict(
                    title='Mach',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.1, y=1.1, orientation='h')
            )
            st.plotly_chart(fig_alt_mach)

            # Speed (KTAS and KIAS) vs. Distance
            st.write("**Speed (KTAS and KIAS) vs. Distance**")
            fig_speed = go.Figure()
            # Tamarack VKTAS
            fig_speed.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['VKTAS (kts)'],
                    name='VKTAS - Tamarack',
                    line=dict(color='blue')
                )
            )
            # Tamarack VKIAS
            fig_speed.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['VKIAS (kts)'],
                    name='VKIAS - Tamarack',
                    line=dict(color='blue', dash='dot')
                )
            )
            fig_speed.update_layout(
                title='Speed vs. Distance',
                xaxis_title='Distance (NM)',
                yaxis_title='Speed (kts)',
                legend_title='Speed Type'
            )
            st.plotly_chart(fig_speed)

            # Add VKTAS vs. Time chart
            st.write("**Speed (KTAS) vs. Time**")
            fig_speed_time = go.Figure()
            # Tamarack VKTAS
            fig_speed_time.add_trace(
                go.Scatter(
                    x=tamarack_data['Time (hr)'],
                    y=tamarack_data['VKTAS (kts)'],
                    name='VKTAS - Tamarack',
                    line=dict(color='blue')
                )
            )
            fig_speed_time.update_layout(
                title='Speed vs. Time',
                xaxis_title='Time (hr)',
                yaxis_title='Speed (kts)',
                legend_title='Speed Type'
            )
            st.plotly_chart(fig_speed_time)

            # Rate of Climb (ROC) and Gradient vs. Distance
            st.write("**Rate of Climb (ROC) and Gradient vs. Distance**")
            fig_roc = go.Figure()
            fig_roc.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['ROC (fpm)'],
                    name='ROC (fpm) - Tamarack',
                    line=dict(color='blue')
                )
            )
            fig_roc.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['Gradient (%)'],
                    name='Gradient (%) - Tamarack',
                    yaxis='y2',
                    line=dict(color='orange')
                )
            )
            fig_roc.update_layout(
                xaxis=dict(
                    title='Distance (NM)',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    gridwidth=1
                ),
                yaxis=dict(title='ROC (fpm)'),
                yaxis2=dict(
                    title='Gradient (%)',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.1, y=1.1, orientation='h')
            )
            st.plotly_chart(fig_roc)

        except ValueError as e:
            st.warning(f"Error rendering charts: {e}")
            st.write("Displaying raw data instead:")
            st.write("Tamarack Data:")
            st.dataframe(tamarack_data)

    # Display graphs for Flatwing only if Tamarack data is empty
    elif not flatwing_data.empty:
        st.subheader("Flight Profile Visualizations - Flatwing")
        try:
            # Altitude and Mach vs. Distance with secondary Y-axis for Mach
            st.write("**Altitude and Mach vs. Distance**")
            fig_alt_mach = go.Figure()
            fig_alt_mach.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['Altitude (ft)'],
                    name='Altitude (ft) - Flatwing',
                    line=dict(color='purple')
                )
            )
            fig_alt_mach.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['Mach'],
                    name='Mach - Flatwing',
                    yaxis='y2',
                    line=dict(color='red')
                )
            )
            fig_alt_mach.update_layout(
                xaxis=dict(
                    title='Distance (NM)',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    gridwidth=1
                ),
                yaxis=dict(title='Altitude (ft)'),
                yaxis2=dict(
                    title='Mach',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.1, y=1.1, orientation='h')
            )
            st.plotly_chart(fig_alt_mach)

            # Speed (KTAS and KIAS) vs. Distance
            st.write("**Speed (KTAS and KIAS) vs. Distance**")
            fig_speed = go.Figure()
            # Flatwing VKTAS
            fig_speed.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['VKTAS (kts)'],
                    name='VKTAS - Flatwing',
                    line=dict(color='purple')
                )
            )
            # Flatwing VKIAS
            fig_speed.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['VKIAS (kts)'],
                    name='VKIAS - Flatwing',
                    line=dict(color='purple', dash='dot')
                )
            )
            fig_speed.update_layout(
                title='Speed vs. Distance',
                xaxis_title='Distance (NM)',
                yaxis_title='Speed (kts)',
                legend_title='Speed Type'
            )
            st.plotly_chart(fig_speed)

            # Add VKTAS vs. Time chart
            st.write("**Speed (KTAS) vs. Time**")
            fig_speed_time = go.Figure()
            # Flatwing VKTAS
            fig_speed_time.add_trace(
                go.Scatter(
                    x=flatwing_data['Time (hr)'],
                    y=flatwing_data['VKTAS (kts)'],
                    name='VKTAS - Flatwing',
                    line=dict(color='purple')
                )
            )
            fig_speed_time.update_layout(
                title='Speed vs. Time',
                xaxis_title='Time (hr)',
                yaxis_title='Speed (kts)',
                legend_title='Speed Type'
            )
            st.plotly_chart(fig_speed_time)

            # Rate of Climb (ROC) and Gradient vs. Distance
            st.write("**Rate of Climb (ROC) and Gradient vs. Distance**")
            fig_roc = go.Figure()
            fig_roc.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['ROC (fpm)'],
                    name='ROC (fpm) - Flatwing',
                    line=dict(color='purple')
                )
            )
            fig_roc.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['Gradient (%)'],
                    name='Gradient (%) - Flatwing',
                    yaxis='y2',
                    line=dict(color='red')
                )
            )
            fig_roc.update_layout(
                xaxis=dict(
                    title='Distance (NM)',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    gridwidth=1
                ),
                yaxis=dict(title='ROC (fpm)'),
                yaxis2=dict(
                    title='Gradient (%)',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.1, y=1.1, orientation='h')
            )
            st.plotly_chart(fig_roc)

        except ValueError as e:
            st.warning(f"Error rendering charts: {e}")
            st.write("Displaying raw data instead:")
            st.write("Flatwing Data:")
            st.dataframe(flatwing_data)