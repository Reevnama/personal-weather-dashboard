"""
The purpose of this python file is to automatically run the dashboard script without having to write the terminal command "streamlit run ...".

This will also allow me to add arguments to command without the user having to necessarily add them themselves.
"""

import subprocess
from pathlib import Path

dashboard = Path(__file__).with_name('dashboard.py')
subprocess.run(["streamlit", "run", f"{dashboard}", 
                "--server.runOnSave=True"])