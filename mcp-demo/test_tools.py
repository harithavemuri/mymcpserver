"""
Test script to isolate which tool is causing the punkt_tab error.
"""
import asyncio
from mcp.tools.text_processor import TextProcessor
from mcp.tools.sentiment_analyzer import SentimentAnalyzer
from mcp.tools.keyword_extractor import KeywordExtractor
from mcp.models import TextRequest

async def test_tool(tool, name):
    print(f"\nTesting {name}...")
    try:
        request = TextRequest(
            text="This is a test sentence to check if the tool works properly.",
            params={"to_upper": True} if name == "TextProcessor" else {}
        )
        response = await tool.process(request)
        print(f"✅ {name} worked successfully!")
        print(f"Response: {response.result}")
        return True
    except Exception as e:
        print(f"❌ Error in {name}:")
        print(str(e))
        return False

async def main():
    # Test each tool one by one
    tools = [
        (TextProcessor(), "TextProcessor"),
        (SentimentAnalyzer(), "SentimentAnalyzer"),
        (KeywordExtractor(), "KeywordExtractor"),
    ]

    for tool, name in tools:
        success = await test_tool(tool, name)
        if not success:
            print(f"\nStopping tests due to error in {name}")
            break

if __name__ == "__main__":
    asyncio.run(main())
