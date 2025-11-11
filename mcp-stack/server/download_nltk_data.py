"""
Script to download NLTK data required for the application.
Run this script once to download all necessary NLTK data.
"""
import nltk
import os

def download_nltk_data():
    """Download required NLTK data packages."""
    print("Checking for required NLTK data...")
    
    # List of NLTK data packages to download
    nltk_packages = [
        'punkt',         # For tokenization
        'stopwords',     # For stop word filtering
        'wordnet',       # For lemmatization
        'averaged_perceptron_tagger',  # For part-of-speech tagging
        'vader_lexicon'  # For sentiment analysis
    ]
    
    # Download each package if not already present
    for package in nltk_packages:
        try:
            nltk.data.find(f'tokenizers/{package}')
            print(f"✓ {package} is already downloaded")
        except LookupError:
            print(f"Downloading {package}...")
            nltk.download(package, quiet=False)
    
    print("\nNLTK data setup complete!")

if __name__ == "__main__":
    download_nltk_data()
