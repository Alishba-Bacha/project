from langchain_core.tools import tool
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
import httpx
import os
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

# ============================================
# Pydantic Models for Input Validation
# ============================================

class GroundingQueryInput(BaseModel):
    query: str = Field(description="The claim or question to verify against academic sources")
    source_filter: Optional[str] = Field(
        default=None, 
        description="Filter by source: 'arxiv', 'pubmed', 'journal', or None"
    )
    num_results: int = Field(default=3, ge=1, le=10, description="Number of evidence snippets to retrieve")

    @field_validator('query')
    def query_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class CalculateConfidenceInput(BaseModel):
    claim: str = Field(description="The original claim being verified")
    evidence_texts: List[str] = Field(description="List of evidence snippets retrieved")
    evidence_sources: List[str] = Field(description="Sources of each evidence snippet")

    @field_validator('evidence_texts')
    def evidence_not_empty(cls, v):
        if not v:
            raise ValueError('At least one evidence text required')
        return v

class FetchPaperMetadataInput(BaseModel):
    """Input schema for fetching paper metadata from external APIs"""
    paper_title: Optional[str] = Field(None, description="Title of the paper to search for")
    arxiv_id: Optional[str] = Field(None, description="arXiv ID if known")
    doi: Optional[str] = Field(None, description="DOI if known")

    @field_validator('paper_title', 'arxiv_id', 'doi')
    def at_least_one_identifier(cls, v, info):
        # This validator runs for each field, so we need to check all fields
        field_name = info.field_name
        values = info.data
        
        # Only validate when all fields are being processed
        if field_name == 'doi':  # Last field to be validated
            if not any([values.get('paper_title'), values.get('arxiv_id'), values.get('doi')]):
                raise ValueError('Must provide at least one identifier (title, arxiv_id, or doi)')
        return v

class CheckCitationAccuracyInput(BaseModel):
    """Input schema for citation verification tool"""
    citation_text: str = Field(description="The citation text to verify")
    expected_source: Optional[str] = Field(None, description="Expected source if known")

# ============================================
# Tool 1: Grounding Tool (Vector DB Query)
# ============================================

@tool(args_schema=GroundingQueryInput)
def query_evidence_base(query: str, source_filter: Optional[str] = None, num_results: int = 3) -> str:
    """
    Query the vector database for evidence related to a claim or question.
    
    This tool searches through pre-indexed academic papers and sources
    to find relevant evidence snippets that can help verify a claim.
    It connects to a ChromaDB instance containing embedded academic texts.
    
    Args:
        query: The claim or question to verify against academic sources
        source_filter: Optional filter by source type ('arxiv', 'pubmed', 'journal', or None)
        num_results: Number of evidence snippets to retrieve (between 1 and 10)
        
    Returns:
        Formatted string containing evidence snippets with source metadata
        and confidence scores, or an error message if the database is not found.
    """
    try:
        DB_PATH = Path(__file__).resolve().parents[1] / "chroma_db"
        
        # Check if DB exists
        if not DB_PATH.exists():
            return f"⚠️ Vector database not found at {DB_PATH}. Please run vector_store.py first."
        
        client = chromadb.PersistentClient(path=str(DB_PATH))
        
        # Try to get collection, return error if not exists
        try:
            collection = client.get_collection("hallucination_detector")
        except ValueError:
            return "⚠️ Collection 'hallucination_detector' not found. Please run vector_store.py first."
        
        # Build query parameters
        query_params = {
            "query_texts": [query],
            "n_results": num_results
        }
        
        # Add metadata filter if specified
        if source_filter:
            query_params["where"] = {"source": source_filter}
        
        # Execute query
        results = collection.query(**query_params)
        
        if not results["documents"][0]:
            return f"No evidence found for query: '{query}'"
        
        # Format results
        formatted_results = []
        for i, (doc, metadata) in enumerate(zip(
            results["documents"][0], 
            results["metadatas"][0]
        )):
            # Calculate confidence if distances available
            confidence = 0.7  # Default confidence
            if "distances" in results and results["distances"] and results["distances"][0]:
                distance = results["distances"][0][i]
                confidence = 1 - (min(distance, 1.0) / 2)  # Normalize distance to confidence
            
            result_text = f"""
Evidence {i+1} (Confidence: {confidence:.2f}):
Source: {metadata.get('source', 'unknown')} | Type: {metadata.get('doc_type', 'unknown')}
Paper ID: {metadata.get('paper_id', 'N/A')}
Excerpt: {doc[:300]}...
"""
            formatted_results.append(result_text)
        
        return "\n".join(formatted_results)
    
    except Exception as e:
        return f"Error querying evidence base: {str(e)}"

