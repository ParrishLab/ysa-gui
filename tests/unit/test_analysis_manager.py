"""Unit tests for AnalysisManager class."""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.managers.analysis_manager import AnalysisManager


@pytest.mark.unit
class TestAnalysisManager:
    """Test cases for AnalysisManager."""

    @pytest.fixture
    def analysis_manager(self, mock_main_window):
        """Create AnalysisManager instance for testing."""
        return AnalysisManager(mock_main_window)

    def test_init(self, analysis_manager, mock_main_window):
        """Test AnalysisManager initialization."""
        assert analysis_manager.main_window is mock_main_window

    def test_setup_analysis_thread(self, analysis_manager, mock_main_window):
        """Test analysis thread setup."""
        # Mock the loading dialog and analysis thread creation
        mock_loading_dialog = Mock()
        mock_analysis_thread = Mock()

        # Mock the imports within the method
        with patch('src.widgets.LoadingDialog.LoadingDialog', return_value=mock_loading_dialog) as mock_dialog_class, \
             patch('src.managers.analysis_manager.AnalysisThread', return_value=mock_analysis_thread) as mock_thread_class:

            analysis_manager.setup_analysis_thread()

            # Verify dialog was created and assigned
            mock_dialog_class.assert_called_once_with(mock_main_window)
            assert mock_main_window.loading_dialog is mock_loading_dialog
            mock_loading_dialog.analysis_cancelled.connect.assert_called_once()

            # Verify thread was created and assigned
            mock_thread_class.assert_called_once_with(mock_main_window)
            assert mock_main_window.analysis_thread is mock_analysis_thread
            mock_analysis_thread.progress_updated.connect.assert_called_once()
            mock_analysis_thread.analysis_completed.connect.assert_called_once()

    def test_on_analysis_completed_cpp_mode(self, analysis_manager, mock_main_window):
        """Test analysis completion in C++ mode."""
        mock_main_window.use_cpp = True

        # Set up proper data structure for the channels
        mock_main_window.data = np.zeros((64, 64), dtype=object)
        mock_main_window.data[0, 0] = {
            "signal": np.random.randn(1000).astype(np.float32),
            "SzTimes": np.array([[5.0, 10.0, 1.0]]),  # seizure times
            "SETimes": np.array([[30.0, 35.0, 2.0]]),  # SE times
        }  # For (1,1)
        mock_main_window.data[0, 1] = {
            "signal": np.random.randn(1000).astype(np.float32),
            "SzTimes": np.array([[15.0, 20.0, 1.5]]),  # seizure times
            "SETimes": np.array([]),  # Empty SE times
        }  # For (1,2)

        mock_main_window.recording_length = 60.0
        mock_main_window.sampling_rate = 100

        # Mock analysis_thread attributes that get copied over
        mock_main_window.analysis_thread = Mock()
        mock_main_window.analysis_thread.recording_length = 60.0
        mock_main_window.analysis_thread.sampling_rate = 100  # Real integer for math
        mock_main_window.analysis_thread.time_vector = np.linspace(0, 60, 6000)
        mock_main_window.analysis_thread.active_channels = [(1, 1), (1, 2)]  # Real list for iteration
        mock_main_window.analysis_thread.data = mock_main_window.data
        mock_main_window.analysis_thread.min_strength = 0.1
        mock_main_window.analysis_thread.max_strength = 1.0

        # Mock required UI components (active_channels needs to be iterable)
        mock_main_window.active_channels = [(1, 1), (1, 2)]  # This is already a real list
        mock_main_window.ui_manager.progress_bar.setRange = Mock()
        mock_main_window.ui_manager.speed_combo = Mock()
        mock_main_window.db_scan_settings_widget = Mock()
        mock_main_window.cluster_tracker = Mock()
        mock_main_window.loading_dialog = Mock()
        mock_main_window.n_std_dev = 4
        mock_main_window.peak_settings_widget = Mock()
        mock_main_window.grid_widget = Mock()
        # Create a 2D array for cells that can be subscripted
        mock_main_window.grid_widget.cells = [[Mock() for _ in range(64)] for _ in range(64)]
        mock_main_window.data_manager = Mock()
        mock_main_window.second_plot_widget = Mock()
        mock_main_window.graph_widget = Mock()

        with patch('src.widgets.RasterPlot.RasterPlot'), \
             patch('src.widgets.DischargeStartDialog.DischargeStartDialog'):
            analysis_manager.on_analysis_completed()

        # Verify data manager methods were called
        mock_main_window.data_manager.create_grid.assert_called_once()
        mock_main_window.update_grid.assert_called_once_with(first=True)

    def test_cancel_analysis(self, analysis_manager, mock_main_window):
        """Test analysis cancellation."""
        mock_thread = Mock()
        mock_main_window.analysis_thread = mock_thread
        mock_main_window.loading_dialog = Mock()

        analysis_manager.cancel_analysis()

        mock_thread.requestInterruption.assert_called_once()
        mock_main_window.loading_dialog.hide.assert_called_once()

    def test_find_discharges(self, analysis_manager, mock_main_window):
        """Test discharge finding initialization."""
        mock_main_window.custom_region = (10.0, 20.0)
        mock_main_window.sampling_rate = 100
        mock_main_window.active_channels = [(1, 1), (1, 2)]

        # Mock grid_widget and lasso selected cells
        mock_cell = Mock()
        mock_cell.row = 0
        mock_cell.col = 0
        mock_main_window.grid_widget.get_lasso_selected_cells.return_value = [mock_cell]

        # Mock other required attributes
        mock_main_window.data = Mock()
        mock_main_window.signal_analyzer = Mock()

        with patch('src.managers.analysis_manager.DischargeFinderThread') as mock_thread_class:
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread

            analysis_manager.find_discharges()

            mock_thread_class.assert_called_once()
            mock_thread.start.assert_called_once()

    def test_auto_analyze_start(self, analysis_manager, mock_main_window):
        """Test starting auto analysis."""
        mock_main_window.is_auto_analyzing = False
        mock_main_window.custom_region = (10.0, 20.0)

        # Mock plotted channels with proper attributes
        mock_channel = Mock()
        mock_channel.row = 1
        mock_channel.col = 1
        mock_main_window.plotted_channels = [mock_channel]

        mock_main_window.active_discharges = [
            {'time': 10.0, 'channels': [(1, 1)]},
            {'time': 20.0, 'channels': [(1, 2)]}
        ]

        # Mock required UI components
        mock_main_window.togglePropLinesAction = Mock()
        mock_main_window.cluster_tracker = Mock()
        mock_main_window.cluster_tracker.seizures = Mock()
        mock_main_window.cluster_tracker.seizure_graphics_items = Mock()

        # Mock discharges as a subscriptable object (dict or array)
        mock_main_window.discharges = {(1, 1): ([10.0, 15.0, 18.0], [1.0, 1.2, 0.8])}

        analysis_manager.auto_analyze()

        assert mock_main_window.is_auto_analyzing is True
        assert mock_main_window.current_discharge_index == 0

    def test_auto_analyze_stop(self, analysis_manager, mock_main_window):
        """Test auto analysis with no discharges in region (should not start)."""
        mock_main_window.is_auto_analyzing = False
        mock_main_window.custom_region = (50.0, 60.0)  # Region with no discharges

        # Mock plotted channels with proper attributes
        mock_channel = Mock()
        mock_channel.row = 1
        mock_channel.col = 1
        mock_main_window.plotted_channels = [mock_channel]

        # Mock discharges outside the region
        mock_main_window.discharges = {(1, 1): ([10.0, 15.0], [1.0, 1.2])}
        mock_main_window.togglePropLinesAction = Mock()

        analysis_manager.auto_analyze()

        # Should remain False since no discharges in region
        assert mock_main_window.is_auto_analyzing is False

    def test_analyze_next_discharge_valid(self, analysis_manager, mock_main_window):
        """Test analyzing next discharge with valid index."""
        mock_main_window.is_auto_analyzing = True
        mock_main_window.current_discharge_index = 0
        mock_main_window.discharges_to_analyze = [10.0, 20.0]  # Use this instead of active_discharges
        mock_main_window.sampling_rate = 100
        mock_main_window.ui_manager.progress_bar = Mock()

        with patch('src.managers.analysis_manager.QTimer') as mock_timer:
            analysis_manager.analyze_next_discharge()

            # Verify progress bar was updated (actual value is 990, so let's check for that)
            expected_value = int(10.0 * 100) - int(0.1 * 100)  # 1000 - 10 = 990
            mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(expected_value)

            # Verify timer was started
            mock_timer.singleShot.assert_called()

    def test_analyze_next_discharge_end_of_list(self, analysis_manager, mock_main_window):
        """Test analyzing when at end of discharge list."""
        mock_main_window.is_auto_analyzing = True
        mock_main_window.current_discharge_index = 5
        mock_main_window.discharges_to_analyze = [10.0]  # Index 5 > length, so should stop

        # Mock cluster_tracker properly for the save call
        mock_main_window.cluster_tracker = Mock()
        mock_main_window.active_channels = [(1, 1), (1, 2)]  # Make this iterable
        mock_main_window.custom_region = (0, 10, 20, 30)  # Make this iterable for * operator

        analysis_manager.analyze_next_discharge()

        # Should reset analysis state
        assert mock_main_window.is_auto_analyzing is False

    @patch('src.managers.analysis_manager.QDialog')
    @patch('src.managers.analysis_manager.QVBoxLayout')
    @patch('src.managers.analysis_manager.QHBoxLayout')
    @patch('src.widgets.RasterPlot.RasterPlot')
    def test_edit_raster_settings(self, mock_raster_plot, mock_hlayout, mock_vlayout, mock_dialog, analysis_manager, mock_main_window, qapp):
        """Test raster plot creation and dialog setup."""
        mock_main_window.raster_plot = None
        mock_main_window.data = np.zeros((64, 64), dtype=object)
        mock_main_window.sampling_rate = 100
        mock_main_window.active_channels = [(1, 1), (1, 2)]
        mock_main_window.raster_downsample_factor = 2

        mock_plot_instance = Mock()
        mock_plot_instance.spike_threshold = 0.5
        mock_raster_plot.return_value = mock_plot_instance

        mock_dialog_instance = Mock()
        mock_dialog.return_value = mock_dialog_instance

        analysis_manager.edit_raster_settings()

        # Verify raster plot was created
        mock_raster_plot.assert_called_once_with(
            mock_main_window.data,
            mock_main_window.sampling_rate,
            mock_main_window.active_channels,
            mock_main_window.raster_downsample_factor
        )
        assert mock_main_window.raster_plot is mock_plot_instance

        # Verify dialog was created
        mock_dialog.assert_called_once_with(mock_main_window)


