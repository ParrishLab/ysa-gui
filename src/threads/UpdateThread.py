from PyQt5.QtCore import QThread, pyqtSignal
from helpers.update.Updater import check_for_update, download_and_install_update


class UpdateThread(QThread):
    update_started   = pyqtSignal()
    update_progress  = pyqtSignal(str)      # optional text updates
    update_completed = pyqtSignal(bool)     # True = launched installer ok
    update_error     = pyqtSignal(str)

    def __init__(self, latest_release, parent=None):
        super().__init__(parent)
        self.latest_release = latest_release
        self.parent = parent

    def run(self):
        try:
            self.update_started.emit()

            release = self.latest_release
            if release is None:
                has_update, release = check_for_update()
                if not has_update or not release:
                    self.update_completed.emit(False)
                    return

            # Emit progress text
            self.update_progress.emit("Downloading update…")

            ok = download_and_install_update(release)
            self.update_completed.emit(bool(ok))

        except Exception as e:
            self.update_error.emit(str(e))
            self.update_completed.emit(False)
