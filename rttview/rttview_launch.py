"""PyInstaller entry point -- thin launcher so the package imports cleanly."""
from rttview.__main__ import main

if __name__ == "__main__":
    main()
