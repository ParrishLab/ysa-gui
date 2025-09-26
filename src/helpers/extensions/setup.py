from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext
import pybind11
import os
import sys
import subprocess


def get_hdf5_paths():
    """
    Dynamically find HDF5 installation paths.
    Priority: (1) HDF5_DIR/HDF5_ROOT, (2) active conda env, (3) Homebrew, (4) platform fallbacks.
    Returns: include_dir, library_dir, lib_dir (alias), libraries, extra_link_args.
    """
    import os, subprocess, sys

    def pack(inc, lib, libs=None, extra=None):
        d = {
            "include_dir": inc,
            "library_dir": lib,
            "libraries": libs or ["hdf5", "hdf5_hl"],
            "extra_link_args": (extra or []) + (
                [f"-Wl,-rpath,{lib}"] if sys.platform == "darwin" else []
            ),
        }
        # Back-compat alias if other code still uses "lib_dir"
        d["lib_dir"] = d["library_dir"]
        return d
    
    def first_existing(paths):
        for p in paths:
            if os.path.isdir(p):
                return p
        return None
    
    # Respect explicit overrides for library names (optional)
    env_libs = os.environ.get("HDF5_LIBS")
    default_libs = env_libs.split(",") if env_libs else ["hdf5", "hdf5_hl"]

    # 1) HDF5_DIR / HDF5_ROOT
    for var in ("HDF5_DIR", "HDF5_ROOT"):
        base = os.environ.get(var)
        if base:
            inc, lib = os.path.join(base, "include"), os.path.join(base, "lib")
            if os.path.isdir(inc) and os.path.isdir(lib):
                return pack(inc, lib)
            
    # 2) Active conda env
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        inc, lib = os.path.join(conda_prefix, "include"), os.path.join(conda_prefix, "lib")
        if os.path.isdir(inc) and os.path.isdir(lib):
            return pack(inc, lib)
        
    # 3) Homebrew (works for both /opt/homebrew and /usr/local)
    try:
        prefix = subprocess.check_output(["brew", "--prefix", "hdf5"]).decode().strip()
        inc = first_existing([os.path.join(prefix, "include", "hdf5"), os.path.join(prefix, "include")])
        lib = os.path.join(prefix, "lib")
        if inc and os.path.isdir(lib):
            return pack(inc, lib)
    except Exception:
        pass

    # 4) Existing platform fallbacks
    fallback_paths = {
        "darwin": {
            "include_dir": [
                "/opt/homebrew/include/hdf5",
                "/usr/local/include/hdf5",
                "/usr/include/hdf5",
                "/opt/homebrew/include", 
                "/usr/local/include",
            ],
            "lib_dir": ["/opt/homebrew/lib", "/usr/local/lib", "/usr/lib"],
        },
        "linux": {
            "include_dir": [
                "/usr/include/hdf5/serial",
                "/usr/local/include/hdf5",
                "/usr/include/hdf5",
                "/usr/include", 
            ],
            "lib_dir": ["/usr/lib/x86_64-linux-gnu", "/usr/local/lib", "/usr/lib"],
        },
    }

    platform_paths = fallback_paths.get(sys.platform, fallback_paths["linux"])
    include_dir = first_existing(platform_paths["include_dir"])
    lib_dir = first_existing(platform_paths["lib_dir"])

    if not include_dir or not lib_dir:
        raise RuntimeError("Could not find HDF5 installation paths")

    # Normalize key names and add rpath on macOS
    return pack(include_dir, lib_dir)


# Determine compilation flags based on platform
extra_compile_flags = ["-std=c++17", "-O3"]
extra_link_flags = []

# Universal binary for macOS
if sys.platform == "darwin":
    extra_compile_flags.extend(["-arch", "arm64", "-arch", "x86_64"])
    extra_link_flags.extend(["-arch", "arm64", "-arch", "x86_64"])

# Get HDF5 paths
hdf5_paths = get_hdf5_paths()

ext_modules = [
    Pybind11Extension(
        "sz_se_detect",
        ["sz_se_detect.cpp"],
        include_dirs=[
            pybind11.get_include(),
            hdf5_paths["include_dir"],
        ],
        library_dirs=[hdf5_paths["lib_dir"]],
        libraries=["hdf5_cpp", "hdf5"],
        extra_compile_args=extra_compile_flags + [f"-I{hdf5_paths['include_dir']}"],
        extra_link_args=extra_link_flags + [f"-L{hdf5_paths['lib_dir']}"],
    ),
    Pybind11Extension(
        "signal_analyzer",
        ["signal_analyzer.cpp"],
        include_dirs=[pybind11.get_include()],
        extra_compile_args=extra_compile_flags,
        extra_link_args=extra_link_flags,
    ),
]

setup(
    name="neuro_signal_processing",
    version="0.0.3",
    author="Jake Cahoon",
    author_email="jacobbcahoon@gmail.com",
    description="A module for seizure and status epilepticus detection, and signal analysis",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.6",
)
