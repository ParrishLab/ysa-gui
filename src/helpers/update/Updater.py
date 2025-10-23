"""
PyUpdater-based auto-update system for YSA GUI.

This replaces the old manual download-and-open system with a robust,
production-ready updater that handles:
- Delta updates (only downloads changed files)
- Signature verification (ed25519)
- Background downloads with progress
- Automatic installation and rollback on failure
- Cross-platform support (macOS, Windows)
"""

import sys
import os
from typing import Optional, Callable
from pyupdater.client import Client
from pyupdater.client import ClientError

try:
    from helpers.Constants import __version__ as VERSION
except Exception:
    VERSION = "0.0.0"

# PyUpdater configuration
APP_NAME = "YsaGUI"
COMPANY_NAME = "ParrishLab"
UPDATE_URLS = ["http://localhost:8000/"]

# Client configuration
CLIENT_CONFIG = {
    "APP_NAME": APP_NAME,
    "COMPANY_NAME": COMPANY_NAME,
    "UPDATE_URLS": UPDATE_URLS,
    "PUBLIC_KEY": "+dencBWqOcAcCoa2xI/65Z11gF07P3WMv+w9BMEs8kg",
}


class UpdateChecker:
    """Wrapper for PyUpdater client with simplified API."""

    def __init__(self, progress_callback: Optional[Callable[[int], None]] = None):
        """
        Initialize the update checker.

        Args:
            progress_callback: Optional callback for download progress (0-100)
        """
        self.client = Client(CLIENT_CONFIG, refresh=True, progress_hooks=[self._progress_hook] if progress_callback else None)
        self.progress_callback = progress_callback
        self.app_update = None

    def _progress_hook(self, data: dict):
        """Internal progress hook for PyUpdater."""
        if self.progress_callback and "percent_complete" in data:
            self.progress_callback(int(data["percent_complete"]))

    def check_for_update(self) -> bool:
        """
        Check if an update is available.

        Returns:
            True if an update is available, False otherwise.
        """
        try:
            # Refresh the update manifest
            self.client.refresh()

            # Get the latest version for this platform
            self.app_update = self.client.update_check(APP_NAME, VERSION)

            return self.app_update is not None
        except ClientError as e:
            print(f"Update check failed: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during update check: {e}")
            return False

    def download_update(self) -> bool:
        """
        Download the update.

        Returns:
            True if download succeeded, False otherwise.
        """
        if not self.app_update:
            print("No update available to download")
            return False

        try:
            # Download the update (with delta support)
            return self.app_update.download()
        except Exception as e:
            print(f"Update download failed: {e}")
            return False

    def extract_and_restart(self) -> bool:
        """
        Extract the update and restart the application.

        Returns:
            True if extraction succeeded, False otherwise.
            Note: If True, the app will restart and this function won't return normally.
        """
        if not self.app_update:
            print("No update available to extract")
            return False

        try:
            # Extract and restart (PyUpdater handles the restart automatically)
            if self.app_update.extract_restart():
                # This should not return - the app will restart
                return True
            else:
                print("Failed to extract and restart")
                return False
        except Exception as e:
            print(f"Update extraction failed: {e}")
            return False

    def get_latest_version(self) -> Optional[str]:
        """Get the version string of the latest available update."""
        if self.app_update:
            return self.app_update.version
        return None


def check_for_update() -> tuple[bool, Optional[str]]:
    """
    Simple API for checking if an update is available.

    Returns:
        (has_update, version_string) tuple
    """
    checker = UpdateChecker()
    has_update = checker.check_for_update()
    version = checker.get_latest_version() if has_update else None
    return has_update, version


def download_and_install_update(progress_callback: Optional[Callable[[int], None]] = None) -> bool:
    """
    Download and install an available update.

    Args:
        progress_callback: Optional callback for download progress (0-100)

    Returns:
        True if successful (app will restart), False otherwise
    """
    checker = UpdateChecker(progress_callback)

    # Check for update
    if not checker.check_for_update():
        print("No update available")
        return False

    print(f"Update available: {checker.get_latest_version()}")

    # Download the update
    print("Downloading update...")
    if not checker.download_update():
        print("Download failed")
        return False

    print("Download complete, extracting and restarting...")

    # Extract and restart
    if checker.extract_and_restart():
        # App will restart here - this return should not be reached
        return True

    print("Failed to extract and restart")
    return False


# =============================================================================
# SETUP INSTRUCTIONS (run these ONCE to initialize PyUpdater)
# =============================================================================
#
# 1. Generate signing keys (run from project root):
#    ```
#    pyupdater keys -c
#    ```
#    This creates a .pyupdater/ directory with keys.
#
# 2. Get your public key:
#    ```
#    pyupdater keys --show
#    ```
#    Copy the public key and set it in CLIENT_CONFIG["PUBLIC_KEY"] above.
#
# 3. Initialize PyUpdater config (run from project root):
#    ```
#    pyupdater init
#    ```
#    Follow prompts to set APP_NAME, COMPANY_NAME, and UPDATE_URLS.
#
# 4. The CI/CD pipeline (build-and-release.yml) needs to be updated to:
#    - Sign the build with `pyupdater pkg --sign`
#    - Upload packages with `pyupdater upload --service github`
#
# See: https://www.pyupdater.org/usage-cli/ for full documentation.
# =============================================================================


if __name__ == "__main__":
    # Simple CLI test
    has_update, version = check_for_update()
    if has_update:
        print(f"Update available: {version}")
        print("Run with --install to download and install")

        if "--install" in sys.argv:
            success = download_and_install_update()
            if not success:
                print("Update installation failed")
                sys.exit(1)
    else:
        print("No update available")
