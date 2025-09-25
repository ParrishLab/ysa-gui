# YSA GUI Test Suite

This directory contains comprehensive tests for the YSA GUI application.

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures and test configuration
├── unit/                 # Unit tests for individual components
│   ├── test_data_manager.py
│   ├── test_analysis_manager.py
│   ├── test_event_handler.py
│   ├── test_playback_manager.py
│   ├── test_visualization_manager.py
│   └── test_ui_manager.py
├── integration/          # Integration tests for component interactions
│   ├── test_grid_widget.py
│   ├── test_graph_widget.py
│   └── test_main_window.py
└── README.md            # This file
```

## Test Categories

### Unit Tests
- **Purpose**: Test individual classes and methods in isolation
- **Scope**: Single components with mocked dependencies
- **Location**: `tests/unit/`
- **Markers**: `@pytest.mark.unit`

### Integration Tests
- **Purpose**: Test component interactions and UI functionality
- **Scope**: Multiple components working together
- **Location**: `tests/integration/`
- **Markers**: `@pytest.mark.integration`

## Running Tests

### Quick Start
```bash
# Run all tests
python run_tests.py --all

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run with coverage
python run_tests.py --all --coverage
```

### Using pytest directly
```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit/ -m unit
pytest tests/integration/ -m integration

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_data_manager.py -v
```

### Test Markers

Use markers to control which tests run:

- `unit`: Unit tests
- `integration`: Integration tests
- `slow`: Tests that take longer than 5 seconds
- `gui`: Tests requiring display/GUI components
- `matlab`: Tests requiring MATLAB engine
- `performance`: Performance-related tests
- `smoke`: Basic functionality tests

Examples:
```bash
# Skip slow tests
pytest -m "not slow"

# Run only GUI tests
pytest -m gui

# Run unit tests but skip MATLAB-dependent ones
pytest -m "unit and not matlab"
```

## Test Configuration

### pytest.ini
Main pytest configuration including:
- Test discovery patterns
- Coverage settings
- Warning filters
- Test markers

### conftest.py
Shared test fixtures including:
- QApplication instance (`qapp`)
- Mock MainWindow (`mock_main_window`)
- Sample test data (`sample_brw_data`, `temp_hdf5_file`)
- Mock MATLAB engine (`mock_matlab_engine`)

### Environment Setup
Tests automatically configure:
- Headless Qt environment (`QT_QPA_PLATFORM=offscreen`)
- Python path for imports
- Mock data and dependencies

## Writing New Tests

### Unit Test Example
```python
@pytest.mark.unit
class TestMyComponent:
    """Test cases for MyComponent."""

    @pytest.fixture
    def my_component(self, mock_main_window):
        """Create MyComponent instance for testing."""
        return MyComponent(mock_main_window)

    def test_initialization(self, my_component):
        """Test component initialization."""
        assert my_component is not None

    def test_method_behavior(self, my_component):
        """Test specific method behavior."""
        result = my_component.some_method()
        assert result is not None
```

### Integration Test Example
```python
@pytest.mark.integration
class TestMyWidgetIntegration:
    """Integration tests for MyWidget."""

    @pytest.fixture
    def my_widget(self, qapp, mock_main_window):
        """Create MyWidget for integration testing."""
        return MyWidget(mock_main_window)

    def test_widget_creation(self, my_widget):
        """Test widget creation and properties."""
        assert my_widget.isVisible() is False
```

## CI/CD Integration

Tests run automatically on:
- **Push**: to main and develop branches
- **Pull Requests**: to main and develop branches
- **Releases**: full test suite before building artifacts

### GitHub Actions Workflows

1. **test.yml**: Main testing workflow
   - Runs on multiple OS (Ubuntu, Windows, macOS)
   - Tests Python 3.9, 3.10, 3.11
   - Includes linting, type checking, and security scans

2. **release.yml**: Release workflow
   - Runs full test suite before release
   - Builds executables for multiple platforms
   - Creates GitHub releases with artifacts

## Coverage Requirements

- **Minimum Coverage**: 75%
- **Reports**: HTML, XML, and terminal output
- **Exclusions**: Test files, external dependencies

## Troubleshooting

### Common Issues

1. **Qt GUI Tests Failing**
   ```bash
   export QT_QPA_PLATFORM=offscreen
   pytest tests/integration/
   ```

2. **Import Errors**
   ```bash
   export PYTHONPATH=src:$PYTHONPATH
   pytest
   ```

3. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt -r requirements-test.txt
   ```

4. **Headless Display Issues (Linux)**
   ```bash
   sudo apt-get install xvfb
   xvfb-run -a pytest tests/
   ```

### Debug Mode
```bash
# Run with debug output
pytest -v -s --tb=long

# Drop into debugger on failure
pytest --pdb

# Run single test with maximum verbosity
pytest tests/unit/test_data_manager.py::TestDataManager::test_init -vvv
```

## Performance Considerations

- Tests use mocked dependencies to avoid external services
- Large data fixtures are generated programmatically
- GUI tests run in headless mode for speed
- Slow tests are marked and can be skipped in CI

## Contributing

When adding new features:

1. Write unit tests for new classes/methods
2. Add integration tests for UI components
3. Update fixtures in `conftest.py` if needed
4. Mark tests appropriately (`@pytest.mark.unit`, etc.)
5. Ensure tests pass locally before submitting PR