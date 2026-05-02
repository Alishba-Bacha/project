"""
test_lab3.py
Test script to verify Lab 3 implementation
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

def test_tools():
    """Test if tools can be imported"""
    print("🧪 Testing tools import...")
    try:
        from src.tools import all_tools, query_evidence_base
        print(f"✅ Successfully imported {len(all_tools)} tools")
        print(f"   Tools: {[tool.name for tool in all_tools]}")
        return True
    except Exception as e:
        print(f"❌ Failed to import tools: {e}")
        return False

def test_graph():
    """Test if graph can be built"""
    print("\n🧪 Testing graph build...")
    try:
        from src.graph import build_hallucination_detector_graph
        graph = build_hallucination_detector_graph()
        print("✅ Successfully built graph")
        return True
    except Exception as e:
        print(f"❌ Failed to build graph: {e}")
        return False

def test_vector_db():
    """Test if vector DB exists"""
    print("\n🧪 Testing vector database...")
    db_path = Path(__file__).resolve().parents[1] / "chroma_db"
    if db_path.exists():
        print(f"✅ Vector DB found at {db_path}")
        
        # Try to query it
        try:
            from src.tools import query_evidence_base
            result = query_evidence_base.invoke({
                'query': 'test query',
                'num_results': 1
            })
            print(f"   Query result: {result[:100]}...")
        except Exception as e:
            print(f"   ⚠️ Could not query DB: {e}")
    else:
        print(f"❌ Vector DB not found at {db_path}")
        print("   Please run vector_store.py first")

if __name__ == "__main__":
    print("="*50)
    print("LAB 3 VERIFICATION")
    print("="*50)
    
    tests_passed = 0
    tests_total = 3
    
    if test_tools():
        tests_passed += 1
    if test_graph():
        tests_passed += 1
    
    test_vector_db()
    # Don't count vector DB in pass/fail since it's optional for this test
    
    print("\n" + "="*50)
    print(f"RESULTS: {tests_passed}/{tests_total} core tests passed")
    
    if tests_passed == tests_total:
        print("✅ Lab 3 implementation is ready!")
        print("\nNext steps:")
        print("1. Run: python src/vector_store.py (if not done)")
        print("2. Run: python src/run_agent.py")
    else:
        print("⚠️ Please fix the failing tests above")