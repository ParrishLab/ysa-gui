import os
import math
import numpy as np
import numpy.typing as npt
import h5py
from typing import Union
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton
from PyQt5.QtGui import QColor
from sklearn.cluster import DBSCAN
from scipy.signal import spectrogram
import pyqtgraph as pg

from helpers.Constants import SE, SEIZURE
from threads.AnalysisThread import AnalysisThread
from threads.DischargeFinderThread import DischargeFinderThread


class AnalysisManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def setup_analysis_thread(self):
        """Setup analysis thread and loading dialog"""
        from widgets.LoadingDialog import LoadingDialog

        self.main_window.loading_dialog = LoadingDialog(self.main_window)
        self.main_window.loading_dialog.analysis_cancelled.connect(
            self.main_window.cancel_analysis)

        self.main_window.analysis_thread = AnalysisThread(self.main_window)
        self.main_window.analysis_thread.progress_updated.connect(
            self.main_window.loading_dialog.update_progress
        )
        self.main_window.analysis_thread.analysis_completed.connect(
            self.main_window.on_analysis_completed
        )

    def run_analysis(self):
        """Run analysis based on button clicked"""
        button_clicked = self.main_window.sender()
        if button_clicked is not None:
            if button_clicked.text().__contains__("Run"):
                print("Running analysis")
                do_analysis = True
            elif button_clicked.text().__contains__("RAM"):
                print(f"Button text: {button_clicked.text()}")
                print("Running view with low RAM")
                do_analysis = False
            else:
                print("Running view without analysis")
                do_analysis = False
        else:
            do_analysis = False

        try:
            if self.main_window.data is not None:
                if not self._confirm_analysis_overwrite():
                    return
                self._reset_analysis_state()

            self._prepare_analysis(do_analysis)

        except Exception as e:
            print(f"Error: {e}")

    def _confirm_analysis_overwrite(self):
        """Confirm overwriting existing analysis"""
        alert = QMessageBox(self.main_window)
        alert.setText(
            "Loaded analysis will be deleted. Are you sure you would like to continue?"
        )
        alert.setStandardButtons(QMessageBox.Yes | QMessageBox.Abort)
        alert.setIcon(QMessageBox.Warning)
        button = alert.exec()

        return button != QMessageBox.Abort

    def _reset_analysis_state(self):
        """Reset analysis state before new analysis"""
        import gc

        self.main_window.graph_widget.update_red_lines(
            0, self.main_window.sampling_rate)
        self.main_window.ui_manager.order_combo.setCurrentIndex(0)
        self.main_window.show_order_checkbox.setCheckState(False)
        self.main_window.toggle_order(
            self.main_window.show_order_checkbox.checkState())
        self.main_window.raster_plot = None
        self.main_window.analysis_thread = AnalysisThread(self.main_window)
        self.main_window.analysis_thread.progress_updated.connect(
            self.main_window.loading_dialog.update_progress
        )
        self.main_window.analysis_thread.analysis_completed.connect(
            self.main_window.on_analysis_completed
        )
        self.main_window.hide_spread_lines()
        self.main_window.show_discharge_peaks = False
        self.main_window.clear_found_discharges()
        self.main_window.arrow_items = []
        self.main_window.prop_arrow_items = []
        self.main_window.seized_cells = []
        self.main_window.clear_plots()
        self.main_window.min_strength = None
        self.main_window.max_strength = None
        self.main_window.recording_length = None
        self.main_window.time_vector = None
        del self.main_window.data
        self.main_window.data = None
        self.main_window.active_channels = []
        self.main_window.selected_channel = []
        self.main_window.plotted_channels = [None] * 4
        self.main_window.selected_subplot = None
        self.main_window.min_voltage = None
        self.main_window.max_voltage = None
        self.main_window.overall_min_voltage = None
        self.main_window.overall_max_voltage = None
        self.main_window.centroids = []
        self.main_window.cluster_tracker.clear_plot(
            self.main_window.grid_widget.scene)
        self.main_window.cluster_tracker.clear()
        self.main_window.cluster_tracker.seizures.clear()
        self.main_window.cluster_tracker.seizure_graphics_items.clear()
        self.main_window.create_grid()
        self.main_window.set_widgets_enabled()
        gc.collect()

    def _prepare_analysis(self, do_analysis):
        """Prepare and start analysis thread"""
        self.main_window.ui_manager.run_button.setEnabled(False)
        self.main_window.update()

        selected_drive = self._get_drive()
        if selected_drive:
            temp_data_path = os.path.join(selected_drive, "temp_data")
        else:
            temp_data_path = os.path.expanduser("~/temp_data")

        print("Temp data path:", temp_data_path)

        with h5py.File(self.main_window.file_path, "r") as f:
            channels = f["/3BRecInfo/3BMeaStreams/Raw/Chs"][()]
            num_channels = len(channels)
            print(f"Number of channels: {num_channels}")
            self.main_window.loading_dialog.progress_bar.setRange(
                0, num_channels)

        self.main_window.analysis_thread.file_path = self.main_window.file_path
        self.main_window.analysis_thread.do_analysis = do_analysis
        self.main_window.analysis_thread.use_low_ram = (
            True if self.main_window.low_ram_checkbox.isChecked() else False
        )
        self.main_window.analysis_thread.eng = self.main_window.eng
        self.main_window.analysis_thread.use_cpp = self.main_window.use_cpp
        self.main_window.analysis_thread.temp_data_path = temp_data_path
        self.main_window.loading_dialog.show()
        self.main_window.analysis_thread.start()

    def _get_drive(self):
        """Get available drive for temp data"""
        drives = []
        for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive_path = f"{drive}:"
            if os.path.exists(drive_path):
                try:
                    temp_file_path = os.path.join(
                        drive_path, "temp_write_test.txt")
                    with open(temp_file_path, "w") as f:
                        f.write("test")
                    os.remove(temp_file_path)
                    drives.append(drive_path)
                except (IOError, OSError):
                    pass
        if drives:
            return drives[0]
        else:
            return None

    def on_analysis_completed(self):
        """Handle analysis completion"""
        from widgets.RasterPlot import RasterPlot
        from widgets.DischargeStartDialog import DischargeStartDialog

        try:
            from helpers.extensions.signal_analyzer import SignalAnalyzer
        except ImportError:
            print("Failed to import signal_analyzer module.")
            SignalAnalyzer = None

        self.main_window.loading_dialog.hide()
        self.main_window.data = self.main_window.analysis_thread.data

        self.main_window.min_strength = self.main_window.analysis_thread.min_strength
        self.main_window.max_strength = self.main_window.analysis_thread.max_strength
        self.main_window.recording_length = self.main_window.analysis_thread.recording_length
        self.main_window.sampling_rate = self.main_window.analysis_thread.sampling_rate
        self.main_window.distance = int(
            self.main_window.sampling_rate / 10) + 20
        self.main_window.db_scan_settings_widget.set_bin_size_range(
            1 / self.main_window.sampling_rate, 0.5
        )
        self.main_window.cluster_tracker.sampling_rate = self.main_window.sampling_rate
        self.main_window.fs_range = (0.5, self.main_window.sampling_rate / 2)
        self.main_window.time_vector = self.main_window.analysis_thread.time_vector
        self.main_window.active_channels = self.main_window.analysis_thread.active_channels
        self.main_window.min_voltage = float("inf")
        self.main_window.max_voltage = float("-inf")

        self.main_window.peak_settings_widget.threshold_slider.setValue(
            self.main_window.n_std_dev)
        self.main_window.peak_settings_widget.threshold_value.setText(
            str(self.main_window.n_std_dev))
        self.main_window.peak_settings_widget.distance_slider.setValue(
            self.main_window.distance)
        self.main_window.peak_settings_widget.distance_value.setText(
            str(self.main_window.distance))

        if SignalAnalyzer:
            self.main_window.signal_analyzer = SignalAnalyzer(
                self.main_window.time_vector,
                n_std_dev=4,
                distance=70,
                sampling_rate=self.main_window.sampling_rate,
            )
            self.main_window.signal_analyzer.snr_threshold = 35

        delta_t = 1 / self.main_window.sampling_rate
        delta_t_str = str(delta_t)
        self.main_window.ui_manager.speed_combo.clear()
        self.main_window.ui_manager.speed_combo.addItems(
            [delta_t_str, "0.1", "0.25", "0.5", "1.0", "2.0", "4.0", "16.0"]
        )

        for row, col in self.main_window.active_channels:
            volt_signal = self.main_window.data[row - 1, col - 1]["signal"]
            voltages = np.abs(np.diff(volt_signal))
            min_range = np.min(voltages)
            max_range = np.max(voltages)
            self.main_window.min_voltage = min(
                self.main_window.min_voltage, min_range)
            self.main_window.max_voltage = max(
                self.main_window.max_voltage, max_range)

            self.main_window.grid_widget.update_cursor()

        self.main_window.ui_manager.progress_bar.setSamplingRate(
            self.main_window.sampling_rate)
        self.main_window.ui_manager.progress_bar.setRange(
            0, int(self.main_window.recording_length *
                   self.main_window.sampling_rate)
        )

        self.main_window.create_grid()
        self.main_window.update_grid(first=True)
        self.main_window.raster_plot = RasterPlot(
            self.main_window.data,
            self.main_window.sampling_rate,
            self.main_window.active_channels,
            self.main_window.raster_downsample_factor,
        )
        self.main_window.raster_plot.generate_raster()
        self.main_window.raster_plot.create_raster_plot(
            self.main_window.second_plot_widget)
        self.main_window.raster_plot.set_main_window(self.main_window)

        title = "Select Channel"
        for i in range(4):
            self.main_window.graph_widget.plot(
                [],
                [],
                title,
                "sec",
                "mV",
                i,
                "",
                np.array([]),
                np.array([]),
            )

        self.main_window.discharge_start_dialog = DischargeStartDialog(
            self.main_window)

        sz_cells = []
        se_cells = []
        no_event_cells = []
        for row, col in self.main_window.active_channels:
            sz_events = self.main_window.data[row - 1, col - 1]["SzTimes"]
            se_events = self.main_window.data[row - 1, col - 1]["SETimes"]
            if len(se_events) > 0:
                se_cells.append(
                    self.main_window.grid_widget.cells[row - 1][col - 1])
                continue
            if len(sz_events) > 0:
                sz_cells.append(
                    self.main_window.grid_widget.cells[row - 1][col - 1])
                continue
            no_event_cells.append(
                self.main_window.grid_widget.cells[row - 1][col - 1])

        self.main_window.grid_widget.add_overlay(sz_cells, SEIZURE)
        self.main_window.grid_widget.add_overlay(se_cells, SE)
        self.main_window.grid_widget.add_overlay(
            no_event_cells, QColor(0, 0, 0))

        self.main_window.set_widgets_enabled()

    def cancel_analysis(self):
        """Cancel ongoing analysis"""
        print("Cancelling Analysis")
        self.main_window.analysis_thread.requestInterruption()
        self.main_window.analysis_thread.wait()

        self.main_window.analysis_thread.eng = None
        self.main_window.loading_dialog.hide()
        print("Analysis Cancelled")

    def find_discharges(self):
        """Find discharges in selected region"""
        self.main_window.set_custom_region()
        start, stop = self.main_window.custom_region

        lasso_selected_cells = [
            (cell.row + 1, cell.col + 1)
            for cell in self.main_window.grid_widget.get_lasso_selected_cells()
        ]
        if len(lasso_selected_cells) > 0:
            print("Finding discharges in highlighted cells")
            self.main_window.discharge_finder = DischargeFinderThread(
                self.main_window.data, lasso_selected_cells, self.main_window.signal_analyzer, start, stop
            )
        else:
            print("Finding discharges in all active cells")
            self.main_window.discharge_finder = DischargeFinderThread(
                self.main_window.data, self.main_window.active_channels, self.main_window.signal_analyzer, start, stop
            )
        self.main_window.discharge_finder.finished.connect(
            self.on_discharge_finder_finished
        )
        self.main_window.discharge_finder.start()

    def on_discharge_finder_finished(self, discharges: dict[tuple[int, int], tuple[Union[npt.NDArray[np.float64], list[float]], Union[npt.NDArray[np.float64], list[float]]]]):
        """Handle discharge finder completion"""
        self.main_window.discharges = discharges
        for i in range(4):
            if self.main_window.plotted_channels[i] is not None:
                for item in self.main_window.graph_widget.plot_widgets[i].items():
                    if isinstance(item, pg.ScatterPlotItem):
                        self.main_window.graph_widget.plot_widgets[i].removeItem(
                            item)

        self.main_window.graph_widget.plot_peaks()

    def auto_analyze(self):
        """Start automatic analysis of discharges"""
        if self.main_window.custom_region is None or self.main_window.plotted_channels[0] is None:
            return

        self.main_window.togglePropLinesAction.setChecked(True)
        self.main_window.toggle_prop_lines(True)

        self.main_window.cluster_tracker.seizures.clear()
        self.main_window.cluster_tracker.seizure_graphics_items.clear()
        self.main_window.cluster_tracker.last_seizure = None
        start, stop = self.main_window.custom_region
        row, col = self.main_window.plotted_channels[0].row, self.main_window.plotted_channels[0].col
        discharges_x, _ = self.main_window.discharges[row, col]

        self.main_window.current_discharge_index = 0
        self.main_window.discharges_to_analyze = [
            x for x in discharges_x if start <= x <= stop
        ]

        if not self.main_window.discharges_to_analyze:
            print("No discharges to analyze in the selected region")
            return

        self.main_window.is_auto_analyzing = True
        self.analyze_next_discharge()

    def analyze_next_discharge(self):
        """Analyze the next discharge in the queue"""
        if not self.main_window.is_auto_analyzing or self.main_window.current_discharge_index >= len(
            self.main_window.discharges_to_analyze
        ):
            if self.main_window.is_auto_analyzing:
                print("Auto-analysis complete")

                self.main_window.cluster_tracker.save_discharges_to_hdf5(
                    self.main_window.file_path, *self.main_window.custom_region
                )
            self.main_window.is_auto_analyzing = False
            return

        discharge_x = self.main_window.discharges_to_analyze[self.main_window.current_discharge_index]
        print(f"Analyzing discharge at {discharge_x}")
        discharge_index = int(discharge_x * self.main_window.sampling_rate)
        start_index = max(0, discharge_index -
                          int(0.1 * self.main_window.sampling_rate))
        end_index = min(
            len(self.main_window.time_vector) - 1,
            discharge_index + int(0.15 * self.main_window.sampling_rate)
        )

        self.main_window.ui_manager.progress_bar.setValue(start_index)
        self.main_window.update_grid()
        if self.main_window.lock_to_playhead:
            self.main_window.lock_plots_to_playhead()

        QTimer.singleShot(50, lambda: self.continue_analysis(end_index))

    def continue_analysis(self, end_index):
        """Continue analysis for current discharge"""
        if not self.main_window.is_auto_analyzing:
            return

        current_index = self.main_window.ui_manager.progress_bar.value()
        if current_index < end_index:
            self.main_window.ui_manager.progress_bar.setValue(
                current_index + 1)
            self.main_window.update_grid()
            if self.main_window.lock_to_playhead:
                self.main_window.lock_plots_to_playhead()
            QTimer.singleShot(5, lambda: self.continue_analysis(end_index))
        else:
            self.main_window.current_discharge_index += 1
            QTimer.singleShot(50, self.analyze_next_discharge)

    def terminate_auto_analysis(self):
        """Terminate automatic analysis"""
        self.main_window.is_auto_analyzing = False

    def edit_raster_settings(self):
        """Edit raster plot settings"""
        from widgets.RasterPlot import RasterPlot

        if self.main_window.raster_plot is None:
            self.main_window.raster_plot = RasterPlot(
                self.main_window.data,
                self.main_window.sampling_rate,
                self.main_window.active_channels,
                self.main_window.raster_downsample_factor,
            )
            self.main_window.raster_plot.set_main_window(self.main_window)

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Edit Raster Settings")
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.setMinimumSize(300, 200)

        layout = QVBoxLayout(dialog)

        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Spike Threshold:")
        threshold_input = QLineEdit(
            str(self.main_window.raster_plot.spike_threshold))
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(threshold_input)
        layout.addLayout(threshold_layout)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("Apply")
        ok_button.clicked.connect(dialog.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        if dialog.exec() == QDialog.Accepted:
            try:
                spike_threshold = float(threshold_input.text())

                self.main_window.raster_plot.spike_threshold = spike_threshold

                self.main_window.update_raster()
            except ValueError:
                QMessageBox.warning(
                    self.main_window,
                    "Invalid Input",
                    "Invalid input values. Please enter valid numbers.",
                )

