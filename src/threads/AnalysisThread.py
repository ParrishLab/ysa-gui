import os
from time import perf_counter
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from helpers.alert import alert
from threads.ProgressUpdaterThread import ProgressUpdaterThread

from ysa_signal import process_and_store


class AnalysisThread(QThread):
    analysis_completed = pyqtSignal()
    progress_updated = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.file_path = None
        self.data = np.empty((64, 64), dtype=object)
        self.min_strength = None
        self.max_strength = None
        self.recording_length = None
        self.sampling_rate = None
        self.time_vector = None
        self.active_channels = []
        self.spike_data = []
        self.raster_downsample_factor = 1
        self.raster_plot = None
        self.progress_updater_thread = None
        self.temp_data_path = None
        self.do_analysis = False

    def run(self):
        start = perf_counter()
        self.data = np.empty((64, 64), dtype=object)
        # Create temporary directory if it doesn't exist
        if self.temp_data_path is not None:
            os.makedirs(self.temp_data_path, exist_ok=True)
        try:
            self.progress_updater_thread = ProgressUpdaterThread(
                self.temp_data_path)
            self.progress_updater_thread.progress_updated.connect(
                self.progress_updated)
            self.progress_updater_thread.start()

            # Use ysa_signal package
            processed_data = process_and_store(
                file_path=self.file_path,
                do_analysis=self.do_analysis,
                temp_data_path=self.temp_data_path
            )

            # Copy data and metadata from ProcessedData
            self.data = processed_data.data
            self.sampling_rate = processed_data.sampling_rate
            self.recording_length = processed_data.recording_length
            self.time_vector = processed_data.time_vector
            self.active_channels = processed_data.active_channels

            for cell_data in self.data.flatten():
                if cell_data is None:
                    continue
                signal = cell_data["signal"]
                if signal is not None:
                    # Print stats about the signal
                    min_strength = signal.min()
                    max_strength = signal.max()
                    mean_strength = signal.mean()
                    std_strength = signal.std()
                    print(
                        f"min: {min_strength}, max: {max_strength}, mean: {mean_strength}, std: {std_strength}\n{signal[:20]}"
                    )
                    break
            self.analysis_completed.emit()
            end = perf_counter()
            analysis_time = end - start
            alert(f"Analysis completed in {analysis_time:.2f} seconds.")
        except Exception as e:
            print(f"Error: {e}")
            alert(f"Error during analysis:\n{str(e)}")
        finally:
            if self.progress_updater_thread is not None:
                self.progress_updater_thread.requestInterruption()
                self.progress_updater_thread.wait()
            # Clean up temporary directory if it exists
            if os.path.exists(self.temp_data_path):
                os.rmdir(self.temp_data_path)
