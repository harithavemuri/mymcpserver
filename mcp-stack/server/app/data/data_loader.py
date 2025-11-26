"""Data loading and querying functionality for MCP sample data."""
import json
import os
import sys
import nltk
import logging
from datetime import datetime
from difflib import get_close_matches, SequenceMatcher
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Literal
from pydantic import BaseModel, Field, field_validator
from logging.handlers import RotatingFileHandler

# Import ratio from difflib for string similarity
def ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Configure logging
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Create formatters
class CustomFormatter(logging.Formatter):
    """Custom formatter that includes module and function name where the logging call was made"""
    def format(self, record):
        record.funcName = record.funcName or 'unknown'
        record.module = record.module or 'unknown'
        if record.levelno >= logging.ERROR:
            return f"{record.levelname:8} [{record.module}.{record.funcName}:{record.lineno}] {record.msg}"
        elif record.levelno >= logging.INFO:
            return f"{record.levelname:8} {record.msg}"
        else:  # DEBUG
            return f"{record.levelname:8} [{record.module}.{record.funcName}] {record.msg}"

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Console handler - only show INFO and above
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = CustomFormatter()
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler - show DEBUG and above with more details
file_handler = RotatingFileHandler(
    'data_loader.log',
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(module)s.%(funcName)s:%(lineno)d]',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Get logger for this module
logger = logging.getLogger(__name__)

# Set up NLTK data
try:
    # First try to import from the package's __init__.py
    from . import nltk_data_dir
    logger.info(f"Using NLTK data from: {nltk_data_dir}")

    # Ensure punkt is available
    try:
        nltk.data.find('tokenizers/punkt')
        logger.debug("Punkt tokenizer found")
    except LookupError:
        logger.warning("Punkt tokenizer not found. Attempting to download...")
        nltk.download('punkt')
        logger.info("Successfully downloaded punkt tokenizer")

    # Now import NLTK-dependent modules
    from textblob import TextBlob
    from rake_nltk import Rake

except ImportError as e:
    logger.error(f"Failed to initialize NLTK environment: {str(e)}")
    raise RuntimeError("Failed to set up NLTK environment. Please ensure all dependencies are installed.")

# Initialize RAKE (Rapid Automatic Keyword Extraction)
rake_nltk = Rake()

def analyze_sentiment(text: str) -> Dict[str, float]:
    """Analyze sentiment of the given text and return polarity and subjectivity.

    This function uses TextBlob for sentiment analysis, with VADER as a fallback.

    Args:
        text: The text to analyze

    Returns:
        Dictionary with 'polarity' (from -1 to 1) and 'subjectivity' (0 to 1) scores
    """
    logger.debug("Starting sentiment analysis", extra={"text_length": len(text)})

    if not text.strip():
        logger.warning("Empty text provided for sentiment analysis")
        return {"polarity": 0.0, "subjectivity": 0.0}

    try:
        # Ensure NLTK data is available
        try:
            nltk.data.find('tokenizers/punkt')
            logger.debug("NLTK punkt tokenizer found")
        except LookupError as e:
            logger.warning("NLTK punkt tokenizer not found, attempting to download...")
            from nltk_setup import setup_nltk
            setup_nltk()
            logger.info("NLTK data download completed")

        # First try TextBlob
        logger.debug("Running TextBlob sentiment analysis")
        analysis = TextBlob(text)

        # Get sentiment scores
        polarity = float(analysis.sentiment.polarity)
        subjectivity = float(analysis.sentiment.subjectivity)

        logger.debug("TextBlob analysis results", extra={
            "polarity": polarity,
            "subjectivity": subjectivity,
            "analyzed_text_sample": text[:100] + (text[100:] and '...')
        })

        # If TextBlob returns neutral, try VADER as a fallback
        if abs(polarity) < 0.1:  # If sentiment is very close to neutral
            logger.debug("TextBlob returned neutral sentiment, trying VADER as fallback")
            try:
                from nltk.sentiment import SentimentIntensityAnalyzer
                sia = SentimentIntensityAnalyzer()
                vader_scores = sia.polarity_scores(text)

                logger.debug("VADER analysis results", extra={
                    "vader_scores": vader_scores,
                    "analyzed_text_sample": text[:100] + (text[100:] and '...')
                })

                # Use VADER's compound score if it's more decisive
                if abs(vader_scores['compound']) > 0.1:  # If VADER has a stronger opinion
                    logger.debug("Using VADER sentiment score")
                    polarity = float(vader_scores['compound'])  # Scale -1 to 1
                    subjectivity = 0.5 + abs(polarity * 0.5)  # More extreme = more subjective
            except Exception as e:
                logger.warning("VADER sentiment analysis failed, using TextBlob results",
                             exc_info=True)

        sentiment = {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "analyzer": "TextBlob" if abs(polarity) >= 0.1 else "VADER"
        }

        logger.info("Sentiment analysis completed", extra={
            "polarity": sentiment["polarity"],
            "subjectivity": sentiment["subjectivity"],
            "analyzer": sentiment.get("analyzer", "TextBlob")
        })

        return sentiment

    except Exception as e:
        logger.error("Error in sentiment analysis", exc_info=True, extra={
            "error": str(e),
            "text_sample": text[:100] + (text[100:] and '...')
        })
        # Return neutral sentiment on error
        return {"polarity": 0.0, "subjectivity": 0.5, "analyzer": "error"}

