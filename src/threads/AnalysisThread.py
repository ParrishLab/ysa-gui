import os
import shutil
import time
from time import perf_counter
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from helpers.alert import alert
from threads.ProgressUpdaterThread import ProgressUpdaterThread

from ysa_signal import process_and_store


class AnalysisThread(QThread):
    analysis_completed = pyqtSignal()
    analysis_failed = pyqtSignal(str)
    progress_updated = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ok = False
        self.last_error = None
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
            print(f"[AnalysisThread] temp_data_path={self.temp_data_path!r}")
            
            # Start the background progress poller (files/heartbeat -> percent)
            self.progress_updater_thread = ProgressUpdaterThread(self.temp_data_path)
            self.progress_updater_thread.progress_updated.connect(self.progress_updated)
            self.progress_updater_thread.start()

            debug = os.environ.get("YSA_DEBUG", "").strip() == "1"
            smoke = os.environ.get("YSA_SMOKE_TEST", "").strip() == "1"

            if debug:
                print("[DEBUG] AnalysisThread running (debug mode ON)")
                print(f"[DEBUG] file_path={self.file_path!r}, do_analysis={self.do_analysis}, temp={self.temp_data_path!r}")

            # Kick the UI so it doesn't look frozen
            self.progress_updated.emit("Preparing…", 1)

            if smoke:
                # CI smoke-test path: show progress, don't do heavy work
                for i in range(0, 101, 5):
                    if self.isInterruptionRequested():
                        break
                    self.progress_updated.emit(f"Debug: simulating analysis… {i}%", i)
                    time.sleep(0.05)

                # Minimal data so on_analysis_completed() has something sane
                self.data = np.empty((64, 64), dtype=object)
                self.active_channels = []
                self.sampling_rate = 100
                self.recording_length = 1.0
                self.time_vector = np.linspace(0, self.recording_length, int(self.recording_length*self.sampling_rate))
                self.min_strength = 0.0
                self.max_strength = 0.0
            else:
                # ---- Real analysis ----  (Use ysa_signal package)
                self.progress_updated.emit("Reading file…", 5)
                if debug:
                    print("[DEBUG] Starting process_and_store() call")
                processed_data = process_and_store(
                    file_path=self.file_path,
                    do_analysis=self.do_analysis,
                    temp_data_path=self.temp_data_path
                )
                if debug:
                    print("[DEBUG] process_and_store() returned successfully")
                    print(f"[DEBUG] Active channels: {len(self.active_channels)}")

                # Copy data and metadata from ProcessedData
                self.data = processed_data.data
                self.sampling_rate = processed_data.sampling_rate
                self.recording_length = processed_data.recording_length
                self.time_vector = processed_data.time_vector
                self.active_channels = processed_data.active_channels

                # Compute mix/max event strength across all cells
                min_s, max_s = None, None
                for cell in self.data.flatten():
                    if cell is None:
                        continue
                    for key in ("SzTimes", "SETimes"):
                        arr = cell.get(key)
                        if arr is None or np.size(arr) == 0:
                            continue
                        arr = np.atleast_2d(arr)
                        if arr.shape[1] >= 3:
                            strengths = arr[:, 2].astype(float)
                            if strengths.size:
                                smin = float(np.nanmin(strengths))
                                smax = float(np.nanmax(strengths))
                                min_s = smin if (min_s is None or smin < min_s) else min_s
                                max_s = smax if (max_s is None or smax > max_s) else max_s

                # Fallback if no events had strengths
                if min_s is None: min_s = 0.0
                if max_s is None: max_s = 0.0

                self.min_strength = min_s
                self.max_strength = max_s
                
            # Finish up
            self.progress_updated.emit("Finalizing…", 100)
            self.analysis_completed.emit()
            end = perf_counter()
            analysis_time = end - start
            min, sec = divmod(analysis_time, 60)
            alert(f"Analysis completed in {int(min)} min {sec:.2f} s.")
            self.ok = True
        except Exception as e:
            print(f"Error: {e}")
            self.analysis_failed.emit(str(e))
            self.last_error = str(e)
            self.data = None
            self.sampling_rate = None
            # ensure the dialog closes even on error
            try:
                self.analysis_completed.emit()
            except Exception:
                pass
        finally:
            if self.progress_updater_thread is not None:
                self.progress_updater_thread.requestInterruption()
                self.progress_updater_thread.wait()

            # Clean up temporary directory if it exists
            if self.temp_data_path and os.path.isdir(self.temp_data_path):
                try:
                    # In debug mode, remove everything; otherwise only remove if empty
                    if os.environ.get("YSA_DEBUG") == "1":
                        shutil.rmtree(self.temp_data_path, ignore_errors=True)
                        print(f"[DEBUG] Removed temp directory {self.temp_data_path}")
                    else:
                        os.rmdir(self.temp_data_path)
                        print(f"[INFO] Removed empty temp directory {self.temp_data_path}")
                except Exception as e:
                    print(f"[WARN] Temp dir cleanup skipped: {e}")

