"""
Script to set up NLTK data in the correct location.
Run this script to download and configure NLTK data.
"""
import os
import nltk

# Define the NLTK data directory
nltk_data_dir = os.path.join(os.path.expanduser('~'), 'nltk_data')

# Create the directory if it doesn't exist
os.makedirs(nltk_data_dir, exist_ok=True)

# Add the directory to NLTK's data path
nltk.data.path.append(nltk_data_dir)

# List of NLTK data packages to download
required_data = [
    'punkt',
    'stopwords',
    'wordnet',
    'averaged_perceptron_tagger',
    'vader_lexicon'
]

print(f"Setting up NLTK data in: {nltk_data_dir}")

# Download each required package
for package in required_data:
    try:
        print(f"Downloading {package}...")
        nltk.download(package, download_dir=nltk_data_dir)
        print(f"✓ {package} downloaded successfully")
    except Exception as e:
        print(f"✗ Error downloading {package}: {str(e)}")

# Special handling for punkt_tab (create a symlink on Windows)
try:
    punkt_dir = os.path.join(nltk_data_dir, 'tokenizers', 'punkt')
    punkt_tab_dir = os.path.join(nltk_data_dir, 'tokenizers', 'punkt_tab')
    
    if os.path.exists(punkt_dir) and not os.path.exists(punkt_tab_dir):
        print("Creating punkt_tab symlink...")
        if os.name == 'nt':  # Windows
            import ctypes
            ctypes.windll.kernel32.CreateSymbolicLinkW(
                punkt_tab_dir,
                punkt_dir,
                1  # Directory flag
            )
        else:  # Unix-like
            os.symlink(punkt_dir, punkt_tab_dir)
        print("✓ Created punkt_tab symlink")
    elif os.path.exists(punkt_tab_dir):
        print("✓ punkt_tab already exists")
    else:
        print("⚠ Could not create punkt_tab symlink: punkt directory not found")
except Exception as e:
    print(f"⚠ Error creating punkt_tab symlink: {str(e)}")

print("\nNLTK data setup complete!")
