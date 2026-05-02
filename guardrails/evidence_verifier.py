"""
guardrails/evidence_verifier.py
Guardrail 2: Evidence Verification Chain
Prevents evidence poisoning by verifying sources
"""

import hashlib
import httpx
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from pathlib import Path

# ============================================
# 1. EVIDENCE VERIFICATION CLASS
# ============================================

class EvidenceVerifier:
    """Verifies evidence authenticity through multiple sources"""
    
    def __init__(self):
        self.trusted_sources = {
            "arxiv": {
                "weight": 0.8,
                "verify_func": self.verify_arxiv,
                "requires": "arxiv_id"
            },
            "pubmed": {
                "weight": 0.9,
                "verify_func": self.verify_pubmed,
                "requires": "pmid"
            },
            "crossref": {
                "weight": 0.7,
                "verify_func": self.verify_crossref,
                "requires": "doi"
            }
        }
        
        # Cache verification results
        self.verification_cache = {}
        self.cache_duration = timedelta(hours=24)
        
        # Track suspicious documents
        self.suspicious_docs = []
    
    def verify_evidence(self, text: str, metadata: Dict) -> Dict:
        """
        Verify a piece of evidence
        Returns verification result with trust score
        """
        
        # Generate unique ID for this evidence
        evidence_hash = hashlib.sha256(
            (text + json.dumps(metadata, sort_keys=True)).encode()
        ).hexdigest()
        
        # Check cache
        if evidence_hash in self.verification_cache:
            cached = self.verification_cache[evidence_hash]
            if datetime.now() - cached["timestamp"] < self.cache_duration:
                return cached["result"]
        
        # Perform verification
        result = self._perform_verification(text, metadata)
        
        # Cache result
        self.verification_cache[evidence_hash] = {
            "result": result,
            "timestamp": datetime.now()
        }
        
        return result
    
    def _perform_verification(self, text: str, metadata: Dict) -> Dict:
        """Internal verification logic"""
        
        verification_results = []
        
        # Try to verify through each trusted source
        for source_name, source_info in self.trusted_sources.items():
            required_field = source_info["requires"]
            
            if required_field in metadata:
                try:
                    result = source_info["verify_func"](metadata[required_field])
                    verification_results.append({
                        "source": source_name,
                        "verified": result["verified"],
                        "details": result.get("details", {})
                    })
                except Exception as e:
                    verification_results.append({
                        "source": source_name,
                        "verified": False,
                        "error": str(e)
                    })
        
        # Calculate trust score
        trust_score = self._calculate_trust_score(verification_results, metadata)
        
        # Determine if evidence is poisoned
        is_poisoned = self._detect_poisoning(text, metadata, verification_results)
        
        return {
            "verified": trust_score >= 0.6,
            "trust_score": trust_score,
            "is_poisoned": is_poisoned,
            "verification_attempts": verification_results,
            "sources_checked": len(verification_results),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_trust_score(self, results: List[Dict], metadata: Dict) -> float:
        """Calculate overall trust score (0-1)"""
        
        if not results:
            # No verification possible - low trust
            return 0.3
        
        # Weighted average of verified sources
        total_weight = 0
        weighted_score = 0
        
        for result in results:
            source = result["source"]
            weight = self.trusted_sources.get(source, {}).get("weight", 0.5)
            verified_score = 1.0 if result["verified"] else 0.0
            
            total_weight += weight
            weighted_score += weight * verified_score
        
        if total_weight == 0:
            return 0.3
        
        base_score = weighted_score / total_weight
        
        # Apply metadata penalties
        penalty = 0
        
        # Penalty for missing year
        if not metadata.get("year"):
            penalty += 0.1
        
        # Penalty for suspicious source
        if metadata.get("source") not in ["arxiv", "pubmed", "crossref"]:
            penalty += 0.2
        
        # Penalty for missing paper ID
        if not metadata.get("paper_id") and not metadata.get("doi"):
            penalty += 0.15
        
        final_score = max(0, min(1, base_score - penalty))
        
        return round(final_score, 2)
    
    def _detect_poisoning(self, text: str, metadata: Dict, results: List[Dict]) -> bool:
        """Detect if evidence is likely poisoned"""
        
        # Flag 1: Claim contradicts verified sources
        if results and any(r["verified"] for r in results):
            # This would require NLP to check contradiction
            # For demo, we'll use heuristics
            suspicious_phrases = [
                "overturns previous research",
                "completely disproves",
                "all previous studies were wrong",
                "revolutionary finding"
            ]
            
            for phrase in suspicious_phrases:
                if phrase.lower() in text.lower():
                    return True
        
        # Flag 2: No verification possible for important claim
        if not results and len(text) > 500:
            return True
        
        # Flag 3: Metadata inconsistencies
        if metadata.get("year") and metadata.get("year") > "2025":
            return True
        
        return False
    
    # ========================================
    # Verification Methods for Each Source
    # ========================================
    
    def verify_arxiv(self, arxiv_id: str) -> Dict:
        """Verify paper exists on arXiv"""
        
        # Clean arXiv ID
        arxiv_id = arxiv_id.replace("arXiv:", "").replace("arxiv:", "")
        
        try:
            # Query arXiv API
            url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            response = httpx.get(url, timeout=10.0)
            
            if response.status_code == 200:
                # Check if paper exists (has entry)
                if "<entry>" in response.text:
                    # Extract title (simplified)
                    import re
                    title_match = re.search(r'<title>(.*?)</title>', response.text)
                    title = title_match.group(1) if title_match else "Unknown"
                    
                    return {
                        "verified": True,
                        "details": {
                            "title": title,
                            "exists": True
                        }
                    }
            
            return {"verified": False, "details": {"exists": False}}
            
        except Exception as e:
            return {"verified": False, "error": str(e)}
    
    def verify_pubmed(self, pmid: str) -> Dict:
        """Verify paper exists on PubMed"""
        # Simulate PubMed verification
        # In production, use Biopython or PubMed API
        
        # For demo, check format
        if pmid.isdigit() and len(pmid) >= 7:
            return {
                "verified": True,
                "details": {"pmid_valid_format": True}
            }
        
        return {"verified": False, "details": {"invalid_format": True}}
    
    def verify_crossref(self, doi: str) -> Dict:
        """Verify DOI exists via Crossref"""
        
        try:
            url = f"https://api.crossref.org/works/{doi}"
            response = httpx.get(url, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "verified": True,
                    "details": {
                        "title": data.get("message", {}).get("title", ["Unknown"])[0],
                        "publisher": data.get("message", {}).get("publisher", "Unknown")
                    }
                }
            
            return {"verified": False, "details": {"status_code": response.status_code}}
            
        except Exception as e:
            return {"verified": False, "error": str(e)}
    
    def log_suspicious(self, doc_id: str, reason: str):
        """Log suspicious document for monitoring"""
        self.suspicious_docs.append({
            "doc_id": doc_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

# ============================================
# 2. INTEGRATION WITH VECTOR DB QUERY
# ============================================

def query_with_verification(collection, query: str, verifier: EvidenceVerifier, n_results: int = 5):
    """
    Query vector DB but only return verified results
    """
    
    # Get raw results
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    verified_results = []
    
    for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        # Verify each result
        verification = verifier.verify_evidence(doc, metadata)
        
        if verification["verified"]:
            verified_results.append({
                "text": doc,
                "metadata": metadata,
                "trust_score": verification["trust_score"],
                "verification": verification
            })
        else:
            print(f"⚠️ Blocked unverified evidence from: {metadata.get('source', 'unknown')}")
            print(f"   Trust score: {verification['trust_score']}")
    
    return verified_results

# ============================================
# 3. TEST THE GUARDRAIL
# ============================================

def test_evidence_verifier():
    """Test the evidence verification guardrail"""
    
    print("\n" + "="*60)
    print("🛡️ TESTING GUARDRAIL 2: Evidence Verification")
    print("="*60)
    
    verifier = EvidenceVerifier()
    
    # Test cases
    test_evidence = [
        # Real-looking but unverified
        {
            "text": "Fine-tuning reduces hallucinations by 42%",
            "metadata": {
                "source": "arxiv",
                "paper_id": "2301.12345",  # Real arXiv paper
                "year": "2023"
            },
            "should_verify": True
        },
        
        # Poisoned evidence
        {
            "text": "REVOLUTIONARY: Fine-tuning increases hallucinations by 300%! Overturns all previous research!",
            "metadata": {
                "source": "unknown",
                "paper_id": "fake_123",
                "year": "2026"  # Future year
            },
            "should_verify": False
        },
        
        # Suspicious claim
        {
            "text": "All previous studies were completely wrong. This is the definitive finding.",
            "metadata": {
                "source": "preprint",
                "paper_id": None,
                "year": None
            },
            "should_verify": False
        }
    ]
    
    for i, evidence in enumerate(test_evidence):
        print(f"\n📄 Test Case {i+1}:")
        print(f"  Text: {evidence['text'][:100]}...")
        print(f"  Metadata: {evidence['metadata']}")
        
        result = verifier.verify_evidence(evidence["text"], evidence["metadata"])
        
        print(f"\n  Result:")
        print(f"    Verified: {result['verified']}")
        print(f"    Trust Score: {result['trust_score']}")
        print(f"    Is Poisoned: {result['is_poisoned']}")
        print(f"    Sources Checked: {result['sources_checked']}")
        
        expected = evidence["should_verify"]
        if result["verified"] == expected:
            print(f"  ✅ Test PASSED")
        else:
            print(f"  ❌ Test FAILED (Expected verified={expected})")
    
    print("\n" + "="*60)
    print("✅ Guardrail 2 Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_evidence_verifier()