"""Unit tests for PlaybackManager class."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.managers.playback_manager import PlaybackManager


@pytest.mark.unit
class TestPlaybackManager:
    """Test cases for PlaybackManager."""

    @pytest.fixture
    def playback_manager(self, mock_main_window):
        """Create PlaybackManager instance for testing."""
        return PlaybackManager(mock_main_window)

    def test_init(self, playback_manager, mock_main_window):
        """Test PlaybackManager initialization."""
        assert playback_manager.main_window is mock_main_window

    def test_skip_backward_no_data(self, playback_manager, mock_main_window):
        """Test skip backward with no data loaded."""
        mock_main_window.data = None
        mock_main_window.plotted_channels = [None] * 4

        playback_manager.skip_backward()

        # Should return early without errors
        mock_main_window.ui_manager.progress_bar.setValue.assert_not_called()

    def test_skip_backward_with_seizure(self, playback_manager, mock_main_window):
        """Test skip backward to previous seizure."""
        # Setup test data
        mock_main_window.data = np.zeros((64, 64), dtype=object)
        mock_main_window.data[1, 1] = {
            'SzTimes': np.array([[5.0, 10.0, 1.0], [20.0, 25.0, 1.5]]),
            'SETimes': np.array([])
        }

        # Setup plotted channel
        mock_channel = Mock()
        mock_channel.row, mock_channel.col = 1, 1
        mock_main_window.plotted_channels = [mock_channel, None, None, None]

        # Current time at 15 seconds
        mock_main_window.ui_manager.progress_bar.value.return_value = 1500
        mock_main_window.sampling_rate = 100

        playback_manager.skip_backward()

        # Should skip to seizure at 5.0 seconds (500 samples) - the previous seizure before current time
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(500)
        mock_main_window.update_grid.assert_called_once()

    def test_step_backward(self, playback_manager, mock_main_window):
        """Test step backward by speed interval."""
        mock_main_window.ui_manager.speed_combo.currentText.return_value = "1.0"
        mock_main_window.ui_manager.progress_bar.value.return_value = 500
        mock_main_window.sampling_rate = 100

        playback_manager.step_backward()

        # Should move back by 1.0 * 100 = 100 samples
        expected_value = 500 - 100
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(expected_value)
        mock_main_window.update_grid.assert_called_once()

    def test_step_backward_boundary(self, playback_manager, mock_main_window):
        """Test step backward at start boundary."""
        mock_main_window.ui_manager.speed_combo.currentText.return_value = "2.0"
        mock_main_window.ui_manager.progress_bar.value.return_value = 100
        mock_main_window.sampling_rate = 100

        playback_manager.step_backward()

        # Should clamp to 0
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(0)

    def test_pause_playback(self, playback_manager, mock_main_window):
        """Test pause playback functionality."""
        playback_manager.pause_playback()

        # Should update button and stop timer
        mock_main_window.ui_manager.play_pause_button.setText.assert_called_with("\uf04b")
        mock_main_window.playback_timer.stop.assert_called_once()

    def test_play_pause_start_playing(self, playback_manager, mock_main_window):
        """Test starting playback."""
        mock_main_window.ui_manager.play_pause_button.text.return_value = "\uf04b"  # Currently showing play

        playback_manager.play_pause()

        mock_main_window.ui_manager.play_pause_button.setText.assert_called_with("⏸")
        mock_main_window.playback_timer.start.assert_called_with(50)

    def test_play_pause_stop_playing(self, playback_manager, mock_main_window):
        """Test stopping playback."""
        mock_main_window.ui_manager.play_pause_button.text.return_value = "⏸"

        playback_manager.play_pause()

        mock_main_window.ui_manager.play_pause_button.setText.assert_called_with("\uf04b")
        mock_main_window.playback_timer.stop.assert_called_once()

    def test_update_playback(self, playback_manager, mock_main_window):
        """Test playback position update during play."""
        mock_main_window.ui_manager.speed_combo.currentText.return_value = "0.5"
        mock_main_window.ui_manager.progress_bar.value.return_value = 1000
        mock_main_window.ui_manager.progress_bar.maximum.return_value = 6000
        mock_main_window.sampling_rate = 100
        mock_main_window.lock_to_playhead = False

        playback_manager.update_playback()

        # Should advance by 0.5 * 100 = 50 samples
        expected_value = 1000 + 50
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(expected_value)

    def test_update_playback_end_of_recording(self, playback_manager, mock_main_window):
        """Test playback update at end of recording."""
        mock_main_window.ui_manager.speed_combo.currentText.return_value = "1.0"
        mock_main_window.ui_manager.progress_bar.value.return_value = 5950
        mock_main_window.ui_manager.progress_bar.maximum.return_value = 6000
        mock_main_window.sampling_rate = 100

        playback_manager.update_playback()

        # Should stop at maximum and pause
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(6000)
        mock_main_window.playback_timer.stop.assert_called_once()
        mock_main_window.ui_manager.play_pause_button.setText.assert_called_with("\uf04b")

    def test_lock_plots_to_playhead(self, playback_manager, mock_main_window):
        """Test locking plots to follow playhead."""
        mock_main_window.ui_manager.progress_bar.value.return_value = 1000
        mock_main_window.sampling_rate = 100

        # Mock plot widgets and view boxes
        mock_plot_widget = Mock()
        mock_plot_item = Mock()
        mock_view_box = Mock()

        mock_plot_widget.getPlotItem.return_value = mock_plot_item
        mock_plot_item.getViewBox.return_value = mock_view_box
        mock_view_box.viewRange.return_value = [(5.0, 15.0), (0, 1)]  # 10 second window

        mock_main_window.graph_widget.plot_widgets = [mock_plot_widget]

        playback_manager.lock_plots_to_playhead()

        # Should center view on current time (10.0 seconds)
        current_time = 1000 / 100  # 10.0 seconds
        x_width = 10.0  # 15.0 - 5.0
        x_min = current_time - x_width / 2  # 5.0
        x_max = current_time + x_width / 2  # 15.0

        mock_view_box.setRange.assert_called_with(xRange=(x_min, x_max), padding=0)

    def test_step_forward(self, playback_manager, mock_main_window):
        """Test step forward by speed interval."""
        mock_main_window.ui_manager.speed_combo.currentText.return_value = "2.0"
        mock_main_window.ui_manager.progress_bar.value.return_value = 1000
        mock_main_window.ui_manager.progress_bar.maximum.return_value = 6000
        mock_main_window.sampling_rate = 100

        playback_manager.step_forward()

        # Should move forward by 2.0 * 100 = 200 samples
        expected_value = 1000 + 200
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(expected_value)
        mock_main_window.update_grid.assert_called_once()

    def test_step_forward_boundary(self, playback_manager, mock_main_window):
        """Test step forward at end boundary."""
        mock_main_window.ui_manager.speed_combo.currentText.return_value = "1.0"
        mock_main_window.ui_manager.progress_bar.value.return_value = 5900
        mock_main_window.ui_manager.progress_bar.maximum.return_value = 6000
        mock_main_window.sampling_rate = 100

        playback_manager.step_forward()

        # Should clamp to maximum
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(6000)

    def test_skip_forward_with_se_event(self, playback_manager, mock_main_window):
        """Test skip forward to next SE event."""
        # Setup test data
        mock_main_window.data = np.zeros((64, 64), dtype=object)
        mock_main_window.data[1, 1] = {
            'SzTimes': np.array([]),
            'SETimes': np.array([[15.0, 20.0, 2.0], [30.0, 35.0, 1.8]])
        }
        mock_main_window.recording_length = 60.0
        mock_main_window.last_skip_time = 0.0

        # Setup plotted channel
        mock_channel = Mock()
        mock_channel.row, mock_channel.col = 1, 1
        mock_main_window.plotted_channels = [mock_channel, None, None, None]

        # Current time at 10 seconds
        mock_main_window.ui_manager.progress_bar.value.return_value = 1000
        mock_main_window.sampling_rate = 100

        playback_manager.skip_forward()

        # Should skip to SE event at 15.0 seconds (1500 samples)
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(1500)
        mock_main_window.update_grid.assert_called_once()

    def test_set_playback_speed(self, playback_manager, mock_main_window):
        """Test setting playback speed."""
        playback_manager.set_playback_speed(2)

        mock_main_window.playback_timer.setInterval.assert_called_with(50)

    def test_seek_position(self, playback_manager, mock_main_window):
        """Test seeking to specific position."""
        mock_main_window.raster_plot = None
        mock_main_window.lock_to_playhead = False

        playback_manager.seek_position(1500)

        mock_main_window.graph_widget.update_red_lines.assert_called_with(1500, mock_main_window.sampling_rate)
        mock_main_window.update_grid.assert_called_once()

    def test_seek_position_with_raster_plot(self, playback_manager, mock_main_window):
        """Test seeking with raster plot active."""
        mock_raster_plot = Mock()
        mock_raster_red_line = Mock()
        mock_raster_plot.raster_red_line = mock_raster_red_line
        mock_main_window.raster_plot = mock_raster_plot
        mock_main_window.ui_manager.progress_bar.maximum.return_value = 6000
        mock_main_window.active_channels = [(1, 1), (1, 2), (2, 1), (2, 2)]
        mock_main_window.lock_to_playhead = False

        playback_manager.seek_position(3000)

        # Should update raster plot red line position
        percentage = 3000 / 6000  # 0.5
        scaled_percentage = percentage * 4  # 2.0
        mock_raster_red_line.setPos.assert_called_with(scaled_percentage)


@pytest.mark.unit
class TestPlaybackManagerEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def playback_manager(self, mock_main_window):
        """Create PlaybackManager instance for testing."""
        return PlaybackManager(mock_main_window)

    def test_skip_backward_no_plotted_channels(self, playback_manager, mock_main_window):
        """Test skip backward with no channels plotted."""
        mock_main_window.data = np.zeros((64, 64), dtype=object)
        mock_main_window.plotted_channels = [None] * 4

        playback_manager.skip_backward()

        # Should handle gracefully
        mock_main_window.ui_manager.progress_bar.setValue.assert_not_called()

    def test_skip_forward_no_events_found(self, playback_manager, mock_main_window):
        """Test skip forward when no future events exist."""
        # Setup test data with no future events
        mock_main_window.data = np.zeros((64, 64), dtype=object)
        mock_main_window.data[1, 1] = {
            'SzTimes': np.array([[5.0, 10.0, 1.0]]),  # Past event
            'SETimes': np.array([])
        }
        mock_main_window.recording_length = 60.0
        mock_main_window.last_skip_time = 0.0

        # Setup plotted channel
        mock_channel = Mock()
        mock_channel.row, mock_channel.col = 1, 1
        mock_main_window.plotted_channels = [mock_channel, None, None, None]

        # Current time at 20 seconds (after the only event)
        mock_main_window.ui_manager.progress_bar.value.return_value = 2000
        mock_main_window.ui_manager.progress_bar.maximum.return_value = 6000
        mock_main_window.sampling_rate = 100

        playback_manager.skip_forward()

        # Should skip to end of recording
        mock_main_window.ui_manager.progress_bar.setValue.assert_called_with(6000)

    def test_lock_plots_to_playhead_empty_widgets(self, playback_manager, mock_main_window):
        """Test lock plots to playhead with no plot widgets."""
        mock_main_window.ui_manager.progress_bar.value.return_value = 1000
        mock_main_window.sampling_rate = 100
        mock_main_window.graph_widget.plot_widgets = []

        # Should handle empty list gracefully
        playback_manager.lock_plots_to_playhead()

        # No exceptions should be raised