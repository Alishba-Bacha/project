"""
run_agent.py
Script to run the hallucination detection agent with a sample query.
"""

import sys
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from graph import build_hallucination_detector_graph
from langchain_core.messages import HumanMessage
import json


def run_agent(query: str):
    """
    Run the hallucination detection agent with a user query
    """
    print("="*60)
    print("🔍 HALLUCINATION DETECTOR AGENT")
    print("="*60)
    print(f"Query: {query}\n")
    
    try:
        # Build the graph
        graph = build_hallucination_detector_graph()
        
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "paper_text": "",
            "claims_extracted": [],
            "verification_results": {},
            "confidence_scores": {},
            "citations_checked": [],
            "iteration_count": 0
        }
        
        thread_id = "session_1"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Run the graph
        final_state = None
        for step in graph.stream(initial_state, config=config):
            # Print progress
            for node_name, state in step.items():
                if "messages" in state and state["messages"]:
                    last_message = state["messages"][-1]
                    if hasattr(last_message, "content") and last_message.content:
                        print(f"\n📝 [{node_name}] {last_message.__class__.__name__}: {last_message.content[:200]}...")
            
            final_state = step
        
        # Print final result
        if final_state:
            print("\n" + "="*60)
            print("✅ FINAL RESULT")
            print("="*60)
            
            last_state = list(final_state.values())[-1]
            final_messages = last_state["messages"]
            final_response = final_messages[-1]
            
            print(f"\n{final_response.content}")
            
            # Print summary stats
            print("\n📊 Summary:")
            print(f"  - Total messages: {len(final_messages)}")
            print(f"  - Iterations: {last_state.get('iteration_count', 0)}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test queries
    test_queries = [
        "Verify this claim: 'Fine-tuning LLMs reduces hallucinations in medical papers'",
        "Check this citation: 'According to Smith et al. (2023), arXiv:2301.12345, hallucination rates drop by 40%'",
        "Find evidence about fact verification techniques in academic writing"
    ]
    
    # Run first query
    result = run_agent(test_queries[0])