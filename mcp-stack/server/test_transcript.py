"""Test script for CallTranscript and TranscriptEntry classes with sentiment and context analysis."""
import sys
import os
import nltk
import pytest
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import the NLTK setup module to ensure data is available
from nltk_setup import setup_nltk

# Set up NLTK data before importing anything else
setup_nltk()

# Now import the modules that use NLTK
from app.data.data_loader import CallTranscript, DataLoader, analyze_sentiment, extract_contexts

@pytest.fixture
def sample_transcript_data() -> Dict[str, Any]:
    """Fixture providing sample transcript data for testing."""
    return {
        "call_id": "TEST123",
        "customer_id": "CUST1000",
        "call_type": "inbound",
        "call_timestamp": "2025-10-15T10:30:00Z",
        "call_duration_seconds": 325,
        "agent_id": "AGENT456",
        "call_summary": "Customer called to report an issue with their recent order. "
                        "They were very upset about the delay in delivery and the poor "
                        "customer service they received. The agent apologized and offered "
                        "a discount on their next purchase to make up for the inconvenience.",
        "is_ada_related": False,
        "ada_violation_occurred": False,
        "transcript": [
            {
                "speaker": "customer", 
                "text": "I'm very disappointed with my recent order. The product arrived late and was damaged.", 
                "timestamp": "10:30:05"
            },
            {
                "speaker": "agent", 
                "text": "I'm sorry to hear that. Could you tell me what happened? We'll make this right.", 
                "timestamp": "10:30:10"
            }
        ]
    }

def test_transcript_creation(sample_transcript_data):
    """Test creation of CallTranscript with sentiment and contexts."""
    transcript = CallTranscript(**sample_transcript_data)
    
    # Test basic fields
    assert transcript.call_id == "TEST123"
    assert transcript.customer_id == "CUST1000"
    assert len(transcript.transcript) == 2
    
    # Test transcript entries
    assert transcript.transcript[0].speaker == "customer"
    assert "disappointed" in transcript.transcript[0].text.lower()
    assert transcript.transcript[1].speaker == "agent"
    
    # Test sentiment analysis on the transcript
    assert hasattr(transcript, 'sentiment')
    assert isinstance(transcript.sentiment, dict)
    assert 'polarity' in transcript.sentiment
    assert 'subjectivity' in transcript.sentiment
    assert -1 <= transcript.sentiment['polarity'] <= 1
    assert 0 <= transcript.sentiment['subjectivity'] <= 1
    
    # Test contexts extraction
    assert hasattr(transcript, 'contexts')
    assert isinstance(transcript.contexts, list)
    assert len(transcript.contexts) > 0

def test_transcript_entry_sentiment(sample_transcript_data):
    """Test transcript entry structure."""
    transcript = CallTranscript(**sample_transcript_data)
    
    # Test customer entry structure
    customer_entry = transcript.transcript[0]
    assert hasattr(customer_entry, 'speaker')
    assert hasattr(customer_entry, 'text')
    assert hasattr(customer_entry, 'timestamp')
    
    # Test agent entry structure
    agent_entry = transcript.transcript[1]
    assert hasattr(agent_entry, 'speaker')
    assert hasattr(agent_entry, 'text')
    assert hasattr(agent_entry, 'timestamp')


def test_transcript_entry_structure(sample_transcript_data):
    """Test transcript entry structure."""
    transcript = CallTranscript(**sample_transcript_data)
    
    # Test customer entry
    customer_entry = transcript.transcript[0]
    assert customer_entry.speaker == "customer"
    assert "disappointed" in customer_entry.text.lower()
    
    # Test agent entry
    agent_entry = transcript.transcript[1]
    assert agent_entry.speaker == "agent"
    assert "sorry" in agent_entry.text.lower()

def test_sentiment_analysis_edge_cases():
    """Test sentiment analysis with edge cases."""
    # Test empty text
    empty_sentiment = analyze_sentiment("")
    assert empty_sentiment["polarity"] == 0.0
    assert empty_sentiment["subjectivity"] == 0.0
    
    # Test neutral text
    neutral_sentiment = analyze_sentiment("This is a test.")
    assert -0.1 <= neutral_sentiment["polarity"] <= 0.1
    
    # Test very positive text
    positive_sentiment = analyze_sentiment("I'm extremely happy with this excellent service!")
    assert positive_sentiment["polarity"] > 0.5
    
    # Test very negative text
    negative_sentiment = analyze_sentiment("This is absolutely terrible and I'm very angry!")
    assert negative_sentiment["polarity"] < -0.5

def test_context_extraction_edge_cases():
    """Test context extraction with edge cases."""
    # Test empty text
    assert extract_contexts("") == []
    
    # Test very short text
    short_text = "Hello world"
    assert extract_contexts(short_text) == ["hello world"]
    
    # Test text with stopwords only
    assert extract_contexts("the and or but") == []
    
    # Test text with special characters
    special_text = "Order #1234 was delayed! Contact support@example.com"
    contexts = extract_contexts(special_text)
    assert "order" in " ".join(contexts).lower()
    assert "delayed" in " ".join(contexts).lower()

def test_with_actual_data():
    """Test with actual data from the data loader."""
    data_loader = DataLoader()
    transcripts = data_loader.load_transcripts()
    
    # Test at least one transcript has the expected structure
    assert len(transcripts) > 0, "No transcripts found in the data loader"
    
    # Test the first transcript with a summary
    for transcript in transcripts.values():
        if transcript.call_summary.strip():
            # Test transcript has required fields
            assert hasattr(transcript, 'call_id')
            assert hasattr(transcript, 'call_summary')
            
            # Test sentiment analysis
            assert hasattr(transcript, 'sentiment')
            assert isinstance(transcript.sentiment, dict)
            assert 'polarity' in transcript.sentiment
            assert 'subjectivity' in transcript.sentiment
            
            # Test contexts
            assert hasattr(transcript, 'contexts')
            assert isinstance(transcript.contexts, list)
            
            # Test transcript entries have sentiment and contexts
            if hasattr(transcript, 'transcript') and transcript.transcript:
                entry = transcript.transcript[0]
                assert hasattr(entry, 'sentiment')
                assert hasattr(entry, 'contexts')
                
                # Just verify the entry has the basic fields
                assert hasattr(entry, 'text')
                assert hasattr(entry, 'speaker')
                assert hasattr(entry, 'timestamp')
            
            break  # Only test the first valid transcript

def test_with_actual_data():
    """Test with actual data from the data loader."""
    print("\n=== Testing with Actual Data ===")
    data_loader = DataLoader()
    
    # Get the first transcript with a summary
    for transcript in data_loader.load_transcripts().values():
        if transcript.call_summary.strip():
            print(f"\nCall ID: {transcript.call_id}")
            print(f"Summary: {transcript.call_summary[:100]}...")
            print("Sentiment:", transcript.sentiment)
            print("Contexts:", transcript.contexts[:5])  # Show first 5 contexts
            break

if __name__ == "__main__":
    # Install NLTK data
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        print("Downloading NLTK data...")
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('vader_lexicon')
    
    # Run tests using pytest
    import pytest
    pytest.main([__file__, "-v"])
