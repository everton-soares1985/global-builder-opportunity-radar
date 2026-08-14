"""Local launcher for the Global Builder Opportunity Radar.

Configuration:
- Activate .venv before running.
- Use `python -X utf8 radar.py --help`.
"""

from global_builder_radar.cli import app

if __name__ == "__main__":
    app()
