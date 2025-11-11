"""
Data package initialization.
This ensures NLTK data is properly set up before any other imports.
"""
import os
import nltk

def setup_nltk_data():
    """Set up NLTK data directory and download required packages."""
    # Try multiple possible NLTK data locations
    possible_paths = [
        os.path.join(os.path.expanduser('~'), 'nltk_data'),
        os.path.join(os.path.dirname(__file__), 'nltk_data'),
        os.path.join(os.getcwd(), 'nltk_data')
    ]
    
    for nltk_data_dir in possible_paths:
        try:
            # Create directory if it doesn't exist
            os.makedirs(nltk_data_dir, exist_ok=True)
            
            # Add to NLTK's data path
            if nltk_data_dir not in nltk.data.path:
                nltk.data.path.append(nltk_data_dir)
            
            # Set environment variable
            os.environ['NLTK_DATA'] = nltk_data_dir
            
            # Check if punkt is available
            try:
                nltk.data.find('tokenizers/punkt')
                return nltk_data_dir
            except LookupError:
                # Download punkt if not found
                nltk.download('punkt', download_dir=nltk_data_dir, quiet=True)
                nltk.download('stopwords', download_dir=nltk_data_dir, quiet=True)
                nltk.download('wordnet', download_dir=nltk_data_dir, quiet=True)
                nltk.download('averaged_perceptron_tagger', download_dir=nltk_data_dir, quiet=True)
                nltk.download('vader_lexicon', download_dir=nltk_data_dir, quiet=True)
                
                # Verify download
                nltk.data.find('tokenizers/punkt')
                return nltk_data_dir
                
        except Exception as e:
            continue
    
    # If we get here, we couldn't set up NLTK data
    raise RuntimeError(
        "Could not set up NLTK data. Please run 'python -m nltk.downloader punkt' manually."
    )

# Set up NLTK data when the package is imported
try:
    nltk_data_dir = setup_nltk_data()
    print(f"NLTK data initialized from: {nltk_data_dir}")
except Exception as e:
    print(f"Warning: Could not initialize NLTK data: {str(e)}")
    print("Some features may not work correctly.")
