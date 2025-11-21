from time import perf_counter
from PyQt5.QtCore import QThread, pyqtSignal
import os


class ProgressUpdaterThread(QThread):
    # status text + percent (0..100) s
    progress_updated = pyqtSignal(str, int)

    def __init__(self, temp_data_path):
        super().__init__()
        self.temp_data_path = temp_data_path
        self.start_time = perf_counter()

    def run(self):
        last_pct = 0
        print(f"[ProgressUpdater] watching dir: {self.temp_data_path!r}")
        
        while not self.isInterruptionRequested():
            if self.temp_data_path and os.path.isdir(self.temp_data_path):
                try:
                    temp_files = os.listdir(self.temp_data_path)
                except Exception:
                    temp_files = []
                    print(f"[ProgressUpdater] listdir error for {self.temp_data_path!r}: {e}")
                count = len(temp_files)
                # Heuristic: cap to 99 so the worker can set 100 on completion.
                pct = min(count, 99)
                msg = f"Processing… ({count} chunks)"
            else:
                # Heartbeat percent (smooth 0..95 loop every ~5s)
                elapsed = perf_counter() - self.start_time
                pct = int((elapsed * 20) % 96)  # 0..95
                msg = "Processing…"

            if pct != last_pct:
                self.progress_updated.emit(msg, pct)
                last_pct = pct

            self.msleep(100)  # 10 times per second

        # On interruption/completion, emit a final "completed" tick
        self.progress_updated.emit("Analysis completed.", 100)
