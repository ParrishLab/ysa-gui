"""Unit tests for DataManager class."""
import pytest
import math
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import h5py

from src.managers.data_manager import DataManager


@pytest.mark.unit
class TestDataManager:
    """Test cases for DataManager."""

    @pytest.fixture
    def data_manager(self, mock_main_window):
        """Create DataManager instance for testing."""
        return DataManager(mock_main_window)

    def test_init(self, data_manager, mock_main_window):
        """Test DataManager initialization."""
        assert data_manager.main_window is mock_main_window

    def test_get_channels_success(self, data_manager, temp_hdf5_file):
        """Test successful channel retrieval from HDF5 file."""
        data_manager.main_window.file_path = temp_hdf5_file

        rows, cols = data_manager.get_channels()

        assert len(rows) == 4
        assert len(cols) == 4
        assert list(rows) == [1, 1, 2, 2]
        assert list(cols) == [1, 2, 1, 2]

    def test_get_channels_file_not_found(self, data_manager):
        """Test channel retrieval with non-existent file."""
        data_manager.main_window.file_path = "/nonexistent/file.brw"

        with pytest.raises(FileNotFoundError):
            data_manager.get_channels()

    def test_normalize_strength_within_range(self, data_manager):
        """Test strength normalization within valid range."""
        data_manager.main_window.min_strength = 1.0
        data_manager.main_window.max_strength = 5.0

        result = data_manager.normalize_strength(3.0)
        # The actual implementation uses sqrt of the normalized value
        expected = math.sqrt((3.0 - 1.0) / (5.0 - 1.0))
        assert result == expected

    def test_normalize_strength_edge_cases(self, data_manager):
        """Test strength normalization edge cases."""
        data_manager.main_window.min_strength = 1.0
        data_manager.main_window.max_strength = 1.0  # Same min/max

        # Should raise ZeroDivisionError when min == max
        with pytest.raises(ZeroDivisionError):
            data_manager.normalize_strength(1.0)

    def test_setup_background_image_success(self, data_manager, tmp_path):
        """Test successful background image setup."""
        # Create test image file
        test_image = tmp_path / "test_image.jpg"
        test_image.write_text("fake image data")

        # Create test BRW file path
        test_brw = tmp_path / "test_data_slice1.brw"

        with patch('glob.glob', return_value=[str(test_image)]):
            # Mock the grid_widget directly
            data_manager.main_window.grid_widget = Mock()
            result = data_manager.setup_background_image(str(test_brw))

        assert result is True
        data_manager.main_window.grid_widget.setBackgroundImage.assert_called_once_with(str(test_image))

    def test_setup_background_image_no_match(self, data_manager, tmp_path):
        """Test background image setup with no matching image."""
        test_brw = tmp_path / "test_data_slice1.brw"

        with patch('glob.glob', return_value=[]):
            result = data_manager.setup_background_image(str(test_brw))

        assert result is False

    @patch('PyQt5.QtWidgets.QInputDialog.getItem')
    @patch('h5py.File')
    def test_load_discharges_success(self, mock_h5py, mock_input_dialog, data_manager):
        """Test successful discharge loading."""
        # Initialize discharges as empty dict instead of Mock
        data_manager.main_window.discharges = {}

        # Mock the input dialog to return a valid selection
        mock_input_dialog.return_value = ("1_1", True)

        # Mock HDF5 file structure
        mock_file = MagicMock()
        mock_h5py.return_value.__enter__.return_value = mock_file

        mock_tracked_group = MagicMock()
        mock_file.__getitem__.return_value = mock_tracked_group
        mock_tracked_group.keys.return_value = ['1_1', '1_2']

        # Mock timerange group and discharge data
        mock_timerange_group = MagicMock()
        mock_tracked_group.__getitem__.return_value = mock_timerange_group
        mock_timerange_group.keys.return_value = ['discharge_1', 'discharge_2']

        # Mock discharge dataset with attributes
        mock_discharge_dataset = MagicMock()
        mock_discharge_dataset.attrs = {
            'start_point': [1, 1],
            'end_point': [2, 2],
            'start_time': 1.0,
            'end_time': 2.0,
            'duration': 1.0,
            'length': 1.5,
            'avg_speed': 1.5,
            'points': np.array([[1, 1], [2, 2]]),
            'timestamps': np.array([1.0, 2.0])
        }
        mock_timerange_group.__getitem__.return_value = mock_discharge_dataset

        data_manager.main_window.file_path = "test.brw"
        data_manager.load_discharges()

        # Verify the dialog was called
        mock_input_dialog.assert_called_once()

    def test_get_min_max_strengths(self, data_manager):
        """Test min/max strength calculation."""
        # Setup test data in the format the method expects
        data_manager.main_window.active_channels = [(1, 1), (1, 2)]
        data_manager.main_window.data = np.zeros((64, 64), dtype=object)

        # Setup data for channel (1,1) -> index [0, 0]
        data_manager.main_window.data[0, 0] = {
            'SzTimes': np.array([[1.0, 2.0, 0.5], [3.0, 4.0, 1.5]]),
            'SETimes': np.array([[7.0, 8.0, 2.0]])
        }

        # Setup data for channel (1,2) -> index [0, 1]
        data_manager.main_window.data[0, 1] = {
            'SzTimes': np.array([[5.0, 6.0, 0.8]]),
            'SETimes': np.array([])  # Empty array
        }

        data_manager.get_min_max_strengths()

        assert data_manager.main_window.min_strength == 0.5
        assert data_manager.main_window.max_strength == 2.0

    def test_clear_found_discharges(self, data_manager):
        """Test clearing found discharges."""
        # Setup some discharge data
        data_manager.main_window.discharges = {(1, 1): ([1.0, 2.0], [0.5, 0.6])}

        data_manager.clear_found_discharges()

        assert len(data_manager.main_window.discharges) == 0


@pytest.mark.unit
class TestDataManagerIntegration:
    """Integration tests for DataManager with real file operations."""

    def test_full_data_loading_workflow(self, temp_hdf5_file, mock_main_window):
        """Test complete data loading workflow."""
        data_manager = DataManager(mock_main_window)
        mock_main_window.file_path = temp_hdf5_file

        # Test channel loading
        rows, cols = data_manager.get_channels()
        assert len(rows) == 4
        assert len(cols) == 4

        # Test that active_channels gets set correctly
        active_channels = list(zip(rows, cols))
        assert (1, 1) in active_channels
        assert (2, 2) in active_channels