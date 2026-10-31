"""Compatibility entry point for Streamlit Cloud; application source lives in source-code/."""
from pathlib import Path
import runpy
import sys

source_root = Path(__file__).resolve().parent / "source-code"
sys.path.insert(0, str(source_root))
runpy.run_path(str(source_root / "app.py"), run_name="__main__")
