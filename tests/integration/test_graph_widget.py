"""Integration tests for GraphWidget class."""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtCore import Qt, QPointF

from src.widgets.GraphWidget import GraphWidget


@pytest.mark.integration
class TestGraphWidgetIntegration:
    """Integration tests for GraphWidget with real Qt and PyQtGraph components."""

    @pytest.fixture
    def graph_widget(self, qapp, mock_main_window):
        """Create GraphWidget instance for testing."""
        return GraphWidget(mock_main_window)

    def test_graph_widget_initialization(self, graph_widget):
        """Test GraphWidget initialization creates proper plot structure."""
        # Verify basic structure
        assert graph_widget.main_window is not None
        assert len(graph_widget.plot_widgets) == 4
        assert len(graph_widget.red_lines) == 4
        assert len(graph_widget.trace_curves) == 4

        # Verify minimap
        assert graph_widget.minimap is not None
        assert graph_widget.minimap_region is not None

    def test_plot_widgets_configuration(self, graph_widget):
        """Test that plot widgets are properly configured."""
        for i, plot_widget in enumerate(graph_widget.plot_widgets):
            # Verify basic plot widget properties
            assert plot_widget is not None

            # Verify view box configuration
            view_box = plot_widget.getPlotItem().getViewBox()
            assert view_box is not None

            # Verify red line is added
            red_line = graph_widget.red_lines[i]
            assert red_line is not None

    def test_minimap_functionality(self, graph_widget):
        """Test minimap creation and functionality."""
        minimap = graph_widget.minimap
        assert minimap is not None

        # Verify minimap region
        region = graph_widget.minimap_region
        assert region is not None
        assert region.movable is True

    def test_plot_data_display(self, graph_widget, mock_main_window):
        """Test plotting data on graph widgets."""
        # Setup sample data
        x_data = np.linspace(0, 10, 1000)
        y_data = np.sin(x_data)

        # Setup mock channel data
        mock_channel = Mock()
        mock_channel.row = 1
        mock_channel.col = 1

        mock_main_window.plotted_channels = [mock_channel, None, None, None]
        mock_main_window.data = np.zeros((64, 64), dtype=object)
        mock_main_window.data[1, 1] = {'signal': y_data}
        mock_main_window.time_vector = x_data

        # Plot channel
        graph_widget.plot(mock_channel, 0)

        # Verify data was plotted
        assert graph_widget.x_data[0] is not None
        assert graph_widget.y_data[0] is not None
        assert graph_widget.trace_curves[0] is not None

    def test_red_line_updates(self, graph_widget):
        """Test red line position updates."""
        initial_position = 100
        sampling_rate = 1000

        graph_widget.update_red_lines(initial_position, sampling_rate)

        # Verify red lines are positioned correctly
        expected_time = initial_position / sampling_rate
        for red_line in graph_widget.red_lines:
            assert red_line.value() == expected_time

    def test_view_mode_changes(self, graph_widget):
        """Test changing view modes."""
        # Test changing to rectangle mode
        graph_widget.change_view_mode("rect")

        # Should complete without errors (smoke test)
        assert True

    def test_region_selection(self, graph_widget):
        """Test region selection on plots."""
        signals_received = []

        def region_handler(start, end, plot_index):
            signals_received.append((start, end, plot_index))

        graph_widget.region_clicked.connect(region_handler)

        # Simulate region selection
        start_time = 5.0
        end_time = 10.0
        plot_index = 0

        graph_widget.region_clicked.emit(start_time, end_time, plot_index)

        assert len(signals_received) == 1
        assert signals_received[0] == (start_time, end_time, plot_index)

    def test_minimap_region_changes(self, graph_widget):
        """Test minimap region changes affecting main plots."""
        # Setup some data first
        x_data = np.linspace(0, 100, 10000)
        y_data = np.sin(x_data)

        graph_widget.x_data[0] = x_data
        graph_widget.y_data[0] = y_data

        # Mock trace curve
        graph_widget.trace_curves[0] = Mock()

        # Change minimap region
        graph_widget.minimap_region.setRegion([20, 40])

        # Should trigger updates without errors
        # This is primarily a smoke test


