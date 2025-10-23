"""Thread for handling background updates with progress reporting."""

from PyQt5.QtCore import QThread, pyqtSignal
from helpers.update.Updater import download_and_install_update


class UpdateThread(QThread):
    """Background thread for downloading and installing updates."""

    update_completed = pyqtSignal(bool)
    progress_update = pyqtSignal(int)  # Emits download progress (0-100)

    def __init__(self):
        super().__init__()

    def run(self):
        """Download and install the update in the background."""

        def progress_callback(percent: int):
            """Called by PyUpdater during download."""
            self.progress_update.emit(percent)

        # This will download, extract, and restart the app if successful
        success = download_and_install_update(progress_callback=progress_callback)
        self.update_completed.emit(success)
