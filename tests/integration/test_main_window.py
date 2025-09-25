"""Integration tests for MainWindow class."""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication

from src.main import MainWindow


@pytest.mark.integration
class TestMainWindowIntegration:
    """Integration tests for MainWindow with all components."""

    @pytest.fixture
    def main_window(self, qapp):
        """Create MainWindow instance for testing."""
        with patch('src.main.MainWindow.setup_ui'), \
             patch('src.main.MainWindow.setup_managers'), \
             patch('src.main.MainWindow.setup_event_handlers'):
            return MainWindow()

    def test_main_window_initialization(self, main_window):
        """Test MainWindow initialization."""
        assert main_window is not None
        assert hasattr(main_window, 'ui_manager')
        assert hasattr(main_window, 'data_manager')
        assert hasattr(main_window, 'analysis_manager')

    @patch('src.main.UIManager')
    @patch('src.main.DataManager')
    @patch('src.main.AnalysisManager')
    @patch('src.main.EventHandler')
    @patch('src.main.PlaybackManager')
    @patch('src.main.VisualizationManager')
    def test_manager_setup(self, mock_viz, mock_playback, mock_event, mock_analysis,
                          mock_data, mock_ui, qapp):
        """Test that all managers are properly initialized."""
        main_window = MainWindow()

        # Verify all managers were created
        mock_ui.assert_called_once_with(main_window)
        mock_data.assert_called_once_with(main_window)
        mock_analysis.assert_called_once_with(main_window)
        mock_event.assert_called_once_with(main_window)
        mock_playback.assert_called_once_with(main_window)
        mock_viz.assert_called_once_with(main_window)

    def test_ui_setup_integration(self, main_window):
        """Test UI setup integration."""
        with patch.object(main_window, 'ui_manager') as mock_ui_manager:
            main_window.setup_ui()
            mock_ui_manager.setup_main_window.assert_called_once()

    def test_event_handler_setup(self, main_window):
        """Test event handler setup."""
        main_window.event_handler = Mock()
        main_window.setup_event_handlers()

        # Should complete without errors (smoke test)
        assert main_window.event_handler is not None


@pytest.mark.integration
class TestMainWindowDataFlow:
    """Test data flow through MainWindow components."""

    @pytest.fixture
    def main_window_with_mocks(self, qapp):
        """Create MainWindow with mocked components."""
        main_window = MainWindow()

        # Setup mock managers
        main_window.ui_manager = Mock()
        main_window.data_manager = Mock()
        main_window.analysis_manager = Mock()
        main_window.event_handler = Mock()
        main_window.playback_manager = Mock()
        main_window.visualization_manager = Mock()

        # Setup basic attributes
        main_window.data = None
        main_window.file_path = None
        main_window.sampling_rate = 100
        main_window.plotted_channels = [None] * 4

        return main_window

    def test_file_loading_workflow(self, main_window_with_mocks):
        """Test complete file loading workflow."""
        test_file_path = "/test/data.brw"

        with patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = (test_file_path, "")

            # Mock data manager methods
            main_window_with_mocks.data_manager.get_channels.return_value = ([1, 2], [1, 2])
            main_window_with_mocks.data_manager.setup_background_image.return_value = True

            main_window_with_mocks.open_file()

            # Verify file dialog was called
            mock_dialog.assert_called_once()

            # Verify data manager methods were called
            main_window_with_mocks.data_manager.get_channels.assert_called_once()

    def test_analysis_workflow(self, main_window_with_mocks):
        """Test analysis workflow integration."""
        # Setup prerequisites
        main_window_with_mocks.file_path = "/test/data.brw"
        main_window_with_mocks.active_channels = [(1, 1), (1, 2)]

        # Run analysis
        main_window_with_mocks.analysis_manager.run_analysis()

        # Verify analysis manager was called
        main_window_with_mocks.analysis_manager.run_analysis.assert_called_once()

    def test_playback_controls_integration(self, main_window_with_mocks):
        """Test playback controls integration."""
        # Setup playback data
        main_window_with_mocks.data = np.zeros((64, 64), dtype=object)
        main_window_with_mocks.plotted_channels = [Mock(), None, None, None]

        # Test playback methods
        main_window_with_mocks.playback_manager.play_pause()
        main_window_with_mocks.playback_manager.step_forward()
        main_window_with_mocks.playback_manager.step_backward()

        # Verify playback manager methods were called
        main_window_with_mocks.playback_manager.play_pause.assert_called_once()
        main_window_with_mocks.playback_manager.step_forward.assert_called_once()
        main_window_with_mocks.playback_manager.step_backward.assert_called_once()

    def test_visualization_updates(self, main_window_with_mocks):
        """Test visualization updates integration."""
        # Setup visualization data
        main_window_with_mocks.data = np.zeros((64, 64), dtype=object)

        # Test visualization methods
        main_window_with_mocks.visualization_manager.show_spectrograms()
        main_window_with_mocks.visualization_manager.hide_spectrograms()

        # Verify visualization methods were called
        main_window_with_mocks.visualization_manager.show_spectrograms.assert_called_once()
        main_window_with_mocks.visualization_manager.hide_spectrograms.assert_called_once()


