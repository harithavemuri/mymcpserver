"""
Test script to check sentiment analyzer with a specific text.
"""
import asyncio
from mcp import MPCHost

async def test_sentiment():
    """Test the sentiment analyzer with a specific text."""
    port = 8002
    text = "I am very sad"
    
    print(f"Testing sentiment analysis for text: {text}")
    
    async with MPCHost(f"http://localhost:{port}") as host:
        # Check if server is healthy
        if not await host.health_check():
            print("Error: MCP server is not running or not healthy")
            return
        
        print("\nProcessing text...")
        response = await host.process_text(text)
        
        # Print the raw response for debugging
        print("\nRaw response:")
        import json
        print(json.dumps(response.model_dump(), indent=2))
        
        if response.success and response.result:
            print("\nProcessing successful!")
            
            # Get the results from the response
            results = getattr(response.result, 'results', {})
            
            # Print sentiment analysis results
            sentiment = results.get('sentiment_analyzer', {})
            if sentiment:
                print("\nSentiment Analysis:")
                print(f"  - Polarity: {sentiment.get('polarity', 'N/A')}")
                print(f"  - Subjectivity: {sentiment.get('subjectivity', 'N/A')}")
                print(f"  - Label: {sentiment.get('label', 'N/A')}")
                print(f"  - Word Count: {sentiment.get('word_count', 'N/A')}")
                print(f"  - Sentence Count: {sentiment.get('sentence_count', 'N/A')}")
        else:
            print(f"\nError: {response.error}")

if __name__ == "__main__":
    asyncio.run(test_sentiment())
