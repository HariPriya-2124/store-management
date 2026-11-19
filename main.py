"""
Root launcher for Store Management System.
Redirects execution into store_management_system/main.py.
"""

import sys
import os
from pathlib import Path
import importlib.util

PROJECT_DIR = Path(__file__).resolve().parent / "store_management_system"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

target = PROJECT_DIR / "main.py"
spec = importlib.util.spec_from_file_location("store_main", str(target))
store_main = importlib.util.module_from_spec(spec)
sys.modules["store_main"] = store_main
spec.loader.exec_module(store_main)

main = store_main.main
SupermarketApp = getattr(store_main, "SupermarketApp", None)

if __name__ == "__main__":
    main()