def _get_predefined_contexts() -> List[str]:
    """Return a list of predefined context categories."""
    return [
        # Customer service related
        "billing issue", "payment problem", "refund request", "account access", "login issue",
        "password reset", "shipping delay", "damaged product", "wrong item", "missing item",
        "return request", "exchange request", "warranty claim", "product quality", "defective product",
        "order status", "tracking information", "delivery issue", "late delivery", "shipping address",
        "price match", "discount request", "coupon code", "promotion inquiry", "membership issue",
        "subscription cancel", "renewal issue", "auto-renewal", "trial period", "upgrade request",
        "downgrade request", "feature request", "bug report", "technical issue", "app problem",
        "website error", "checkout issue", "cart problem", "payment method", "credit card decline",
        "fraud alert", "identity verification", "account suspension", "account closure", "reactivate account",
        "privacy concern", "data deletion", "terms of service", "return policy", "shipping policy",
        "product availability", "backorder status", "pre-order inquiry", "gift card", "store credit",
        "loyalty points", "reward program", "referral bonus", "price inquiry", "product comparison",
        "product specification", "size chart", "color option", "product recommendation", "assembly required",
        "installation help", "user manual", "product tutorial", "troubleshooting", "firmware update",
        "compatibility issue", "accessory missing", "battery life", "warranty registration", "extended warranty",
        "service plan", "repair request", "replacement part", "maintenance service", "safety recall",
        "product recall", "safety concern", "allergic reaction", "ingredient list", "nutrition information",
        "dietary restriction", "allergy information", "expiration date", "batch number", "authenticity check",
        "counterfeit product", "unauthorized seller", "marketplace issue", "third-party seller", "fulfillment by merchant",
        "dropshipping inquiry", "wholesale order", "bulk purchase", "business account", "tax exemption",
        "reseller inquiry", "partnership request", "affiliate program", "influencer program", "press inquiry",
        "media request", "sponsorship", "charity donation", "corporate gifting", "event planning",
        "venue inquiry", "catering service", "rental service", "equipment rental", "staffing request",
        "career opportunity", "job application", "internship program", "volunteer opportunity", "training program",
        "workshop registration", "webinar signup", "conference ticket", "speaking engagement", "panel discussion",
        "interview request", "media appearance", "product review", "testimonial submission", "case study",
        "white paper request", "research survey", "customer feedback", "satisfaction survey", "complaint submission",
        "escalation request", "manager callback", "executive contact", "legal inquiry", "regulatory compliance",
        "data breach", "security concern", "phishing report", "scam alert", "fraud report",
        "unauthorized charge", "billing dispute", "chargeback inquiry", "payment plan", "financial hardship",
        "deferment request", "forbearance request", "loan application", "credit increase", "credit limit",
        "interest rate", "payment extension", "late fee waiver", "overdraft fee", "service charge",
        "tax document", "invoice request", "receipt copy", "order confirmation", "shipping confirmation",
        "tracking number", "delivery confirmation", "signature required", "delivery instructions", "special handling",
        "gift wrapping", "gift message", "gift receipt", "wishlist inquiry", "registry search",
        "bridal registry", "baby registry", "wedding registry", "anniversary gift", "birthday gift",
        "graduation gift", "holiday gift", "corporate gift", "thank you gift", "sympathy gift",
        "get well gift", "congratulations gift", "new baby gift", "housewarming gift", "retirement gift"
    ]

