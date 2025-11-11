"""
Script to set up NLTK data for the application.
Run this script once to download all necessary NLTK data.
"""
import nltk
import os
import sys

def setup_nltk_data():
    """Download and set up NLTK data."""
    print("Setting up NLTK data...")
    
    # Set NLTK data path to a directory where we have write permissions
    nltk_data_dir = os.path.join(os.path.expanduser('~'), 'nltk_data')
    os.makedirs(nltk_data_dir, exist_ok=True)
    nltk.data.path.append(nltk_data_dir)
    
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
            try:
                nltk.download(package, download_dir=nltk_data_dir, quiet=False)
                print(f"✓ Successfully downloaded {package}")
            except Exception as e:
                print(f"✗ Failed to download {package}: {str(e)}")
    
    # Update NLTK data path
    nltk.data.path.append(nltk_data_dir)
    
    # Set environment variable for NLTK to find the data
    os.environ['NLTK_DATA'] = nltk_data_dir
    
    print("\nNLTK data setup complete!")
    print(f"NLTK data directory: {nltk_data_dir}")
    
    # Verify the data can be found
    print("\nVerifying NLTK data...")
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        print("✓ NLTK data verification successful!")
        return True
    except LookupError as e:
        print(f"✗ NLTK data verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = setup_nltk_data()
    if success:
        print("\nYou can now run the application with NLTK support.")
    else:
        print("\nThere were issues setting up NLTK data. Please check the error messages above.")
        sys.exit(1)
