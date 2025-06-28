import streamlit as st
import plotly.graph_objects as go


def display_simulation_results(
    tamarack_data, tamarack_results, flatwing_data, flatwing_results, v1_cut_enabled,
    dep_latitude, dep_longitude, arr_latitude, arr_longitude, distance_nm, bearing_deg, winds_temps_source, cruise_alt,
    departure_airport, arrival_airport, calculate_range_rings
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
    """
    # Display distance and bearing
    st.success(f"Distance: {distance_nm:.1f} NM | Bearing: {bearing_deg:.1f}°")

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
    tamarack_time_based_ring = None
    tamarack_reserve_fuel_ring = None
    tamarack_max_range_ring = None
    flatwing_time_based_ring = None
    flatwing_reserve_fuel_ring = None
    flatwing_max_range_ring = None
    flatwing_fuel_exhaustion = None

    # Tamarack range rings
    if not tamarack_data.empty and not tamarack_results.get("error"):
        tamarack_time_based_ring, tamarack_reserve_fuel_ring, tamarack_max_range_ring = calculate_range_rings(
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

    # Flatwing range rings and fuel exhaustion point
    if not flatwing_data.empty:
        if flatwing_results.get("error"):
            # If Flatwing ran out of fuel, get the last position
            flatwing_fuel_exhaustion = (flatwing_results.get("Last Lat"), flatwing_results.get("Last Lon"))
        else:
            flatwing_time_based_ring, flatwing_reserve_fuel_ring, flatwing_max_range_ring = calculate_range_rings(
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
    if tamarack_time_based_ring:
        fig.add_trace(
            go.Scattergeo(
                lat=tamarack_time_based_ring[0],
                lon=tamarack_time_based_ring[1],
                mode='lines',
                line=dict(width=1, color='orange', dash='dash'),
                name='Tamarack Max Distance (Time-Based)'
            )
        )
        fig.add_trace(
            go.Scattergeo(
                lat=tamarack_reserve_fuel_ring[0],
                lon=tamarack_reserve_fuel_ring[1],
                mode='lines',
                line=dict(width=1, color='orange', dash='dot'),
                name='Tamarack Max Range (Reserve Fuel)'
            )
        )
        fig.add_trace(
            go.Scattergeo(
                lat=tamarack_max_range_ring[0],
                lon=tamarack_max_range_ring[1],
                mode='lines',
                line=dict(width=1, color='orange', dash='solid'),
                name='Tamarack Max Range (Full Fuel)'
            )
        )

    # Add Flatwing range rings if available
    if flatwing_time_based_ring:
        fig.add_trace(
            go.Scattergeo(
                lat=flatwing_time_based_ring[0],
                lon=flatwing_time_based_ring[1],
                mode='lines',
                line=dict(width=1, color='purple', dash='dash'),
                name='Flatwing Max Distance (Time-Based)'
            )
        )
        fig.add_trace(
            go.Scattergeo(
                lat=flatwing_reserve_fuel_ring[0],
                lon=flatwing_reserve_fuel_ring[1],
                mode='lines',
                line=dict(width=1, color='purple', dash='dot'),
                name='Flatwing Max Range (Reserve Fuel)'
            )
        )
        fig.add_trace(
            go.Scattergeo(
                lat=flatwing_max_range_ring[0],
                lon=flatwing_max_range_ring[1],
                mode='lines',
                line=dict(width=1, color='purple', dash='solid'),
                name='Flatwing Max Range (Full Fuel)'
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

    # Display V-speeds and final results
    if tamarack_results or flatwing_results:
        # Check for exceedances or errors
        if tamarack_results.get("exceedances"):
            for msg in tamarack_results["exceedances"]:
                st.error(msg)
            return
        elif tamarack_results.get("error"):
            st.error(tamarack_results["error"])
        if flatwing_results.get("exceedances"):
            for msg in flatwing_results["exceedances"]:
                st.error(msg)
            return
        elif flatwing_results.get("error"):
            st.error(flatwing_results["error"])

        # Display Tamarack results if available
        if not tamarack_data.empty:
            st.subheader("Final Results - Tamarack")
            with st.expander("Takeoff", expanded=True):
                takeoff_metrics = {
                    "Takeoff Roll Dist (ft)": tamarack_results.get("Takeoff Roll Dist (ft)"),
                    "Dist to 35 ft (ft)": tamarack_results.get("Dist to 35 ft (ft)"),
                    "Segment 1 Gradient (%)": tamarack_results.get("Segment 1 Gradient (%)"),
                    "Dist to 400 ft (ft)": tamarack_results.get("Dist to 400 ft (ft)"),
                    "Segment 2 Gradient (%)": tamarack_results.get("Segment 2 Gradient (%)"),
                    "Dist to 1500 ft (ft)": tamarack_results.get("Dist to 1500 ft (ft)"),
                    "Segment 3 Gradient (%)": tamarack_results.get("Segment 3 Gradient (%)"),
                }
                for key, value in takeoff_metrics.items():
                    if value is not None:
                        st.write(f"**{key}**: {value}")

            with st.expander("Climb"):
                climb_metrics = {
                    "Climb Time (min)": tamarack_results.get("Climb Time (min)"),
                    "Climb Dist (NM)": tamarack_results.get("Climb Dist (NM)"),
                    "Climb Fuel (lb)": tamarack_results.get("Climb Fuel (lb)"),
                }
                for key, value in climb_metrics.items():
                    if value is not None:
                        st.write(f"**{key}**: {value}")

            with st.expander("Cruise"):
                cruise_metrics = {
                    "Cruise Fuel (lb)": tamarack_results.get("Cruise Fuel (lb)"),
                    "Cruise Time (min)": tamarack_results.get("Cruise Time (min)"),
                    "Cruise Dist (NM)": tamarack_results.get("Cruise Dist (NM)"),
                    "Cruise Efficiency (NM/lb)": tamarack_results.get("Cruise Efficiency (NM/lb)"),
                    "Cruise Fuel Rate (lb/hr)": tamarack_results.get("Cruise Fuel Rate (lb/hr)"),
                    "Max M Reached": tamarack_results.get("Max M Reached"),
                }
                for key, value in cruise_metrics.items():
                    if value is not None:
                        st.write(f"**{key}**: {value}")
                if tamarack_results.get("Step Altitudes (ft)"):
                    st.write("**Step Altitudes (ft)**: " + ", ".join(map(str, tamarack_results["Step Altitudes (ft)"])))

            with st.expander("Descent and Landing"):
                descent_metrics = {
                    "Descent Fuel (lb)": tamarack_results.get("Descent Fuel (lb)"),
                    "Descent Time (min)": tamarack_results.get("Descent Time (min)"),
                    "Descent Dist (NM)": tamarack_results.get("Descent Dist (NM)"),
                    "Landing Dist (ft)": tamarack_results.get("Landing Dist (ft)"),
                    "Dist from 35 ft (ft)": tamarack_results.get("Dist from 35 ft (ft)"),
                }
                for key, value in descent_metrics.items():
                    if value is not None:
                        st.write(f"**{key}**: {value}")

            with st.expander("Overall"):
                overall_metrics = {
                    "Block Time (hr)": tamarack_results.get("Block Time (hr)"),
                    "Block Speed (kts)": tamarack_results.get("Block Speed (kts)"),
                    "Block Fuel (lb)": tamarack_results.get("Block Fuel (lb)"),
                    "Fuel Burn Rate (lb/hr)": tamarack_results.get("Fuel Burn Rate (lb/hr)"),
                    "Fuel Remaining (lb)": tamarack_results.get("Fuel Remaining (lb)"),
                }
                for key, value in overall_metrics.items():
                    if value is not None:
                        st.write(f"**{key}**: {value}")

        # Display Flatwing results if available
        if not flatwing_data.empty:
            st.subheader("Final Results - Flatwing")
            with st.expander("Takeoff", expanded=True):
                takeoff_metrics = {
                    "Takeoff Roll Dist (ft)": flatwing_results.get("Takeoff Roll Dist (ft)"),
                    "Dist to 35 ft (ft)": flatwing_results.get("Dist to 35 ft (ft)"),
                    "Segment 1 Gradient (%)": flatwing_results.get("Segment 1 Gradient (%)"),
                    "Dist to 400 ft (ft)": flatwing_results.get("Dist to 400 ft (ft)"),
                    "Segment 2 Gradient (%)": flatwing_results.get("Segment 2 Gradient (%)"),
                    "Dist to 1500 ft (ft)": flatwing_results.get("Dist to 1500 ft (ft)"),
                    "Segment 3 Gradient (%)": flatwing_results.get("Segment 3 Gradient (%)"),
                }
                for key, value in takeoff_metrics.items():
                    if value is not None:
                        st.write(f"**{key}**: {value}")

            with st.expander("Climb"):
                climb_metrics = {
                    "Climb Time (min)": flatwing_results.get("Climb Time (min)"),
                    "Climb Dist (NM)": flatwing_results.get("Climb Dist (NM)"),
                    "Climb Fuel (lb)": flatwing_results.get("Climb Fuel (lb)"),
                }
                for key, value in climb_metrics.items():
                    if value is not None:
                        st.write(f"**{key}**: {value}")

            with st.expander("Cruise"):
                cruise_metrics = {
                    "Cruise Fuel (lb)": flatwing_results.get("Cruise Fuel (lb)"),
                    "Cruise Time (min)": flatwing_results.get("Cruise Time (min)"),
                    "Cruise Dist (NM)": flatwing_results.get("Cruise Dist (NM)"),
                    "Cruise Efficiency (NM/lb)": flatwing_results.get("Cruise Efficiency (NM/lb)"),
                    "Cruise Fuel Rate (lb/hr)": flatwing_results.get("Cruise Fuel Rate (lb/hr)"),
                    "Max M Reached": flatwing_results.get("Max M Reached"),
                }
                for key, value in cruise_metrics.items():
                    if value is not None:
                        st.write(f"**{key}**: {value}")
                if flatwing_results.get("Step Altitudes (ft)"):
                    st.write("**Step Altitudes (ft)**: " + ", ".join(map(str, flatwing_results["Step Altitudes (ft)"])))

            with st.expander("Descent and Landing"):
                descent_metrics = {
                    "Descent Fuel (lb)": flatwing_results.get("Descent Fuel (lb)"),
                    "Descent Time (min)": flatwing_results.get("Descent Time (min)"),
                    "Descent Dist (NM)": flatwing_results.get("Descent Dist (NM)"),
                    "Landing Dist (ft)": flatwing_results.get("Landing Dist (ft)"),
                    "Dist from 35 ft (ft)": flatwing_results.get("Dist from 35 ft (ft)"),
                }
                for key, value in descent_metrics.items():
                    if value is not None:
                        st.write(f"**{key}**: {value}")

            with st.expander("Overall"):
                overall_metrics = {
                    "Block Time (hr)": flatwing_results.get("Block Time (hr)"),
                    "Block Speed (kts)": flatwing_results.get("Block Speed (kts)"),
                    "Block Fuel (lb)": flatwing_results.get("Block Fuel (lb)"),
                    "Fuel Burn Rate (lb/hr)": flatwing_results.get("Fuel Burn Rate (lb/hr)"),
                    "Fuel Remaining (lb)": flatwing_results.get("Fuel Remaining (lb)"),
                }
                for key, value in overall_metrics.items():
                    if value is not None:
                        st.write(f"**{key}**: {value}")

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
                    y=tamarack_data['Speed (VKTAS)'],
                    name='VKTAS - Tamarack',
                    line=dict(color='blue')
                )
            )
            # Flatwing VKTAS
            fig_speed.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['Speed (VKTAS)'],
                    name='VKTAS - Flatwing',
                    line=dict(color='purple')
                )
            )
            # Tamarack VKIAS
            fig_speed.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['Speed (VKIAS)'],
                    name='VKIAS - Tamarack',
                    line=dict(color='orange')
                )
            )
            # Flatwing VKIAS
            fig_speed.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['Speed (VKIAS)'],
                    name='VKIAS - Flatwing',
                    line=dict(color='red')
                )
            )
            fig_speed.update_layout(
                xaxis=dict(
                    title='Distance (NM)',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    gridwidth=1
                ),
                yaxis=dict(title='Speed (kts)'),
                legend=dict(x=0.1, y=1.1, orientation='h')
            )
            st.plotly_chart(fig_speed)

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
            fig_speed.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['Speed (VKTAS)'],
                    name='VKTAS - Tamarack',
                    line=dict(color='blue')
                )
            )
            fig_speed.add_trace(
                go.Scatter(
                    x=tamarack_data['Distance (NM)'],
                    y=tamarack_data['Speed (VKIAS)'],
                    name='VKIAS - Tamarack',
                    line=dict(color='orange')
                )
            )
            fig_speed.update_layout(
                xaxis=dict(
                    title='Distance (NM)',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    gridwidth=1
                ),
                yaxis=dict(title='Speed (kts)'),
                legend=dict(x=0.1, y=1.1, orientation='h')
            )
            st.plotly_chart(fig_speed)

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
            fig_speed.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['Speed (VKTAS)'],
                    name='VKTAS - Flatwing',
                    line=dict(color='purple')
                )
            )
            fig_speed.add_trace(
                go.Scatter(
                    x=flatwing_data['Distance (NM)'],
                    y=flatwing_data['Speed (VKIAS)'],
                    name='VKIAS - Flatwing',
                    line=dict(color='red')
                )
            )
            fig_speed.update_layout(
                xaxis=dict(
                    title='Distance (NM)',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.5)',
                    gridwidth=1
                ),
                yaxis=dict(title='Speed (kts)'),
                legend=dict(x=0.1, y=1.1, orientation='h')
            )
            st.plotly_chart(fig_speed)

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