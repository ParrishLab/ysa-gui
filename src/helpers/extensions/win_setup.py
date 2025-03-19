from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext
import pybind11
import os
import shutil
from setuptools.command.install import install
from setuptools.command.develop import develop

hdf5_dir = os.path.join(os.environ.get("GITHUB_WORKSPACE", ""), "HDF5-1.14.5-win64")
hdf5_include_dir = os.path.join(hdf5_dir, "include")
hdf5_lib_dir = os.path.join(hdf5_dir, "lib")
hdf5_bin_dir = os.path.join(hdf5_dir, "bin")

# Path is only set for the build process
os.environ["PATH"] = hdf5_bin_dir + os.pathsep + os.environ["PATH"]


# Create custom install commands to copy DLLs
class CustomInstallCommand(install):
    def run(self):
        install.run(self)
        # Copy HDF5 DLLs to the package directory
        self._copy_dlls()

    def _copy_dlls(self):
        # Get the installed package directory
        install_dir = self.install_lib
        # Copy required DLLs
        for dll in ["hdf5.dll", "hdf5_cpp.dll"]:
            src = os.path.join(hdf5_bin_dir, dll)
            dst = os.path.join(install_dir, dll)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"Copied {src} to {dst}")
            else:
                print(f"Warning: Could not find {src}")


class CustomDevelopCommand(develop):
    def run(self):
        develop.run(self)
        # Copy HDF5 DLLs to the package directory
        self._copy_dlls()

    def _copy_dlls(self):
        # Get the development package directory
        if self.distribution.packages:
            package_dir = self.distribution.packages[0]
        else:
            package_dir = "."
        # Copy required DLLs
        for dll in ["hdf5.dll", "hdf5_cpp.dll"]:
            src = os.path.join(hdf5_bin_dir, dll)
            dst = os.path.join(package_dir, dll)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"Copied {src} to {dst}")
            else:
                print(f"Warning: Could not find {src}")


use_dynamic = True
if use_dynamic:
    compile_args = ["/std:c++17", f"/I{hdf5_include_dir}", "/DH5_BUILT_AS_DYNAMIC_LIB"]
    libraries = ["hdf5_cpp", "hdf5"]
else:
    compile_args = ["/std:c++17", f"/I{hdf5_include_dir}"]
    libraries = ["libhdf5_cpp", "libhdf5"]

link_args = [
    f"/LIBPATH:{hdf5_lib_dir}",
    "/DEPENDENTLOADFLAG:0x2000",
]

ext_modules = [
    Pybind11Extension(
        "sz_se_detect",
        ["sz_se_detect_win.cpp"],
        include_dirs=[
            pybind11.get_include(),
            hdf5_include_dir,
        ],
        library_dirs=[hdf5_lib_dir],
        libraries=libraries,
        extra_compile_args=compile_args,
        extra_link_args=link_args,
    ),
    Pybind11Extension(
        "signal_analyzer",
        ["signal_analyzer.cpp"],
        include_dirs=[pybind11.get_include()],
        extra_compile_args=["/std=c++17"],
    ),
]

setup(
    name="sz_se_detect",
    version="0.0.1",
    author="Jake Cahoon",
    author_email="jacobbcahoon@gmail.com",
    description="A module for seizure and status epilepticus detection",
    ext_modules=ext_modules,
    cmdclass={
        "build_ext": build_ext,
        "install": CustomInstallCommand,
        "develop": CustomDevelopCommand,
    },
    zip_safe=False,
    python_requires=">=3.6",
    # Make empty packages list to avoid issues with develop command
    packages=[],
)
