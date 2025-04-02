# updater_app.py
import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QProgressBar,
    QLabel,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)
from PyQt5.QtCore import QThread, pyqtSignal
import qdarktheme
from NewUpdater import AppUpdater
import subprocess


class UpdateWorker(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(bool)

    def __init__(self, release, install_dir, current_version):
        super().__init__()
        self.release = release
        self.install_dir = install_dir
        self.updater = AppUpdater(
            current_version=current_version, install_dir=install_dir
        )

        self.setup_logging()

    def get_log_file(self):
        if sys.platform == "darwin":
            log_file = Path(os.path.expanduser("~")) / ".mea_updater" / "updater.log"
        elif sys.platform == "win32":
            log_file = (
                Path(os.path.expanduser("~"))
                / "AppData"
                / "Local"
                / "mea_updater"
                / "updater.log"
            )
        return log_file

    def setup_logging(self):
        import logging

        log_file = self.get_log_file()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def run(self):
        try:
            self.logger.info("Starting update process")
            self.progress.emit("Downloading update...", 0)

            self.logger.info("Downloading update")
            update_file = self.updater.download_update(self.release)

            if not update_file:
                self.logger.error("Download failed")
                self.progress.emit("Download failed.", 100)
                self.finished.emit(False)
                return

            self.logger.info(f"Download completed: {update_file}")
            self.progress.emit("Installing update...", 50)

            self.logger.info("Starting installation")
            success = self.updater.install_update(update_file)

            if success:
                self.logger.info("Installation completed successfully")
                self.progress.emit("Installation complete!", 100)
                self.finished.emit(True)
            else:
                self.logger.error("Installation failed")
                self.progress.emit("Installation failed.", 100)
                self.finished.emit(False)

        except Exception as e:
            self.logger.exception("Error during update process")
            self.progress.emit(f"Error: {str(e)}", 100)
            self.finished.emit(False)


class UpdaterWindow(QMainWindow):
    def __init__(self, release=None, install_dir=None, current_version=None):
        super().__init__()

        # Set up logging
        self.setup_logging()
        self.install_dir = self.get_install_dir()
        self.release = release
        self.init_ui()
        self.start_update(current_version)

    # NOTE: Still need to debug this for windows to makesure the correct path is returned
    def get_install_dir(self):
        if sys.platform == "darwin":
            install_dir = Path("/Applications/")
        elif sys.platform == "win32":
            if sys.maxsize > 2**32:
                install_dir = Path("C:/Program Files/")
            else:
                install_dir = Path("C:/Program Files (x86)/")
        else:
            install_dir = Path("/usr/local/bin/")
        return install_dir

    def get_log_file(self):
        if sys.platform == "darwin":
            log_file = Path(os.path.expanduser("~")) / ".mea_updater" / "updater.log"
        elif sys.platform == "win32":
            log_file = (
                Path(os.path.expanduser("~"))
                / "AppData"
                / "Local"
                / "mea_updater"
                / "updater.log"
            )
        return log_file

    def setup_logging(self):
        import logging

        log_file = self.get_log_file()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def init_ui(self):
        self.setWindowTitle("MEA GUI Updater")
        self.setFixedSize(400, 150)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add status label
        self.status_label = QLabel("Preparing update...")
        layout.addWidget(self.status_label)

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        # Center the window
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2
        )

    def start_update(self, current_version):
        self.worker = UpdateWorker(self.release, self.install_dir, current_version)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.handle_completion)
        self.worker.start()

    def update_progress(self, message, percentage):
        self.status_label.setText(message)
        self.progress_bar.setValue(percentage)

    def handle_completion(self, success):
        if success:
            self.logger.info("Update completed successfully")
            QMessageBox.information(
                self,
                "Update Complete",
                "The update has been installed successfully. The application will now restart.",
            )
            # Launch the main application
            app_path = (
                self.install_dir / "MEA GUI.app"
                if sys.platform == "darwin"
                else self.install_dir / "MEA GUI.exe"
            )
            if app_path.exists():
                self.logger.info(f"Launching application at: {app_path}")
                if sys.platform == "darwin":
                    subprocess.Popen(["open", app_path])
                elif sys.platform == "win32":
                    subprocess.Popen([app_path], shell=True)

            else:
                self.logger.error(f"Application not found at: {app_path}")
        else:
            self.logger.error("Update process failed")
            QMessageBox.critical(
                self,
                "Update Failed",
                "The update process failed. Please check the logs at ~/.mea_updater/updater.log",
            )
        self.close()


def main():
    app = QApplication(sys.argv)
    # extract version from arg
    try:
        version = sys.argv[1]
    except IndexError:
        sys.exit("No version provided")

    qdarktheme.setup_theme()

    if sys.platform == "darwin":
        install_dir = Path("/Applications/")
    elif sys.platform == "win32":
        if sys.maxsize > 2**32:
            install_dir = Path("C:/Program Files/")
        else:
            install_dir = Path("C:/Program Files (x86)/")
    else:
        # TODO: Linux placeholder
        install_dir = Path("/usr/local/bin/")

    updater = AppUpdater(current_version=version, install_dir=install_dir)
    update_available, release = updater.check_for_update()

    if update_available and release:
        window = UpdaterWindow(release=release, current_version=version)
        window.show()
        window.raise_()
        return app.exec()
    else:
        print("No update available")
        return 0


if __name__ == "__main__":
    sys.exit(main())