def _get_similarity(phrase1: str, phrase2: str) -> float:
    """Calculate similarity between two phrases using Levenshtein distance."""
    return ratio(phrase1.lower(), phrase2.lower())

def _find_best_match(phrase: str, threshold: float = 0.6) -> Optional[str]:
    """Find the best matching predefined context, if similarity is above threshold.

    Args:
        phrase: The phrase to match against predefined contexts
        threshold: Minimum similarity score (0-1) to consider a match (default: 0.6)

    Returns:
        The best matching predefined context, or None if no good match is found
    """
    if not phrase or not phrase.strip():
        return None

    predefined = _get_predefined_contexts()
    best_match = None
    highest_similarity = 0.0

    # Clean up the input phrase
    phrase = phrase.lower().strip()

    # First try exact match (case-insensitive)
    for context in predefined:
        if phrase == context.lower():
            logger.debug(f"Exact match found for '{phrase}': '{context}'")
            return context

    # If no exact match, try fuzzy matching
    for context in predefined:
        if not context:  # Skip empty contexts
            continue

        # Calculate similarity
        similarity = _get_similarity(phrase, context)

        # Debug logging for high similarity matches
        if similarity > 0.5:  # Only log if there's at least some similarity
            logger.debug(f"Comparing '{phrase}' with '{context}': {similarity:.2f}")

        if similarity > highest_similarity:
            highest_similarity = similarity
            best_match = context

    # Only return a match if it meets the threshold
    if highest_similarity >= threshold:
        logger.debug(f"Best match for '{phrase}': '{best_match}' (similarity: {highest_similarity:.2f})")
        return best_match

    logger.debug(f"No good match found for '{phrase}'. Best was '{best_match}' with similarity {highest_similarity:.2f}")
    return None

def _get_generic_words():
    """Return a set of generic words that shouldn't be used as standalone contexts."""
    return {
        'regarding', 'about', 'call', 'contact', 'regard', 'discuss', 'discussion',
        'issue', 'problem', 'matter', 'situation', 'thing', 'something', 'anything',
        'everything', 'nothing', 'someone', 'anyone', 'everyone', 'no one', 'need',
        'want', 'would like', 'please', 'thank', 'thanks', 'hello', 'hi', 'hey',
        'help', 'assist', 'assistance', 'support', 'question', 'query', 'concern',
        'information', 'detail', 'details', 'regards', 'best', 'sincerely', 'kind',
        'regarding the', 'about the', 'call about', 'contact about', 'just', 'like',
        'really', 'very', 'much', 'many', 'some', 'any', 'all', 'every', 'each',
        'this', 'that', 'these', 'those', 'here', 'there', 'where', 'when', 'how',
        'what', 'which', 'who', 'whom', 'whose', 'why', 'whether', 'can', 'could',
        'would', 'should', 'may', 'might', 'must', 'shall', 'will', 'with', 'without',
        'for', 'from', 'to', 'in', 'on', 'at', 'by', 'about', 'as', 'if', 'then',
        'else', 'when', 'where', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should',
        'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn', 'didn',
        'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn',
        'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn'
    }

def _is_too_generic(phrase: str) -> bool:
    """Check if a phrase is too generic to be useful as a context."""
    generic_words = _get_generic_words()

    # Single words that are too generic on their own
    if len(phrase.split()) == 1 and phrase.lower() in generic_words:
        return True

    # Very short phrases that don't convey much meaning
    if len(phrase) < 4:  # Very short phrases like 'in', 'at', 'on', etc.
        return True

    # Get the set of generic words
    generic_words = _get_generic_words()

    # Check if the phrase is just a sequence of generic words
    words = phrase.lower().split()
    if all(word in generic_words for word in words):
        return True

    # Common phrases that are too generic
    generic_phrases = {
        'call regarding', 'regarding the', 'about the', 'call about', 'contact about',
        'in regards to', 'with regard to', 'with respect to', 'as per', 'as per the',
        'in reference to', 'with reference to', 'in relation to', 'in connection with',
        'in terms of', 'in the matter of', 'on the subject of', 'on the topic of',
        'with reference', 'with regards', 'in response to', 'in reply to', 're:', 'fw:'
    }

    # Check if the phrase starts with any generic phrase
    if any(phrase.lower().startswith(gp) for gp in generic_phrases):
        return True

    return False

