# NewUpdater.py
import os
import stat
import sys
import platform
import requests
import subprocess
import shutil
from pathlib import Path
from packaging import version

GITHUB_REPO = "booka66/mea-gui"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
# NOTE: Need to add the windows protected path
PROTECTED_PATHS = ["Contents/Resources/MEAUpdater.app"]


class AppUpdater:
    def __init__(self, current_version: str, install_dir: Path = None):
        self.is_frozen = getattr(sys, "frozen", False)
        self.current_version = current_version
        if install_dir:
            self.app_path = Path(install_dir)
        else:
            self.app_path = (
                Path(sys._MEIPASS)
                if self.is_frozen
                else Path(os.path.dirname(os.path.abspath(__file__)))
            )
        self.system = platform.system()
        self.machine = platform.machine()
        self.temp_dir = Path(os.path.expanduser("~")) / ".app_updates"

    # NOTE: Make sure this works on windows
    def _is_protected_path(self, path):
        """Check if a path should be protected during updates"""
        try:
            rel_path = path.relative_to(self.app_path)
            return str(rel_path) in PROTECTED_PATHS or any(
                str(rel_path).startswith(p + "/") for p in PROTECTED_PATHS
            )
        except ValueError:
            return False

    def _preserve_protected_files(self, source_dir, target_dir):
        """Preserve protected files by copying them from source to target"""
        for protected_path in PROTECTED_PATHS:
            source = source_dir / protected_path
            target = target_dir / protected_path
            if source.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    shutil.rmtree(target, onerror=self._remove_readonly)
                shutil.copytree(source, target, symlinks=True)

    def _remove_readonly(self, func, path, _):
        """Clear the readonly bit and reattempt the removal"""
        if not self._is_protected_path(Path(path)):
            os.chmod(path, stat.S_IWRITE)
            func(path)

    def _clean_directory(self, path):
        """Safely remove a directory and its contents if it exists, preserving protected paths."""
        try:
            path = Path(path)
            if path.exists():
                # First try to fix permissions, excluding protected paths
                for root, dirs, files in os.walk(str(path)):
                    root_path = Path(root)
                    for d in dirs:
                        dir_path = root_path / d
                        if not self._is_protected_path(dir_path):
                            try:
                                os.chmod(str(dir_path), stat.S_IRWXU)
                            except Exception:
                                pass
                    for f in files:
                        file_path = root_path / f
                        if not self._is_protected_path(file_path):
                            try:
                                os.chmod(str(file_path), stat.S_IRWXU)
                            except Exception:
                                pass

                # Then remove non-protected contents
                for item in path.iterdir():
                    if not self._is_protected_path(item):
                        if item.is_dir():
                            shutil.rmtree(item, onerror=self._remove_readonly)
                        else:
                            item.unlink()

            # Create new directory with proper permissions if it doesn't exist
            path.mkdir(parents=True, exist_ok=True)
            os.chmod(path, stat.S_IRWXU)  # 700 permissions

        except Exception as e:
            print(f"Failed to clean directory {path}: {e}")
            raise

    def check_for_update(self):
        try:
            response = requests.get(GITHUB_API_URL, timeout=5)
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release["tag_name"].lstrip("v")
                current_version = self.current_version.lstrip("v")

                # Consider no local installation as needing an update
                if not self._is_app_installed():
                    return True, latest_release

                return version.parse(latest_version) > version.parse(
                    current_version
                ), latest_release
            return False, None
        except Exception as e:
            print(f"Update check failed: {e}")
            return False, None

    def _is_app_installed(self):
        """Check if the application is installed in the target directory"""
        if self.system == "Darwin":
            return (self.app_path / "MEA GUI.app").exists()
        else:
            return (self.app_path / "MEA_GUI.exe").exists()

    def _get_download_url(self, assets):
        if self.system == "Darwin":
            arch_suffix = "arm64" if self.machine == "arm64" else "x86_64"
            asset_name = f"MEA_GUI_MacOS_{arch_suffix}.pkg"
        else:
            asset_name = "MEA_GUI_Windows.exe"

        for asset in assets:
            if asset["name"] == asset_name:
                return asset["browser_download_url"]
        return None

    def download_update(self, release):
        try:
            # Clean temp directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, onerror=self._remove_readonly)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(self.temp_dir, stat.S_IRWXU)

            download_url = self._get_download_url(release["assets"])
            if not download_url:
                raise Exception("No suitable update found for your platform")

            ext = ".pkg" if self.system == "Darwin" else ".exe"
            update_file = self.temp_dir / f"update{ext}"

            print(f"Downloading from {download_url}...")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            block_size = 8192
            downloaded = 0

            with open(update_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = int(100 * downloaded / total_size)
                        print(f"Download progress: {percent}%", end="\r")

            print("\nDownload complete!")
            # Ensure the downloaded file has proper permissions
            os.chmod(update_file, stat.S_IRWXU)

            return update_file

        except Exception as e:
            print(f"Download failed: {e}")
            return None

    # NOTE: Need to make this work on windows
    def _remove_app_with_privileges(self, target_app):
        """
        Attempts to remove the application using elevated privileges if needed.
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Get a more precise check for running application
            app_name = target_app.name.replace(".app", "")
            logger.info(f"Checking if {app_name} is running")

            # More precise process check using pgrep
            ps_result = subprocess.run(
                ["pgrep", "-f", f"{app_name}.app"], capture_output=True, text=True
            )

            if ps_result.stdout.strip():
                # Double-check with a more specific lsof command
                lsof_result = subprocess.run(
                    ["lsof", str(target_app)], capture_output=True, text=True
                )

                if lsof_result.returncode == 0:
                    logger.error("Application is confirmed to be running")
                    raise Exception(
                        "Application is currently running. Please close it before updating."
                    )

            logger.info(f"Attempting to remove: {target_app}")

            # First try to kill any remaining file locks
            subprocess.run(
                ["pkill", "-f", f"{app_name}.app"], capture_output=True, text=True
            )

            # Small delay to ensure processes are terminated
            import time

            time.sleep(1)

            # Try normal removal first
            try:
                shutil.rmtree(target_app)
                logger.info("Successfully removed app without privileges")
                return True
            except PermissionError:
                logger.info("Permission denied, attempting with admin privileges")
                # If normal removal fails, try with admin privileges
                path = str(target_app).replace('"', '\\"')

                # First ensure no processes are using the app with sudo
                subprocess.run(
                    ["sudo", "pkill", "-f", f"{app_name}.app"],
                    capture_output=True,
                    text=True,
                )

                command = f'rm -rf "{path}"'
                if self._request_admin_privileges(command):
                    logger.info("Successfully removed app with admin privileges")
                    return True
                logger.error("Failed to remove app even with admin privileges")
                raise Exception(
                    "Failed to remove existing application - permission denied"
                )
        except Exception as e:
            logger.exception(f"Error removing application: {str(e)}")
            raise

    # NOTE: Does windows have a similar command to osascript?
    def _request_admin_privileges(self, command):
        """
        Executes a command with admin privileges using osascript.
        Uses proper AppleScript syntax with improved error handling.
        """
        import logging

        logger = logging.getLogger(__name__)

        escaped_command = command.replace('"', '\\"')
        script = f'''
        try
            do shell script "{escaped_command}" with administrator privileges
            return "Success"
        on error errMsg
            return "Error: " & errMsg
        end try
        '''

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                check=False,  # Don't raise an exception on non-zero exit
                capture_output=True,
                text=True,
            )

            if "Error:" in result.stdout:
                logger.error(f"Admin privileges error: {result.stdout}")
                return False

            logger.info("Successfully executed command with admin privileges")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Admin privileges error: {e.stderr}")
            return False

    def _update_macos(self, pkg_file):
        try:
            app_location = self.app_path
            extract_dir = self.temp_dir / "pkg_contents"
            payload_dir = self.temp_dir / "payload_contents"

            # Clean directories with proper permissions
            for directory in [extract_dir, payload_dir]:
                self._clean_directory(directory)

            print("Extracting package contents...")

            # Try xar first
            result = subprocess.run(
                ["xar", "-xf", str(pkg_file), "-C", str(extract_dir)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # Fallback to pkgutil if xar fails
                result = subprocess.run(
                    ["pkgutil", "--expand", str(pkg_file), str(extract_dir)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    raise Exception(f"Failed to extract package: {result.stderr}")

            # Find the Payload file
            payload = None
            for file in extract_dir.rglob("Payload"):
                payload = file
                break

            if not payload:
                raise Exception("Payload not found in package")

            print("Extracting payload...")
            result = subprocess.run(
                ["tar", "-xf", str(payload), "-C", str(payload_dir)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise Exception(f"Failed to extract payload: {result.stderr}")

            # Look for the .app bundle
            app_bundle = None
            for path in payload_dir.rglob("*.app"):
                app_bundle = path
                break

            if not app_bundle:
                raise Exception("Application bundle not found in extracted contents")

            print(f"Installing application to: {app_location}")

            target_app = app_location / app_bundle.name
            if target_app.exists():
                # Before removing existing app, preserve protected files
                print("Preserving protected files...")
                temp_preserve = self.temp_dir / "preserved"
                temp_preserve.mkdir(parents=True, exist_ok=True)
                self._preserve_protected_files(target_app, temp_preserve)

                print("Removing existing application...")
                self._remove_app_with_privileges(target_app)

            print("Installing new version...")
            shutil.copytree(app_bundle, target_app, symlinks=True)

            # Restore protected files if they were preserved
            if "temp_preserve" in locals() and temp_preserve.exists():
                print("Restoring protected files...")
                self._preserve_protected_files(temp_preserve, target_app)

            # Set proper permissions on new installation
            for root, dirs, files in os.walk(str(target_app)):
                root_path = Path(root)
                for d in dirs:
                    dir_path = root_path / d
                    if not self._is_protected_path(dir_path):
                        os.chmod(str(dir_path), stat.S_IRWXU)
                for f in files:
                    file_path = root_path / f
                    if not self._is_protected_path(file_path):
                        os.chmod(str(file_path), stat.S_IRWXU)

            return True

        except Exception as e:
            print(f"MacOS update failed: {e}")
            return False
        finally:
            # Cleanup
            try:
                for directory in [extract_dir, payload_dir]:
                    if directory.exists():
                        shutil.rmtree(directory, onerror=self._remove_readonly)
            except Exception as e:
                print(f"Cleanup failed: {e}")

    # NOTE: Need to make this work on windows
    def _update_windows(self, exe_file):
        try:
            app_location = self.app_path
            extract_dir = self.temp_dir / "installer_contents"

            # Clean and recreate extraction directory
            self._clean_directory(extract_dir)

            # Use 7zip to extract the installer
            result = subprocess.run(
                ["7z", "x", str(exe_file), f"-o{extract_dir}", "-y"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise Exception(f"Failed to extract installer: {result.stderr}")

            # Copy the updated contents
            app_dir = extract_dir / "app"
            if not app_dir.exists():
                raise Exception("Application directory not found in extracted contents")

            print(f"Installing application to: {app_location}")

            # Create the app location directory if it doesn't exist
            app_location.mkdir(parents=True, exist_ok=True)

            # Copy contents
            for item in app_dir.iterdir():
                dest = app_location / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                else:
                    if dest.exists():
                        shutil.rmtree(dest, onerror=self._remove_readonly)
                    shutil.copytree(item, dest, symlinks=True)

            return True

        except Exception as e:
            print(f"Windows update failed: {e}")
            return False
        finally:
            try:
                if extract_dir.exists():
                    shutil.rmtree(extract_dir, onerror=self._remove_readonly)
            except Exception as e:
                print(f"Cleanup failed: {e}")

    def install_update(self, update_file):
        try:
            if self.system == "Darwin":
                success = self._update_macos(update_file)
            else:
                success = self._update_windows(update_file)

            if success:
                # Clean up temp directory
                if self.temp_dir.exists():
                    shutil.rmtree(self.temp_dir, onerror=self._remove_readonly)

            return success

        except Exception as e:
            print(f"Installation failed: {e}")
            return False


def main():
    # When run directly, install/update in the current directory
    current_dir = Path.cwd()
    current_dir = Path("/Applications/")
    updater = AppUpdater(install_dir=current_dir)

    print("Checking for updates...")
    update_available, release = updater.check_for_update()

    if update_available:
        if updater._is_app_installed():
            print("Update available. Downloading...")
        else:
            print("Application not found. Downloading...")

        update_file = updater.download_update(release)

        if update_file:
            print("Installing...")
            if updater.install_update(update_file):
                print("Installation successful!")
                sys.exit(0)
            else:
                print("Installation failed.")
                sys.exit(1)
        else:
            print("Download failed.")
            sys.exit(1)
    else:
        print("No update available.")
        sys.exit(0)


if __name__ == "__main__":
    main()
