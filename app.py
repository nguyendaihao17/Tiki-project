"""Compatibility entry point for Streamlit Cloud."""
from pathlib import Path
import runpy
import sys

project_root = Path(__file__).resolve().parent / "03_08_TikiLens"
source_root = project_root / "source-code"
sys.path.insert(0, str(source_root))
runpy.run_path(str(source_root / "app.py"), run_name="__main__")
