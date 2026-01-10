"""
Constants, configuration, and styling for F1 Analytics
"""

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================
DEFAULT_CACHE_DIR = './fastf1_cache'
DEFAULT_SEASONS = [2022, 2023, 2024, 2025]

# ============================================================================
# STYLING - GITHUB DARK THEME
# ============================================================================
COLORS = {
    'primary': '#58a6ff',      # Blue accent
    'danger': '#f85149',       # Red accent
    'success': '#238636',      # Green
    'background': '#0d1117',   # Main dark background
    'surface': '#161b22',      # Secondary surface
    'border': '#30363d',       # Border color
    'text_primary': '#c9d1d9', # Main text
    'text_secondary': '#8b949e',  # Secondary text
}

# Streamlit CSS
STREAMLIT_DARK_THEME = """
<style>
    /* Main container dark theme */
    .stMainBlockContainer {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
    }
    
    /* Text colors */
    body {
        color: #c9d1d9;
        background-color: #0d1117;
    }
    
    /* Heading colors */
    h1, h2, h3, h4, h5, h6 {
        color: #58a6ff;
    }
    
    /* Selectbox and inputs */
    [data-baseweb="select"] {
        background-color: #161b22;
    }
    
    [data-testid="stSelectbox"] > div {
        background-color: #161b22;
    }
    
    /* Button */
    button {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        border: 1px solid #30363d;
    }
    
    button:hover {
        background-color: #2ea043;
    }
    
    /* Input fields */
    input {
        background-color: #0d1117;
        color: #c9d1d9;
        border: 1px solid #30363d;
    }
    
    /* Info boxes */
    [data-testid="stInfoBox"] {
        background-color: #161b22;
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #161b22;
        border-radius: 8px;
        padding: 15px;
    }
</style>
"""

# Plotly dark theme configuration
PLOTLY_DARK_CONFIG = {
    'template': 'plotly_dark',
    'paper_bgcolor': COLORS['background'],
    'plot_bgcolor': COLORS['surface'],
    'font': {
        'color': COLORS['text_primary'],
        'size': 11
    },
    'grid_color': COLORS['border'],
}

# ============================================================================
# DRIVER DISPLAY CONFIGURATION
# ============================================================================
DRIVER_COLORS = {
    'primary': COLORS['primary'],    # Driver 1 - Blue
    'secondary': COLORS['danger'],   # Driver 2 - Red
}

# ============================================================================
# TELEMETRY DATA COLUMNS
# ============================================================================
TELEMETRY_COLUMNS = ['Speed', 'Throttle', 'Brake', 'Gear', 'DRS', 'Distance']
COMPARISON_METRICS = {
    'Speed': {'unit': 'km/h', 'range': (50, 350)},
    'Throttle': {'unit': '%', 'range': (0, 100)},
    'Brake': {'unit': '%', 'range': (0, 100)},
}
