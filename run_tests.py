#!/usr/bin/env python3
"""
run_tests.py
------------
Auto-test runner for SDP-202X project.
Monitors file changes and automatically runs tests.

Usage:
    python run_tests.py                    # Start watching for changes
    python run_tests.py --run-once         # Run tests once and exit
    python run_tests.py --levelup-only     # Run only LevelUpSystem tests
"""

import sys
import os 
import time
import subprocess
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class TestRunner(FileSystemEventHandler):
    """File system event handler that runs tests on file changes."""

    def __init__(self, args):
        self.args = args
        self.last_run = 0
        self.debounce_time = 1.0  # Wait 1 second between runs
        self.project_root = Path(__file__).parent

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        # Only care about Python files in src/ or tests/
        file_path = Path(event.src_path)
        file_path_str = str(file_path).replace('\\', '/')  # Convert to forward slashes for consistency
        if not (file_path.suffix == '.py' and
                ('src/' in file_path_str or 'tests/' in file_path_str)):
            return

        # Debounce rapid file changes
        current_time = time.time()
        if current_time - self.last_run < self.debounce_time:
            return

        self.last_run = current_time
        self.run_tests()

    def run_tests(self):
        """Run the test suite."""
        print("\n" + "="*60)
        print("Running tests...")
        print("="*60)

        # Build pytest command
        cmd = ["python", "-m", "pytest"]

        if self.args.levelup_only:
            cmd.extend(["tests/ui/test_level_up_ui.py", "tests/entities/test_player_leveling.py", "-v"])
        else:
            cmd.extend(["-v"])

        if self.args.coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-fail-under=70"
            ])

        # Run tests
        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=False)

            if result.returncode == 0:
                print("All tests passed!")
            else:
                print("Some tests failed!")

        except KeyboardInterrupt:
            print("\nTest execution interrupted")
            return False
        except Exception as e:
            print(f"Error running tests: {e}")
            return False

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Auto-test runner for SDP-202X")
    parser.add_argument("--run-once", action="store_true",
                       help="Run tests once and exit")
    parser.add_argument("--levelup-only", action="store_true",
                       help="Run only LevelUpSystem tests")
    parser.add_argument("--coverage", action="store_true",
                       help="Generate coverage report")

    args = parser.parse_args()

    # Check if pytest is available
    try:
        import pytest # noqa: F401
    except ImportError:
        print("pytest not found. Please install with:")
        print("   pip install -r requirements-test.txt")
        return 1

    # Create test runner
    test_runner = TestRunner(args)

    # Run tests once if requested
    if args.run_once:
        success = test_runner.run_tests()
        return 0 if success else 1

    # Start file watcher
    print("Starting file watcher...")
    print("Monitoring: src/ and tests/ directories")
    print("Press Ctrl+C to stop")
    print("Tests will run automatically on file changes")

    if args.levelup_only:
        print("Running only LevelUpSystem tests")

    # Run initial tests
    test_runner.run_tests()

    # Set up observer
    event_handler = test_runner
    observer = Observer()

    # Watch src/ and tests/ directories
    for directory in ["src", "tests"]:
        if os.path.exists(directory):
            observer.schedule(event_handler, directory, recursive=True)

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nFile watcher stopped")

    observer.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())