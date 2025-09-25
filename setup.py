"""Setup script for YSA GUI."""

from setuptools import setup, find_packages

setup(
    name="ysa-gui",
    version="1.0.0",
    description="A PyQt5-based application for analyzing MEA neural data",
    author="YSA GUI Development Team",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "numpy>=1.21.0",
        "scipy>=1.7.0",
        "h5py>=3.6.0",
        "pyqtgraph>=0.12.0",
        "matplotlib>=3.5.0",
        "scikit-learn>=1.0.0",
        "pandas>=1.3.0",
        "psutil>=5.8.0",
        "Pillow>=8.3.0",
        "loguru>=0.6.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "pytest-qt>=4.2.0",
            "pytest-xvfb>=3.0.0",
            "pytest-timeout>=2.1.0",
            "pytest-asyncio>=0.21.0",
            "factory-boy>=3.3.0",
            "freezegun>=1.2.0",
            "hypothesis>=6.82.0",
            "faker>=19.0.0",
            "coverage>=7.3.0",
            "pytest-html>=3.2.0",
            "pytest-json-report>=1.5.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
            "pylint>=2.17.0",
            "bandit>=1.7.0",
            "safety>=2.3.0",
        ],
    },
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "ysa-gui=src.main:main",
        ],
    },
)