"""
schema.py
Pydantic models for API request/response validation
Task 1: Endpoint Design & Schema Validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class RequestStatus(str, Enum):
    """Status of the request"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChatRequest(BaseModel):
    """
    Request model for the chat endpoint.
    Required by Task 1: Must include message and thread_id
    """
    
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=10000,
        description="User query to send to the hallucination detector"
    )
    
    thread_id: Optional[str] = Field(
        default=None,
        description="Thread ID for conversation persistence. If not provided, a new UUID is generated.",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    # Optional parameters for fine-tuning
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for grouping multiple requests"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata for the request"
    )
    
    @field_validator('message')
    def message_not_empty(cls, v):
        """Validate that message is not empty or just whitespace"""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()
    
    @field_validator('thread_id')
    def validate_thread_id(cls, v):
        """Validate thread_id format if provided"""
        if v is not None:
            # Try to parse as UUID if it looks like one
            if len(v) == 36 and v.count('-') == 4:
                try:
                    UUID(v)
                except ValueError:
                    # Not a valid UUID but still accept as string ID
                    pass
        return v
    
    def get_thread_id(self) -> str:
        """Get or generate a thread ID"""
        if self.thread_id:
            return self.thread_id
        return str(uuid4())


class ChatResponse(BaseModel):
    """
    Response model for the chat endpoint.
    Required by Task 1: Must include final answer and status
    """
    
    thread_id: str = Field(
        ..., 
        description="Thread ID for this conversation"
    )
    
    message: str = Field(
        ..., 
        description="Final response from the hallucination detector"
    )
    
    status: RequestStatus = Field(
        ..., 
        description="Status of the request processing"
    )
    
    confidence_scores: Optional[Dict[str, float]] = Field(
        default=None,
        description="Confidence scores for verification results"
    )
    
    tools_used: List[str] = Field(
        default_factory=list,
        description="List of tools called during processing"
    )
    
    processing_time: float = Field(
        ..., 
        description="Total processing time in seconds"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if status is FAILED"
    )


class StreamEvent(BaseModel):
    """
    Event model for streaming responses (SSE format)
    """
    
    event: str = Field(
        ..., 
        description="Event type: 'node_start', 'node_end', 'tool_call', 'token', 'complete', 'error'"
    )
    
    data: Dict[str, Any] = Field(
        ..., 
        description="Event data payload"
    )
    
    thread_id: str = Field(
        ..., 
        description="Thread ID for this conversation"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Event timestamp"
    )


class HealthResponse(BaseModel):
    """Health check response model"""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.now)
    graph_ready: bool = Field(..., description="Whether LangGraph is initialized")
    checkpointer_ready: bool = Field(..., description="Whether checkpointer is ready")


class ErrorResponse(BaseModel):
    """Error response model"""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    thread_id: Optional[str] = Field(None, description="Thread ID if applicable")
    timestamp: datetime = Field(default_factory=datetime.now)