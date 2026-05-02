"""
graph.py
Builds the hallucination detection agent graph with proper Ollama integration.
"""

import operator
from typing import TypedDict, Annotated, List, Dict, Any, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
import json
from pathlib import Path
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
parent_dir = str(Path(__file__).resolve().parents[1])
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import tools
try:
    from tools import all_tools
    logger.info(f"✅ Imported {len(all_tools)} tools")
except ImportError as e:
    logger.error(f"Failed to import tools: {e}")
    all_tools = []

# Import HITL
try:
    from hitl import request_human_approval, HIGH_RISK_TOOLS
    logger.info("✅ Imported HITL modules")
except ImportError:
    logger.warning("HITL modules not found, using auto-approve")
    def request_human_approval(tool_name: str, input_data: dict) -> bool:
        return True
    HIGH_RISK_TOOLS = []

# Import memory
try:
    from memory import memory
    logger.info("✅ Imported memory")
except ImportError as e:
    logger.warning(f"Memory import failed: {e}")
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()
    logger.info("✅ Using MemorySaver fallback")

# Define state
class AgentState(TypedDict):
    messages: List[BaseMessage]
    paper_text: str
    claims_extracted: List[str]
    verification_results: Dict[str, Any]
    confidence_scores: Dict[str, float]
    citations_checked: List[str]
    iteration_count: int

def create_llm():
    """Create and return the LLM instance using langchain-ollama"""
    try:
        # Use the new ChatOllama from langchain_ollama
        from langchain_ollama import ChatOllama
        
        # First check if Ollama is accessible
        import requests
        try:
            # Test connection to Ollama
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                logger.info(f"Available Ollama models: {model_names}")
                
                # Choose a model - try different options
                preferred_models = ["llama3.2:1b", "llama3.2", "tinyllama", "llama2:latest"]
                selected_model = None
                
                for model in preferred_models:
                    if any(model in m for m in model_names):
                        selected_model = next(m for m in model_names if model in m)
                        break
                
                if not selected_model and model_names:
                    selected_model = model_names[0]
                    logger.info(f"Using first available model: {selected_model}")
                elif not selected_model:
                    logger.error("No models available in Ollama. Please pull a model first.")
                    logger.info("Run: ollama pull llama3.2:1b")
                    return MockLLM()
                
                # Create ChatOllama instance
                llm = ChatOllama(
                    model=selected_model,
                    temperature=0.7,
                    num_predict=2048,
                    top_k=10,
                    top_p=0.95,
                )
                logger.info(f"✅ Connected to Ollama with model: {selected_model}")
                return llm
            else:
                logger.error(f"Ollama returned unexpected status: {response.status_code}")
                return MockLLM()
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to Ollama. Please ensure Ollama is running.")
            logger.info("Run 'ollama serve' in a terminal if it's not already running.")
            return MockLLM()
            
    except ImportError:
        logger.error("langchain-ollama not installed. Run: pip install langchain-ollama")
        return MockLLM()
    except Exception as e:
        logger.error(f"Error creating LLM: {e}")
        return MockLLM()

class MockLLM:
    """Mock LLM for testing when Ollama is not available"""
    def __init__(self):
        logger.warning("Using MockLLM - no real LLM calls will be made")
    
    def invoke(self, messages):
        """Mock invoke method"""
        last_message = messages[-1].content if messages else ""
        
        # Simulate tool usage
        if "evidence" in last_message.lower() or "verify" in last_message.lower():
            return AIMessage(
                content="I'll help verify this claim by searching for evidence.",
                tool_calls=[
                    {
                        "name": "query_evidence_base",
                        "args": {"query": last_message, "num_results": 3},
                        "id": "mock_call_1"
                    }
                ]
            )
        return AIMessage(
            content=f"[MOCK RESPONSE] Processing query: '{last_message[:50]}...'"
        )
    
    def bind_tools(self, tools):
        """Mock bind_tools - returns self for chaining"""
        logger.info(f"MockLLM: Binding {len(tools)} tools")
        return self

def create_agent():
    """Create the agent with tools using proper tool binding"""
    llm = create_llm()
    
    # Try to bind tools - ChatOllama from langchain-ollama supports this
    try:
        # For newer versions that support tool binding
        if hasattr(llm, 'bind_tools'):
            llm_with_tools = llm.bind_tools(all_tools)
            logger.info(f"✅ Tools bound to LLM using bind_tools()")
        else:
            # Fallback for versions without bind_tools
            logger.warning("LLM doesn't support bind_tools(), using without tools")
            llm_with_tools = llm
            
    except NotImplementedError:
        logger.warning("bind_tools not implemented, using basic LLM")
        llm_with_tools = llm
    except Exception as e:
        logger.warning(f"Failed to bind tools: {e}")
        llm_with_tools = llm
    
    return llm_with_tools

def agent_node(state: AgentState) -> AgentState:
    """Agent node that processes messages and decides next actions"""
    logger.info("🤖 Agent Node: Thinking...")
    
    # Get the LLM with tools
    llm_with_tools = create_agent()
    
    # Create a system message
    system_message = HumanMessage(content="""You are a hallucination detection assistant for academic papers. 
Your task is to verify claims and citations against reliable sources.
Use the available tools to:
- Query evidence database for supporting information
- Check citation accuracy
- Calculate confidence scores

Always use tools when you need external information.""")

    # Prepare messages with system prompt
    messages = [system_message] + state["messages"]
    
    try:
        # Get response from LLM
        response = llm_with_tools.invoke(messages)
        
        # Check if response includes tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"🤖 Agent requested {len(response.tool_calls)} tool calls")
            for tc in response.tool_calls:
                logger.info(f"  - Tool: {tc.get('name', 'unknown')}")
        
        # Update state
        new_state = state.copy()
        new_state["messages"] = state["messages"] + [response]
        new_state["iteration_count"] = state.get("iteration_count", 0) + 1
        
        logger.info(f"✅ Agent responded (iteration {new_state['iteration_count']})")
        return new_state
        
    except Exception as e:
        logger.error(f"Error in agent node: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error message
        error_message = AIMessage(content=f"I encountered an error: {str(e)}")
        state["messages"].append(error_message)
        return state

def build_hallucination_detector_graph():
    """Build and return the hallucination detector graph"""
    logger.info("Building Hallucination Detector Graph...")
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    
    # Add edges
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)
    
    # Compile with checkpointer
    if memory:
        graph = workflow.compile(checkpointer=memory)
    else:
        graph = workflow.compile()
        
    logger.info("✅ Graph built successfully!")
    
    return graph

# Create the graph instance
graph = build_hallucination_detector_graph()

if __name__ == "__main__":
    print("✅ Graph module loaded successfully")
    print(f"   - Memory type: {type(memory).__name__}")
    print(f"   - Tools available: {len(all_tools)}")