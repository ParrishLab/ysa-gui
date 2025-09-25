#!/usr/bin/env python3
"""Test runner script for YSA GUI project."""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return its exit code."""
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tests for YSA GUI project")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--lint", action="store_true", help="Run linting")
    parser.add_argument("--type-check", action="store_true", help="Run type checking")
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Set up environment
    project_root = str(Path(__file__).parent)
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    if current_pythonpath:
        os.environ['PYTHONPATH'] = f"{project_root}:{current_pythonpath}"
    else:
        os.environ['PYTHONPATH'] = project_root
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'

    # Also add to sys.path for immediate effect
    import sys
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    exit_code = 0

    # Default to running all if no specific tests specified
    if not any([args.unit, args.integration, args.lint, args.type_check]):
        args.all = True

    # Type checking
    if args.type_check or args.all:
        print("Running type checking...")
        cmd = ["mypy", "src/", "--ignore-missing-imports", "--no-strict-optional"]
        exit_code |= run_command(cmd, "Type checking with mypy")

    # Linting
    if args.lint or args.all:
        print("Running linting...")
        cmd = ["flake8", "src/", "tests/", "--max-line-length=100", "--extend-ignore=E203,W503"]
        exit_code |= run_command(cmd, "Linting with flake8")

    # Unit tests
    if args.unit or args.all:
        print("Running unit tests...")
        cmd = ["pytest", "tests/unit/"]
        if args.verbose:
            cmd.append("-v")
        if args.fast:
            cmd.extend(["-m", "not slow"])
        if args.coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])

        exit_code |= run_command(cmd, "Unit tests")

    # Integration tests
    if args.integration or args.all:
        print("Running integration tests...")
        cmd = ["pytest", "tests/integration/"]
        if args.verbose:
            cmd.append("-v")
        if args.fast:
            cmd.extend(["-m", "not slow"])
        if args.coverage:
            cmd.extend(["--cov=src", "--cov-append", "--cov-report=term-missing"])

        exit_code |= run_command(cmd, "Integration tests")

    # Generate coverage report
    if args.coverage and (args.unit or args.integration or args.all):
        print("Generating coverage report...")
        cmd = ["pytest", "--cov=src", "--cov-report=html", "--cov-report=xml", "tests/"]
        if args.fast:
            cmd.extend(["-m", "not slow"])

        run_command(cmd, "Coverage report generation")
        print("\nCoverage report generated:")
        print("  HTML: htmlcov/index.html")
        print("  XML: coverage.xml")

    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())