def extract_contexts(text: str, top_n: int = 5, similarity_threshold: float = 0.6) -> List[str]:
    """Extract key contexts from text using RAKE algorithm and match with predefined contexts.

    Args:
        text: The text to analyze
        top_n: Maximum number of contexts to return (default: 5)
        similarity_threshold: Minimum similarity score (0-1) to match a predefined context (default: 0.6)

    Returns:
        List of key contexts (phrases) matched to predefined categories when possible
    """
    if not text or not text.strip():
        logger.debug("Empty text provided to extract_contexts")
        return []

    logger.debug(f"Extracting contexts from text: '{text[:100]}...'")

    # Extract candidate phrases using RAKE or fallback methods
    candidates = []
    extraction_method = ""

    # Try RAKE first
    try:
        candidates = _extract_with_rake(text, top_n * 3)  # Get more candidates for better matching
        extraction_method = "RAKE"
        logger.debug(f"Extracted {len(candidates)} candidates using RAKE")
    except Exception as e:
        logger.warning(f"RAKE extraction failed: {str(e)}")
        try:
            # Fall back to NLTK
            candidates = _extract_with_nltk(text, top_n * 3)
            extraction_method = "NLTK"
            logger.debug(f"Extracted {len(candidates)} candidates using NLTK")
        except Exception as e:
            logger.warning(f"NLTK extraction failed: {str(e)}")
            # Final fallback to simple extraction
            candidates = _extract_simple(text, top_n * 3)
            extraction_method = "simple"
            logger.debug(f"Extracted {len(candidates)} candidates using simple method")

    logger.debug(f"Extraction method: {extraction_method}, candidates: {candidates}")

    # Match candidates with predefined contexts
    matched_contexts = set()

    for phrase in candidates:
        if not phrase or not phrase.strip():
            continue

        # Clean up the phrase
        phrase = phrase.strip().lower()

        # Skip generic words and phrases
        if _is_too_generic(phrase):
            logger.debug(f"Skipping generic phrase: '{phrase}'")
            continue

        # Try to find a matching predefined context
        matched = _find_best_match(phrase, similarity_threshold)
        if matched:
            logger.debug(f"Matched '{phrase}' to predefined context: '{matched}'")
            matched_contexts.add(matched)
        else:
            # If no close match, use the original phrase if it's not too generic
            words = phrase.split()
            if len(words) > 1:  # Prefer multi-word phrases
                # Only add if the phrase is meaningful (not just a sequence of generic words)
                meaningful_words = [w for w in words if w not in _get_generic_words()]
                if meaningful_words:  # Only add if there are some meaningful words
                    logger.debug(f"Adding meaningful phrase: '{phrase}'")
                    matched_contexts.add(phrase)

        # Stop if we have enough unique contexts
        if len(matched_contexts) >= top_n * 2:  # Get more to allow for filtering
            break

    # Convert to list and take top_n items, removing any remaining generic phrases
    result = []
    for ctx in list(matched_contexts):
        if not _is_too_generic(ctx):
            result.append(ctx)
            if len(result) >= top_n * 2:  # Still collect more for filtering
                break

    # If we don't have enough contexts, try to extract more with different methods
    if len(result) < top_n and extraction_method != "simple":
        remaining = top_n - len(result)
        logger.debug(f"Only found {len(result)} contexts, trying to get {remaining} more")
        try:
            # Try a different extraction method
            additional = []
            if extraction_method == "RAKE":
                additional = _extract_with_nltk(text, remaining * 2)
            else:
                additional = _extract_with_rake(text, remaining * 2)

            for phrase in additional:
                if not phrase or not phrase.strip() or _is_too_generic(phrase):
                    continue
                phrase = phrase.strip().lower()
                matched = _find_best_match(phrase, similarity_threshold)
                if matched and matched not in result:
                    result.append(matched)
                    if len(result) >= top_n:
                        break
        except Exception as e:
            logger.warning(f"Error in fallback extraction: {str(e)}")

    # Filter out any generic contexts that might have slipped through
    result = [ctx for ctx in result if not _is_too_generic(ctx)]

    # If we still don't have enough, add some meaningful generic contexts
    if len(result) < top_n:
        logger.debug("Adding meaningful generic contexts")
        meaningful_generic_contexts = [
            "customer inquiry", "billing question", "account assistance",
            "order status", "shipping inquiry", "product information",
            "technical support", "service request", "payment issue",
            "refund inquiry", "warranty information"
        ]

        for ctx in meaningful_generic_contexts:
            if ctx not in result and len(result) < top_n:
                result.append(ctx)

    # Ensure we don't return more than requested and remove any duplicates
    result = list(dict.fromkeys(result))[:top_n]

    logger.info("Extracted contexts", extra={
        "contexts_count": len(result),
        "contexts_sample": result[:3],
        "extraction_method": extraction_method,
        "original_text_sample": text[:100] + ('...' if len(text) > 100 else '')
    })

    return result

