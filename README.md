# F1 Performance Analyzer

Desktop application for Formula 1 telemetry analysis with modular functionality system.

## Features

**Current Functionalities:**
- **Fastest Lap Comparison**: Compare telemetry data (speed, throttle, brake) between two drivers' fastest laps

**Planned Functionalities:**
- Sector Analysis
- Race Progression
- Tyre Strategy Analysis
- Gap Analysis

## Architecture

The application uses a modular plugin-based architecture allowing easy addition of new analysis functionalities.

```
f1-performance-analyzer/
├── main.py                          # Entry point
├── canvas.py                        # Main window and visualization
├── workers.py                       # Async data loading threads
└── functionalities/                 # Analysis modules
    ├── base.py                      # Base class
    └── fastest_lap_comparison.py   # Fastest lap analysis
```

## Requirements

- Python 3.8+
- PyQt5
- FastF1
- Matplotlib
- Pandas

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python main.py
```

### Fastest Lap Comparison

1. Select functionality: "Fastest Lap Comparison"
2. Choose year (2022-2025)
3. Select Grand Prix
4. Pick session type (Qualifying or Race)
5. Select two drivers to compare
6. Click "COMPARE FASTEST LAPS"

The application automatically finds each driver's fastest lap and displays detailed telemetry comparison.

## Data Source

This application uses the FastF1 library to fetch official Formula 1 timing data. First run will be slower due to data caching.

## Cache

FastF1 data is cached locally in `./fastf1_cache` directory to improve performance on subsequent runs.

## Adding New Functionalities

To add a new analysis functionality:

1. Create new file in `functionalities/` directory
2. Extend `BaseFunctionality` class
3. Implement required methods
4. Register in `canvas.py` functionality selector

## License

MIT