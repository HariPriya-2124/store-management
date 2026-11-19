#!/bin/bash
# One-click launcher for Store Management System on macOS
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo " Starting Store Management System..."
echo "=========================================================="

if [ -f ".venv/bin/python" ]; then
    .venv/bin/python main.py
else
    python3 main.py
fi