@pytest.mark.unit
class TestAnalysisManagerStateMachine:
    """Test the state machine behavior of AnalysisManager."""

    @pytest.fixture
    def analysis_manager(self, mock_main_window):
        """Create AnalysisManager with state tracking."""
        manager = AnalysisManager(mock_main_window)
        mock_main_window.is_auto_analyzing = False
        mock_main_window.current_discharge_index = 0
        return manager

    def test_auto_analyze_state_transitions(self, analysis_manager, mock_main_window):
        """Test state transitions during auto analysis."""
        # Setup required attributes
        mock_main_window.custom_region = (10.0, 20.0)
        mock_channel = Mock()
        mock_channel.row = 1
        mock_channel.col = 1
        mock_main_window.plotted_channels = [mock_channel]

        # Setup discharge data
        mock_main_window.active_discharges = [
            {'time': 10.0, 'channels': [(1, 1)]},
            {'time': 20.0, 'channels': [(1, 2)]}
        ]

        # Mock required UI components
        mock_main_window.togglePropLinesAction = Mock()
        mock_main_window.cluster_tracker = Mock()
        mock_main_window.cluster_tracker.seizures = Mock()
        mock_main_window.cluster_tracker.seizure_graphics_items = Mock()

        # Mock discharges as a subscriptable object
        mock_main_window.discharges = {(1, 1): ([10.0, 15.0, 20.0], [1.0, 1.2, 0.8])}

        # Initialize the analysis state
        mock_main_window.is_auto_analyzing = False

        # Start analysis
        assert not mock_main_window.is_auto_analyzing
        analysis_manager.auto_analyze()
        assert mock_main_window.is_auto_analyzing

        # Stop analysis
        analysis_manager.auto_analyze()
        assert not mock_main_window.is_auto_analyzing

    def test_discharge_index_progression(self, analysis_manager, mock_main_window):
        """Test discharge index progression during analysis."""
        mock_main_window.is_auto_analyzing = True
        mock_main_window.current_discharge_index = 0  # Initialize the index
        mock_main_window.discharges_to_analyze = [10.0, 20.0, 30.0]
        mock_main_window.sampling_rate = 100
        mock_main_window.ui_manager.progress_bar = Mock()
        mock_main_window.time_vector = [0] * 6000  # Mock time vector with proper length
        mock_main_window.lock_to_playhead = False
        mock_main_window.is_analyzing_channel_discharge = False  # Not analyzing, so index increments

        # Mock required methods
        mock_main_window.update_grid = Mock()
        mock_main_window.playback_manager = Mock()

        # Calculate expected end_index for first discharge (10.0 seconds)
        # end_index = min(len(time_vector)-1, discharge_index + int(0.15 * sampling_rate))
        # discharge_index = 10.0 * 100 = 1000
        # end_index = min(5999, 1000 + 15) = 1015
        expected_end_index = 1015
        mock_main_window.ui_manager.progress_bar.value.return_value = expected_end_index

        with patch('src.managers.analysis_manager.QTimer') as mock_timer:
            # Make the timer execute the callback immediately
            def execute_immediately(delay, callback):
                if callable(callback):
                    callback()
            mock_timer.singleShot.side_effect = execute_immediately

            # Analyze first discharge
            assert mock_main_window.current_discharge_index == 0
            analysis_manager.analyze_next_discharge()

            # Index should increment after the analysis completes
            assert mock_main_window.current_discharge_index == 1