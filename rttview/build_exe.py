"""Build a single-file rttview executable with PyInstaller.

Cross-platform: run `python build_exe.py` on Windows, macOS or Linux. The output
lands in ./dist/rttview (or dist\rttview.exe on Windows).
"""
import os
import PyInstaller.__main__

sep = os.pathsep  # ';' on Windows, ':' elsewhere
PyInstaller.__main__.run([
    "--onefile",
    "--name", "rttview",
    "--clean",
    "--noconfirm",
    "--collect-submodules", "rttview",
    "--add-data", f"rttview/efc{sep}rttview/efc",
    "rttview_launch.py",
])
