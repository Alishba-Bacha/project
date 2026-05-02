"""
Hallucination Detector Package
"""
from .tools import all_tools, query_evidence_base, calculate_verification_confidence, fetch_paper_metadata, verify_citation_accuracy

__all__ = [
    'all_tools',
    'query_evidence_base',
    'calculate_verification_confidence',
    'fetch_paper_metadata',
    'verify_citation_accuracy'
]