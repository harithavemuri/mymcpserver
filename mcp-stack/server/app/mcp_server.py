"""MCP Server implementation using FastMCP."""
import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field, validator
import google.generativeai as genai

# Add the parent directory to the path to allow importing app modules
sys.path.append(str(Path(__file__).parent.parent))
from app.data.data_loader import data_loader, Customer, CallTranscript

# Configure logging to stderr as per MCP standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Important: Log to stderr, not stdout
)
logger = logging.getLogger(__name__)

# Initialize Gemini AI if API key is available
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class MCPConfig(BaseModel):
    """Configuration for the MCP server."""
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    reload: bool = os.getenv("ENV") == "development"

class GeminiRequest(BaseModel):
    """Request model for Gemini AI generation."""
    prompt: str = Field(..., description="The prompt to send to Gemini AI")
    model: str = Field("gemini-1.5-flash", description="The Gemini model to use")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Sampling temperature")
    max_tokens: int = Field(2048, gt=0, description="Maximum number of tokens to generate")

# Initialize FastMCP
app = FastMCP(
    name="mcp-server",
    version="0.1.0"
)

# Initialize prompts dictionary with general and customer-specific prompts
app.prompts = {
    # General prompts
    "analyze_sentiment": "Analyze the sentiment of the following text: {text}",
    "summarize_call": "Please summarize the following call transcript: {transcript}",
    "extract_action_items": "Extract action items from the following text: {text}",
    "categorize_issue": "Categorize the following customer issue: {issue_description}",
    "generate_response": "Generate a professional response to the following message: {message}",

    # Customer-related prompts
    "find_customer_by_id": "Retrieve customer details for customer ID: {customer_id}",
    "find_customer_by_email": "Find customer with email address: {email}",
    "search_customers_by_name": "Search for customers with names containing: {name_query}",
    "find_customers_by_company": "List all customers from company: {company_name}",
    "find_customers_by_location": "Find customers in {city}, {state}, {country}",
    "get_customer_call_history": "Retrieve call history for customer ID: {customer_id}",
    "find_high_value_customers": "Identify high-value customers with criteria: {criteria}",
    "get_customer_interaction_summary": "Generate a summary of all interactions for customer ID: {customer_id}",
    "find_similar_customers": "Find customers similar to customer ID: {customer_id} based on {criteria}",
    "get_customer_retention_risk": "Analyze retention risk for customer ID: {customer_id}",
    "get_customer_lifetime_value": "Calculate lifetime value for customer ID: {customer_id}",
    "find_customers_by_product": "Find all customers who purchased product: {product_id}",
    "get_customer_support_tickets": "Retrieve all support tickets for customer ID: {customer_id}",
    "find_customers_needing_followup": "Identify customers who need follow-up based on {criteria}"
}

@app.tool()
async def gemini_generate(prompt: str, model: str = "gemini-1.5-flash", temperature: float = 0.7, ctx: Context = None) -> str:
    """
    Generate text using Google's Gemini AI.

    Args:
        prompt: The prompt to send to the model
        model: The Gemini model to use (default: gemini-1.5-flash)
        temperature: Sampling temperature (0.0 to 1.0)

    Returns:
        The generated text response from Gemini AI
    """
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY environment variable.")
    try:
        # Initialize the model
        model = genai.GenerativeModel(model)

        # Generate content
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": 2048,
            }
        )
        return response.text
    except Exception as e:
        error_msg = f"Error generating content with Gemini: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise

@app.tool()
async def analyze_sentiment(text: str) -> Dict[str, float]:
    """
    Analyze the sentiment of the given text.

    Args:
        text: The text to analyze

    Returns:
        A dictionary containing 'polarity' and 'subjectivity' scores
    """
    # This is a placeholder implementation
    # In a real implementation, you would use a proper sentiment analysis model
    return {"polarity": 0.5, "subjectivity": 0.5}

