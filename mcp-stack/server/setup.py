from setuptools import setup, find_packages

def download_nltk_data():
    """Download required NLTK data."""
    import nltk

    # List of NLTK data packages to download
    nltk_data = [
        'punkt',
        'stopwords',
        'wordnet',
        'averaged_perceptron_tagger',
        'vader_lexicon'  # For sentiment analysis
    ]

    print("Downloading NLTK data...")
    for data in nltk_data:
        try:
            nltk.download(data, quiet=True)
            print(f"Downloaded NLTK data: {data}")
        except Exception as e:
            print(f"Error downloading NLTK data {data}: {str(e)}")

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="mcp-server",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
    # This will run the download_nltk_data function after installation
    # when someone runs: pip install -e .
    cmdclass={
        'develop': lambda _: download_nltk_data(),
        'install': lambda _: download_nltk_data()
    },
    # Include any non-python files that are part of your package
    include_package_data=True,
    # Add any additional metadata
    author="Your Name",
    author_email="your.email@example.com",
    description="MCP Server for handling customer feedback and analysis",
    url="https://github.com/yourusername/mcp-stack",
)

# Also run the download when setup.py is run directly
if __name__ == "__main__":
    download_nltk_data()
