#!/usr/bin/env python3
"""
Integration test for YSA GUI.
Tests that the GUI can launch and optionally process a test file.
"""

import os
import sys
import signal
import argparse
from pathlib import Path

# Set QT_QPA_PLATFORM before importing Qt
if sys.platform == 'darwin':
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
elif sys.platform == 'win32':
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer


def test_gui_launch(test_file=None, timeout_seconds=10):
    """
    Test that the GUI can launch successfully.

    Args:
        test_file: Optional path to a .brw or .h5 file to load
        timeout_seconds: How long to let the GUI run before exiting

    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"Starting GUI launch test...")
    print(f"  Platform: {sys.platform}")
    print(f"  QT_QPA_PLATFORM: {os.environ.get('QT_QPA_PLATFORM', 'default')}")
    print(f"  Test file: {test_file or 'None'}")
    print(f"  Timeout: {timeout_seconds}s")

    # Add src to path so we can import main
    src_path = Path(__file__).parent.parent / 'src'
    sys.path.insert(0, str(src_path))

    try:
        # Import after adding to path
        import main

        # Create application
        app = QApplication(sys.argv)

        # Set up a timer to exit after timeout
        success = [False]  # Use list to allow modification in nested function

        def on_timeout():
            print(f"[OK] GUI ran successfully for {timeout_seconds} seconds")
            success[0] = True
            app.quit()

        timer = QTimer()
        timer.timeout.connect(on_timeout)
        timer.setSingleShot(True)
        timer.start(timeout_seconds * 1000)

        # Create main window
        print("Creating main window...")
        window = main.MainWindow()

        # If test file provided, try to load it
        if test_file and os.path.exists(test_file):
            print(f"Loading test file: {test_file}")
            window.file_path = test_file
            window.set_widgets_enabled()
            # Don't run analysis for now - just verify loading works
            # window.run_analysis()

        # Show window (in offscreen mode this won't actually display)
        window.show()
        print("[OK] Window created and shown")

        # Run event loop
        app.exec_()

        return success[0]

    except Exception as e:
        print(f"[ERROR] GUI test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Test YSA GUI launch')
    parser.add_argument('--test-file', type=str, help='Path to test file to load')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout in seconds')
    args = parser.parse_args()

    success = test_gui_launch(
        test_file=args.test_file,
        timeout_seconds=args.timeout
    )

    if success:
        print("\n[PASS] GUI integration test PASSED")
        sys.exit(0)
    else:
        print("\n[FAIL] GUI integration test FAILED")
        sys.exit(1)


if __name__ == '__main__':
    main()
