"""
PyInstaller Build Script for Store Management System.
Generates a standalone executable distribution for macOS, Windows, and Linux.
Configures cache and build artifacts within the project directory for portability.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MAIN_FILE = BASE_DIR / "main.py"
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
BUILD_DIR = BASE_DIR / "build"
DIST_DIR = BASE_DIR / "dist"
CACHE_DIR = BUILD_DIR / "pyinstaller_cache"

def build():
    print(f"Building Store Management System for {platform.system()} ({platform.machine()})...")

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Set PyInstaller cache directory to local build folder to prevent permission issues
    os.environ["PYINSTALLER_CONFIG_DIR"] = str(CACHE_DIR)

    # Separator for PyInstaller --add-data differs by OS (: on Unix/macOS, ; on Windows)
    sep = ";" if platform.system() == "Windows" else ":"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=StoreManagementSystem",
        "--onedir",
        "--windowed",
        "--clean",
        "--noconfirm",
        f"--workpath={BUILD_DIR}",
        f"--distpath={DIST_DIR}",
        f"--add-data={DATA_DIR}{sep}data",
        f"--add-data={ASSETS_DIR}{sep}assets",
        f"--add-data={BASE_DIR / 'config.py'}{sep}.",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=matplotlib",
        "--hidden-import=matplotlib.backends.backend_tkagg",
        "--hidden-import=PIL",
        str(MAIN_FILE),
    ]

    print("Executing command:")
    print(" ".join(cmd))

    env = os.environ.copy()
    env["PYINSTALLER_CONFIG_DIR"] = str(CACHE_DIR)

    result = subprocess.run(cmd, cwd=str(BASE_DIR), env=env)
    if result.returncode == 0:
        print("\n✓ Build completed successfully!")
        dist_path = DIST_DIR / "StoreManagementSystem"
        print(f"Binary directory located at: {dist_path}")
    else:
        print(f"\n❌ Build failed with exit code {result.returncode}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    build()
