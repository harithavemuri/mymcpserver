"""Test script to verify sentence-transformers model loading."""
import logging
from sentence_transformers import SentenceTransformer

def test_model_loading():
    """Test if the sentence-transformers model loads correctly."""
    try:
        print("Loading sentence-transformers model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully!")

        # Test encoding
        text = "This is a test sentence."
        embedding = model.encode(text)
        print(f"Embedding shape: {embedding.shape}")
        print("Test completed successfully!")
        return True
    except Exception as e:
        print(f"Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_model_loading()
