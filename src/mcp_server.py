"""
mcp_server.py
MCP server for hallucination detection tools.
"""

from mcp.server.fastmcp import FastMCP
from tools import (
    query_evidence_base,
    calculate_verification_confidence,
    fetch_paper_metadata,
    verify_citation_accuracy
)
import logging
import json
import sys
from typing import Dict, Any, Optional

# Set up logging to file
logging.basicConfig(
    filename='mcp_server.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filemode='w'
)
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("HallucinationTools")

def call_langchain_tool(tool, **kwargs):
    """
    Helper function to call LangChain StructuredTool objects correctly.
    """
    logger.debug(f"Calling tool {tool.name} with args: {kwargs}")
    
    try:
        # Method 1: Try using invoke() method (LangChain way)
        if hasattr(tool, 'invoke'):
            result = tool.invoke(kwargs)
            logger.debug(f"Used invoke() method")
        
        # Method 2: Try calling the underlying function
        elif hasattr(tool, 'func') and callable(tool.func):
            result = tool.func(**kwargs)
            logger.debug(f"Used func attribute")
        
        # Method 3: Try calling the tool directly
        elif callable(tool):
            result = tool(**kwargs)
            logger.debug(f"Used direct call")
        
        else:
            raise ValueError(f"Cannot call tool {tool.name}: no callable method found")
        
        # Parse result if it's JSON string
        if isinstance(result, str):
            try:
                return json.loads(result)
            except:
                return result
        return result
        
    except Exception as e:
        logger.error(f"Error calling tool {tool.name}: {e}")
        raise

@mcp.tool()
def search_evidence(query: str, num_results: int = 3) -> Dict[str, Any]:
    """
    Search for evidence related to a query in the academic database.
    
    Args:
        query: The search query or claim to find evidence for
        num_results: Number of evidence snippets to return (default: 3)
    
    Returns:
        Dictionary with query and evidence results
    """
    logger.info(f"🔍 search_evidence called with query: '{query}', num_results: {num_results}")
    
    try:
        # Validate inputs
        if not query or not query.strip():
            return {
                "status": "error",
                "message": "Query cannot be empty"
            }
        
        # Call the LangChain tool correctly
        result = call_langchain_tool(
            query_evidence_base,
            query=query.strip(),
            num_results=num_results
        )
        
        return {
            "status": "success",
            "query": query,
            "evidence": result,
            "num_results": num_results
        }
        
    except Exception as e:
        logger.error(f"❌ Error in search_evidence: {str(e)}")
        return {
            "status": "error",
            "query": query,
            "message": f"Error searching evidence: {str(e)}"
        }

@mcp.tool()
def verify_claim(claim: str) -> Dict[str, Any]:
    """
    Verify a claim by finding evidence and calculating confidence.
    
    Args:
        claim: The claim to verify
    
    Returns:
        Dictionary with claim, verification results, and confidence score
    """
    logger.info(f"🔍 verify_claim called with claim: '{claim}'")
    
    try:
        # Validate input
        if not claim or not claim.strip():
            return {
                "status": "error",
                "message": "Claim cannot be empty"
            }
        
        claim = claim.strip()
        
        # Step 1: Get evidence
        logger.info("Step 1: Searching for evidence...")
        evidence_result = call_langchain_tool(
            query_evidence_base,
            query=claim,
            num_results=3
        )
        
        # Step 2: Parse evidence into texts and sources
        evidence_texts = []
        evidence_sources = []
        
        if isinstance(evidence_result, dict):
            # If the tool returns a dictionary with evidence
            if 'evidence' in evidence_result:
                evidence_texts = [evidence_result['evidence']]
            else:
                evidence_texts = [str(evidence_result)]
        elif isinstance(evidence_result, str):
            evidence_texts = [evidence_result]
        elif isinstance(evidence_result, list):
            evidence_texts = evidence_result
        else:
            evidence_texts = [str(evidence_result)]
        
        evidence_sources = ["vector_db"] * len(evidence_texts)
        
        logger.info(f"Found {len(evidence_texts)} evidence snippets")
        
        # Step 3: Calculate confidence
        logger.info("Step 2: Calculating confidence...")
        confidence_result = call_langchain_tool(
            calculate_verification_confidence,
            claim=claim,
            evidence_texts=evidence_texts,
            evidence_sources=evidence_sources
        )
        
        logger.info(f"✅ verify_claim completed successfully")
        
        return {
            "status": "success",
            "claim": claim,
            "evidence": evidence_result,
            "verification": confidence_result,
            "evidence_count": len(evidence_texts)
        }
        
    except Exception as e:
        logger.error(f"❌ Error in verify_claim: {str(e)}")
        return {
            "status": "error",
            "claim": claim,
            "message": f"Error verifying claim: {str(e)}"
        }

@mcp.tool()
def fetch_paper(paper_title: Optional[str] = None, arxiv_id: Optional[str] = None, doi: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch paper metadata from academic APIs.
    
    Args:
        paper_title: Title of the paper to search for
        arxiv_id: arXiv ID if known
        doi: DOI if known
    
    Returns:
        Paper metadata
    """
    logger.info(f"🔍 fetch_paper called with title: {paper_title}, arxiv_id: {arxiv_id}, doi: {doi}")
    
    try:
        result = call_langchain_tool(
            fetch_paper_metadata,
            paper_title=paper_title,
            arxiv_id=arxiv_id,
            doi=doi
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Error in fetch_paper: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@mcp.tool()
def verify_citation(citation_text: str, expected_source: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify citation accuracy.
    
    Args:
        citation_text: The citation text to verify
        expected_source: Expected source if known
    
    Returns:
        Citation verification result
    """
    logger.info(f"🔍 verify_citation called with: {citation_text[:50]}...")
    
    try:
        result = call_langchain_tool(
            verify_citation_accuracy,
            citation_text=citation_text,
            expected_source=expected_source
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Error in verify_citation: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    logger.info("🚀 Starting HallucinationTools MCP server...")
    logger.info(f"Python version: {sys.version}")
    
    try:
        # Run the server with stdio transport
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)