@pytest.mark.integration
class TestGraphWidgetDataIntegration:
    """Test GraphWidget integration with data structures."""

    @pytest.fixture
    def graph_widget_with_data(self, qapp, mock_main_window, sample_brw_data):
        """Create GraphWidget with sample data."""
        mock_main_window.data = sample_brw_data
        mock_main_window.sampling_rate = 100
        mock_main_window.time_vector = np.linspace(0, 60, 6000)

        return GraphWidget(mock_main_window)

    def test_multiple_channel_plotting(self, graph_widget_with_data, mock_main_window):
        """Test plotting multiple channels simultaneously."""
        # Setup multiple channels
        channels = []
        for i in range(4):
            channel = Mock()
            channel.row = i + 1
            channel.col = i + 1
            channels.append(channel)

        mock_main_window.plotted_channels = channels

        # Setup data for all channels
        for i in range(4):
            mock_main_window.data[i + 1, i + 1] = {
                'signal': np.sin(np.linspace(0, 10, 6000) + i)
            }

        # Plot all channels
        for i, channel in enumerate(channels):
            graph_widget_with_data.plot(channel, i)

        # Verify all channels were plotted
        for i in range(4):
            assert graph_widget_with_data.x_data[i] is not None
            assert graph_widget_with_data.y_data[i] is not None

    def test_data_downsampling(self, graph_widget_with_data, mock_main_window):
        """Test data downsampling for large datasets."""
        # Create large dataset
        large_data = np.random.randn(100000)

        mock_channel = Mock()
        mock_channel.row = 1
        mock_channel.col = 1

        mock_main_window.data[1, 1] = {'signal': large_data}
        mock_main_window.time_vector = np.linspace(0, 1000, 100000)

        # Plot with downsampling
        graph_widget_with_data.plot(mock_channel, 0)

        # Should handle large data without issues (smoke test)
        assert graph_widget_with_data.x_data[0] is not None

    def test_seizure_markers_display(self, graph_widget_with_data, mock_main_window):
        """Test displaying seizure and SE markers."""
        # Setup seizure data
        mock_main_window.data[1, 1] = {
            'signal': np.random.randn(6000),
            'SzTimes': np.array([[10.0, 20.0, 1.0]]),
            'SETimes': np.array([[30.0, 40.0, 1.5]])
        }

        mock_channel = Mock()
        mock_channel.row = 1
        mock_channel.col = 1

        graph_widget_with_data.plot(mock_channel, 0)

        # Should handle markers without errors (smoke test)
        assert True


@pytest.mark.integration
class TestGraphWidgetInteraction:
    """Test GraphWidget user interaction."""

    @pytest.fixture
    def graph_widget(self, qapp, mock_main_window):
        """Create GraphWidget for interaction testing."""
        return GraphWidget(mock_main_window)

    def test_plot_zoom_and_pan(self, graph_widget):
        """Test plot zooming and panning functionality."""
        plot_widget = graph_widget.plot_widgets[0]
        view_box = plot_widget.getPlotItem().getViewBox()

        # Set initial range
        view_box.setRange(xRange=(0, 100), yRange=(-1, 1))

        # Get current range
        x_range, y_range = view_box.viewRange()

        assert len(x_range) == 2
        assert len(y_range) == 2

    def test_context_menu_actions(self, graph_widget):
        """Test context menu functionality."""
        save_single_received = False
        save_all_received = False

        def single_handler():
            nonlocal save_single_received
            save_single_received = True

        def all_handler():
            nonlocal save_all_received
            save_all_received = True

        graph_widget.save_single_plot.connect(single_handler)
        graph_widget.save_all_plots.connect(all_handler)

        # Emit signals
        graph_widget.save_single_plot.emit()
        graph_widget.save_all_plots.emit()

        assert save_single_received
        assert save_all_received

    def test_mouse_tracking(self, graph_widget):
        """Test mouse tracking on plots."""
        # Enable mouse tracking
        plot_widget = graph_widget.plot_widgets[0]
        plot_widget.setMouseTracking(True)

        # Should enable without errors (smoke test)
        assert plot_widget.hasMouseTracking()


@pytest.mark.integration
class TestGraphWidgetSignalHandling:
    """Test GraphWidget signal handling and connections."""

    @pytest.fixture
    def graph_widget(self, qapp, mock_main_window):
        """Create GraphWidget for signal testing."""
        return GraphWidget(mock_main_window)

    def test_minimap_region_signal_connection(self, graph_widget):
        """Test minimap region signal connection."""
        # Verify signal connection exists
        assert graph_widget.minimap_region.sigRegionChanged is not None

    def test_plot_widget_signal_propagation(self, graph_widget):
        """Test that plot widget signals propagate correctly."""
        # This is more of a structural test to ensure signals are properly connected
        for i, plot_widget in enumerate(graph_widget.plot_widgets):
            view_box = plot_widget.getPlotItem().getViewBox()
            assert view_box is not None
            assert hasattr(view_box, 'menu')


@pytest.mark.integration
class TestGraphWidgetPerformance:
    """Test GraphWidget performance characteristics."""

    def test_rapid_data_updates(self, qapp, mock_main_window):
        """Test rapid data updates don't cause performance issues."""
        graph_widget = GraphWidget(mock_main_window)

        # Create test data
        x_data = np.linspace(0, 10, 1000)

        mock_channel = Mock()
        mock_channel.row = 1
        mock_channel.col = 1

        # Rapid updates
        for i in range(10):
            y_data = np.sin(x_data + i * 0.1)
            mock_main_window.data[1, 1] = {'signal': y_data}
            mock_main_window.time_vector = x_data

            graph_widget.plot(mock_channel, 0)

        # Should complete without performance issues
        assert graph_widget.x_data[0] is not None

    def test_large_dataset_handling(self, qapp, mock_main_window):
        """Test handling of large datasets."""
        graph_widget = GraphWidget(mock_main_window)

        # Create very large dataset
        large_x = np.linspace(0, 1000, 50000)
        large_y = np.random.randn(50000)

        mock_channel = Mock()
        mock_channel.row = 1
        mock_channel.col = 1

        mock_main_window.data[1, 1] = {'signal': large_y}
        mock_main_window.time_vector = large_x

        # Should handle large data gracefully
        graph_widget.plot(mock_channel, 0)

        assert graph_widget.x_data[0] is not None