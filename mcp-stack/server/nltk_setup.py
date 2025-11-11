"""
NLTK Data Setup Script

This script ensures that all required NLTK data is downloaded and available
before the application starts. It should be imported before any other modules
that use NLTK.
"""
import os
import sys
import nltk
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_nltk():
    """Set up NLTK data directory and download required packages."""
    try:
        # Set the NLTK data directory to a user-writable location
        nltk_data_dir = os.path.join(os.path.expanduser('~'), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)

        # Add to NLTK's data path
        nltk.data.path.append(nltk_data_dir)

        # Set environment variable for NLTK to find the data
        os.environ['NLTK_DATA'] = nltk_data_dir

        # List of NLTK data packages to download
        nltk_packages = [
            'punkt',         # For tokenization
            'stopwords',     # For stop word filtering
            'wordnet',       # For lemmatization
            'averaged_perceptron_tagger',  # For part-of-speech tagging
            'vader_lexicon'  # For sentiment analysis
        ]

        logger.info("Checking NLTK data...")

        # Download each package if not already present
        for package in nltk_packages:
            try:
                nltk.data.find(f'tokenizers/{package}')
                logger.info(f" {package} is already downloaded")
            except LookupError:
                logger.info(f"Downloading {package}...")
                try:
                    nltk.download(package, download_dir=nltk_data_dir, quiet=True)
                    logger.info(f" Successfully downloaded {package}")
                except Exception as e:
                    logger.error(f" Failed to download {package}: {str(e)}")

        # Special handling for punkt_tab
        try:
            nltk.data.find('tokenizers/punkt_tab')
            logger.info(" punkt_tab is already available")
        except LookupError:
            logger.info("Setting up punkt_tab...")
            try:
                punkt_dir = os.path.join(nltk_data_dir, 'tokenizers', 'punkt')
                punkt_tab_dir = os.path.join(nltk_data_dir, 'tokenizers', 'punkt_tab')

                if os.path.exists(punkt_dir):
                    if not os.path.exists(punkt_tab_dir):
                        logger.info(f"Creating symlink from {punkt_dir} to {punkt_tab_dir}")
                        if os.name == 'nt':  # Windows
                            import ctypes
                            if hasattr(ctypes, 'windll'):
                                ctypes.windll.kernel32.CreateSymbolicLinkW(
                                    punkt_tab_dir,
                                    punkt_dir,
                                    1  # Directory flag
                                )
                                logger.info(" Created punkt_tab symlink")
                            else:
                                logger.warning("Could not create symlink: ctypes.windll not available")
                        else:  # Unix-like
                            os.symlink(punkt_dir, punkt_tab_dir)
                            logger.info(" Created punkt_tab symlink")
                    else:
                        logger.info(" punkt_tab already exists")
                else:
                    logger.warning(f"Could not create punkt_tab: {punkt_dir} does not exist")
            except Exception as e:
                logger.error(f" Could not create punkt_tab symlink: {str(e)}")

        logger.info("NLTK setup complete!")
        return True
        
    except Exception as e:
        logger.error(f"Error in NLTK setup: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    setup_nltk()
