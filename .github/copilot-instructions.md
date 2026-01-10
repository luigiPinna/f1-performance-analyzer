# F1 Performance Analyzer - AI Coding Instructions

## Architecture Overview

This is a **PyQt5 desktop application** for Formula 1 telemetry analysis using a **plugin-based functionality system**. The app loads F1 race data via FastF1 library and displays telemetry comparisons.

### Component Map
- **[main.py](main.py)**: Entry point - creates QApplication and MainWindow
- **[src/canvas.py](src/canvas.py)**: Main UI window (`MainWindow`) and telemetry visualization (`TelemetryCanvas`)
- **[src/workers.py](src/workers.py)**: Background QThread workers for non-blocking data loading
- **[src/functionalities/base.py](src/functionalities/base.py)**: `BaseFunctionality` abstract class for plugin architecture
- **[src/functionalities/fastest_lap_comparison.py](src/functionalities/fastest_lap_comparison.py)**: Concrete analysis module (currently only implemented functionality)

### Data Flow
1. **Initialization**: `MainWindow` spawns `CalendarLoaderThread` to fetch F1 calendar (2022-2025)
2. **GP Selection**: User selects year → GP → session type (Qualifying/Race)
3. **Session Load**: `SessionLoaderThread` loads session data and extracts available drivers
4. **Comparison**: `FastestLapComparisonThread` finds fastest laps for two drivers, loads telemetry, emits signal
5. **Visualization**: `TelemetryCanvas` plots Speed, Throttle, Brake traces side-by-side in matplotlib

### Cache Strategy
FastF1 data cached in `./fastf1_cache/{year}/{race}/` as `.ff1pkl` files. Subsequent runs use cache, dramatically improving performance.

## Critical Workflows

### Adding New Analysis Functionalities
1. Create `src/functionalities/my_feature.py` extending `BaseFunctionality`
2. Implement `get_name()` returning display string
3. `init_ui()` creates control panel; use signals to trigger analysis
4. Spawn worker thread from `src/workers.py` for heavy operations
5. Register in **[canvas.py#L254](src/canvas.py#L254)** (`on_functionality_changed` method) and combo box

### UI Styling Pattern
Dark GitHub theme applied globally in `MainWindow.setStyleSheet()`:
- **Background**: `#0d1117` (main), `#161b22` (panels)
- **Accents**: `#58a6ff` (blue), `#f85149` (red - secondary driver)
- **QComboBox/QPushButton**: Custom styles with hover/pressed states
- Matplotlib figures use `plt.style.use('dark_background')` with custom axis colors (`#161b22`, `#30363d`)

### Worker Thread Pattern
All data loading happens in `QThread` subclasses:
- Inherit from `QThread`, define `finished` and `error` signals
- Implement `run()` method with try/except
- Connect signals in main thread before `thread.start()`
- Example: [FastestLapComparisonThread](src/workers.py#L112) emits `finished(tel1, tel2, lap1_info, lap2_info)`

## Project Conventions

### Signal/Slot Naming
- Signal: `finished`, `error`, `progress` - follow QThread conventions
- Connect with `.connect(slot_method)` before thread start
- Always emit in try/except to avoid thread crashes

### Error Handling
- Errors bubble through signal emission: `self.error.emit(f"message")`
- `MainWindow.on_error()` displays `QMessageBox.critical()`
- No silent failures; every user-facing operation reports status

### FastF1 API Patterns
- `fastf1.get_session(year, gp_name, session_type)` → loads session
- `session.laps.pick_drivers(abbr)` → filter by 3-letter abbreviation
- `lap.pick_fastest()` → single fastest lap per driver
- `lap.get_car_data().add_distance()` → telemetry dataframe with Distance column
- Lap times are `Timedelta` objects; convert with `.total_seconds()`

### DataFrame Access (Pandas)
- Check validity: `pd.notna(value)` before access
- Access columns: `df['ColumnName']`, not dot notation
- Series operations: `series.notna().any()` to check for valid data

## Testing & Development

### Running the App
```bash
python main.py
```
- Initial run loads and caches 4 years of race calendars (~30s)
- Subsequent runs instant (cache hit)
- Session loads may take 5-10s per session (first time)

### Debugging Tips
- Matplotlib error? Check axis facecolor matches figure facecolor (`#161b22`)
- FastF1 cache issues? Delete `fastf1_cache/` and restart
- UI freezes? Worker thread not spawned (check `thread.start()` called)
- Driver not found? Session data incomplete; verify abbreviation matches FastF1 convention (e.g., "HAM", "VER")

## Key Files & Patterns

| File | Purpose | Key Pattern |
|------|---------|-------------|
| [src/functionalities/fastest_lap_comparison.py](src/functionalities/fastest_lap_comparison.py) | User-facing UI for comparison | Drives functionality UI + signals to workers |
| [src/workers.py](src/workers.py) | Non-blocking data operations | Thread workers emit signals with results |
| [src/canvas.py](src/canvas.py) | Window layout + visualization | Matplotlib canvas integration in PyQt5 |
| [requirements.txt](requirements.txt) | Dependencies | FastF1 3.7.0, PyQt5, Matplotlib 3.10.7 |

## Common Tasks

**Add telemetry metric**: Extend `plot_comparison()` in [TelemetryCanvas](src/canvas.py#L45) - add subplot for new data column

**Add session filter**: Modify `SessionLoaderThread` to filter drivers by criteria (grid position, status, etc.)

**Optimize cache loading**: FastF1 cache path set in workers - adjust `cache_dir` path or enable compression if needed

---

*Last updated: January 8, 2026 | Architecture: PyQt5 + FastF1 | Current Feature: Fastest Lap Comparison*
