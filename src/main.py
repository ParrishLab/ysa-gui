import os
import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Any, Optional, TYPE_CHECKING, List

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if TYPE_CHECKING:
    from src.widgets.GridWidget import GridWidget
    from src.widgets.GraphWidget import GraphWidget
    from src.widgets.LegendWidget import LegendWidget
import numpy.typing as npt
from urllib.request import pathname2url

import numpy as np
import pyqtgraph as pg
import qdarktheme
from PyQt5.QtCore import (
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QKeyEvent,
    QMouseEvent,
    QResizeEvent,
)
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QGraphicsEllipseItem,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
)
from sklearn.cluster import DBSCAN

from src.helpers.Constants import (
    ACTIVE,
    FONT_FAMILY,
    FONT_FILE,
    MAC,
    SE,
    SEIZURE,
    __version__ as VERSION,
    WIN,
)
from src.helpers.update.Updater import check_for_update
from src.managers.analysis_manager import AnalysisManager
from src.managers.data_manager import DataManager
from src.managers.event_handler import EventHandler
from src.managers.menu_manager import MenuManager
from src.managers.playback_manager import PlaybackManager
from src.managers.ui_manager import UIManager
from src.managers.visualization_manager import VisualizationManager
from src.threads.MatlabEngineThread import MatlabEngineThread
from src.threads.UpdateThread import UpdateThread
from src.widgets.ColorCell import ColorCell
from src.widgets.DocumentationViewer import DocumentationViewer
from src.widgets.GroupSelectionDialog import Group, GroupSelectionDialog
from src.widgets.Media import SaveChannelPlotsDialog
from src.widgets.VideoEditor import VideoEditor


