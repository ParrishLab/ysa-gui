"""Shared pytest fixtures for YSA GUI tests."""
import os
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up environment for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['DISPLAY'] = ':99'

import numpy as np
import h5py
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def mock_main_window():
    """Create a mock MainWindow for testing."""
    with patch('src.main.MainWindow') as mock_window:
        mock_instance = Mock()
        mock_window.return_value = mock_instance

        # Common attributes
        mock_instance.file_path = "/test/path/file.brw"
        mock_instance.sampling_rate = 100
        mock_instance.recording_length = 60.0
        mock_instance.active_channels = [(1, 1), (1, 2), (2, 1), (2, 2)]
        mock_instance.data = np.zeros((64, 64), dtype=object)
        mock_instance.time_vector = np.linspace(0, 60, 6000)

        # UI components
        mock_instance.grid_widget = Mock()
        mock_instance.graph_widget = Mock()
        # Create properly mocked plot widgets
        mock_plot_widget1 = Mock()
        mock_plot_widget2 = Mock()

        # Setup the chain: plot_widget -> getPlotItem() -> getViewBox() -> viewRange()
        mock_plot_widget1.getPlotItem().getViewBox().viewRange.return_value = [[0, 10], [0, 1]]
        mock_plot_widget2.getPlotItem().getViewBox().viewRange.return_value = [[0, 10], [0, 1]]

        mock_instance.graph_widget.plot_widgets = [mock_plot_widget1, mock_plot_widget2]
        mock_instance.legend_widget = Mock()

        # Managers
        mock_instance.data_manager = Mock()
        mock_instance.analysis_manager = Mock()
        mock_instance.ui_manager = Mock()
        mock_instance.ui_manager.progress_bar.maximum.return_value = 6000  # Set a real max value
        mock_instance.event_handler = Mock()
        mock_instance.playback_manager = Mock()
        mock_instance.visualization_manager = Mock()

        yield mock_instance


@pytest.fixture
def sample_brw_data():
    """Create sample BRW-like data for testing."""
    return {
        'signal': np.random.randn(6000).astype(np.float32),
        'SzTimes': np.array([[5.0, 10.0, 1.0], [20.0, 25.0, 1.5]]),
        'SETimes': np.array([[30.0, 35.0, 2.0]]),
        'DischargeTimes': np.array([1.0, 2.0, 3.0, 4.0])
    }


@pytest.fixture
def temp_hdf5_file(tmp_path, sample_brw_data):
    """Create a temporary HDF5 file with test data."""
    file_path = tmp_path / "test_data.brw"

    with h5py.File(file_path, 'w') as f:
        # Create basic structure
        rec_info = f.create_group("3BRecInfo")
        rec_vars = rec_info.create_group("3BRecVars")

        rec_vars.create_dataset("NRecFrames", data=6000)
        rec_vars.create_dataset("SamplingRate", data=100.0)

        # Create channel info
        streams = rec_info.create_group("3BMeaStreams")
        raw = streams.create_group("Raw")
        chs = raw.create_group("Chs")

        # Sample channels
        rows = [1, 1, 2, 2]
        cols = [1, 2, 1, 2]
        chs.create_dataset("Row", data=rows)
        chs.create_dataset("Col", data=cols)

        # Add some test data
        data_group = f.create_group("Data")
        for i, (row, col) in enumerate(zip(rows, cols)):
            ch_data = data_group.create_group(f"Ch_{row}_{col}")
            ch_data.create_dataset("signal", data=sample_brw_data['signal'])

    return str(file_path)


@pytest.fixture
def mock_matlab_engine():
    """Create a mock MATLAB engine."""
    with patch('src.threads.MatlabEngineThread.matlab.engine') as mock_engine:
        mock_eng = Mock()
        mock_engine.start_matlab.return_value = mock_eng

        # Mock common MATLAB functions
        mock_eng.sz_se_detect.return_value = (
            np.array([[5.0, 10.0]]),  # seizure times
            np.array([[30.0, 35.0]]),  # SE times
            np.array([1.0, 2.0, 3.0])  # discharge times
        )

        yield mock_eng


@pytest.fixture
def mock_pyqtgraph():
    """Mock pyqtgraph components."""
    with patch('src.main.pg') as mock_pg:
        mock_pg.setConfigOptions = Mock()
        mock_pg.mkPen = Mock(return_value=Mock())
        mock_pg.PlotWidget = Mock
        mock_pg.InfiniteLine = Mock
        yield mock_pg


@pytest.fixture
def disable_gui_updates():
    """Disable GUI updates during testing."""
    with patch('PyQt5.QtCore.QTimer.start'), \
         patch('PyQt5.QtWidgets.QWidget.update'), \
         patch('PyQt5.QtWidgets.QWidget.repaint'):
        yield


@pytest.fixture
def sample_analysis_results():
    """Create sample analysis results."""
    return {
        'seizure_times': np.array([[5.0, 10.0, 1.0], [20.0, 25.0, 1.5]]),
        'se_times': np.array([[30.0, 35.0, 2.0]]),
        'discharge_times': np.array([1.0, 2.0, 3.0, 4.0]),
        'peak_thresholds': {(1, 1): 0.5, (1, 2): 0.6}
    }


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment before each test."""
    # Basic environment setup
    yield

    # Basic cleanup after test - QTimer cleanup is handled by Qt automatically