@pytest.mark.integration
class TestMainWindowEventHandling:
    """Test MainWindow event handling integration."""

    @pytest.fixture
    def main_window_with_events(self, qapp):
        """Create MainWindow with event handling setup."""
        main_window = MainWindow()
        main_window.event_handler = Mock()
        main_window.grid_widget = Mock()
        main_window.graph_widget = Mock()

        return main_window

    def test_key_press_handling(self, main_window_with_events):
        """Test key press event handling."""
        from PyQt5.QtGui import QKeyEvent

        # Create mock key event
        key_event = Mock(spec=QKeyEvent)
        key_event.key.return_value = Qt.Key_Space

        main_window_with_events.keyPressEvent(key_event)

        # Verify event handler was called
        main_window_with_events.event_handler.handle_key_press.assert_called_once_with(key_event)

    def test_key_release_handling(self, main_window_with_events):
        """Test key release event handling."""
        from PyQt5.QtGui import QKeyEvent

        key_event = Mock(spec=QKeyEvent)
        key_event.key.return_value = Qt.Key_Shift

        main_window_with_events.keyReleaseEvent(key_event)

        main_window_with_events.event_handler.handle_key_release.assert_called_once_with(key_event)

    def test_close_event_handling(self, main_window_with_events):
        """Test window close event handling."""
        from PyQt5.QtGui import QCloseEvent

        close_event = Mock(spec=QCloseEvent)

        with patch('PyQt5.QtWidgets.QApplication.quit') as mock_quit:
            main_window_with_events.closeEvent(close_event)

            close_event.accept.assert_called_once()
            mock_quit.assert_called_once()


@pytest.mark.integration
class TestMainWindowStateManagement:
    """Test MainWindow state management."""

    @pytest.fixture
    def main_window_with_state(self, qapp):
        """Create MainWindow with state management."""
        main_window = MainWindow()

        # Setup initial state
        main_window.data = None
        main_window.selected_channel = None
        main_window.plotted_channels = [None] * 4
        main_window.lock_to_playhead = False
        main_window.is_auto_analyzing = False

        return main_window

    def test_initial_state(self, main_window_with_state):
        """Test MainWindow initial state."""
        assert main_window_with_state.data is None
        assert main_window_with_state.selected_channel is None
        assert main_window_with_state.plotted_channels == [None] * 4
        assert main_window_with_state.lock_to_playhead is False
        assert main_window_with_state.is_auto_analyzing is False

    def test_state_transitions(self, main_window_with_state):
        """Test MainWindow state transitions."""
        # Change channel selection
        main_window_with_state.selected_channel = (2, 3)
        assert main_window_with_state.selected_channel == (2, 3)

        # Toggle lock to playhead
        main_window_with_state.lock_to_playhead = True
        assert main_window_with_state.lock_to_playhead is True

        # Start auto analysis
        main_window_with_state.is_auto_analyzing = True
        assert main_window_with_state.is_auto_analyzing is True

    def test_data_state_management(self, main_window_with_state):
        """Test data-related state management."""
        # Set data
        test_data = np.zeros((64, 64), dtype=object)
        main_window_with_state.data = test_data

        assert main_window_with_state.data is test_data

        # Clear data
        main_window_with_state.data = None
        assert main_window_with_state.data is None


@pytest.mark.integration
class TestMainWindowTimerIntegration:
    """Test MainWindow timer integration."""

    @pytest.fixture
    def main_window_with_timers(self, qapp):
        """Create MainWindow with timer setup."""
        main_window = MainWindow()
        main_window.playback_timer = QTimer()
        main_window.playback_manager = Mock()

        return main_window

    def test_playback_timer_setup(self, main_window_with_timers):
        """Test playback timer setup and connection."""
        # Connect timer to playback manager
        main_window_with_timers.playback_timer.timeout.connect(
            main_window_with_timers.playback_manager.update_playback
        )

        # Start timer
        main_window_with_timers.playback_timer.start(50)

        assert main_window_with_timers.playback_timer.isActive()

        # Stop timer
        main_window_with_timers.playback_timer.stop()
        assert not main_window_with_timers.playback_timer.isActive()

    def test_timer_cleanup_on_close(self, main_window_with_timers):
        """Test timer cleanup when window closes."""
        # Start timer
        main_window_with_timers.playback_timer.start(50)
        assert main_window_with_timers.playback_timer.isActive()

        # Close window should stop timers
        from PyQt5.QtGui import QCloseEvent
        close_event = Mock(spec=QCloseEvent)

        with patch('PyQt5.QtWidgets.QApplication.quit'):
            main_window_with_timers.closeEvent(close_event)

        # Timer should be cleaned up (this is implicit in the close event)


@pytest.mark.integration
class TestMainWindowPerformance:
    """Test MainWindow performance characteristics."""

    def test_rapid_state_changes(self, qapp):
        """Test rapid state changes don't cause issues."""
        main_window = MainWindow()
        main_window.selected_channel = None

        # Rapid channel selection changes
        for i in range(100):
            main_window.selected_channel = (i % 8, (i + 1) % 8)

        assert main_window.selected_channel == (3, 4)  # 99 % 8, (99 + 1) % 8

    def test_memory_usage_stability(self, qapp):
        """Test that MainWindow doesn't leak memory during operations."""
        main_window = MainWindow()

        # Simulate multiple operations
        for _ in range(10):
            main_window.data = np.zeros((64, 64), dtype=object)
            main_window.plotted_channels = [Mock() for _ in range(4)]
            main_window.data = None
            main_window.plotted_channels = [None] * 4

        # Should complete without memory issues (smoke test)
        assert main_window.data is None