def _extract_with_rake(text: str, top_n: int) -> List[str]:
    """Extract contexts using RAKE algorithm."""
    try:
        logger.debug("Attempting to extract contexts with RAKE...")

        # Ensure NLTK data is available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.info("Downloading required NLTK data for RAKE...")
            from nltk_setup import setup_nltk
            setup_nltk()

        # Initialize RAKE with custom stopwords
        from rake_nltk import Rake
        rake = Rake()

        # Extract keywords with scores
        rake.extract_keywords_from_text(text)
        keyword_scores = rake.get_ranked_phrases_with_scores()

        # Sort by score (descending) and get top N
        keyword_scores.sort(key=lambda x: x[0], reverse=True)
        top_keywords = [phrase for score, phrase in keyword_scores[:top_n] if score > 0]

        if not top_keywords:
            logger.debug("RAKE returned no valid keywords")
            return []

        return top_keywords

    except Exception as e:
        logger.error("RAKE extraction failed", exc_info=True)
        return []

def _extract_with_nltk(text: str, top_n: int) -> List[str]:
    """Extract contexts using NLTK's word tokenizer and stopwords."""
    try:
        logger.debug("Falling back to NLTK word tokenizer...")

        # Ensure NLTK data is available
        try:
            from nltk.tokenize import word_tokenize
            from nltk.corpus import stopwords

            # Try to load stopwords
            try:
                stop_words = set(stopwords.words('english'))
            except LookupError:
                logger.info("Downloading NLTK stopwords...")
                from nltk_setup import setup_nltk
                setup_nltk()
                stop_words = set(stopwords.words('english'))

            # Tokenize and filter words
            words = [
                word.lower() for word in word_tokenize(text)
                if word.isalnum() and word.lower() not in stop_words and len(word) > 3
            ]

            # Get unique words and return top N
            return list(set(words))[:top_n]

        except Exception as e:
            logger.error("NLTK tokenization failed", exc_info=True)
            return []

    except Exception as e:
        logger.error("Error in NLTK fallback", exc_info=True)
        return []

def _extract_simple(text: str, top_n: int) -> List[str]:
    """Simple word-based extraction as final fallback."""
    try:
        logger.debug("Using simple word splitting as final fallback...")
        words = [
            word.lower() for word in text.split()
            if word.isalnum() and len(word) > 3
        ]
        return list(set(words))[:top_n]
    except Exception as e:
        logger.error("Simple extraction failed", exc_info=True)
        return []

# Data models
class WorkAddress(BaseModel):
    """Work address data model."""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"

class Employment(BaseModel):
    """Employment information data model."""
    company: str
    position: str
    work_email: Optional[str] = None
    work_phone: Optional[str] = None
    work_address: Optional[WorkAddress] = None

class Customer(BaseModel):
    """Customer data model."""
    customer_id: str
    personal_info: Dict[str, Any]
    home_address: Dict[str, str]
    employment: Employment

class CallTranscript(BaseModel):
    """Call transcript data model with sentiment and context analysis."""
    call_id: str
    customer_id: str
    call_type: str
    call_timestamp: str
    call_duration_seconds: int
    agent_id: str
    call_summary: str
    is_ada_related: bool
    ada_violation_occurred: bool
    transcript: List[Dict[str, Any]]
    sentiment: Dict[str, float] = Field(
        default_factory=dict,
        description="Sentiment analysis results with 'polarity' (-1 to 1) and 'subjectivity' (0 to 1)"
    )
    contexts: List[str] = Field(
        default_factory=list,
        description="List of key contexts extracted from the call summary"
    )

    def __init__(self, **data):
        """Initialize the transcript and analyze the call summary."""
        super().__init__(**data)

        # Analyze the call summary if it exists
        if hasattr(self, 'call_summary') and self.call_summary and self.call_summary.strip():
            try:
                # Analyze sentiment
                self.sentiment = analyze_sentiment(self.call_summary)
                logger.debug(f"Analyzed sentiment: {self.sentiment}")

                # Extract contexts (key phrases)
                self.contexts = extract_contexts(self.call_summary)
                logger.debug(f"Extracted contexts: {self.contexts}")

            except Exception as e:
                logger.error(f"Error analyzing call summary: {str(e)}", exc_info=True)
                # Set default values on error
                self.sentiment = {"polarity": 0.0, "subjectivity": 0.0}
                self.contexts = []
        else:
            # Empty summary - set default values
            self.sentiment = {"polarity": 0.0, "subjectivity": 0.0}
            self.contexts = []

    @field_validator('call_summary', mode='before')
    @classmethod
    def analyze_call_summary(cls, v: str) -> str:
        """Analyze the call summary and set sentiment and contexts."""
        return v

