"""
langsmith_config.py
Setup LangSmith tracing for your LangGraph agent
"""

import os
from pathlib import Path
from langsmith import Client
from langsmith.wrappers import wrap_openai
from langchain_openai import ChatOpenAI
from datetime import datetime

# ============================================
# 1. LANGSMITH SETUP
# ============================================

def setup_langsmith():
    """
    Configure LangSmith tracing
    Get your API key from: https://smith.langchain.com
    """
    
    # LangSmith configuration
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = "your_api_key_here"  # Replace with your key
    os.environ["LANGCHAIN_PROJECT"] = "hallucination-detector-lab7"
    
    print("✅ LangSmith configured")
    print(f"   Project: {os.environ['LANGCHAIN_PROJECT']}")
    print(f"   View traces at: https://smith.langchain.com/projects")

# ============================================
# 2. TRACE COLLECTOR
# ============================================

class TraceAnalyzer:
    """Analyze LangSmith traces for bottlenecks"""
    
    def __init__(self):
        self.client = Client()
        self.project_name = "hallucination-detector-lab7"
    
    def get_recent_traces(self, limit: int = 10):
        """Get recent traces from LangSmith"""
        
        try:
            runs = list(self.client.list_runs(
                project_name=self.project_name,
                limit=limit
            ))
            
            return runs
        except Exception as e:
            print(f"Error fetching traces: {e}")
            return []
    
    def analyze_latency(self, runs):
        """Analyze latency per node"""
        
        node_latencies = {}
        
        for run in runs:
            if hasattr(run, 'latency') and run.latency:
                node_name = run.name or "unknown"
                
                if node_name not in node_latencies:
                    node_latencies[node_name] = []
                
                node_latencies[node_name].append(run.latency)
        
        # Calculate averages
        analysis = {}
        for node, latencies in node_latencies.items():
            analysis[node] = {
                "avg_latency": sum(latencies) / len(latencies),
                "min_latency": min(latencies),
                "max_latency": max(latencies),
                "count": len(latencies)
            }
        
        return analysis
    
    def analyze_failure_points(self, runs):
        """Identify where failures occur"""
        
        failures = []
        
        for run in runs:
            if hasattr(run, 'error') and run.error:
                failures.append({
                    "run_id": run.id,
                    "name": run.name,
                    "error": str(run.error),
                    "latency": run.latency if hasattr(run, 'latency') else None
                })
        
        return failures
    
    def identify_bottlenecks(self, runs):
        """Identify the slowest components"""
        
        latencies = []
        for run in runs:
            if hasattr(run, 'latency') and run.latency:
                latencies.append({
                    "node": run.name,
                    "latency": run.latency,
                    "run_id": run.id
                })
        
        # Sort by latency
        latencies.sort(key=lambda x: x["latency"], reverse=True)
        
        if latencies:
            slowest = latencies[0]
            return {
                "slowest_node": slowest["node"],
                "slowest_latency": slowest["latency"],
                "top_3_slowest": latencies[:3]
            }
        
        return None

# ============================================
# 3. GENERATE TRACE REPORT
# ============================================

def generate_trace_report():
    """Generate bottleneck analysis from traces"""
    
    analyzer = TraceAnalyzer()
    
    print("\n" + "="*60)
    print("🔍 Trace-Based Bottleneck Analysis")
    print("="*60)
    
    # Get traces
    runs = analyzer.get_recent_traces(limit=20)
    
    if not runs:
        print("⚠️ No traces found. Run some queries first!")
        return
    
    # Analyze latency
    latency_analysis = analyzer.analyze_latency(runs)
    
    print("\n📊 Node Latency Analysis:")
    print("-"*40)
    for node, stats in sorted(latency_analysis.items(), key=lambda x: x[1]['avg_latency'], reverse=True):
        print(f"  {node}: {stats['avg_latency']:.3f}s (n={stats['count']})")
    
    # Identify bottlenecks
    bottlenecks = analyzer.identify_bottlenecks(runs)
    
    if bottlenecks:
        print(f"\n🐌 SLOWEST NODE: {bottlenecks['slowest_node']}")
        print(f"   Latency: {bottlenecks['slowest_latency']:.3f}s")
    
    # Analyze failures
    failures = analyzer.analyze_failure_points(runs)
    
    if failures:
        print(f"\n❌ FAILURE POINTS ({len(failures)} failures):")
        for f in failures[:5]:
            print(f"  - {f['name']}: {f['error'][:100]}")
    
    # Generate bottleneck analysis text
    analysis_text = f"""Bottleneck Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SLOWEST COMPONENT: {bottlenecks['slowest_node'] if bottlenecks else 'Unknown'}
Average Latency: {bottlenecks['slowest_latency']:.3f}s if bottlenecks else 'N/A'

FAILURE ANALYSIS:
- Total Failures: {len(failures)}
- Most Common Failure Node: {max(set([f['name'] for f in failures]), key=[f['name'] for f in failures].count) if failures else 'None'}

PROPOSED FIX:
1. For {bottlenecks['slowest_node'] if bottlenecks else 'N/A'}: 
   - Implement caching for frequent queries
   - Optimize vector DB indexing
   - Consider async execution

2. For failure prevention:
   - Add retry logic with exponential backoff
   - Implement timeout handling
   - Add fallback responses for tool failures

3. Overall optimization:
   - Reduce context window size
   - Batch tool calls when possible
   - Use streaming responses for long operations
"""
    
    # Save analysis
    analysis_path = Path(__file__).resolve().parent.parent / "evaluation" / "bottleneck_analysis.txt"
    with open(analysis_path, 'w') as f:
        f.write(analysis_text)
    
    print(f"\n✅ Bottleneck analysis saved to: {analysis_path}")
    
    return bottlenecks, failures

if __name__ == "__main__":
    setup_langsmith()
    generate_trace_report()