class MainWindow(QMainWindow):
    gridUpdateRequested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"YSA GUI {VERSION}")

        # If true, the lag is way too much for the user to interact with the trace plots
        pg.setConfigOptions(antialias=False)

        # Initialize managers
        self.menu_manager = MenuManager(self)
        self.ui_manager = UIManager(self)
        self.data_manager = DataManager(self)
        self.analysis_manager = AnalysisManager(self)
        self.event_handler = EventHandler(self)
        self.playback_manager = PlaybackManager(self)
        self.visualization_manager = VisualizationManager(self)

        # Functions to run on startup that setup the main window
        self.setup_variables()
        self.menu_manager.setup_menu_bar()
        self.ui_manager.setup_main_window()
        self.analysis_manager.setup_analysis_thread()
        self.setup_matlab_thread()
        self.set_widgets_enabled()

    def setup_variables(self):
        """Initialize all instance variables"""
        # File and recording settings
        self.file_path = None
        self.recording_length = None
        self.sampling_rate = 100
        self.time_vector = None
        self.data = None

        # Channel settings
        self.active_channels = None
        self.selected_channel = None
        self.plotted_channels: list[Optional[ColorCell]] = [None] * 4
        self.selected_subplot = None

        # Raster settings
        self.raster_tooltip = None
        self.raster_downsample_factor = 1
        self.opacity = 1.0
        self.do_show_spread_lines = False
        self.do_show_prop_lines = False
        self.raster_plot = None

        # Recording and video settings
        self.is_recording_video = False

        # Region settings
        self.current_region = None
        self.custom_region = None
        self.last_skip_time = 0

        # Peak and discharge settings
        self.peak_thresholds = {}
        self.discharges = {}
        self.show_discharge_peaks = False
        self.active_discharges = []
        self.snr_threshold = 35
        self.current_discharge_index = 0
        self.is_auto_analyzing = False
        self.low_pass_cutoff = 35
        self.discharge_starts_points = []
        self.discharge_start_dialog = None
        self.last_found_discharge_time = None
        self.track_discharge_beginnings = False

        # Min and max values
        self.overall_min_voltage = None
        self.overall_max_voltage = None
        self.min_strength = None
        self.max_strength = None

        # UI settings
        self.groups = []
        self.left_pane = None
        self.right_pane = None
        self.grid_widget: Optional['GridWidget'] = None
        self.graph_widget: Optional['GraphWidget'] = None
        self.legend_widget: Optional['LegendWidget'] = None
        self.show_order_checkbox: Optional[QCheckBox] = None
        self.lock_to_playhead = False
        self.do_show_false_color_map = True
        self.do_show_events = True
        self.order_amount = 10

        # Analysis settings
        self.n_std_dev = 4
        self.distance = 10
        self.chunk_size = 256
        self.overlap = 0
        self.fs_range = (0.5, 50)
        self.centroids = []
        self.eps = 4.8
        self.min_samples = 4
        self.max_distance = 10
        self.bin_size = 0.0133
        self.signal_analyzer = None
        self.use_cpp: bool = True

        # Miscellaneous
        self.seized_cells = []
        self.arrow_items = []
        self.prop_arrow_items = []
        self.markers = []
        self.spaital_sections = []

        # Additional variables
        self.need_confirmation = False

    def setup_matlab_thread(self):
        """Setup MATLAB engine thread"""
        def on_engine_started(eng: Any):
            self.engine_started = True
            self.eng = eng
            self.set_widgets_enabled()

        def on_engine_error(error: str):
            print(f"Error starting MATLAB engine: {error}")
            self.use_cpp = True
            self.eng = None
            self.set_widgets_enabled()

        cwd = os.path.dirname(os.path.realpath(__file__))
        matlab_path = os.path.join(cwd, "helpers", "mat")

        self.matlab_thread = MatlabEngineThread(cwd, matlab_path)
        self.matlab_thread.engine_started.connect(on_engine_started)
        self.matlab_thread.error_occurred.connect(on_engine_error)
        self.matlab_thread.start()
        self.eng = None
        self.use_cpp = True
        self.ui_manager.cpp_mode_checkbox.setChecked(True)
        self.engine_started = False

    def set_widgets_enabled(self):
        """Enable/disable widgets based on current state"""
        # Enable analysis widgets if file is loaded and engine is ready
        analysis_ready = self.file_path is not None and (
            self.engine_started or self.use_cpp)
        self.ui_manager.set_analysis_widgets_enabled(analysis_ready)

        # Enable playback and data-dependent widgets if data is loaded
        data_loaded = self.data is not None
        self.ui_manager.set_playback_widgets_enabled(data_loaded)
        self.menu_manager.set_data_dependent_actions_enabled(data_loaded)

    # Event handling methods
    def resizeEvent(self, a0: QResizeEvent | None):
        super().resizeEvent(a0)
        self.visualization_manager.redraw_arrows()

    def mousePressEvent(self, a0: QMouseEvent | None):
        self.event_handler.handle_mouse_press(a0)
        super().mousePressEvent(a0)

    def keyPressEvent(self, a0: QKeyEvent | None):
        self.event_handler.handle_key_press(a0)

    def keyReleaseEvent(self, a0: QKeyEvent | None):
        self.event_handler.handle_key_release(a0)

    # File handling methods

    def open_file(self):
        """Open and load a BRW file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            directory="/Users/booka66/Jake-Squared/Sz_SE_Detection/",
            filter="BRW Files (*.brw)",
        )

        if file_path:
            print("Selected file path:", file_path)
            file_path = os.path.normpath(file_path)
            self.file_path = file_path

            try:
                baseName = os.path.basename(file_path)
                self.setWindowTitle(f"YSA GUI {VERSION} - {baseName}")

                # Try to find and set background image
                if not self.data_manager.setup_background_image(file_path):
                    print("No matching background image found")

            except Exception as e:
                print(f"Error: {e}")

        self.set_widgets_enabled()

    def upload_image(self):
        """Upload MEA grid background image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            directory="/Users/booka66/Jake-Squared/Sz_SE_Detection/",
            filter="Image Files (*.jpg *.png *.jpeg *.bmp)",
        )

        if self.grid_widget is None:
            return

        self.grid_widget.setBackgroundImage(file_path)

    def viewHDF5(self):
        """View HDF5 file contents"""
        from src.widgets.HDFViewer import HDF5Viewer

        if self.file_path is not None:
            if hasattr(self, "hdf5_viewer") and self.hdf5_viewer is not None:
                self.hdf5_viewer.raise_()
                self.hdf5_viewer.activateWindow()
            else:
                self.hdf5_viewer = HDF5Viewer(self.file_path, parent=self)
                self.hdf5_viewer.destroyed.connect(
                    lambda: setattr(self, "hdf5_viewer", None)
                )
                self.hdf5_viewer.show()

    def open_docs(self):
        """Open documentation viewer"""
        cwd = Path(__file__).resolve().parent
        print(f"Current working directory: {cwd}")
        file_path = cwd / "html" / "index.html"
        print(f"Opening documentation: {file_path}")
        if not file_path.exists():
            # Must not be running from the pre-built executable
            file_path = cwd / ".." / "docs" / "_build" / "html" / "index.html"

        if not file_path.exists():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(f"Documentation not found at {file_path}.")
            msg.setWindowTitle("Documentation")
            msg.exec_()
            return

        url = f"file://{pathname2url(str(file_path.absolute()))}"
        self.doc_viewer = DocumentationViewer(url)
        self.doc_viewer.show()

    # Toggle methods for UI elements
    def toggle_events(self, checked: bool):
        self.do_show_events = checked
        self.update_grid()

    def toggle_raster_color_mode(self):
        if self.raster_plot:
            self.raster_plot.toggle_color_mode()

    def toggle_false_color_map(self, checked: bool):
        self.do_show_false_color_map = checked
        self.update_grid()

    def toggle_regions(self, checked: bool):
        if self.graph_widget is None:
            return

        self.graph_widget.do_show_regions = checked
        if checked:
            self.graph_widget.show_regions()
        else:
            self.graph_widget.hide_regions()

    def toggle_events_overlay(self, checked: bool):
        if self.grid_widget is None:
            return
        self.grid_widget.toggle_overlay(checked)

    def toggle_legend(self, checked: bool):
        if self.legend_widget is None:
            return
        self.legend_widget.setVisible(checked)
        if self.data is not None:
            self.visualization_manager.redraw_arrows()
            self.update_grid()

    def toggle_mini_map(self, checked: bool):
        if self.graph_widget is None:
            return
        self.graph_widget.toggle_mini_map(checked)

    def toggle_antialiasing(self, checked: bool):
        if self.graph_widget is None:
            return
        pg.setConfigOptions(antialias=checked)
        for i in range(4):
            if self.plotted_channels[i] is not None:
                self.graph_widget.plot_widgets[i].clear()

                curve = self.graph_widget.plot_widgets[i].plot(
                    pen=pg.mkPen("k", width=3)
                )
                curve.setData(
                    self.graph_widget.x_data[i], self.graph_widget.y_data[i]
                )
                curve.setDownsampling(auto=True, method="peak", ds=100)
                curve.setClipToView(True)

                self.graph_widget.plot_widgets[i].addItem(
                    self.graph_widget.red_lines[i]
                )

        self.update_grid()

    def toggle_spectrogram(self, checked: bool):
        if checked:
            self.visualization_manager.show_spectrograms()
        else:
            self.visualization_manager.hide_spectrograms()

    def toggle_prop_lines(self, checked: bool):
        self.do_show_prop_lines = checked
        if checked:
            self.visualization_manager.show_prop_lines()
        else:
            self.visualization_manager.hide_prop_lines()

    def toggle_playheads(self, checked: bool):
        if self.graph_widget is None:
            return
        for red_line in self.graph_widget.red_lines:
            red_line.setVisible(checked)
        if hasattr(self, 'raster_plot') and self.raster_plot and hasattr(self.raster_plot, 'raster_red_line'):
            raster_red_line = self.raster_plot.raster_red_line
            if raster_red_line:
                raster_red_line.setVisible(checked)

    def toggle_cpp_mode(self, state: Qt.CheckState):
        self.use_cpp = state == Qt.CheckState.Checked
        self.set_widgets_enabled()

    def toggle_lines(self, checked: bool):
        self.do_show_spread_lines = checked
        if checked:
            self.visualization_manager.show_spread_lines()
        else:
            self.visualization_manager.hide_spread_lines()

    def toggle_order(self, state: Qt.CheckState):
        if state == Qt.CheckState.Checked:
            self.visualization_manager.show_seizure_order()
        else:
            self.visualization_manager.hide_seizure_order()

    # Dialog and settings methods
    def open_discharge_start_dialog(self):
        if (
            self.discharge_start_dialog is None
            or self.discharge_start_dialog.isVisible()
        ):
            return
        self.discharge_start_dialog.show()

    def set_bin_size(self):
        bin_size, ok = QInputDialog.getText(
            self,
            "Set Bin Size",
            "Size:",
            QLineEdit.EchoMode.Normal,
            str(self.bin_size),
        )

        if ok:
            try:
                bin_size = float(bin_size)
                if bin_size <= 0:
                    raise ValueError("Bin size must be greater than 0.")
                self.bin_size = bin_size
            except ValueError as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText(str(e))
                msg.setWindowTitle("Invalid Bin Size")
                msg.exec_()

    def set_order_amount(self):
        order_amount, ok = QInputDialog.getInt(
            self,
            "Set Order Amount",
            "Amount:",
            self.order_amount,
        )

        if ok:
            if order_amount < 1:
                order_amount = 1
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText("Order amount must be greater than 0.")
                msg.setWindowTitle("Invalid Order Amount")
                msg.exec_()

            self.order_amount = order_amount
            if self.show_order_checkbox is not None:
                self.toggle_order(self.show_order_checkbox.checkState())

    def create_groups(self):
        if self.grid_widget is None:
            return
        dialog = GroupSelectionDialog(
            self, self.grid_widget.image_path, self.active_channels
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            groups: List[Group] = dialog.get_groups()
            self.groups = groups
            for group in groups:
                for row, col in group.channels:
                    cell = self.grid_widget.cells[row - 1][col - 1]
                    color = [int(255 * x) for x in group.color]
                    cell.setColor(QColor(*color), 1, self.opacity)
            if self.raster_plot:
                self.raster_plot.set_groups(groups)
                self.raster_plot.update_raster_plot_data()

    # Remaining critical methods from original
    def initialize_data(self):
        self.data_manager.initialize_data()

    def update_tab_layout(self, index: int):
        """Update tab layout when switching tabs"""
        if not self.is_recording_video:
            print(f"Updating tab layout: {index}")
            if self.main_tab_widget.currentWidget() == self.main_tab:
                if self.left_pane:
                    self.left_pane.setVisible(True)
                if self.right_pane:
                    self.right_pane.setVisible(True)
                if self.tab_widget:
                    if self.tab_widget.currentIndex() == 0:
                        self.grid_widget.setVisible(True)
                        self.second_plot_widget.setVisible(False)
                        self.opacity_label.setVisible(True)
                        self.opacity_slider.setVisible(True)
                    elif self.tab_widget.currentIndex() == 1:
                        self.grid_widget.setVisible(False)
                        self.second_plot_widget.setVisible(True)
                        self.opacity_label.setVisible(False)
                        self.opacity_slider.setVisible(False)
            elif self.main_tab_widget.currentWidget() == self.stats_tab:
                self.left_pane.setVisible(False)
                self.right_pane.setVisible(False)
                self.visualization_manager.show_statistics_widgets()

    def clear_plots(self):
        """Clear all plotted channels"""
        for i in range(4):
            channel = self.plotted_channels[i]
            if channel is not None:
                channel.plotted_state = False
                channel.plotted_shape = None
                channel.update()
            self.graph_widget.plot_widgets[i].clear()
            self.graph_widget.x_data[i] = None
            self.graph_widget.y_data[i] = None
            self.graph_widget.plot_widgets[i].setTitle("Select Channel")
            self.graph_widget.plot_widgets[i].setLabel("bottom", "sec")
            self.graph_widget.plot_widgets[i].setLabel("left", "mV")
            for item in self.graph_widget.plot_widgets[i].items():
                if isinstance(
                    item, (pg.LinearRegionItem,
                           pg.ScatterPlotItem, pg.ImageItem)
                ):
                    self.graph_widget.plot_widgets[i].removeItem(item)

        self.plotted_channels = [None] * 4
        self.graph_widget.trace_curves = [None] * 4
        self.grid_widget.update()
        self.current_region = None
        self.update_raster_plotted_channels()

    def update_raster_plotted_channels(self):
        """Update raster plot with currently plotted channels"""
        if self.raster_plot is not None:
            raster_plotted_channels = []
            for i in range(4):
                if self.plotted_channels[i] is not None:
                    row, col = (
                        self.plotted_channels[i].row + 1,
                        self.plotted_channels[i].col + 1,
                    )
                    raster_plotted_channels.append((row, col))
            self.raster_plot.set_plotted_channels(raster_plotted_channels)

    def set_raster_order(self, index):
        """Set raster plot ordering"""
        from src.widgets.RasterPlot import RasterPlot

        if self.raster_plot is None:
            self.raster_plot = RasterPlot(
                self.data,
                self.sampling_rate,
                self.active_channels,
                self.raster_downsample_factor,
            )
            self.raster_plot.set_main_window(self)
        if index == 0:
            self.raster_plot.set_raster_order("default")
            if self.show_order_checkbox is not None:
                self.show_order_checkbox.setCheckState(False)
                self.show_order_checkbox.setEnabled(False)
        elif index == 1:
            self.raster_plot.set_raster_order("seizure")
            if self.show_order_checkbox is not None:
                self.show_order_checkbox.setEnabled(True)
        elif index == 2:
            self.raster_plot.set_raster_order("SE")
            if self.show_order_checkbox is not None:
                self.show_order_checkbox.setEnabled(True)

        if self.show_order_checkbox is not None:
            self.toggle_order(self.show_order_checkbox.checkState())

        if self.show_order_checkbox is not None and self.show_order_checkbox.isChecked():
            self.visualization_manager.show_seizure_order()
        else:
            self.visualization_manager.hide_seizure_order()

        self.update_raster_plotted_channels()

    def update_raster(self):
        """Update raster plot"""
        from src.widgets.RasterPlot import RasterPlot

        if self.raster_plot is None:
            self.raster_plot = RasterPlot(
                self.data,
                self.sampling_rate,
                self.active_channels,
                self.raster_downsample_factor,
            )
            self.raster_plot.set_main_window(self)
        else:
            self.raster_plot.downsample_factor = self.raster_downsample_factor

        self.raster_plot.generate_raster()
        self.raster_plot.create_raster_plot(self.second_plot_widget)

    def set_grid_opacity(self, value):
        """Set grid opacity"""
        self.opacity = value / 100.0
        for row in range(self.grid_widget.rows):
            for col in range(self.grid_widget.cols):
                cell = self.grid_widget.cells[row][col]
                color = cell.brush().color()
                cell.setColor(color, 1, self.opacity)

    def deselect_cell(self):
        """Deselect currently selected cell"""
        if self.selected_channel is not None and len(self.selected_channel) > 0:
            row, col = self.selected_channel
            self.grid_widget.cells[row][col].clicked_state = False
            self.grid_widget.cells[row][col].update()
            self.selected_channel = None
            self.grid_widget.hide_all_selected_tooltips()

    def set_custom_region(self):
        """Set custom region from current plot view"""
        start, stop = self.graph_widget.plot_widgets[0].viewRange()[0]
        self.custom_region = (start, stop)

    # Complex grid update method - keeping from original for now
    def update_grid(self, first=False, red=True):
        """Update grid visualization - core method from original"""
        if first:
            self.initialize_data()
            self.data_manager.get_min_max_strengths()

        current_time = self.ui_manager.progress_bar.value() / self.sampling_rate
        self.need_confirmation = False

        if self.do_show_prop_lines and self.custom_region:
            self.handle_prop_lines(current_time)
        else:
            self.clear_discharges(current_time)

        if self.do_show_false_color_map:
            colors, min_gray_value, max_gray_value = self.get_false_color_map_colors(
                current_time
            )
            high_luminance_cells = []
            if self.track_discharge_beginnings:
                gray_range = max_gray_value - min_gray_value

                for row in self.grid_widget.cells:
                    for cell in row:
                        cell.is_high_luminance = False

                if gray_range > 50:
                    if (
                        self.last_found_discharge_time is None
                        or current_time - self.last_found_discharge_time > 0.5
                    ):
                        luminance_threshold = np.percentile(
                            [cell.get_luminance() for cell in self.cells], 96
                        )

                        high_luminance_cells = self.get_high_luminance_cells(
                            luminance_threshold
                        )
                        high_luminance_indices = [
                            self.active_channels.index(
                                (cell.row + 1, cell.col + 1))
                            for cell in high_luminance_cells
                        ]
                        if red:
                            for index in high_luminance_indices:
                                colors[index] = self.visualization_manager.blend_colors(
                                    colors[index], QColor(
                                        255, 0, 0, int(255 * 0.3)), 1
                                )

                        if len(high_luminance_cells) > 0:
                            self.need_confirmation = True
                            self.discharge_start_dialog.current_time = current_time

        else:
            colors = [ACTIVE] * len(self.active_channels)

        newly_seized_cells = []
        newly_se_cells = []
        cells_to_remove = []

        found_se = [False] * len(self.active_channels)
        found_seizure = [False] * len(self.active_channels)

        for i, (row, col) in enumerate(self.active_channels):
            if self.do_show_events:
                self.get_new_se_cells(
                    row, col, current_time, colors, i, newly_se_cells, found_se
                )
                self.get_new_seizure_cells(
                    row,
                    col,
                    current_time,
                    colors,
                    i,
                    newly_seized_cells,
                    found_seizure,
                    found_se,
                )

            if not found_se[i] and not found_seizure[i]:
                self.cells[i].setColor(colors[i], 1, self.opacity)
                if self.do_show_spread_lines and (row, col) in self.seized_cells:
                    cells_to_remove.append((row, col))

        if self.do_show_spread_lines:
            for row, col in newly_seized_cells:
                self.seized_cells.append((row, col))
                self.visualization_manager.draw_spread_arrows(
                    row, col, "seizure")
            for row, col in newly_se_cells:
                self.seized_cells.append((row, col))
                self.visualization_manager.draw_spread_arrows(row, col, "SE")
            for row, col in cells_to_remove:
                self.seized_cells.remove((row, col))
                self.visualization_manager.remove_seizure_arrows(row, col)

        self.grid_widget.update()

    # Additional methods needed for grid update
    def handle_prop_lines(self, current_time):
        """Handle propagation lines display"""
        start, stop = self.custom_region
        discharged_cells = []
        for row, col in self.active_channels:
            if (row - 1, col - 1) in self.discharges:
                discharge_times, _ = self.discharges[(row - 1, col - 1)]
                for discharge_time in discharge_times:
                    if (
                        start <= discharge_time <= stop
                        and abs(discharge_time - current_time) < self.bin_size
                    ):
                        discharged_cells.append((row, col))
                        break

            for item in self.centroids:
                self.grid_widget.scene.removeItem(item)
            self.centroids.clear()

        if discharged_cells:
            X = np.array(discharged_cells)
            db = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(X)
            labels = db.labels_

            unique_labels = set(labels)
            centroids = []
            for label in unique_labels:
                if label != -1:
                    cluster_points = X[labels == label]
                    centroid = np.mean(cluster_points, axis=0)
                    centroids.append(centroid)

                    centroid_row, centroid_col = centroid
                    centroid_item = QGraphicsEllipseItem(0, 0, 10, 10)
                    centroid_item.setBrush(Qt.red)
                    centroid_item.setPos(
                        centroid_col *
                        self.grid_widget.cells[0][0].rect().width() - 5,
                        centroid_row *
                        self.grid_widget.cells[0][0].rect().height() - 5,
                    )
                    self.grid_widget.scene.addItem(centroid_item)
                    self.centroids.append(centroid_item)

            self.cluster_tracker.update(centroids, current_time)

            cell_width = self.grid_widget.cells[0][0].rect().width()
            cell_height = self.grid_widget.cells[0][0].rect().height()
            self.cluster_tracker.draw_cluster_lines(
                self.grid_widget.scene, cell_width, cell_height
            )
        else:
            self.cluster_tracker.update([], current_time)
            cell_width = self.grid_widget.cells[0][0].rect().width()
            cell_height = self.grid_widget.cells[0][0].rect().height()
            self.cluster_tracker.draw_cluster_lines(
                self.grid_widget.scene, cell_width, cell_height
            )

    def clear_discharges(self, current_time):
        """Clear discharge visualization"""
        for item in self.centroids:
            self.grid_widget.scene.removeItem(item)
        self.centroids.clear()

        self.cluster_tracker.update([], current_time)
        cell_width = self.grid_widget.cells[0][0].rect().width()
        cell_height = self.grid_widget.cells[0][0].rect().height()
        self.cluster_tracker.draw_cluster_lines(
            self.grid_widget.scene, cell_width, cell_height
        )

    def get_false_color_map_colors(self, current_time):
        """Get false color map colors"""
        bin_start = int((current_time - self.bin_size) * self.sampling_rate)
        bin_end = int((current_time + self.bin_size) * self.sampling_rate)
        bin_voltages = [signal[bin_start:bin_end] for signal in self.signals]

        if self.overall_min_voltage is None or self.overall_max_voltage is None:
            ignore_samples = int(20 * self.sampling_rate)
            trimmed_signals = self.signals[:, ignore_samples:-ignore_samples]
            self.overall_min_voltage = np.min(trimmed_signals)
            self.overall_max_voltage = np.max(trimmed_signals)

        voltage_ranges = []
        for voltages in bin_voltages:
            if voltages.size > 0:
                min_voltage = np.min(voltages)
                max_voltage = np.max(voltages)
                log_range = self.log_normalize(max_voltage) - self.log_normalize(
                    min_voltage
                )
                voltage_ranges.append(log_range)
            else:
                voltage_ranges.append(None)

        colors = []
        min_gray_value = float("inf")
        max_gray_value = float("-inf")
        for voltage_range in voltage_ranges:
            if voltage_range is None:
                color = ACTIVE
            else:
                color = self.voltage_range_to_color(voltage_range)
            gray_value = color.getRgb()[0]
            if gray_value < min_gray_value:
                min_gray_value = gray_value
            if gray_value > max_gray_value:
                max_gray_value = gray_value

            colors.append(color)

        return colors, min_gray_value, max_gray_value

    def rgb_to_grayscale(self, rgb) -> QColor:
        """Convert RGB to grayscale"""
        constant = int(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
        return QColor(constant, constant, constant)

    def log_normalize(self, voltage):
        """Log normalize voltage"""
        epsilon = 1e-10
        normalized = (voltage - self.overall_min_voltage) / (
            self.overall_max_voltage - self.overall_min_voltage
        )
        return np.log1p(normalized + epsilon)

    def voltage_range_to_color(self, log_range):
        """Convert voltage range to color"""
        if log_range is None:
            return ACTIVE
        sensitivity = 5
        hue = int((1 - np.tanh(sensitivity * log_range)) * 240)
        saturation = 255
        value = 255 if log_range > 0 else 128

        color = QColor.fromHsv(hue, saturation, value)
        grayscale = self.rgb_to_grayscale(color.getRgb())

        return grayscale

    def get_new_se_cells(
        self, row, col, current_time, colors, i, newly_se_cells, found_se
    ):
        """Get newly SE cells"""
        se_times = np.array(self.se_times_list[i])
        if se_times.size > 0:
            se_mask = (se_times[:, 0] <= current_time) & (
                current_time <= se_times[:, 1]
            )
            if np.any(se_mask):
                se_index = np.where(se_mask)[0][0]
                strength = (
                    self.data_manager.normalize_strength(se_times[se_index, 2])
                    if not self.use_cpp
                    else 1
                )
                if self.do_show_false_color_map:
                    se_color = self.visualization_manager.blend_colors(
                        colors[i], SE, strength)
                else:
                    se_color = SE
                self.cells[i].setColor(se_color, strength**0.25, self.opacity)
                found_se[i] = True
                if self.do_show_spread_lines and (row, col) not in self.seized_cells:
                    newly_se_cells.append((row, col))

    def get_new_seizure_cells(
        self,
        row,
        col,
        current_time,
        colors,
        i,
        newly_seized_cells,
        found_seizure,
        found_se,
    ):
        """Get newly seized cells"""
        seizure_times = np.array(self.seizure_times_list[i])
        if not found_se[i] and seizure_times.size > 0:
            seizure_mask = (seizure_times[:, 0] <= current_time) & (
                current_time <= seizure_times[:, 1]
            )
            if np.any(seizure_mask):
                seizure_index = np.where(seizure_mask)[0][0]
                strength = (
                    self.data_manager.normalize_strength(
                        seizure_times[seizure_index, 2])
                    if not self.use_cpp
                    else 1
                )
                if self.do_show_false_color_map:
                    seizure_color = self.visualization_manager.blend_colors(
                        colors[i], SEIZURE, strength)
                else:
                    seizure_color = SEIZURE
                self.cells[i].setColor(seizure_color, strength, self.opacity)
                found_seizure[i] = True
                if self.do_show_spread_lines and (row, col) not in self.seized_cells:
                    newly_seized_cells.append((row, col))

    def get_high_luminance_cells(self, luminance_threshold):
        """Get high luminance cells for discharge detection"""
        top_cells = [
            cell for cell in self.cells if cell.get_luminance() >= luminance_threshold
        ]
        points = np.array([(cell.row, cell.col) for cell in top_cells])
        for cell in top_cells:
            cell.setColor(QColor(0, 255, 0), 1, self.opacity)

        db = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(points)

        labels = db.labels_
        unique_labels = set(labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)

        high_luminance_cells = []
        for cell, label in zip(top_cells, labels):
            if label in unique_labels:
                high_luminance_cells.append(cell)
                cell.is_high_luminance = True

        return high_luminance_cells

    def show_video_editor(self):
        """Show video editor dialog"""
        editor = VideoEditor(self)
        editor.set_markers(self.markers)
        editor.exec_()

    def save_channel_plots(self):
        """Save channel plots dialog"""
        dialog = SaveChannelPlotsDialog(self)
        dialog.exec_()

    def save_channel_plot(self, plot_index):
        """Save single channel plot dialog"""
        dialog = SaveChannelPlotsDialog(self, plot_index)
        dialog.exec_()


# Font handling functions
def get_font_path():
    """Get font path based on platform"""
    if getattr(sys, "frozen", False):
        if sys.platform == MAC:
            base_path = os.path.join(os.path.dirname(
                sys.executable), "..", "Resources")
        else:
            base_path = os.path.join(
                os.path.dirname(sys.executable), "_internal")
        return os.path.join(base_path, FONT_FILE)
    else:
        return os.path.join(
            os.path.dirname(__file__), "..", "resources", "fonts", FONT_FILE
        )


def get_font_size(app: QApplication):
    """Get appropriate font size for screen"""
    screen = app.primaryScreen()
    dpi = screen.physicalDotsPerInch()

    screen_width = screen.size().width() / dpi
    screen_height = screen.size().height() / dpi
    screen_diagonal = np.sqrt(screen_width ** 2 + screen_height ** 2)

    # Normalize against an average screen size (e.g., 15 inches)
    if screen_diagonal >= 13:
        return 12
    else:
        return 8


# Platform detection
if sys.platform == MAC:
    font_dir = "/Library/Fonts/"
elif sys.platform == WIN:
    font_dir = os.path.join(os.environ["WINDIR"], "Fonts")
else:
    print("Unsupported operating system.")
    sys.exit(1)


def confirm_latest_version(window):
    """Check for updates and offer to update"""
    def handle_update_button(button):
        def on_update_completed(success):
            window.download_msg.close()

            if success:
                sys.exit()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Update process failed.")
                msg.setWindowTitle("Update")
                msg.exec_()

        if button.text() == "&Yes":
            window.download_msg = QMessageBox(window)
            window.download_msg.setIcon(QMessageBox.Information)
            window.download_msg.setText("Downloading update...")
            window.download_msg.setWindowTitle("Update in Progress")
            window.download_msg.setStandardButtons(QMessageBox.NoButton)
            window.download_msg.show()

            window.update_thread = UpdateThread(window.latest_release)
            window.update_thread.update_completed.connect(on_update_completed)
            window.update_thread.start()

    update_available, window.latest_release = check_for_update()
    if update_available:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("An update is available. Would you like to update now?")
        msg.setWindowTitle("Update")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.buttonClicked.connect(handle_update_button)
        msg.exec_()
    else:
        print("No update available.")


def signal_handler(sig: int, frame: Optional[FrameType]) -> None:
    """Handle Ctrl+C gracefully"""
    print("\nShutting down application...")
    QApplication.quit()
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    app = QApplication(sys.argv)
    qdarktheme.setup_theme()

    # Enable Ctrl+C handling in Qt
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Allow Python to handle signals
    timer.start(500)

    font_path = get_font_path()
    font_id = QFontDatabase.addApplicationFont(font_path)

    font_size = get_font_size(app)

    if font_id == -1:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText(
            f"Failed to load required font: {FONT_FAMILY}\n"
            f"Attempted to load from: {font_path}\n"
            "The application may not display correctly."
        )
        msg.setWindowTitle("Font Loading Error")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec_()
    else:
        print("Font loaded successfully")
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            loaded_family = families[0]
            print(f"Font loaded successfully from: {font_path}")
            print(f"Using font family: {loaded_family}")
            font = QFont(loaded_family, font_size)
            app.setFont(font)
        else:
            print("Warning: Font file loaded but no family names found")
            font = QFont(FONT_FAMILY, font_size)
            app.setFont(font)

    window = MainWindow()
    window.showMaximized()
    confirm_latest_version(window)
    try:
        if sys.argv[1]:
            window.file_path = sys.argv[1]
            window.set_widgets_enabled()
            window.analysis_manager.run_analysis()
    except IndexError:
        print("No file path provided")
    sys.exit(app.exec_())
