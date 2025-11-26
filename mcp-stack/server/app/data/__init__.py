"""
Data package initialization.
This ensures NLTK is installed and data is properly set up before any other imports.
"""

# Import the NLTK setup module which will run automatically
from .nltk_setup import nltk_data_dir  # noqa: F401
from .data_service import data_service  # noqa: F401

__all__ = ['data_service', 'nltk_data_dir']
