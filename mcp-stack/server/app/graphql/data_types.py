# At the top of data_types.py
from __future__ import annotations
from typing import List, Optional, Dict, Any, TYPE_CHECKING
import strawberry
from datetime import datetime
from app.data.data_loader import data_loader

@strawberry.type
class SentimentType:
    """Sentiment analysis results."""
    polarity: float
    subjectivity: float
    analyzer: Optional[str] = None

@strawberry.type
class TranscriptEntry:
    speaker: str
    text: str
    timestamp: str

@strawberry.type
class CustomerType:
    customer_id: str = strawberry.field(name="customerId")
    first_name: str = strawberry.field(name="firstName")
    last_name: str = strawberry.field(name="lastName")
    email: str = strawberry.field(name="email")
    phone: str = strawberry.field(name="phone")
    city: str = strawberry.field(name="city")
    state: str = strawberry.field(name="state")
    transcripts: List[CallTranscriptType] = strawberry.field(default_factory=list)

@strawberry.type
class CallTranscriptType:
    call_id: str = strawberry.field(name="callId")
    customer_id: str = strawberry.field(name="customerId")
    call_type: str = strawberry.field(name="callType")
    call_timestamp: str = strawberry.field(name="callTimestamp")
    call_duration_seconds: int = strawberry.field(name="callDurationSeconds")
    agent_id: str = strawberry.field(name="agentId")
    call_summary: str = strawberry.field(name="callSummary")
    is_ada_related: bool = strawberry.field(name="isAdaRelated")
    ada_violation_occurred: bool = strawberry.field(name="adaViolationOccurred")
    transcript: List[TranscriptEntry]
    sentiment: SentimentType = strawberry.field(
        default_factory=lambda: SentimentType(polarity=0.0, subjectivity=0.0, analyzer=None),
        description="Sentiment analysis results"
    )
    contexts: List[str] = strawberry.field(
        default_factory=list,
        description="List of key contexts extracted from the call"
    )

# Now define the methods
def add_methods():
    # Add from_model to CallTranscriptType
    @classmethod
    def from_model_transcript(cls, transcript):
        get_attr = lambda x, a: x[a] if isinstance(x, dict) else getattr(x, a, None)

        transcript_data = get_attr(transcript, 'transcript') or []
        transcript_entries = []
        for entry in (transcript_data if isinstance(transcript_data, list) else []):
            if not isinstance(entry, dict):
                continue

            transcript_entries.append(TranscriptEntry(
                speaker=entry.get('speaker', ''),
                text=entry.get('text', ''),
                timestamp=entry.get('timestamp', '')
            ))

        # Get sentiment data
        sentiment_data = get_attr(transcript, 'sentiment') or {}
        sentiment = SentimentType(
            polarity=float(sentiment_data.get('polarity', 0.0)),
            subjectivity=float(sentiment_data.get('subjectivity', 0.0)),
            analyzer=sentiment_data.get('analyzer')
        )

        # Get contexts
        contexts = get_attr(transcript, 'contexts') or []
        if not isinstance(contexts, list):
            contexts = []

        return cls(
            call_id=get_attr(transcript, 'call_id') or '',
            customer_id=get_attr(transcript, 'customer_id') or '',
            call_type=get_attr(transcript, 'call_type') or '',
            call_timestamp=get_attr(transcript, 'call_timestamp') or '',
            call_duration_seconds=get_attr(transcript, 'call_duration_seconds') or 0,
            agent_id=get_attr(transcript, 'agent_id') or '',
            call_summary=get_attr(transcript, 'call_summary') or '',
            is_ada_related=bool(get_attr(transcript, 'is_ada_related') or False),
            ada_violation_occurred=bool(get_attr(transcript, 'ada_violation_occurred') or False),
            transcript=transcript_entries,
            sentiment=sentiment,
            contexts=contexts
        )

    # Add from_model to CustomerType
    @classmethod
    def from_model_customer(cls, customer, include_transcripts: bool = False):
        email = customer.personal_info.get('email', '')
        phone = customer.personal_info.get('phone', '')

        if not email and hasattr(customer, 'home_address') and customer.home_address:
            email = customer.home_address.get('email', '')
        if not phone and hasattr(customer, 'home_address') and customer.home_address:
            phone = customer.home_address.get('phone', '')

        city = customer.home_address.get('city', '') if hasattr(customer, 'home_address') and customer.home_address else ''
        state = customer.home_address.get('state', '') if hasattr(customer, 'home_address') and customer.home_address else ''

        transcripts = []
        if include_transcripts:
            transcript_models = data_loader.search_transcripts(customer_id=customer.customer_id)
            transcripts = [CallTranscriptType.from_model(t) for t in transcript_models]

        return cls(
            customer_id=customer.customer_id,
            first_name=customer.personal_info.get('first_name', ''),
            last_name=customer.personal_info.get('last_name', ''),
            email=email,
            phone=phone,
            city=city,
            state=state,
            transcripts=transcripts
        )

    # Attach methods to classes
    CallTranscriptType.from_model = from_model_transcript
    CustomerType.from_model = from_model_customer

# Call the function to add methods
add_methods()

# Input types
@strawberry.input
class CustomerFilterInput:
    name: Optional[str] = None
    state: Optional[str] = None
    transcript_text: Optional[str] = None
    include_transcripts: bool = False
    limit: int = 10
    offset: int = 0

@strawberry.input
class TranscriptFilterInput:
    customer_id: Optional[str] = None
    agent_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 10
    offset: int = 0

# Query class
@strawberry.type
class DataQuery:
    @strawberry.field
    async def get_customer(self, customer_id: str) -> Optional[CustomerType]:
        customer = data_loader.get_customer(customer_id)
        if customer:
            return CustomerType.from_model(customer)
        return None

    @strawberry.field
    async def search_customers(
        self,
        filter: CustomerFilterInput
    ) -> List[CustomerType]:
        customers = data_loader.search_customers(
            name=filter.name,
            state=filter.state,
            transcript_text=filter.transcript_text,
            limit=filter.limit,
            offset=filter.offset
        )
        return [CustomerType.from_model(c, include_transcripts=filter.include_transcripts) for c in customers]

    @strawberry.field
    async def get_transcript(self, call_id: str) -> Optional[CallTranscriptType]:
        transcript = data_loader.get_transcript(call_id)
        if transcript:
            return CallTranscriptType.from_model(transcript)
        return None

    @strawberry.field
    async def search_transcripts(
        self,
        filter: TranscriptFilterInput
    ) -> List[CallTranscriptType]:
        transcripts = data_loader.search_transcripts(
            customer_id=filter.customer_id,
            agent_id=filter.agent_id,
            start_date=filter.start_date,
            end_date=filter.end_date,
            limit=filter.limit,
            offset=filter.offset
        )
        return [CallTranscriptType.from_model(t) for t in transcripts]

    @strawberry.field
    async def get_customers_with_transcripts(self) -> List[CustomerType]:
        """Get all customers that have at least one transcript."""
        customers = data_loader.get_customers_with_transcripts()
        return [CustomerType.from_model(c, include_transcripts=True) for c in customers]
