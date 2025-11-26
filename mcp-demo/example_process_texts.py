"""
Example showing how to use MPCHost.process_texts to process multiple texts in parallel.
Uses MCP_SERVER_URL environment variable from .env file.
"""
import asyncio
import os
from dotenv import load_dotenv
from mcp import MPCHost

# Load environment variables from .env file
load_dotenv()

async def main():
    # Initialize the MCP host using environment variable
    async with MPCHost() as host:
        # Sample texts to process
        texts = [
            "I love this product! It's amazing!",
            "The service was terrible and slow.",
            "It's okay, but could be better.",
            "Absolutely fantastic experience!",
            "Not what I expected, quite disappointed."
        ]

        print("Processing texts...")

        # Process texts in parallel (default is 5 concurrent requests)
        responses = await host.process_texts(
            texts=texts,
            params={
                "to_upper": True,  # Example parameter for text processor
                "top_n": 3         # Example parameter for keyword extractor
            },
            max_concurrent=3  # Adjust based on your server capacity
        )

        # Print the results
        for i, (text, response) in enumerate(zip(texts, responses), 1):
            print(f"\n--- Text {i} ---")
            print(f"Original: {text}")
            print(f"Success: {response.success}")

            if response.success and response.result:
                result = response.result
                print("\nProcessing Results:")

                # Access the nested results
                if hasattr(result, 'results') and isinstance(result.results, dict):
                    results = result.results

                    # Text Processing Results
                    if 'text_processor' in results and isinstance(results['text_processor'], dict):
                        tp = results['text_processor']
                        print(f"\nText Analysis:")
                        print(f"- Original: {tp.get('original_text')}")
                        print(f"- Length: {tp.get('length')} characters")
                        print(f"- Words: {tp.get('word_count')}")

                    # Sentiment Analysis Results
                    if 'sentiment_analyzer' in results and isinstance(results['sentiment_analyzer'], dict):
                        sa = results['sentiment_analyzer']
                        print(f"\nSentiment Analysis:")
                        print(f"- Label: {sa.get('label', 'N/A').title()}")
                        print(f"- Polarity: {sa.get('polarity'):.2f}")
                        print(f"- Subjectivity: {sa.get('subjectivity', 'N/A')}")

                    # Keyword Extraction Results
                    if 'keyword_extractor' in results and isinstance(results['keyword_extractor'], dict):
                        ke = results['keyword_extractor']
                        if 'keywords' in ke and ke['keywords']:
                            print(f"\nTop Keywords:")
                            for i, kw in enumerate(ke['keywords'][:5], 1):
                                if isinstance(kw, dict) and 'phrase' in kw and 'score' in kw:
                                    print(f"  {i}. {kw['phrase']} (Score: {kw['score']:.1f})")

                    # Print a separator
                    print("\n" + "="*50)
            else:
                print(f"Error: {response.error}")

if __name__ == "__main__":
    asyncio.run(main())