# ============================================
# Tool 2: Confidence Calculator
# ============================================

@tool(args_schema=CalculateConfidenceInput)
def calculate_verification_confidence(claim: str, evidence_texts: List[str], evidence_sources: List[str]) -> str:
    """
    Calculate a confidence score for claim verification based on available evidence.
    
    This tool analyzes the quantity, diversity, and quality of evidence
    to produce a confidence score and assessment of how well a claim
    is supported. It uses heuristics including number of evidence pieces,
    source diversity, and evidence length/detail.
    
    Args:
        claim: The original claim being verified
        evidence_texts: List of evidence snippets retrieved from sources
        evidence_sources: List of sources corresponding to each evidence snippet
        
    Returns:
        JSON string containing confidence score, assessment level (e.g., 
        "STRONGLY SUPPORTED", "MODERATELY SUPPORTED"), detailed metrics,
        and recommendations for next steps.
    """
    if not evidence_texts:
        return json.dumps({
            "confidence_score": 0,
            "assessment": "NO EVIDENCE",
            "details": "No evidence found to verify this claim",
            "recommendation": "Mark as UNVERIFIED - requires manual check"
        }, indent=2)
    
    # Factors affecting confidence
    num_evidence = len(evidence_texts)
    source_diversity = len(set(evidence_sources))
    
    # Average evidence length as proxy for richness
    avg_evidence_length = sum(len(e) for e in evidence_texts) / num_evidence
    
    # Calculate confidence (simplified heuristic)
    base_confidence = min(num_evidence * 20, 60)  # Up to 60% from quantity
    diversity_bonus = min(source_diversity * 10, 20)  # Up to 20% from diversity
    length_bonus = min(avg_evidence_length / 500 * 10, 20)  # Up to 20% from detail
    
    confidence = min(base_confidence + diversity_bonus + length_bonus, 100)
    
    if confidence >= 80:
        assessment = "STRONGLY SUPPORTED"
        recommendation = "Claim is well-supported by multiple sources"
    elif confidence >= 60:
        assessment = "MODERATELY SUPPORTED"
        recommendation = "Claim has reasonable evidence support"
    elif confidence >= 40:
        assessment = "WEAKLY SUPPORTED"
        recommendation = "Limited evidence - consider gathering more sources"
    else:
        assessment = "INSUFFICIENT EVIDENCE"
        recommendation = "Claim cannot be verified with current evidence"
    
    return json.dumps({
        "confidence_score": round(confidence, 2),
        "assessment": assessment,
        "details": {
            "num_evidence_snippets": num_evidence,
            "unique_sources": source_diversity,
            "avg_evidence_length": round(avg_evidence_length, 2)
        },
        "recommendation": recommendation,
        "timestamp": datetime.now().isoformat()
    }, indent=2)

# ============================================
# Tool 3: External API Fetcher (arXiv)
# ============================================

