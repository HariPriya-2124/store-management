#!/usr/bin/env bash
cd "$(dirname "$0")"
HOME="$(pwd)" .venv/bin/streamlit run app.py
