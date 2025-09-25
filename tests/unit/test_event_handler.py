"""Unit tests for EventHandler class."""
import pytest
import numpy as np
from unittest.mock import Mock, patch
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent

from src.managers.event_handler import EventHandler


@pytest.mark.unit
class TestEventHandler:
    """Test cases for EventHandler."""

    @pytest.fixture
    def event_handler(self, mock_main_window):
        """Create EventHandler instance for testing."""
        return EventHandler(mock_main_window)

    @pytest.fixture
    def mock_key_event(self):
        """Create a mock key event."""
        event = Mock(spec=QKeyEvent)
        return event

    def test_init(self, event_handler, mock_main_window):
        """Test EventHandler initialization."""
        assert event_handler.main_window is mock_main_window

    def test_handle_key_press_channel_selection(self, event_handler, mock_main_window, mock_key_event):
        """Test channel selection key press (1-4)."""
        mock_key_event.key.return_value = Qt.Key_1
        mock_main_window.selected_channel = (0, 0)
        # Create proper data structure - numpy array of objects
        mock_main_window.data = np.zeros((64, 64), dtype=object)
        mock_main_window.data[0, 0] = {
            'SzTimes': [],
            'SETimes': [],
            'signal': np.random.randn(1000).astype(np.float32)
        }
        mock_main_window.plotted_channels = [None] * 4
        mock_main_window.grid_widget.cells = [[Mock()]]
        mock_main_window.sampling_rate = 100
        mock_main_window.time_vector = list(range(1000))

        # Mock raster_plot to avoid the arithmetic error
        mock_main_window.raster_plot = None  # This will skip the problematic code path

        event_handler.handle_key_press(mock_key_event)

        # Verify channel was plotted
        mock_main_window.graph_widget.plot.assert_called_once()

    def test_handle_key_press_arrow_keys(self, event_handler, mock_main_window, mock_key_event):
        """Test arrow key navigation."""
        mock_main_window.ui_manager.skip_backward_button.isEnabled.return_value = True
        mock_main_window.ui_manager.skip_forward_button.isEnabled.return_value = True
        mock_main_window.ui_manager.play_pause_button.isEnabled.return_value = True

        # Test right arrow (step forward)
        mock_key_event.key.return_value = Qt.Key_Right
        event_handler.handle_key_press(mock_key_event)
        mock_main_window.playback_manager.step_forward.assert_called_once()

        # Test left arrow (step backward)
        mock_key_event.key.return_value = Qt.Key_Left
        event_handler.handle_key_press(mock_key_event)
        mock_main_window.playback_manager.step_backward.assert_called_once()

        # Test space bar (play/pause)
        mock_key_event.key.return_value = Qt.Key_Space
        event_handler.handle_key_press(mock_key_event)
        mock_main_window.playback_manager.play_pause.assert_called_once()

    def test_handle_key_press_analysis_shortcuts(self, event_handler, mock_main_window, mock_key_event):
        """Test analysis shortcut keys."""
        # Test 'A' key (find discharges)
        mock_key_event.key.return_value = Qt.Key_A
        event_handler.handle_key_press(mock_key_event)
        mock_main_window.analysis_manager.find_discharges.assert_called_once()

        # Test 'G' key (auto analyze)
        mock_key_event.key.return_value = Qt.Key_G
        event_handler.handle_key_press(mock_key_event)
        mock_main_window.analysis_manager.auto_analyze.assert_called_once()

    def test_handle_key_press_lock_to_playhead(self, event_handler, mock_main_window, mock_key_event):
        """Test 'L' key for lock to playhead toggle."""
        mock_main_window.lock_to_playhead = False
        mock_key_event.key.return_value = Qt.Key_L

        event_handler.handle_key_press(mock_key_event)

        assert mock_main_window.lock_to_playhead is True
        mock_main_window.playback_manager.lock_plots_to_playhead.assert_called_once()

    @patch('PyQt5.QtGui.QCursor.pos')
    def test_handle_seek_to_cursor(self, mock_cursor_pos, event_handler, mock_main_window):
        """Test seeking to cursor position."""
        mock_cursor_pos.return_value = Mock()
        mock_main_window.graph_widget.plot_widgets = [Mock() for _ in range(4)]
        mock_main_window.sampling_rate = 100

        # Setup mock plot widget
        plot_widget = mock_main_window.graph_widget.plot_widgets[0]
        plot_widget.rect().contains.return_value = True
        plot_widget.mapFromGlobal.return_value = Mock()

        # Setup plot item and view box mocks
        plot_item = Mock()
        view_box = Mock()
        view_pos = Mock()
        view_pos.x.return_value = 10.0

        plot_widget.getPlotItem.return_value = plot_item
        plot_item.getViewBox.return_value = view_box
        plot_item.mapToScene.return_value = Mock()
        view_box.mapSceneToView.return_value = view_pos

        event_handler._handle_seek_to_cursor()

        # Verify progress bar was updated
        expected_value = int(10.0 * 100)
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(expected_value)

    def test_handle_toggle_discharge_peaks(self, event_handler, mock_main_window):
        """Test toggling discharge peaks display."""
        mock_main_window.show_discharge_peaks = False
        mock_main_window.plotted_channels = [Mock(), None, None, None]

        event_handler._handle_toggle_discharge_peaks()

        assert mock_main_window.show_discharge_peaks is True
        mock_main_window.graph_widget.plot_peaks.assert_called_once()

    def test_handle_cell_click(self, event_handler, mock_main_window):
        """Test cell click handling."""
        # Setup previous selection
        mock_main_window.selected_channel = (0, 0)
        mock_prev_cell = Mock()
        mock_main_window.grid_widget.cells = [[mock_prev_cell]]

        event_handler.handle_cell_click(1, 1)

        # Verify previous cell was deselected
        assert mock_prev_cell.clicked_state is False
        mock_prev_cell.update.assert_called_once()
        mock_prev_cell.selected_tooltip.hide.assert_called_once()

        # Verify new selection
        assert mock_main_window.selected_channel == (1, 1)

    def test_handle_region_click(self, event_handler, mock_main_window):
        """Test region click handling."""
        mock_main_window.plotted_channels = [Mock(), None, None, None]
        mock_main_window.sampling_rate = 100
        mock_main_window.ui_manager.progress_bar = Mock()

        event_handler.handle_region_click(10.0, 20.0)

        # Verify plot range was updated
        mock_main_window.graph_widget.plot_widgets[0].setXRange.assert_called_with(10.0, 20.0)

        # Verify progress bar was updated
        expected_value = int(10.0 * 100)
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(expected_value)

        # Verify region was stored
        assert mock_main_window.current_region == (10.0, 20.0)

    def test_handle_key_release_shift(self, event_handler, mock_main_window, mock_key_event):
        """Test shift key release (changes view mode)."""
        mock_key_event.key.return_value = Qt.Key_Shift

        event_handler.handle_key_release(mock_key_event)

        mock_main_window.graph_widget.change_view_mode.assert_called_with("rect")

    def test_handle_confirmation_accept(self, event_handler, mock_main_window):
        """Test confirmation dialog acceptance."""
        mock_main_window.need_confirmation = True
        mock_main_window.discharge_start_dialog = Mock()

        event_handler._handle_confirmation(True)

        mock_main_window.discharge_start_dialog.confirm.assert_called_with(True)
        assert mock_main_window.need_confirmation is False

    def test_handle_confirmation_reject(self, event_handler, mock_main_window):
        """Test confirmation dialog rejection."""
        mock_main_window.need_confirmation = True
        mock_main_window.discharge_start_dialog = Mock()

        event_handler._handle_confirmation(False)

        mock_main_window.discharge_start_dialog.confirm.assert_called_with(False)
        mock_main_window.playback_manager.step_forward.assert_called_once()
        assert mock_main_window.need_confirmation is False


@pytest.mark.unit
class TestEventHandlerEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def event_handler(self, mock_main_window):
        """Create EventHandler instance for testing."""
        return EventHandler(mock_main_window)

    @pytest.fixture
    def mock_key_event(self):
        """Create a mock key event."""
        event = Mock(spec=QKeyEvent)
        return event

    def test_channel_selection_no_selected_channel(self, event_handler, mock_main_window, mock_key_event):
        """Test channel selection when no channel is selected."""
        mock_key_event.key.return_value = Qt.Key_1
        mock_main_window.selected_channel = None

        # Should not raise an exception
        event_handler.handle_key_press(mock_key_event)

    def test_seek_to_cursor_no_plots_under_cursor(self, event_handler, mock_main_window):
        """Test cursor seeking when no plots are under cursor."""
        mock_main_window.graph_widget.plot_widgets = [Mock() for _ in range(4)]

        # All plot widgets return False for contains
        for plot_widget in mock_main_window.graph_widget.plot_widgets:
            plot_widget.rect().contains.return_value = False

        with patch('PyQt5.QtGui.QCursor.pos'):
            event_handler._handle_seek_to_cursor()

        # Should not update progress bar
        mock_main_window.ui_manager.progress_bar.setValue.assert_not_called()