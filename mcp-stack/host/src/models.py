"""Data models for the MCP Host."""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

class ModelStatus(str, Enum):
    """Status of a registered model."""
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"

class ModelConfig(BaseModel):
    """Configuration for a model."""
    model_id: str = Field(..., description="Unique identifier for the model")
    model_type: str = Field(..., description="Type/architecture of the model")
    model_path: str = Field(..., description="Path to the model file or directory")
    framework: str = Field(..., description="Framework used for the model (e.g., tensorflow, pytorch)")
    input_shape: List[int] = Field(..., description="Expected input shape of the model")
    output_shape: List[int] = Field(..., description="Expected output shape of the model")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional model metadata")

class ModelInfo(BaseModel):
    """Information about a registered model."""
    model_id: str = Field(..., description="Unique identifier for the model")
    status: ModelStatus = Field(default=ModelStatus.LOADING, description="Current status of the model")
    config: ModelConfig = Field(..., description="Model configuration")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Model performance metrics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional model information")

class PredictionRequest(BaseModel):
    """Request for making a prediction."""
    model_id: str = Field(..., description="ID of the model to use for prediction")
    input_data: Dict[str, Any] = Field(..., description="Input data for prediction")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional prediction parameters")

class PredictionResponse(BaseModel):
    """Response containing prediction results."""
    model_id: str = Field(..., description="ID of the model used for prediction")
    request_id: str = Field(..., description="Unique identifier for the prediction request")
    output_data: Dict[str, Any] = Field(..., description="Prediction output data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the prediction")

# Customer and Transcript Models

class PersonalInfo(BaseModel):
    """Personal information for a customer."""
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email: str
    phone: str
    date_of_birth: Optional[str] = Field(None, alias="dateOfBirth")
    ssn: Optional[str] = None

class Address(BaseModel):
    """Address information."""
    street: str
    city: str
    state: str
    postal_code: str = Field(..., alias="postalCode")
    country: str = "USA"

class Employment(BaseModel):
    """Employment information."""
    company: str
    position: str
    work_email: Optional[str] = Field(None, alias="workEmail")
    work_phone: Optional[str] = Field(None, alias="workPhone")
    work_address: Optional[Address] = Field(None, alias="workAddress")

class Customer(BaseModel):
    """Customer model matching the MCP server's Customer class."""
    customer_id: str = Field(..., alias="customerId")
    personal_info: PersonalInfo = Field(..., alias="personalInfo")
    home_address: Address = Field(..., alias="homeAddress")
    employment: Employment
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class TranscriptEntry(BaseModel):
    """A single entry in a call transcript."""
    speaker: str
    text: str
    timestamp: str

class Sentiment(BaseModel):
    """Sentiment analysis results."""
    polarity: float
    subjectivity: float
    analyzer: Optional[str] = None

class CallTranscript(BaseModel):
    """Call transcript model matching the MCP server's CallTranscript class."""
    call_id: str = Field(..., alias="callId")
    customer_id: str = Field(..., alias="customerId")
    call_type: str = Field(..., alias="callType")
    call_timestamp: str = Field(..., alias="callTimestamp")
    call_duration_seconds: int = Field(..., alias="callDurationSeconds")
    agent_id: str = Field(..., alias="agentId")
    call_summary: str = Field(..., alias="callSummary")
    is_ada_related: bool = Field(..., alias="isAdaRelated")
    ada_violation_occurred: bool = Field(..., alias="adaViolationOccurred")
    transcript: List[TranscriptEntry]
    sentiment: Sentiment
    contexts: List[str] = []

    class Config:
        allow_population_by_field_name = True

class CustomerWithTranscripts(Customer):
    """Customer model that includes related transcripts."""
    transcripts: List[CallTranscript] = []

class CustomerListResponse(BaseModel):
    """Response model for listing customers."""
    items: List[Customer]
    total_count: int = Field(..., alias="totalCount")
    has_next_page: bool = Field(..., alias="hasNextPage")

class TranscriptListResponse(BaseModel):
    """Response model for listing transcripts."""
    items: List[CallTranscript]
    total_count: int = Field(..., alias="totalCount")
    has_next_page: bool = Field(..., alias="hasNextPage")
