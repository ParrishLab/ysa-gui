import os
import platform
import sys
import urllib.request
from packaging import version
import requests
import subprocess
import tempfile
import shutil
from contextlib import closing

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


def _launch_installer(file_path: str) -> bool:
    try:
        if sys.platform == "win32":
            os.startfile(file_path)               # non-blocking on Windows
        elif sys.platform == "darwin":
            subprocess.Popen(["open", file_path]) # non-blocking on macOS
        else:
            print(f"Downloaded update to {file_path} (launch manually).")
        return True
    except Exception as e:
        print(f"Failed to launch installer: {e}")
        return False


def _download_to(file_url: str, final_path: str, timeout: float = 60.0) -> str:
    """
    Download file_url to final_path atomically (tmp file then rename).
    Returns the final_path on success.
    """
    req = urllib.request.Request(
        file_url,
        headers={"User-Agent": "YsaGUI-Updater/1.0 (+github-actions)"},
        method="GET",
    )
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    if os.path.exists(final_path):
        try:
            os.remove(final_path)
        except Exception:
            pass

    with closing(urllib.request.urlopen(req, timeout=timeout)) as r, \
         tempfile.NamedTemporaryFile(delete=False, dir=os.path.dirname(final_path)) as tmp:
        while True:
            chunk = r.read(1024 * 256)
            if not chunk:
                break
            tmp.write(chunk)
        tmp_path = tmp.name

    shutil.move(tmp_path, final_path)  # atomic finalization
    return final_path


def _choose_asset(release: dict) -> str | None:
    """
    Return the browser_download_url for the correct asset, or None.
    Uses exact, stable filenames produced by CI.
    """
    want = None
    arch = platform.machine().lower()  # e.g. 'x86_64', 'arm64', 'aarch64'

    if sys.platform == "win32":
        want = ASSET_WIN
    elif sys.platform == "darwin":
        if "arm" in arch or "aarch64" in arch:
            want = ASSET_MAC_ARM
        else:
            want = ASSET_MAC_X86
    else:
        return None
    
    print(f"Platform: {sys.platform}, Arch: {arch}")
    print(f"Expected asset: {want}")

    for a in release.get("assets", []):
        if a.get("name") == want:
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
        
        dl_name = ASSET_WIN if sys.platform == "win32" else (
            ASSET_MAC_ARM if "arm" in platform.machine().lower() else ASSET_MAC_X86
        )
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        dest = os.path.join(downloads, dl_name)

        # Clean up any older delete-me installers
        for name in os.listdir(downloads):
            if name.endswith("_DELETE_ME.pkg") or name.endswith("_DELETE_ME.exe"):
                try:
                    os.remove(os.path.join(downloads, name))
                except Exception:
                    pass

        print(f"Downloading updater to: {dest}")
        _download_to(download_url, dest, timeout=120.0)

        # Launch asynchronously so the GUI doesn't freeze
        launched = _launch_installer(dest)
        if not launched:
            return False

        print("Installer launched. The app may be closed during update.")
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
