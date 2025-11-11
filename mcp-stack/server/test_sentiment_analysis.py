"""Test script for sentiment analysis and context extraction."""
from app.data.data_loader import DataLoader, CallTranscript
from pprint import pprint

def test_transcript_analysis():
    """Test sentiment analysis and context extraction on a sample transcript."""
    # Sample transcript data
    sample_transcript = {
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
            {"speaker": "customer", "text": "I'm very disappointed with my recent order.", "timestamp": "10:30:05"},
            {"speaker": "agent", "text": "I'm sorry to hear that. Could you tell me what happened?", "timestamp": "10:30:10"}
        ]
    }
    
    # Create transcript instance (this will trigger the analysis)
    transcript = CallTranscript(**sample_transcript)
    
    # Print results
    print("\n=== Transcript Analysis ===")
    print(f"Call ID: {transcript.call_id}")
    print(f"Customer ID: {transcript.customer_id}")
    print("\nSentiment Analysis:")
    pprint(transcript.sentiment)
    print("\nExtracted Contexts:")
    for i, context in enumerate(transcript.contexts, 1):
        print(f"{i}. {context}")
    
    print("\n=== End of Analysis ===")

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
    nltk.download('punkt')
    nltk.download('stopwords')
    
    test_transcript_analysis()
    test_with_actual_data()
