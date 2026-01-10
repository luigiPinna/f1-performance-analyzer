"""
F1 Performance Analyzer - Streamlit Web App
Dark theme with telemetry comparison visualization
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from src.data_service import F1DataService
from src.functionalities import FastestLapComparison
from src.constants import STREAMLIT_DARK_THEME, COLORS, PLOTLY_DARK_CONFIG

# ============================================================================
# PAGE CONFIGURATION & STYLING
# ============================================================================

st.set_page_config(
    page_title="F1 Performance Analyzer",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme CSS (GitHub dark style)
st.markdown(STREAMLIT_DARK_THEME, unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'data_service' not in st.session_state:
    st.session_state.data_service = F1DataService()

if 'functionality' not in st.session_state:
    st.session_state.functionality = FastestLapComparison()

if 'calendar_data' not in st.session_state:
    st.session_state.calendar_data = None

if 'current_session' not in st.session_state:
    st.session_state.current_session = None

if 'current_drivers' not in st.session_state:
    st.session_state.current_drivers = []

if 'current_gp_name' not in st.session_state:
    st.session_state.current_gp_name = None

if 'current_session_type' not in st.session_state:
    st.session_state.current_session_type = None

# ============================================================================
# MAIN LAYOUT
# ============================================================================

# Header
st.markdown("### 🏁 F1 ANALYZER - Telemetry Comparison & Analysis")
st.divider()

# Sidebar for controls
with st.sidebar:
    st.markdown("### Configuration")
    
    # Load calendar if not already loaded
    if st.session_state.calendar_data is None:
        with st.spinner("Loading F1 Calendar..."):
            st.session_state.calendar_data = st.session_state.data_service.load_calendar()
    
    # Year selection
    years = sorted(st.session_state.calendar_data.keys(), reverse=True)
    selected_year = st.selectbox("📅 Select Year", years)
    
    # GP selection
    gps = st.session_state.calendar_data.get(selected_year, [])
    gp_displays = [gp['display'] for gp in gps]
    selected_gp_display = st.selectbox("🏎️ Select Grand Prix", gp_displays)
    selected_gp = next((gp for gp in gps if gp['display'] == selected_gp_display), None)
    
    if selected_gp:
        # Session type selection
        selected_session_type = st.selectbox("🚦 Session Type", ["Qualifying", "Race"])
        
        # Load session button
        if st.button("📊 Load Session", key="load_session_btn", use_container_width=True):
            with st.spinner(f"Loading {selected_gp['name']} {selected_session_type}..."):
                try:
                    session, drivers = st.session_state.data_service.load_session(
                        selected_year,
                        selected_gp['name'],
                        selected_session_type
                    )
                    st.session_state.current_session = session
                    st.session_state.current_drivers = drivers
                    st.session_state.current_gp_name = selected_gp['name']
                    st.session_state.current_session_type = selected_session_type
                    
                    # Notify functionality of new session
                    st.session_state.functionality.on_session_loaded(session, drivers)
                    
                    st.success(f"✅ Loaded {len(drivers)} drivers")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# MAIN CONTENT
# ============================================================================

if st.session_state.current_session is None:
    # Welcome message
    st.info("👈 Select a session from the sidebar to begin analysis")

else:
    # Session loaded - show comparison controls
    st.markdown(f"## {st.session_state.current_gp_name} | {st.session_state.current_session_type}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Driver 1 (Blue)")
        driver1_display = st.selectbox(
            "Select Driver 1",
            [d['display'] for d in st.session_state.current_drivers],
            key="driver1"
        )
        driver1_abbr = next(d['abbreviation'] for d in st.session_state.current_drivers 
                           if d['display'] == driver1_display)
    
    with col2:
        st.markdown("### Driver 2 (Red)")
        driver2_display = st.selectbox(
            "Select Driver 2",
            [d['display'] for d in st.session_state.current_drivers],
            key="driver2",
            index=1 if len(st.session_state.current_drivers) > 1 else 0
        )
        driver2_abbr = next(d['abbreviation'] for d in st.session_state.current_drivers 
                           if d['display'] == driver2_display)
    
    st.divider()
    
    # Compare button
    if st.button("⚡ Compare Fastest Laps", key="compare_btn", use_container_width=True):
        with st.spinner("Analyzing telemetry..."):
            try:
                # Set drivers in functionality and perform comparison
                st.session_state.functionality.set_comparison_drivers(driver1_abbr, driver2_abbr)
                comparison = st.session_state.functionality.perform_comparison()
                
                tel1 = comparison['tel1']
                tel2 = comparison['tel2']
                lap1_info = comparison['lap1_info']
                lap2_info = comparison['lap2_info']
                
                # Display lap info
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    st.metric(
                        f"{lap1_info['driver']} Lap Time",
                        f"{lap1_info['lap_time']:.3f}s"
                    )
                
                with metric_col2:
                    gap = abs(lap1_info['lap_time'] - lap2_info['lap_time'])
                    st.metric(
                        "Gap",
                        f"{gap:.3f}s"
                    )
                
                with metric_col3:
                    st.metric(
                        f"{lap2_info['driver']} Lap Time",
                        f"{lap2_info['lap_time']:.3f}s"
                    )
                
                st.divider()
                
                # Create telemetry plots
                fig = make_subplots(
                    rows=3, cols=1,
                    subplot_titles=("SPEED TRACE", "THROTTLE APPLICATION", "BRAKE APPLICATION"),
                    vertical_spacing=0.12,
                    shared_xaxes=True
                )
                
                # Convert distance to km
                distance1_km = tel1['Distance'] / 1000
                distance2_km = tel2['Distance'] / 1000
                
                # Speed
                fig.add_trace(
                    go.Scatter(
                        x=distance1_km,
                        y=tel1['Speed'],
                        name=f"{lap1_info['driver']} L{int(lap1_info['lap_number'])}",
                        line=dict(color=COLORS['primary'], width=2.5),
                        hovertemplate='<b>Distance:</b> %{x:.2f} km<br><b>Speed:</b> %{y:.1f} km/h<extra></extra>'
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=distance2_km,
                        y=tel2['Speed'],
                        name=f"{lap2_info['driver']} L{int(lap2_info['lap_number'])}",
                        line=dict(color=COLORS['danger'], width=2.5),
                        hovertemplate='<b>Distance:</b> %{x:.2f} km<br><b>Speed:</b> %{y:.1f} km/h<extra></extra>'
                    ),
                    row=1, col=1
                )
                
                # Throttle
                fig.add_trace(
                    go.Scatter(
                        x=distance1_km,
                        y=tel1['Throttle'],
                        name=f"{lap1_info['driver']}",
                        line=dict(color=COLORS['primary'], width=2.5),
                        showlegend=False,
                        hovertemplate='<b>Distance:</b> %{x:.2f} km<br><b>Throttle:</b> %{y:.1f}%<extra></extra>'
                    ),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=distance2_km,
                        y=tel2['Throttle'],
                        name=f"{lap2_info['driver']}",
                        line=dict(color=COLORS['danger'], width=2.5),
                        showlegend=False,
                        hovertemplate='<b>Distance:</b> %{x:.2f} km<br><b>Throttle:</b> %{y:.1f}%<extra></extra>'
                    ),
                    row=2, col=1
                )
                
                # Brake
                fig.add_trace(
                    go.Scatter(
                        x=distance1_km,
                        y=tel1['Brake'] * 100,
                        name=f"{lap1_info['driver']}",
                        line=dict(color=COLORS['primary'], width=2.5),
                        showlegend=False,
                        hovertemplate='<b>Distance:</b> %{x:.2f} km<br><b>Brake:</b> %{y:.1f}%<extra></extra>'
                    ),
                    row=3, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=distance2_km,
                        y=tel2['Brake'] * 100,
                        name=f"{lap2_info['driver']}",
                        line=dict(color=COLORS['danger'], width=2.5),
                        showlegend=False,
                        hovertemplate='<b>Distance:</b> %{x:.2f} km<br><b>Brake:</b> %{y:.1f}%<extra></extra>'
                    ),
                    row=3, col=1
                )
                
                # Update Y axes
                fig.update_yaxes(title_text="Speed (km/h)", row=1, col=1, range=[50, 350])
                fig.update_yaxes(title_text="Throttle (%)", row=2, col=1, range=[0, 100])
                fig.update_yaxes(title_text="Brake (%)", row=3, col=1, range=[0, 100])
                fig.update_xaxes(title_text="Track Distance (km)", row=3, col=1)
                
                # Dark theme
                fig.update_layout(
                    title=f"TELEMETRY COMPARISON | {st.session_state.current_gp_name} | {st.session_state.current_session_type}",
                    template=PLOTLY_DARK_CONFIG['template'],
                    hovermode="x unified",
                    paper_bgcolor=COLORS['background'],
                    plot_bgcolor=COLORS['surface'],
                    font=dict(color=COLORS['text_primary'], size=11),
                    height=900,
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="right",
                        x=0.99,
                        bgcolor=f"rgba(22, 27, 34, 0.8)"
                    )
                )
                
                # Update grid
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=COLORS['border'])
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLORS['border'])
                
                st.plotly_chart(fig, use_container_width=True, key="telemetry_plot")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #8b949e; font-size: 12px; margin-top: 20px;'>
    Powered by Lurby | Data from official F1 sources | © 2026
</div>
""", unsafe_allow_html=True)
