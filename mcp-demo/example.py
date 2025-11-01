"""
MCP (Model Context Protocol) Example

This script demonstrates how to use the MCP server and host to process text
through a workflow of tools.
"""
import asyncio
import json
import sys
from typing import Optional

from mcp import MCPServer, MPCHost, MCPConfig
from mcp.models import TextRequest, ToolName


async def run_server(port: int = 8001):
    """Run the MCP server on the specified port."""
    config = MCPConfig(
        host="0.0.0.0",
        port=port,
        debug=True
    )
    
    # Configure specific tools if needed
    config.tools[ToolName.TEXT_PROCESSOR].params.update({
        "to_upper": True,
        "to_lower": True,
    })
    
    config.tools[ToolName.KEYWORD_EXTRACTOR].params.update({
        "top_n": 5,
        "extract_named_entities": True,
    })
    
    # Create and run the server
    server = MCPServer(config)
    print(f"Starting MCP server on port {port}...")
    await server.run()


async def run_client(port: int = 8008, text: str = None):
    """Run a client that connects to the MCP server."""
    # Create a host instance
    async with MPCHost(f"http://localhost:{port}") as host:
        # Check if server is healthy
        if not await host.health_check():
            print("Error: MCP server is not running or not healthy")
            return
        
        # List available tools
        tools = await host.list_tools()
        print("\nAvailable tools:")
        for tool_name, tool_info in tools.items():
            print(f"- {tool_name}: {tool_info['description']}")
        
        # Use provided text or default example
        if not text:
            text = """
            The Model Context Protocol (MCP) is a powerful framework for building
            AI-powered applications. It enables seamless integration of multiple
            AI models and tools in a unified workflow. With MCP, developers can
            easily chain together different processing steps and create sophisticated
            AI pipelines.
            """
        
        print("\nProcessing text...")
        response = await host.process_text(text)
        
        # Print the raw response for debugging
        print("\nRaw response:")
        print(json.dumps(response.model_dump(), indent=2))
        
        if response.success and response.result:
            print("\nProcessing successful!")
            
            # Get the results from the response
            results = getattr(response.result, 'results', {})
            
            # Print formatted results
            print("\n=== Text Analysis Results ===")
            
            # Get original text
            original_text = getattr(response.result, 'original_text', 'N/A')
            if isinstance(original_text, str):
                print(f"Original text: {original_text[:100]}...")
            
            # Print sentiment analysis results
            sentiment = results.get(ToolName.SENTIMENT_ANALYZER)
            if sentiment:
                print("\nSentiment Analysis:")
                print(f"  - Polarity: {sentiment.get('polarity', 'N/A'):.2f}")
                print(f"  - Subjectivity: {sentiment.get('subjectivity', 'N/A'):.2f}")
                print(f"  - Word Count: {sentiment.get('word_count', 'N/A')}")
                print(f"  - Sentence Count: {sentiment.get('sentence_count', 'N/A')}")
            
            # Print keyword extraction results
            keywords = results.get(ToolName.KEYWORD_EXTRACTOR)
            if keywords and 'keywords' in keywords:
                print("\nTop Keywords:")
                for kw in keywords['keywords'][:5]:
                    print(f"  - {kw.get('phrase', 'N/A')} (score: {kw.get('score', 0):.2f})")
            
            # Print text processing results
            text_processing = results.get(ToolName.TEXT_PROCESSOR)
            if text_processing:
                print("\nText Processing:")
                if 'uppercase' in text_processing:
                    print(f"  - Uppercase: {text_processing['uppercase'][:100]}...")
                if 'lowercase' in text_processing:
                    print(f"  - Lowercase: {text_processing['lowercase'][:100]}...")
                if 'word_count' in text_processing:
                    print(f"  - Word Count: {text_processing['word_count']}")
        
        else:
            print(f"\nError: {response.error}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Example")
    parser.add_argument(
        "--server", 
        action="store_true",
        help="Run the MCP server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8002,
        help="Port to run the server on (default: 8002)"
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Text to analyze (default: uses example text)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.server:
            await run_server(args.port)
        else:
            await run_client(args.port, args.text)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