@tool(args_schema=FetchPaperMetadataInput)
def fetch_paper_metadata(paper_title: Optional[str] = None, arxiv_id: Optional[str] = None, doi: Optional[str] = None) -> str:
    """
    Fetch paper metadata from academic APIs like arXiv and Crossref.
    
    This tool retrieves metadata for academic papers using various identifiers.
    It supports searching by paper title, arXiv ID, or DOI (Digital Object Identifier).
    The tool queries arXiv API and Crossref API to gather comprehensive paper information.
    
    Args:
        paper_title: The title of the paper to search for (optional)
        arxiv_id: The arXiv ID of the paper (optional, e.g., '2103.00020')
        doi: The Digital Object Identifier of the paper (optional, e.g., '10.1038/nature12373')
        
    Returns:
        JSON string containing metadata from available sources (arXiv, Crossref)
        including title, publisher, publication date, and access URLs.
        At least one identifier must be provided.
    """
    results = {}
    
    # Try arXiv API
    if arxiv_id or paper_title:
        try:
            if arxiv_id:
                url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
                response = httpx.get(url, timeout=30.0)
                if response.status_code == 200:
                    # Simple extraction of title from arXiv response
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.text)
                    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
                    entry = root.find('atom:entry', namespace)
                    if entry is not None:
                        title = entry.find('atom:title', namespace)
                        results["arxiv"] = {
                            "status": "found",
                            "title": title.text if title is not None else "Unknown",
                            "url": url
                        }
            elif paper_title:
                url = f"http://export.arxiv.org/api/query?search_query=ti:{paper_title}&max_results=1"
                response = httpx.get(url, timeout=30.0)
                if response.status_code == 200:
                    results["arxiv"] = {
                        "status": "found",
                        "note": f"Search performed for title: {paper_title}",
                        "url": url
                    }
        except Exception as e:
            results["arxiv"] = {"status": "error", "message": str(e)}
    
    # Try Crossref API for DOI
    if doi:
        try:
            url = f"https://api.crossref.org/works/{doi}"
            response = httpx.get(url, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                results["crossref"] = {
                    "status": "found",
                    "title": message.get("title", ["N/A"])[0] if message.get("title") else "N/A",
                    "publisher": message.get("publisher", "N/A"),
                    "published": message.get("published", {}).get("date-parts", [["N/A"]])[0]
                }
        except Exception as e:
            results["crossref"] = {"status": "error", "message": str(e)}
    
    if not results:
        return f"No metadata found for the provided identifiers"
    
    return json.dumps(results, indent=2)

# ============================================
# Tool 4: Citation Verifier
# ============================================

@tool(args_schema=CheckCitationAccuracyInput)
def verify_citation_accuracy(citation_text: str, expected_source: Optional[str] = None) -> str:
    """
    Verify the accuracy of a citation by checking identifiers and sources.
    
    This tool extracts and validates citation identifiers (arXiv IDs, DOIs)
    and provides preliminary analysis for citation verification. It helps
    detect potentially hallucinated or misattributed citations.
    
    Args:
        citation_text: The citation text to verify (e.g., "According to Smith et al. (2020)...")
        expected_source: Optional expected source to compare against
        
    Returns:
        JSON string containing extracted identifiers, verification status,
        analysis summary, and recommended next steps for thorough verification.
    """
    import re
    arxiv_pattern = r'arXiv:[\d\.]+'
    doi_pattern = r'10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+'
    
    arxiv_ids = re.findall(arxiv_pattern, citation_text.lower())
    dois = re.findall(doi_pattern, citation_text)
    
    verification_result = {
        "citation_text": citation_text[:200] + "..." if len(citation_text) > 200 else citation_text,
        "extracted_identifiers": {
            "arxiv_ids": arxiv_ids,
            "dois": dois
        },
        "verification_status": "PENDING",
        "analysis": "Citation verification in progress...",
        "next_steps": [
            "Check if the cited paper exists in academic databases",
            "Verify quoted text appears in the original source",
            "Detect hallucinated citations (non-existent papers)",
            "Flag misattributed claims"
        ]
    }
    
    return json.dumps(verification_result, indent=2)


all_tools = [
    query_evidence_base,
    calculate_verification_confidence,
    fetch_paper_metadata,
    verify_citation_accuracy
]

if __name__ == "__main__":
    # Test the tools
    print("🧪 Testing tools.py")
    print(f"✅ Loaded {len(all_tools)} tools:")
    for tool in all_tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")