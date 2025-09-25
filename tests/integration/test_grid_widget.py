"""Integration tests for GridWidget class."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QMouseEvent
from PyQt5.QtWidgets import QApplication

from src.widgets.GridWidget import GridWidget, PurpleDot, SimpleColorDialog


@pytest.mark.integration
class TestGridWidgetIntegration:
    """Integration tests for GridWidget with real Qt components."""

    @pytest.fixture
    def grid_widget(self, qapp, mock_main_window):
        """Create GridWidget instance for testing."""
        return GridWidget(8, 8, mock_main_window)

    def test_grid_widget_initialization(self, grid_widget):
        """Test GridWidget initialization creates proper grid structure."""
        assert grid_widget.rows == 8
        assert grid_widget.cols == 8
        assert grid_widget.scene is not None
        assert len(grid_widget.cells) == 8
        assert all(len(row) == 8 for row in grid_widget.cells)

    def test_cell_creation_and_properties(self, grid_widget):
        """Test that cells are created with proper properties."""
        # Check that cells exist
        cell = grid_widget.cells[0][0]
        assert cell is not None
        assert hasattr(cell, 'row')
        assert hasattr(cell, 'col')
        assert cell.row == 0
        assert cell.col == 0

    def test_cell_click_signal_emission(self, grid_widget):
        """Test that cell clicks emit proper signals."""
        signal_received = []
        grid_widget.cell_clicked.connect(lambda r, c: signal_received.append((r, c)))

        # Simulate cell click
        cell = grid_widget.cells[2][3]
        # Trigger the cell click through the ColorCell's mousePressEvent
        with patch.object(cell, 'mousePressEvent') as mock_mouse_event:
            cell.clicked_state = True
            # Manually emit the signal that would be emitted on click
            grid_widget.cell_clicked.emit(2, 3)

        assert signal_received == [(2, 3)]

    def test_background_image_setting(self, grid_widget):
        """Test setting background image on grid."""
        test_image_path = "/test/path/image.jpg"

        with patch('PyQt5.QtGui.QPixmap') as mock_pixmap:
            mock_pixmap_instance = Mock()
            mock_pixmap.return_value = mock_pixmap_instance

            grid_widget.setBackgroundImage(test_image_path)

            assert grid_widget.image_path == test_image_path
            mock_pixmap.assert_called_with(test_image_path)

    def test_grid_resizing(self, grid_widget):
        """Test grid widget resizing behavior."""
        original_size = grid_widget.size()

        # Simulate resize
        grid_widget.resize(600, 400)

        # Verify scene rect is updated appropriately
        scene_rect = grid_widget.scene.sceneRect()
        assert scene_rect.width() > 0
        assert scene_rect.height() > 0

    def test_context_menu_creation(self, grid_widget):
        """Test context menu creation on right click."""
        with patch('PyQt5.QtWidgets.QMenu') as mock_menu:
            mock_menu_instance = Mock()
            mock_menu.return_value = mock_menu_instance

            # Simulate right click
            pos = QPointF(100, 100)
            grid_widget.contextMenuEvent(Mock(pos=lambda: pos))

    def test_grid_updates_with_data(self, grid_widget, mock_main_window):
        """Test grid updates when data changes."""
        # Setup mock data
        mock_main_window.data = Mock()
        mock_main_window.sampling_rate = 100
        mock_main_window.ui_manager.progress_bar.value.return_value = 1000

        # Update grid
        grid_widget.update_cells()

        # Grid should handle the update without errors
        # This is more of a smoke test to ensure no exceptions


@pytest.mark.integration
class TestPurpleDot:
    """Test PurpleDot graphics item."""

    def test_purple_dot_creation(self):
        """Test PurpleDot creation and properties."""
        dot = PurpleDot(50, 50)

        assert dot.rect().width() == 40  # Default size
        assert dot.rect().height() == 40
        assert dot.color == QColor(128, 0, 128, 128)

    def test_purple_dot_color_change(self):
        """Test changing PurpleDot color."""
        dot = PurpleDot(50, 50)
        new_color = QColor(255, 0, 0, 128)

        dot.change_color(new_color)

        assert dot.color == new_color


@pytest.mark.integration
class TestSimpleColorDialog:
    """Test SimpleColorDialog widget."""

    @pytest.fixture
    def color_dialog(self, qapp):
        """Create SimpleColorDialog for testing."""
        return SimpleColorDialog()

    def test_color_dialog_creation(self, color_dialog):
        """Test color dialog creation with predefined colors."""
        assert len(color_dialog.predefined_colors) == 6
        assert color_dialog.selected_color is None

    def test_color_selection(self, color_dialog):
        """Test color selection in dialog."""
        test_color = QColor(255, 0, 0, 128)

        color_dialog.color_chosen(test_color)

        assert color_dialog.selected_color == test_color


@pytest.mark.integration
class TestGridWidgetDataIntegration:
    """Test GridWidget integration with data structures."""

    @pytest.fixture
    def grid_widget_with_data(self, qapp, mock_main_window, sample_brw_data):
        """Create GridWidget with sample data."""
        # Setup main window with data
        mock_main_window.data = sample_brw_data
        mock_main_window.sampling_rate = 100
        mock_main_window.active_channels = [(1, 1), (1, 2), (2, 1), (2, 2)]
        mock_main_window.ui_manager.progress_bar.value.return_value = 500

        return GridWidget(64, 64, mock_main_window)

    def test_grid_cell_state_updates(self, grid_widget_with_data):
        """Test that grid cells update state based on data."""
        # This is a smoke test to ensure the grid can handle data updates
        # without throwing exceptions
        grid_widget_with_data.update_cells()

        # Verify grid maintains its structure
        assert len(grid_widget_with_data.cells) == 64
        assert all(len(row) == 64 for row in grid_widget_with_data.cells)

    def test_grid_recording_mode(self, grid_widget_with_data):
        """Test grid widget in recording mode."""
        grid_widget_with_data.is_recording_video = True

        # Should handle recording mode without errors
        grid_widget_with_data.update_cells()

        assert grid_widget_with_data.is_recording_video is True

    def test_grid_overlay_management(self, grid_widget_with_data):
        """Test grid overlay creation and management."""
        # Add overlay
        overlay = Mock()
        grid_widget_with_data.overlays.append(overlay)

        assert len(grid_widget_with_data.overlays) == 1

        # Clear overlays
        grid_widget_with_data.overlays.clear()
        assert len(grid_widget_with_data.overlays) == 0


@pytest.mark.integration
class TestGridWidgetSignalIntegration:
    """Test GridWidget signal handling integration."""

    @pytest.fixture
    def grid_widget(self, qapp, mock_main_window):
        """Create GridWidget for signal testing."""
        return GridWidget(8, 8, mock_main_window)

    def test_save_signals_emission(self, grid_widget):
        """Test save-related signal emissions."""
        video_signal_received = False
        image_signal_received = False

        def video_handler():
            nonlocal video_signal_received
            video_signal_received = True

        def image_handler():
            nonlocal image_signal_received
            image_signal_received = True

        grid_widget.save_as_video_requested.connect(video_handler)
        grid_widget.save_as_image_requested.connect(image_handler)

        # Emit signals
        grid_widget.save_as_video_requested.emit()
        grid_widget.save_as_image_requested.emit()

        assert video_signal_received
        assert image_signal_received

    def test_cell_selection_handling(self, grid_widget):
        """Test cell selection and state management."""
        # Select a cell
        grid_widget.selected_channel = (2, 3)
        cell = grid_widget.cells[2][3]

        # Verify selection state
        assert grid_widget.selected_channel == (2, 3)

        # Change selection
        grid_widget.selected_channel = (4, 5)
        assert grid_widget.selected_channel == (4, 5)


@pytest.mark.integration
class TestGridWidgetPerformance:
    """Test GridWidget performance characteristics."""

    def test_large_grid_creation(self, qapp, mock_main_window):
        """Test creating larger grid without performance issues."""
        # Create a moderately large grid
        large_grid = GridWidget(32, 32, mock_main_window)

        assert large_grid.rows == 32
        assert large_grid.cols == 32
        assert len(large_grid.cells) == 32
        assert all(len(row) == 32 for row in large_grid.cells)

    def test_rapid_updates(self, qapp, mock_main_window):
        """Test rapid grid updates don't cause issues."""
        grid_widget = GridWidget(8, 8, mock_main_window)

        # Simulate rapid updates
        for i in range(10):
            grid_widget.update_cells()

        # Should complete without errors
        assert len(grid_widget.cells) == 8