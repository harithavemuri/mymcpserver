import pytest
from app.data.data_loader import data_loader
from app.graphql.schema import schema

@pytest.mark.asyncio
async def test_get_customers_with_transcripts():
    """Test that we can retrieve customers with their transcripts, including sentiment and contexts."""
    # Make sure we have some test data
    customers = data_loader.load_customers()
    transcripts = data_loader.load_transcripts()
    
    # Ensure we have at least one transcript
    assert len(transcripts) > 0, "No transcripts found in test data"
    
    # Get customers with transcripts using our new query
    query = """
    query GetCustomersWithTranscripts {
        getCustomersWithTranscripts {
            customerId
            firstName
            lastName
            transcripts {
                callId
                callSummary
                sentiment {
                    polarity
                    subjectivity
                }
                contexts
            }
        }
    }
    """
    
    result = await schema.execute(query)
    
    # Check for errors
    assert result.errors is None, f"Query failed: {result.errors}"
    
    # Get the result data
    customers_data = result.data.get("getCustomersWithTranscripts", [])
    
    # Verify we got some results
    assert len(customers_data) > 0, "No customers with transcripts found"
    
    # Verify each customer has at least one transcript with the expected fields
    for customer in customers_data:
        assert len(customer["transcripts"]) > 0, f"Customer {customer['customerId']} has no transcripts"
        
        for transcript in customer["transcripts"]:
            # Verify sentiment exists and has the expected structure
            assert "sentiment" in transcript, f"Transcript {transcript['callId']} is missing sentiment"
            assert isinstance(transcript["sentiment"], dict), "Sentiment should be a dictionary"
            assert "polarity" in transcript["sentiment"], "Sentiment is missing polarity"
            assert "subjectivity" in transcript["sentiment"], "Sentiment is missing subjectivity"
            
            # Verify polarity is between -1 and 1
            assert -1 <= transcript["sentiment"]["polarity"] <= 1, "Polarity should be between -1 and 1"
            
            # Verify subjectivity is between 0 and 1
            assert 0 <= transcript["sentiment"]["subjectivity"] <= 1, "Subjectivity should be between 0 and 1"
            
            # Verify contexts exists and is a list
            assert "contexts" in transcript, f"Transcript {transcript['callId']} is missing contexts"
            assert isinstance(transcript["contexts"], list), "Contexts should be a list"
            
            # If there's a call summary, there should be at least one context
            if transcript.get("callSummary", "").strip():
                assert len(transcript["contexts"]) > 0, \
                    f"Transcript with non-empty summary should have at least one context"
        
        print(f"✓ Customer {customer['firstName']} {customer['lastName']} has {len(customer['transcripts'])} transcripts with sentiment and context analysis")
