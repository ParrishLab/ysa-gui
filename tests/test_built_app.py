#!/usr/bin/env python3
"""
Test the PyInstaller-built application.
This tests the actual executable that users will run.
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path


def find_executable():
    """Find the built YsaGUI executable."""
    dist_path = Path(__file__).parent.parent / 'dist'

    if sys.platform == 'darwin':
        # macOS: Look for .app bundle
        app_path = dist_path / 'YsaGUI.app' / 'Contents' / 'MacOS' / 'YsaGUI'
        if app_path.exists():
            return app_path

        # Alternative: look for onedir build
        app_path = dist_path / 'YsaGUI' / 'YsaGUI.app' / 'Contents' / 'MacOS' / 'YsaGUI'
        if app_path.exists():
            return app_path

    elif sys.platform == 'win32':
        # Windows: Look for .exe
        exe_path = dist_path / 'YsaGUI' / 'YsaGUI.exe'
        if exe_path.exists():
            return exe_path

    raise FileNotFoundError(
        f"Could not find YsaGUI executable in {dist_path}\n"
        f"Make sure PyInstaller build completed successfully."
    )


def test_executable(test_file=None, timeout_seconds=10):
    """
    Test that the built executable can launch and run.

    Args:
        test_file: Optional path to a test file to load
        timeout_seconds: How long to let the app run

    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"Testing built YSA GUI executable...")
    print(f"  Platform: {sys.platform}")

    try:
        exe_path = find_executable()
        print(f"[OK] Found executable: {exe_path}")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return False

    # Build command
    cmd = [str(exe_path)]
    if test_file:
        cmd.append(str(test_file))

    # Set up environment for headless operation
    env = os.environ.copy()
    if sys.platform == 'darwin':
        env['QT_QPA_PLATFORM'] = 'offscreen'
    elif sys.platform == 'win32':
        # On Windows CI, offscreen may not work - try minimal platform
        env['QT_QPA_PLATFORM'] = 'minimal'
        # Also disable GPU acceleration which can cause issues in CI
        env['QT_OPENGL'] = 'software'

    print(f"Launching: {' '.join(cmd)}")
    print(f"  QT_QPA_PLATFORM: {env.get('QT_QPA_PLATFORM', 'default')}")
    if sys.platform == 'win32':
        print(f"  QT_OPENGL: {env.get('QT_OPENGL', 'default')}")

    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f"[OK] Process started (PID: {process.pid})")
        print(f"  Waiting {timeout_seconds} seconds...")

        # Wait for timeout
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)

            # If it exited before timeout, check return code
            if process.returncode == 0:
                print("[OK] Process exited cleanly")
                return True
            else:
                print(f"[ERROR] Process exited with code {process.returncode}")
                if stderr:
                    print("STDERR:", stderr[:1000])
                if stdout:
                    print("STDOUT:", stdout[:1000])

                # On Windows, if we get an access violation, it might be Qt platform issues
                if sys.platform == 'win32' and process.returncode in [3221225477, -1073741819]:
                    print("[INFO] Windows access violation detected - this may be a Qt platform plugin issue")
                    print("[INFO] The executable was built successfully but cannot run in CI without a display")

                return False

        except subprocess.TimeoutExpired:
            # Timeout is expected - the GUI should still be running
            print(f"[OK] Process still running after {timeout_seconds}s")

            # Terminate gracefully
            process.terminate()
            try:
                process.wait(timeout=5)
                print("[OK] Process terminated gracefully")
            except subprocess.TimeoutExpired:
                print("[WARN] Process didn't terminate, forcing kill")
                process.kill()
                process.wait()

            return True

    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Test built YSA GUI executable')
    parser.add_argument('--test-file', type=str, help='Path to test file to load')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout in seconds')
    args = parser.parse_args()

    success = test_executable(
        test_file=args.test_file,
        timeout_seconds=args.timeout
    )

    if success:
        print("\n[PASS] Executable test PASSED")
        sys.exit(0)
    else:
        print("\n[FAIL] Executable test FAILED")
        sys.exit(1)


if __name__ == '__main__':
    main()