@app.tool()
async def get_customer(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve a customer by their ID.

    Args:
        customer_id: The ID of the customer to retrieve

    Returns:
        A dictionary containing the customer's information
    """
    try:
        customer = data_loader.get_customer(customer_id)
        if customer:
            return customer.dict()
        else:
            return {"error": f"Customer with ID {customer_id} not found"}
    except Exception as e:
        logger.error(f"Error retrieving customer {customer_id}: {str(e)}", exc_info=True)
        return {"error": f"Error retrieving customer: {str(e)}"}

@app.tool()
async def search_customers(
    query: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    company: Optional[str] = None,
    has_transcripts: Optional[bool] = None,
    min_transcripts: Optional[int] = None,
    last_contact_days: Optional[int] = None,
    sort_by: str = "relevance",  # 'relevance', 'name', 'last_contact', 'transcript_count'
    sort_order: str = "desc",    # 'asc' or 'desc'
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Advanced search for customers with full-text search and multiple filters.

    Args:
        query: Full-text search across name, email, company, and address
        name: Filter by customer name (partial match, case-insensitive)
        email: Filter by email address (partial match, case-insensitive)
        phone: Filter by phone number (partial match)
        state: Filter by state (exact match, case-insensitive)
        city: Filter by city (partial match, case-insensitive)
        company: Filter by company name (partial match, case-insensitive)
        has_transcripts: Filter customers with/without transcripts
        min_transcripts: Minimum number of transcripts a customer must have
        last_contact_days: Maximum days since last contact
        sort_by: Field to sort by ('relevance', 'name', 'last_contact', 'transcript_count')
        sort_order: Sort order ('asc' or 'desc')
        limit: Maximum number of results to return (default: 10)
        offset: Number of results to skip (for pagination)

    Returns:
        A dictionary containing:
        - results: List of matching customers with relevance scores
        - total: Total number of matches
        - limit: Number of results per page
        - offset: Current offset
    """
    try:
        # Get base customer list
        customers = data_loader.search_customers(
            name=name or (query if not (email or phone or company) else None),
            email=email,
            phone=phone,
            state=state,
            city=city,
            company=company,
            limit=limit,
            offset=offset
        )

        # Convert to dicts and add additional data
        customer_dicts = []
        for customer in customers:
            customer_data = customer.dict()

            # Get transcripts for this customer
            transcripts = data_loader.search_transcripts(customer_id=customer.customer_id)
            transcript_count = len(transcripts)

            # Add transcript metadata
            customer_data['transcript_count'] = transcript_count
            customer_data['last_contact'] = (
                max(t.call_timestamp for t in transcripts).isoformat()
                if transcripts else None
            )

            # Calculate relevance score based on query match
            relevance = 0
            if query:
                query = query.lower()
                fields_to_search = [
                    customer_data.get('personal_info', {}).get('first_name', '').lower(),
                    customer_data.get('personal_info', {}).get('last_name', '').lower(),
                    customer_data.get('personal_info', {}).get('email', '').lower(),
                    customer_data.get('employment', {}).get('company', '').lower(),
                    f"{customer_data.get('home_address', {}).get('city', '')}, {customer_data.get('home_address', {}).get('state', '')}".lower()
                ]

                # Simple relevance scoring
                for field in fields_to_search:
                    if query in field:
                        relevance += 1
                    if field.startswith(query):
                        relevance += 2  # Higher score for prefix matches

            customer_data['_relevance'] = relevance
            customer_dicts.append(customer_data)

        # Apply additional filters
        filtered_customers = []
        for customer in customer_dicts:
            # Apply has_transcripts filter
            if has_transcripts is not None:
                has_transcripts_bool = customer['transcript_count'] > 0
                if has_transcripts != has_transcripts_bool:
                    continue

            # Apply min_transcripts filter
            if min_transcripts is not None and customer['transcript_count'] < min_transcripts:
                continue

            # Apply last_contact_days filter
            if last_contact_days is not None and customer['last_contact']:
                from datetime import datetime, timedelta
                last_contact = datetime.fromisoformat(customer['last_contact'].replace('Z', '+00:00'))
                if (datetime.now(last_contact.tzinfo) - last_contact).days > last_contact_days:
                    continue

            filtered_customers.append(customer)

        # Sort results
        reverse_sort = sort_order.lower() == 'desc'
        if sort_by == 'relevance' and query:
            filtered_customers.sort(key=lambda x: x['_relevance'], reverse=True)
        elif sort_by == 'name':
            filtered_customers.sort(
                key=lambda x: f"{x.get('personal_info', {}).get('last_name', '')} "
                            f"{x.get('personal_info', {}).get('first_name', '')}".lower(),
                reverse=reverse_sort
            )
        elif sort_by == 'last_contact':
            filtered_customers.sort(
                key=lambda x: x.get('last_contact') or '',
                reverse=reverse_sort
            )
        elif sort_by == 'transcript_count':
            filtered_customers.sort(
                key=lambda x: x.get('transcript_count', 0),
                reverse=reverse_sort
            )

        # Apply pagination
        paginated_results = filtered_customers[offset:offset + limit]

        # Remove internal fields before returning
        for customer in paginated_results:
            customer.pop('_relevance', None)

        return {
            'results': paginated_results,
            'total': len(filtered_customers),
            'limit': limit,
            'offset': offset
        }

    except Exception as e:
        logger.error(f"Error in advanced customer search: {str(e)}", exc_info=True)
        return {
            'results': [],
            'total': 0,
            'error': f"Error searching customers: {str(e)}",
            'limit': limit,
            'offset': offset
        }

@app.tool()
async def get_customer_transcripts(customer_id: str) -> List[Dict[str, Any]]:
    """
    Get all transcripts for a specific customer.

    Args:
        customer_id: The ID of the customer

    Returns:
        A list of the customer's call transcripts with sentiment and context analysis
    """
    try:
        # First verify the customer exists
        customer = data_loader.get_customer(customer_id)
        if not customer:
            return [{"error": f"Customer with ID {customer_id} not found"}]

        # Get all transcripts for this customer
        transcripts = data_loader.search_transcripts(customer_id=customer_id)
        return [t.dict() for t in transcripts]
    except Exception as e:
        logger.error(f"Error retrieving transcripts for customer {customer_id}: {str(e)}", exc_info=True)
        return [{"error": f"Error retrieving transcripts: {str(e)}"}]

@app.tool()
async def search_transcripts(
    query: Optional[str] = None,
    customer_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    agent_id: Optional[str] = None,
    call_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_duration: Optional[int] = None,
    max_duration: Optional[int] = None,
    min_sentiment: Optional[float] = None,
    max_sentiment: Optional[float] = None,
    has_context: Optional[bool] = None,
    context: Optional[str] = None,
    is_ada_related: Optional[bool] = None,
    ada_violation_occurred: Optional[bool] = None,
    sort_by: str = "date",  # 'date', 'duration', 'sentiment', 'relevance'
    sort_order: str = "desc",  # 'asc' or 'desc'
    limit: int = 10,
    offset: int = 0,
    include_summary: bool = True,
    include_transcript: bool = False
) -> Dict[str, Any]:
    """
    Advanced search for call transcripts with comprehensive filtering and sorting.

    Args:
        query: Full-text search across call summary and transcript content
        customer_id: Filter by customer ID
        customer_name: Filter by customer name (partial match, case-insensitive)
        agent_id: Filter by agent ID
        call_type: Filter by call type (e.g., 'support', 'sales', 'billing')
        start_date: Filter by start date (YYYY-MM-DD or ISO format)
        end_date: Filter by end date (YYYY-MM-DD or ISO format)
        min_duration: Minimum call duration in seconds
        max_duration: Maximum call duration in seconds
        min_sentiment: Minimum sentiment polarity (-1.0 to 1.0)
        max_sentiment: Maximum sentiment polarity (-1.0 to 1.0)
        has_context: Filter transcripts that have/don't have context data
        context: Filter by specific context (e.g., 'billing', 'technical_support')
        is_ada_related: Filter ADA-related calls
        ada_violation_occurred: Filter calls with ADA violations
        sort_by: Field to sort by ('date', 'duration', 'sentiment', 'relevance')
        sort_order: Sort order ('asc' or 'desc')
        limit: Maximum number of results to return (default: 10)
        offset: Number of results to skip (for pagination)
        include_summary: Whether to include call summary in results (default: True)
        include_transcript: Whether to include full transcript content (default: False)

    Returns:
        A dictionary containing:
        - results: List of matching transcripts
        - total: Total number of matches
        - limit: Number of results per page
        - offset: Current offset
        - aggregations: Summary statistics (counts by call type, sentiment, etc.)
    """
    try:
        # First, get the base set of transcripts
        transcripts = data_loader.search_transcripts(
            customer_id=customer_id,
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        # Convert to dicts and add additional data
        transcript_dicts = []
        call_types = set()
        sentiment_scores = []

        for transcript in transcripts:
            transcript_data = transcript.dict()

            # Get customer data if needed
            if customer_name or query:
                customer = data_loader.get_customer(transcript.customer_id)
                if customer:
                    transcript_data['customer'] = customer.dict()

            # Calculate relevance score if query is provided
            relevance = 0
            if query:
                query = query.lower()

                # Search in call summary
                if 'call_summary' in transcript_data and transcript_data['call_summary']:
                    summary = transcript_data['call_summary'].lower()
                    if query in summary:
                        relevance += summary.count(query) * 2  # More occurrences = higher score
                        if summary.startswith(query):
                            relevance += 5  # Bonus for prefix match in summary

                # Search in transcript content if included
                if include_transcript and 'transcript' in transcript_data:
                    for entry in transcript_data['transcript']:
                        if 'text' in entry and query in entry['text'].lower():
                            relevance += 1

            transcript_data['_relevance'] = relevance

            # Track call types and sentiment for aggregations
            call_type = transcript_data.get('call_type')
            if call_type:
                call_types.add(call_type)

            sentiment = transcript_data.get('sentiment', {}).get('polarity', 0)
            sentiment_scores.append(sentiment)

            transcript_dicts.append(transcript_data)

        # Apply additional filters
        filtered_transcripts = []
        for t in transcript_dicts:
            # Apply call type filter
            if call_type and t.get('call_type') != call_type:
                continue

            # Apply duration filters
            duration = t.get('call_duration_seconds', 0)
            if min_duration is not None and duration < min_duration:
                continue
            if max_duration is not None and duration > max_duration:
                continue

            # Apply sentiment filters
            sentiment = t.get('sentiment', {}).get('polarity', 0)
            if min_sentiment is not None and sentiment < min_sentiment:
                continue
            if max_sentiment is not None and sentiment > max_sentiment:
                continue

            # Apply context filters
            contexts = t.get('contexts', [])
            if has_context is not None:
                has_contexts = bool(contexts)
                if has_context != has_contexts:
                    continue

            if context and context.lower() not in [c.lower() for c in contexts]:
                continue

            # Apply ADA filters
            if is_ada_related is not None and t.get('is_ada_related') != is_ada_related:
                continue

            if ada_violation_occurred is not None and t.get('ada_violation_occurred') != ada_violation_occurred:
                continue

            # Filter by customer name if provided
            if customer_name and 'customer' in t:
                customer = t['customer']
                full_name = f"{customer.get('personal_info', {}).get('first_name', '')} {customer.get('personal_info', {}).get('last_name', '')}"
                if customer_name.lower() not in full_name.lower():
                    continue

            filtered_transcripts.append(t)

        # Sort results
        reverse_sort = sort_order.lower() == 'desc'
        if sort_by == 'date':
            filtered_transcripts.sort(
                key=lambda x: x.get('call_timestamp', ''),
                reverse=reverse_sort
            )
        elif sort_by == 'duration':
            filtered_transcripts.sort(
                key=lambda x: x.get('call_duration_seconds', 0),
                reverse=reverse_sort
            )
        elif sort_by == 'sentiment':
            filtered_transcripts.sort(
                key=lambda x: x.get('sentiment', {}).get('polarity', 0),
                reverse=reverse_sort
            )
        elif sort_by == 'relevance' and query:
            filtered_transcripts.sort(
                key=lambda x: x.get('_relevance', 0),
                reverse=True  # Always sort by relevance in descending order
            )

        # Apply pagination
        paginated_results = filtered_transcripts[offset:offset + limit]

        # Clean up the results
        for t in paginated_results:
            # Remove internal fields
            t.pop('_relevance', None)

            # Include/exclude fields based on parameters
            if not include_summary and 'call_summary' in t:
                t.pop('call_summary')

            if not include_transcript and 'transcript' in t:
                t.pop('transcript')

        # Prepare aggregations
        aggregations = {
            'call_types': {t: sum(1 for x in filtered_transcripts if x.get('call_type') == t)
                          for t in call_types},
            'sentiment': {
                'min': min(sentiment_scores) if sentiment_scores else None,
                'max': max(sentiment_scores) if sentiment_scores else None,
                'avg': sum(sentiment_scores)/len(sentiment_scores) if sentiment_scores else None,
                'count': len(sentiment_scores)
            },
            'total_duration': sum(t.get('call_duration_seconds', 0) for t in filtered_transcripts),
            'total_count': len(filtered_transcripts)
        }

        return {
            'results': paginated_results,
            'total': len(filtered_transcripts),
            'limit': limit,
            'offset': offset,
            'aggregations': aggregations
        }

    except Exception as e:
        logger.error(f"Error in advanced transcript search: {str(e)}", exc_info=True)
        return {
            'results': [],
            'total': 0,
            'error': f"Error searching transcripts: {str(e)}",
            'limit': limit,
            'offset': offset,
            'aggregations': {}
        }

def create_app(config: Optional[MCPConfig] = None) -> FastMCP:
    """
    Create and configure the MCP application.

    Args:
        config: Optional configuration object. If not provided, default values will be used.

    Returns:
        FastMCP: The configured FastMCP application instance.
    """
    if config is None:
        config = MCPConfig()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )

    # Initialize FastMCP
    mcp_app = FastMCP(
        name="mcp-server",
        version="0.1.0"
    )

    # Define prompts
    prompts = {
        # General prompts
        "analyze_sentiment": "Analyze the sentiment of the following text: {text}",
        "summarize_call": "Please summarize the following call transcript: {transcript}",
        "extract_action_items": "Extract action items from the following text: {text}",
        "categorize_issue": "Categorize the following customer issue: {issue_description}",
        "generate_response": "Generate a professional response to the following message: {message}",

        # Customer-related prompts
        "find_customer_by_id": "Retrieve customer details for customer ID: {customer_id}",
        "find_customer_by_email": "Find customer with email address: {email}",
        "search_customers_by_name": "Search for customers with names containing: {name_query}",
        "find_customers_by_company": "List all customers from company: {company_name}",
        "find_customers_by_location": "Find customers in {city}, {state}, {country}",
        "get_customer_call_history": "Retrieve call history for customer ID: {customer_id}",
        "find_high_value_customers": "Identify high-value customers with criteria: {criteria}",
        "get_customer_interaction_summary": "Generate a summary of all interactions for customer ID: {customer_id}",
        "find_similar_customers": "Find customers similar to customer ID: {customer_id} based on {criteria}",
        "get_customer_retention_risk": "Analyze retention risk for customer ID: {customer_id}",
        "get_customer_lifetime_value": "Calculate lifetime value for customer ID: {customer_id}",
        "find_customers_by_product": "Find all customers who purchased product: {product_id}",
        "get_customer_support_tickets": "Retrieve all support tickets for customer ID: {customer_id}",
        "find_customers_needing_followup": "Identify customers who need follow-up based on {criteria}"
    }

    # Add prompts to the app
    mcp_app.prompts = prompts
    @mcp_app.tool()
    async def list_mcp_prompts() -> Dict[str, Any]:
        """List all available MCP prompts and debug info."""
        try:
            debug_info = {
                "available_methods": [m for m in dir(mcp_app) if callable(getattr(mcp_app, m)) and not m.startswith('_')],
                "available_attributes": [a for a in dir(mcp_app) if not callable(getattr(mcp_app, a)) and not a.startswith('_')],
                "prompts_found": False,
                "prompts": {},
                "has_get_prompts": hasattr(mcp_app, 'get_prompts'),
                "has_prompts_attr": hasattr(mcp_app, 'prompts'),
                "app_type": str(type(mcp_app)),
                "app_dir": dir(mcp_app)
            }

            # Try to get prompts using get_prompts method if it exists
            if debug_info["has_get_prompts"]:
                try:
                    prompts = mcp_app.get_prompts()
                    if hasattr(prompts, '__await__'):
                        prompts = await prompts
                    if prompts:
                        debug_info["prompts"] = prompts
                        debug_info["prompts_found"] = True
                except Exception as e:
                    debug_info["get_prompts_error"] = str(e)

            # Fall back to prompts attribute if no prompts found yet
            if not debug_info["prompts_found"] and debug_info["has_prompts_attr"]:
                debug_info["prompts"] = mcp_app.prompts
                debug_info["prompts_found"] = bool(mcp_app.prompts)

            # Check for get_prompts method
            if hasattr(mcp_app, 'get_prompts'):
                debug_info["available_methods"].append("get_prompts")
                try:
                    result = mcp_app.get_prompts()
                    if hasattr(result, '__await__'):
                        result = await result
                    debug_info["prompts"] = result
                    debug_info["prompts_found"] = bool(result)
                except Exception as e:
                    debug_info["get_prompts_error"] = str(e)

            # Check for prompts attribute
            if hasattr(mcp_app, 'prompts'):
                debug_info["available_attributes"].append("prompts")
                try:
                    prompts = mcp_app.prompts
                    if hasattr(prompts, '__aiter__'):
                        prompts = [p async for p in prompts]
                    debug_info["prompts"] = prompts or []
                    debug_info["prompts_found"] = bool(prompts)
                except Exception as e:
                    debug_info["prompts_attribute_error"] = str(e)

            # Check for add_prompt method (common in some MCP implementations)
            if hasattr(mcp_app, 'add_prompt'):
                debug_info["available_methods"].append("add_prompt")

            # Include all callable methods and their docstrings
            debug_info["callable_methods"] = {
                name: getattr(mcp_app, name).__doc__ or "No docstring"
                for name in dir(mcp_app)
                if callable(getattr(mcp_app, name)) and not name.startswith('_')
            }

            # If no prompts found, include all non-callable attributes
            if not debug_info["prompts_found"]:
                debug_info["all_attributes"] = {
                    name: str(type(getattr(mcp_app, name)))
                    for name in dir(mcp_app)
                    if not name.startswith('_') and not callable(getattr(mcp_app, name))
                }

            return debug_info

        except Exception as e:
            logger.error(f"Error in list_mcp_prompts: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": str(e),
                    "type": type(e).__name__,
                    "available_methods": [m for m in dir(mcp_app) if callable(getattr(mcp_app, m)) and not m.startswith('_')]
                }
            )

    # Register tools
    @mcp_app.tool()
    async def get_customer_tool(customer_id: str) -> Dict[str, Any]:
        """Retrieve a customer by their ID."""
        return await get_customer(customer_id)

    @mcp_app.tool()
    async def search_customers_tool(
        query: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        company: Optional[str] = None,
        has_transcripts: Optional[bool] = None,
        min_transcripts: Optional[int] = None,
        last_contact_days: Optional[int] = None,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search for customers with advanced filtering."""
        return await search_customers(
            query=query,
            name=name,
            email=email,
            phone=phone,
            state=state,
            city=city,
            company=company,
            has_transcripts=has_transcripts,
            min_transcripts=min_transcripts,
            last_contact_days=last_contact_days,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )

    # Add more tool registrations as needed...

    return mcp_app

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the MCP server."""
    import uvicorn

    uvicorn.run(
        "app.mcp_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        workers=1
    )

if __name__ == "__main__":
    config = MCPConfig()
    run_server(host=config.host, port=config.port, reload=config.reload)
