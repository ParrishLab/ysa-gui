import ctypes

try:
    ctypes.cdll.LoadLibrary(
        "/Users/booka66/mea-gui/src/helpers/extensions/sz_se_detect.cpython-310-darwin.so"
    )
    print("Library can be loaded")
except Exception as e:
    print(f"Error loading library: {e}")
