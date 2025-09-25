import os
import glob
from typing import cast
import h5py
from h5py import Dataset
import numpy as np
import math
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox

from helpers.Constants import ACTIVE, BACKGROUND, SEIZURE, SE, CELL_SIZE


class DataManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def get_channels(self):
        """Get channels from HDF5 file"""
        with h5py.File(self.main_window.file_path, "r") as f:
            recElectrodeList = cast(
                Dataset, f["/3BRecInfo/3BMeaStreams/Raw/Chs"])
            rows = recElectrodeList["Row"][()]
            cols = recElectrodeList["Col"][()]
        return rows, cols

    def initialize_data(self):
        """Initialize data arrays for analysis"""
        self.main_window.cells = [
            self.main_window.grid_widget.cells[row - 1][col - 1]
            for row, col in self.main_window.active_channels
        ]
        self.main_window.signals = np.array(
            [
                self.main_window.data[row - 1, col - 1]["signal"]
                for row, col in self.main_window.active_channels
            ]
        )
        self.main_window.se_times_list = [
            self.main_window.data[row - 1, col - 1]["SETimes"]
            for row, col in self.main_window.active_channels
        ]
        self.main_window.seizure_times_list = [
            self.main_window.data[row - 1, col - 1]["SzTimes"]
            for row, col in self.main_window.active_channels
        ]

    def create_grid(self):
        """Create the grid with active channels"""
        for row in self.main_window.grid_widget.cells:
            for cell in row:
                cell.setColor(BACKGROUND, 1, self.main_window.opacity)
        for row, col in self.main_window.active_channels:
            self.main_window.grid_widget.cells[row - 1][col - 1].setColor(
                ACTIVE, 1, self.main_window.opacity
            )

    def get_min_max_strengths(self):
        """Calculate min/max strengths from seizure and SE data"""
        self.main_window.min_strength = None
        self.main_window.max_strength = None

        for row, col in self.main_window.active_channels:
            seizure_times = self.main_window.data[row - 1, col - 1]["SzTimes"]
            se_times = self.main_window.data[row - 1, col - 1]["SETimes"]

            if seizure_times.size == 0 and se_times.size == 0:
                continue

            if seizure_times.size > 0:
                if seizure_times.ndim == 1:
                    seizure_times = seizure_times.reshape(1, -1)
                elif seizure_times.ndim == 0:
                    seizure_times = seizure_times.reshape(1, 1)
            else:
                seizure_times = np.empty((0, 3))

            if se_times.size > 0:
                if se_times.ndim == 1:
                    se_times = se_times.reshape(1, -1)
                elif se_times.ndim == 0:
                    se_times = se_times.reshape(1, 1)
            else:
                se_times = np.empty((0, 3))

            times = np.concatenate((seizure_times, se_times), axis=0)

            for timerange in times:
                if len(timerange) >= 3:
                    start, stop, strength = timerange[:3]
                    if self.main_window.min_strength is None or strength < self.main_window.min_strength:
                        self.main_window.min_strength = strength
                    if self.main_window.max_strength is None or strength > self.main_window.max_strength:
                        self.main_window.max_strength = strength

    def normalize_strength(self, strength):
        """Normalize strength value"""
        strength = float(strength)
        return math.sqrt(
            (strength - self.main_window.min_strength) /
            (self.main_window.max_strength - self.main_window.min_strength)
        )

    def load_discharges(self):
        """Load tracked discharges from HDF5 file"""
        from PyQt5.QtWidgets import QInputDialog

        try:
            with h5py.File(self.main_window.file_path, "r") as f:
                tracked_discharges_group = f["tracked_discharges"]
                timeranges = list(tracked_discharges_group.keys())
                time_range, ok = QInputDialog.getItem(
                    self.main_window,
                    "Select Time Range",
                    "Time Range:",
                    timeranges,
                    0,
                    False,
                )
                if ok:
                    timerange_group = tracked_discharges_group[time_range]
                    discharge_datasets = [
                        key
                        for key in timerange_group.keys()
                        if key.startswith("discharge_")
                    ]
                    for discharge_key in discharge_datasets:
                        discharge_dataset = timerange_group[discharge_key]
                        attrs = discharge_dataset.attrs

                        start_point = attrs["start_point"]
                        end_point = attrs["end_point"]
                        start_time = float(attrs["start_time"])
                        end_time = float(attrs["end_time"])
                        duration_s = float(attrs["duration"])
                        length_mm = float(attrs["length"])
                        avg_speed = float(attrs["avg_speed"])
                        points = attrs["points"]
                        timestamps = attrs["timestamps"]

                        if "instant_speeds" in attrs:
                            instant_speeds = attrs["instant_speeds"]
                        else:
                            points_list = (
                                points.tolist() if hasattr(points, "tolist") else points
                            )
                            timestamps_list = (
                                timestamps.tolist()
                                if hasattr(timestamps, "tolist")
                                else timestamps
                            )
                            instant_speeds = []
                            for i in range(len(points_list) - 1):
                                distance = (
                                    np.linalg.norm(
                                        np.array(points_list[i + 1])
                                        - np.array(points_list[i])
                                    )
                                    * CELL_SIZE
                                    / 1000
                                )
                                time_diff = timestamps_list[i +
                                                            1] - timestamps_list[i]
                                speed = distance / time_diff if time_diff > 0 else 0
                                instant_speeds.append(speed)
                            instant_speeds.append(
                                instant_speeds[-1] if instant_speeds else 0
                            )

                        time_since_last_discharge = float(
                            attrs["time_since_last_discharge"]
                        )

                        seizure = {
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration": duration_s,
                            "length": length_mm,
                            "avg_speed": avg_speed,
                            "points": points.tolist()
                            if hasattr(points, "tolist")
                            else points,
                            "timestamps": timestamps.tolist()
                            if hasattr(timestamps, "tolist")
                            else timestamps,
                            "instant_speeds": instant_speeds.tolist()
                            if hasattr(instant_speeds, "tolist")
                            else instant_speeds,
                            "start_point": start_point.tolist()
                            if hasattr(start_point, "tolist")
                            else start_point,
                            "end_point": end_point.tolist()
                            if hasattr(end_point, "tolist")
                            else end_point,
                            "time_since_last_discharge": time_since_last_discharge,
                        }

                        self.main_window.cluster_tracker.seizures.append(
                            seizure)
        except Exception as e:
            print(f"Error loading discharges: {e}")
            print("Attempting to load deprecated discharges")
            try:
                self.load_discharges_deprecated(time_range)
            except Exception as e:
                print(f"Error loading deprecated discharges: {e}")

    def load_discharges_deprecated(self, time_range):
        """Load discharges using deprecated format"""
        with h5py.File(self.main_window.file_path, "r") as f:
            tracked_discharges_group = f["tracked_discharges"]
            timerange_group = tracked_discharges_group[time_range]

            discharge_groups = [
                key for key in timerange_group.keys() if key.startswith("discharge_")
            ]

            for discharge_key in discharge_groups:
                discharge_group = timerange_group[discharge_key]

                start_point = discharge_group["start_point"][:]
                end_point = discharge_group["end_point"][:]
                start_time = float(discharge_group["start_time"][()])
                end_time = float(discharge_group["end_time"][()])
                duration_s = float(discharge_group["duration"][()])
                length_mm = float(discharge_group["length"][()])
                avg_speed = float(discharge_group["avg_speed"][()])
                points = discharge_group["points"][:]
                time_since_last_discharge = float(
                    discharge_group["time_since_last_discharge"][()]
                )

                seizure = {
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration_s,
                    "length": length_mm,
                    "avg_speed": avg_speed,
                    "points": points.tolist(),
                    "start_point": start_point.tolist(),
                    "end_point": end_point.tolist(),
                    "time_since_last_discharge": time_since_last_discharge,
                }

                self.main_window.cluster_tracker.seizures.append(seizure)

            start, end = time_range.split("_")
        print(f"Attempting to save discharges to new format: {start} - {end}")
        self.main_window.cluster_tracker.save_discharges_to_hdf5(
            self.main_window.file_path, float(start), float(end)
        )

    def setup_background_image(self, file_path: str) -> bool:
        """Setup background image for grid based on file path"""
        try:
            baseName = os.path.basename(file_path)
            brwFileName = os.path.basename(file_path)
            dateSlice = "_".join(brwFileName.split("_")[:4])
            dateSliceNumber = (
                dateSlice.split("slice")[0]
                + "slice"
                + dateSlice.split("slice")[1][:1]
            )
            imageName = f"{dateSliceNumber}_pic_cropped.jpg"
            print(f"Trying to find image: {imageName}")

            imageFolder = os.path.dirname(file_path)
            image_pattern = os.path.join(
                imageFolder,
                f"{dateSliceNumber}_*[pP][iI][cC]_*[cC][rR][oO][pP][pP][eE][dD].jpg",
            )
            image_files = glob.glob(image_pattern, recursive=True)

            if image_files:
                image_path = image_files[0]
                self.main_window.grid_widget.setBackgroundImage(image_path)
                return True
            return False

        except Exception as e:
            print(f"Error setting up background image: {e}")
            return False

    def export_discharge_stats(self):
        """Export discharge statistics"""
        if self.main_window.cluster_tracker is None or self.main_window.file_path is None:
            return

        output_dir = os.path.join(os.path.expanduser("~"), "Downloads")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.main_window.cluster_tracker.export_discharges_to_zip(
            self.main_window.file_path, output_dir
        )

    def get_seizure_strength(self, row, col):
        """Get seizure strength for a specific cell at current time"""
        seizure_times = self.main_window.data[row - 1, col - 1]["SzTimes"]
        current_time = self.main_window.ui_manager.progress_bar.value() / self.main_window.sampling_rate
        for timerange in seizure_times:
            start, stop, strength = timerange
            if start <= current_time <= stop:
                return strength
        return 0

    def clear_found_discharges(self):
        """Clear found discharges data"""
        self.main_window.discharges = {}
        self.main_window.graph_widget.plot_peaks()

