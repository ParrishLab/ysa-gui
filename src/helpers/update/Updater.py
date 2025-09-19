import os
import platform
import sys
import urllib.request
from packaging import version
import requests
import subprocess

try:
    from helpers.Constants import __version__ as VERSION
except Exception:
    # Fallback if import path changes; better to fail closed than crash the app
    VERSION = "0.0.0"

GITHUB_REPO = "ParrishLab/ysa-gui"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Filenames saved to disk when downloading the installer
DOWNLOAD_NAME_MAC = "ysa_gui_update_parrish_lab_DELETE_ME.pkg"
DOWNLOAD_NAME_WIN = "ysa_gui_update_parrish_lab_DELETE_ME.exe"

# Asset names as produced by CI release job
ASSET_WIN = "YSA_GUI_Windows.exe"
ASSET_MAC_ARM = "YSA_GUI_MacOS_arm64.pkg"
ASSET_MAC_X86 = "YSA_GUI_MacOS_x86_64.pkg"


def _normalize_tag(tag: str) -> str:
    """Strip a leading 'v' from release tags (e.g., v1.2.3 -> 1.2.3)."""
    return tag[1:] if tag.startswith("v") else tag


def _choose_asset(latest_release: dict) -> str | None:
    """Pick the correct asset download URL for this platform/architecture."""
    assets = latest_release.get("assets", [])
    if sys.platform == "darwin":
        machine = platform.machine().lower()
        is_arm = ("arm64" in machine) or ("aarch64" in machine)
        want = ASSET_MAC_ARM if "arm64" in machine else ASSET_MAC_X86
        for a in assets:
            if a.get("name") == want:
                return a.get("browser_download_url")
        # Fallback: heuristic by suffix if exact name not found
        for a in assets:
            n = a.get("name", "")
            if n.endswith(".pkg") and (("arm64" in machine and "arm64" in n) or ("x86_64" in machine and "x86_64" in n)):
                return a.get("browser_download_url")
    elif sys.platform == "win32":
        for a in assets:
            if a.get("name") == ASSET_WIN or a.get("name", "").lower().endswith(".exe"):
                return a.get("browser_download_url")
    return None


def check_for_update():
    """Return (True, release_json) if a newer release exists for this platform."""
    try:
        resp = requests.get(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "YsaGUI-Updater"
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return False, None
        
        latest_release = resp.json()
        tag = latest_release.get("tag_name", "").strip()
        latest_ver = _normalize_tag(tag)

        # Compare normalized tag vs local VERSION
        if not latest_ver:
            return False, None

        if version.parse(latest_ver) <= version.parse(VERSION):
            return False, None

        # Ensure there is a suitable asset for this platform
        download_url = _choose_asset(latest_release)
        if not download_url:
            return False, None

        return True, latest_release
    except Exception as e:
        print(f"Failed to check for updates: {e}")
        return False, None


def download_and_install_update(release: dict) -> bool:
    """Download the installer to ~/Downloads and launch it."""
    try:
        download_url = _choose_asset(release)
        if not download_url:
            print("No suitable update found for your platform.")
            return False

        # Pick disk file name
        file_name = DOWNLOAD_NAME_MAC if sys.platform == "darwin" else DOWNLOAD_NAME_WIN
        download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(download_folder, exist_ok=True)
        file_path = os.path.join(download_folder, file_name)

        # If an old file exists from a previous run, remove it
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        print(f"Downloading {download_url} to {file_path}")
        urllib.request.urlretrieve(download_url, file_path)  # simple, blocking; ok for GUI helper

        # Launch installer
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", file_path], check=False)
            os.system(f"open '{file_path}'")
        else:
            print(f"Downloaded update to {file_path} (launch it manually)")
        return True
    except Exception as e:
        print(f"Update download/launch failed: {e}")
        return False


def main():
    has_update, release = check_for_update()
    if has_update and release:
        print("Update available. Downloading and launching installer...")
        ok = download_and_install_update(release)
        print("Update process completed." if ok else "Update process failed.")
    else:
        print("No update available.")


if __name__ == "__main__":
    main()
