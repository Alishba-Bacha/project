"""
fixed_main.py
FastAPI application with CORRECTED imports for your project
"""

import sys
import time
import json
from pathlib import Path
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

# Add src directory to Python path FIRST
project_root = Path(__file__).resolve().parents[1]
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(project_root))

# Now import with correct paths
from multi_agent_graph import build_multi_agent_graph
from tools import (
    query_evidence_base,
    calculate_verification_confidence,
    fetch_paper_metadata,
    verify_citation_accuracy
)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import asyncio
from langchain_core.messages import HumanMessage

# ============================================
# Pydantic Schemas (Task 1)
# ============================================

class ChatRequest(BaseModel):
    """Request model with message and thread_id"""
    message: str = Field(..., min_length=1, max_length=10000, description="User query")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation persistence")

class ChatResponse(BaseModel):
    """Response model with final answer and status"""
    thread_id: str
    message: str
    status: str
    tools_used: list = Field(default_factory=list)
    processing_time: float
    timestamp: datetime

class StreamEvent(BaseModel):
    """Streaming event model"""
    event: str
    data: dict
    thread_id: str
    timestamp: datetime

# ============================================
# Global Variables (Task 2 - Persistence)
# ============================================

graph = None
checkpointer = None
initialized = False

# ============================================
# Lifespan Management (Task 2)
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize graph ONCE at startup - critical for persistence"""
    global graph, initialized
    
    print("\n" + "="*60)
    print("🚀 Starting Hallucination Detector API Server")
    print("="*60)
    
    # Check Ollama
    try:
        import httpx
        response = httpx.get("http://localhost:11434", timeout=2)
        print("✅ Ollama is running")
    except:
        print("⚠️ Ollama not detected. Make sure 'ollama serve' is running")
    
    # Initialize graph
    try:
        print("🔄 Initializing LangGraph...")
        graph = build_multi_agent_graph()
        initialized = True
        print("✅ Graph initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize graph: {e}")
        initialized = False
    
    yield
    
    # Cleanup
    print("\n🛑 Shutting down API server")

# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="Hallucination Detector API",
    description="Multi-Agent Hallucination Detection for Academic Papers",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Helper Functions
# ============================================

def get_thread_config(thread_id: str) -> dict:
    """Create thread config for persistence (Task 2)"""
    return {"configurable": {"thread_id": thread_id}}

# ============================================
# Task 2: POST /chat Endpoint
# ============================================

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Synchronous chat endpoint.
    Task 2: Extracts thread_id and passes to graph config.
    """
    
    if not initialized:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    
    start_time = time.time()
    thread_id = request.thread_id or str(uuid.uuid4())
    
    try:
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=request.message)]
        }
        
        # Get thread config for persistence
        config = get_thread_config(thread_id)
        
        # Track tool calls
        tools_used = []
        final_response = ""
        
        # Run graph
        async for event in graph.astream(initial_state, config=config):
            for node_name, node_output in event.items():
                # Extract tool calls
                if isinstance(node_output, dict) and "messages" in node_output:
                    for msg in node_output["messages"]:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                tool_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", str(tc))
                                if tool_name not in tools_used:
                                    tools_used.append(tool_name)
                        
                        # Extract response
                        if hasattr(msg, "content") and msg.content:
                            final_response = msg.content
        
        if not final_response:
            final_response = "Processing completed. Check your graph output."
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            thread_id=thread_id,
            message=final_response,
            status="completed",
            tools_used=tools_used,
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        return ChatResponse(
            thread_id=thread_id,
            message=f"Error: {str(e)}",
            status="failed",
            tools_used=[],
            processing_time=processing_time,
            timestamp=datetime.now()
        )

# ============================================
# Task 3: POST /stream Endpoint (SSE)
# ============================================

@app.post("/stream")
async def stream_endpoint(request: ChatRequest):
    """
    Streaming endpoint with Server-Sent Events (SSE).
    Task 3: Uses graph.astream() to yield chunks.
    """
    
    if not initialized:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    
    thread_id = request.thread_id or str(uuid.uuid4())
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events"""
        
        try:
            # Send start event
            yield f"data: {json.dumps({'event': 'start', 'thread_id': thread_id, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            initial_state = {
                "messages": [HumanMessage(content=request.message)]
            }
            
            config = get_thread_config(thread_id)
            
            # Stream through graph (Task 3: using astream)
            async for event in graph.astream(initial_state, config=config):
                for node_name, node_output in event.items():
                    # Node start event
                    yield f"data: {json.dumps({'event': 'node_start', 'node': node_name, 'thread_id': thread_id})}\n\n"
                    
                    # Extract and send tool calls
                    if isinstance(node_output, dict) and "messages" in node_output:
                        for msg in node_output["messages"]:
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    tool_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", str(tc))
                                    yield f"data: {json.dumps({'event': 'tool_call', 'tool': tool_name, 'thread_id': thread_id})}\n\n"
                            
                            # Stream content chunks
                            if hasattr(msg, "content") and msg.content:
                                content = msg.content
                                # Split into chunks for streaming effect
                                chunks = [content[i:i+100] for i in range(0, len(content), 100)]
                                for chunk in chunks:
                                    yield f"data: {json.dumps({'event': 'token', 'token': chunk, 'node': node_name, 'thread_id': thread_id})}\n\n"
                                    await asyncio.sleep(0.03)  # Smooth streaming
                    
                    # Node end event
                    yield f"data: {json.dumps({'event': 'node_end', 'node': node_name, 'thread_id': thread_id})}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'event': 'complete', 'status': 'success', 'thread_id': thread_id})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'error': str(e), 'thread_id': thread_id})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ============================================
# Additional Endpoints
# ============================================

@app.get("/")
async def root():
    return {
        "service": "Hallucination Detector API",
        "version": "2.0.0",
        "status": "running",
        "graph_ready": initialized,
        "endpoints": {
            "POST /chat": "Synchronous chat",
            "POST /stream": "Streaming chat (SSE)",
            "GET /health": "Health check",
            "GET /docs": "API documentation"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy" if initialized else "degraded",
        "graph_ready": initialized,
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# Run the app
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fixed_main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )