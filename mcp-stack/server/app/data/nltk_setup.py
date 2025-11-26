"""
NLTK Setup Module
----------------
This module ensures NLTK and its required data are properly set up.
It runs automatically when the data package is imported.
"""
import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def ensure_nltk_installed():
    """Ensure NLTK is installed, install it if necessary."""
    try:
        import nltk
        return True
    except ImportError:
        print("NLTK not found. Installing NLTK...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "nltk"])
            import nltk
            print("✓ NLTK installed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to install NLTK: {e}")
            return False

def setup_nltk_data():
    """Set up NLTK data directory and download required packages."""
    if not ensure_nltk_installed():
        return None

    import nltk

    # Define required NLTK data packages
    required_data = [
        'punkt',
        'stopwords',
        'wordnet',
        'averaged_perceptron_tagger',
        'vader_lexicon'
    ]

    # Try multiple possible NLTK data locations
    possible_paths = [
        Path.home() / 'nltk_data',
        Path(__file__).parent / 'nltk_data',
        Path.cwd() / 'nltk_data'
    ]

    # Create directories and add to NLTK path
    nltk_data_dirs = []
    for path in possible_paths:
        try:
            path.mkdir(parents=True, exist_ok=True)
            nltk_data_dirs.append(str(path))
            print(f"✓ Using NLTK data directory: {path}")
        except Exception as e:
            print(f"⚠ Could not create NLTK data directory at {path}: {e}")

    if not nltk_data_dirs:
        print("❌ No valid NLTK data directories could be created")
        return None

    # Add all valid paths to NLTK's data path
    nltk.data.path = nltk_data_dirs + nltk.data.path

    # Download required NLTK data
    for data in required_data:
        try:
            nltk.download(data, quiet=True)
            print(f"✓ Downloaded NLTK data: {data}")
        except Exception as e:
            print(f"⚠ Failed to download NLTK data '{data}': {e}")

    # Handle punkt_tab for Windows
    if platform.system() == 'Windows':
        try:
            punkt_dir = None
            for path in nltk_data_dirs:
                punkt_path = Path(path) / 'tokenizers' / 'punkt'
                if punkt_path.exists():
                    punkt_dir = punkt_path
                    break

            if punkt_dir:
                punkt_tab_dir = punkt_dir.parent / 'punkt_tab'
                if not punkt_tab_dir.exists():
                    shutil.copytree(punkt_dir, punkt_tab_dir)
                    print(f"✓ Created punkt_tab at {punkt_tab_dir}")
                else:
                    print(f"✓ punkt_tab already exists at {punkt_tab_dir}")
        except Exception as e:
            print(f"⚠ Could not create punkt_tab: {e}")

    return nltk_data_dirs[0]

# Run the setup when this module is imported
print("\n=== Initializing NLTK Data ===")
nltk_data_dir = setup_nltk_data()
if nltk_data_dir:
    print(f"\n✓ NLTK data initialization complete. Using directory: {nltk_data_dir}")
else:
    print("\n⚠ NLTK data initialization completed with warnings")
print("=" * 30 + "\n")
