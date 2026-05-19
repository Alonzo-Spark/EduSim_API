import sys
import os

# Align python import path to backend directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.generate_curriculum_from_pdfs import main

if __name__ == "__main__":
    main()