class DataLoader:
    """Load and query MCP sample data."""

    def __init__(self, data_dir: str = "mcp-sampledata/data"):
        """Initialize the data loader with the path to the data directory."""
        self.data_dir = Path(data_dir)
        self._customers = None
        self._transcripts = None

    def load_customers(self) -> Dict[str, Customer]:
        """Load all customer data."""
        if self._customers is None:
            customers_file = self.data_dir / "customers.json"
            with open(customers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._customers = {}
                for cust_data in data.get('customers', []):
                    # Process employment data to handle work_address
                    if 'employment' in cust_data and 'work_address' in cust_data['employment']:
                        work_addr = cust_data['employment']['work_address']
                        if work_addr and not isinstance(work_addr, dict):
                            # If work_address is not a dict, set it to None
                            cust_data['employment']['work_address'] = None

                    # Create Customer instance
                    try:
                        customer = Customer(**cust_data)
                        self._customers[customer.customer_id] = customer
                    except Exception as e:
                        logger.error(f"Error loading customer {cust_data.get('customer_id')}", exc_info=True)
                        continue

        return self._customers

    def load_transcripts(self) -> Dict[str, CallTranscript]:
        """Load all call transcripts from JSON files with sentiment and context analysis."""
        if self._transcripts is None:
            self._transcripts = {}
            transcripts_dir = self.data_dir / "transcripts"

            for file_path in transcripts_dir.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Handle both list and single transcript formats
                    if isinstance(data, list):
                        for item in data:
                            # Ensure we have the required fields with defaults
                            if 'sentiment' not in item:
                                item['sentiment'] = {}
                            if 'contexts' not in item:
                                item['contexts'] = []

                            # Create the transcript (this will trigger the analysis)
                            try:
                                transcript = CallTranscript(**item)
                                # If the call_summary is empty, we need to manually analyze it
                                if not transcript.call_summary.strip():
                                    transcript.sentiment = {}
                                    transcript.contexts = []
                                self._transcripts[transcript.call_id] = transcript
                            except Exception as e:
                                logger.error(f"Error loading transcript from {file_path}", exc_info=True)
                                continue
                    else:
                        # Ensure we have the required fields with defaults
                        if 'sentiment' not in data:
                            data['sentiment'] = {}
                        if 'contexts' not in data:
                            data['contexts'] = []

                        # Create the transcript (this will trigger the analysis)
                        try:
                            transcript = CallTranscript(**data)
                            # If the call_summary is empty, we need to manually analyze it
                            if not transcript.call_summary.strip():
                                transcript.sentiment = {}
                                transcript.contexts = []
                            self._transcripts[transcript.call_id] = transcript
                        except Exception as e:
                            logger.error(f"Error loading transcript from {file_path}", exc_info=True)
                            continue

        return self._transcripts

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get a single customer by ID."""
        customers = self.load_customers()
        return customers.get(customer_id)

    def get_transcript(self, call_id: str) -> Optional[CallTranscript]:
        """Get a single call transcript by ID."""
        transcripts = self.load_transcripts()
        return transcripts.get(call_id)

    def search_customers(
        self,
        name: Optional[str] = None,
        state: Optional[str] = None,
        transcript_text: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Customer]:
        """Search customers with optional filters.

        Args:
            name: Optional name to search for (partial match)
            state: Optional state to filter by
            transcript_text: Optional text to search within customer transcripts
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of matching Customer objects
        """
        customers = list(self.load_customers().values())

        # If searching by transcript text, we need to find customer IDs with matching transcripts first
        customer_ids_with_matching_transcripts = set()
        if transcript_text:
            transcripts = self.load_transcripts().values()
            search_text = transcript_text.lower()

            for transcript in transcripts:
                # Search in call summary
                if search_text in (transcript.call_summary or '').lower():
                    customer_ids_with_matching_transcripts.add(transcript.customer_id)
                    continue

                # Search in transcript entries
                for entry in (transcript.transcript or []):
                    if search_text in (entry.get('text', '') or '').lower():
                        customer_ids_with_matching_transcripts.add(transcript.customer_id)
                        break

        filtered = []
        for cust in customers:
            # Filter by name if provided
            if name and name.lower() not in (
                f"{cust.personal_info.get('first_name', '').lower()} "
                f"{cust.personal_info.get('last_name', '').lower()}"
            ):
                continue

            # Filter by state if provided
            if state and state.upper() != cust.home_address.get('state', '').upper():
                continue

            # Filter by transcript text if provided
            if transcript_text and cust.customer_id not in customer_ids_with_matching_transcripts:
                continue

            filtered.append(cust)

        # Apply pagination
        return filtered[offset:offset + limit]

    def search_transcripts(
        self,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[CallTranscript]:
        """Search call transcripts with optional filters."""
        transcripts = list(self.load_transcripts().values())

        filtered = []
        for trans in transcripts:
            if customer_id and trans.customer_id != customer_id:
                continue

            if agent_id and trans.agent_id != agent_id:
                continue

            if start_date:
                call_date = datetime.fromisoformat(trans.call_timestamp.split('T')[0])
                start = datetime.fromisoformat(start_date)
                if call_date < start:
                    continue

            if end_date:
                call_date = datetime.fromisoformat(trans.call_timestamp.split('T')[0])
                end = datetime.fromisoformat(end_date)
                if call_date > end:
                    continue

            filtered.append(trans)

        return filtered[offset:offset + limit]

    def get_customers_with_transcripts(self) -> List[Customer]:
        """Get all customers that have at least one transcript."""
        # Get all customers and transcripts
        customers = list(self.load_customers().values())
        transcripts = self.load_transcripts()

        # Create a dictionary of customer IDs to their transcripts
        customer_transcripts = {}
        for transcript in transcripts.values():
            if not hasattr(transcript, 'customer_id') or not transcript.customer_id:
                continue
            if transcript.customer_id not in customer_transcripts:
                customer_transcripts[transcript.customer_id] = []
            customer_transcripts[transcript.customer_id].append(transcript)

        # Filter customers to only those with at least one transcript
        result = []
        for customer in customers:
            if customer.customer_id in customer_transcripts and customer_transcripts[customer.customer_id]:
                # Double-check that the customer has at least one transcript
                customer_transcript_count = len(customer_transcripts[customer.customer_id])
                if customer_transcript_count > 0:
                    result.append(customer)

        return result

# Singleton instance
data_loader = DataLoader()
