import os

try:
    hdf5_dir = "path/to/your/HDF5-1.14.5-win64"
    os.environ["PATH"] = os.path.join(hdf5_dir, "bin") + os.pathsep + os.environ["PATH"]
    import sz_se_detect

    print("sz_se_detect module is installed")
except ImportError as e:
    print("sz_se_detect module is not installed")
    print(f"Error: {e}")
