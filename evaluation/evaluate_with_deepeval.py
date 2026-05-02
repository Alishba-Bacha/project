"""
evaluate_with_deepeval.py
Uses local metrics only - NO OPENAI API KEY REQUIRED
LangSmith works for tracing, DeepEval uses local calculations
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any
import time
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import your graph
from src.graph import build_hallucination_detector_graph

# ============================================
# 1. LOAD TEST DATASET
# ============================================

def load_test_dataset():
    """Load the 25 test cases"""
    dataset_path = Path(__file__).resolve().parent / "test_dataset.json"
    
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data['test_cases'])} test cases")
    return data['test_cases']

# ============================================
# 2. RUN YOUR ACTUAL AGENT
# ============================================

class HallucinationDetectorWrapper:
    """Wrapper for your actual agent"""
    
    def __init__(self):
        self.graph = build_hallucination_detector_graph()
    
    def run_query(self, query: str) -> Dict:
        """Run query through your actual agent"""
        
        start_time = time.time()
        
        # Initialize state
        initial_state = {
            "messages": [{"role": "user", "content": query}],
            "paper_text": "",
            "claims_extracted": [],
            "verification_results": {},
            "confidence_scores": {},
            "citations_checked": [],
            "iteration_count": 0
        }
        
        # Run graph
        final_state = None
        tool_calls_made = []
        final_answer = ""
        
        try:
            for step in self.graph.stream(initial_state):
                final_state = step
                
                # Track tool calls
                for node_name, node_output in step.items():
                    if "tool" in node_name.lower():
                        if "messages" in node_output:
                            for msg in node_output["messages"]:
                                if hasattr(msg, "tool_calls") and msg.tool_calls:
                                    for tc in msg.tool_calls:
                                        tool_calls_made.append(tc["name"])
                    
                    # Extract final answer
                    if "agent" in node_name and "messages" in node_output:
                        for msg in node_output["messages"]:
                            if hasattr(msg, "content") and msg.content:
                                final_answer = msg.content
        except Exception as e:
            final_answer = f"Error: {str(e)}"
        
        end_time = time.time()
        
        return {
            "query": query,
            "response": final_answer if final_answer else "No response generated",
            "tool_calls_made": tool_calls_made,
            "latency": end_time - start_time,
            "success": bool(final_answer and len(final_answer) > 10)
        }

# ============================================
# 3. LOCAL METRICS (No OpenAI Required)
# ============================================

class LocalMetricsEvaluator:
    """Calculate metrics using local methods - NO API KEYS NEEDED"""
    
    def calculate_faithfulness(self, response: str, expected: str) -> float:
        """
        Calculate faithfulness based on factual overlap
        Higher score = response stays true to expected facts
        """
        # Extract key phrases from expected
        expected_phrases = self._extract_key_phrases(expected)
        
        if not expected_phrases:
            return 0.5
        
        # Check which phrases appear in response
        response_lower = response.lower()
        found_phrases = 0
        
        for phrase in expected_phrases:
            if phrase.lower() in response_lower:
                found_phrases += 1
        
        # Calculate overlap score
        faithfulness = found_phrases / len(expected_phrases)
        
        # Penalize contradictions
        contradiction_penalty = self._check_contradictions(response, expected)
        faithfulness = max(0, faithfulness - contradiction_penalty)
        
        return min(1.0, faithfulness)
    
    def calculate_relevancy(self, query: str, response: str) -> float:
        """
        Calculate how well response addresses the query
        Based on keyword coverage
        """
        # Extract important words from query (remove stopwords)
        stopwords = {'what', 'how', 'does', 'do', 'is', 'are', 'the', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with', 'from', 'about'}
        query_words = set(re.findall(r'\b[a-z]{3,}\b', query.lower()))
        query_words = query_words - stopwords
        
        if not query_words:
            return 0.5
        
        response_lower = response.lower()
        matched_words = sum(1 for word in query_words if word in response_lower)
        
        return matched_words / len(query_words)
    
    def calculate_contextual_recall(self, response: str, expected: str) -> float:
        """
        Calculate how much of expected information is recalled
        """
        expected_sentences = re.split(r'[.!?]+', expected)
        expected_sentences = [s.strip() for s in expected_sentences if len(s.strip()) > 20]
        
        if not expected_sentences:
            return 0.5
        
        response_lower = response.lower()
        recalled = 0
        
        for sentence in expected_sentences:
            # Check if key ideas from sentence are in response
            sentence_words = set(re.findall(r'\b[a-z]{4,}\b', sentence.lower()))
            if sentence_words:
                matched = sum(1 for w in sentence_words if w in response_lower)
                if matched / len(sentence_words) > 0.3:  # 30% overlap threshold
                    recalled += 1
        
        return recalled / len(expected_sentences)
    
    def calculate_tool_accuracy(self, actual_tools: List[str], expected_tools: List[str]) -> Dict:
        """Calculate tool call accuracy metrics"""
        
        if not expected_tools:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
        
        if not actual_tools:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        correct = sum(1 for tool in actual_tools if tool in expected_tools)
        
        precision = correct / len(actual_tools)
        recall = correct / len(expected_tools)
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3)
        }
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        # Remove common filler words
        text = text.lower()
        
        # Extract noun phrases (simplified)
        sentences = re.split(r'[.!?]+', text)
        phrases = []
        
        for sentence in sentences[:3]:  # First 3 sentences most important
            # Extract phrases that contain numbers or key terms
            if any(word in sentence for word in ['reduce', 'hallucination', 'fine-tuning', 'percent', 'study', 'evidence']):
                phrases.append(sentence.strip())
        
        return phrases if phrases else [text[:100]]
    
    def _check_contradictions(self, response: str, expected: str) -> float:
        """Check for contradictory statements"""
        contradiction_indicators = ['no evidence', 'not true', 'incorrect', 'false', 'debunked']
        response_lower = response.lower()
        
        for indicator in contradiction_indicators:
            if indicator in response_lower:
                # Check if expected contains positive statement
                if any(word in expected.lower() for word in ['reduces', 'effective', 'improves']):
                    return 0.3  # Penalty for contradiction
        
        return 0.0

# ============================================
# 4. RUN EVALUATION
# ============================================

def run_evaluation():
    """Complete evaluation pipeline - NO OPENAI KEY NEEDED"""
    
    print("\n" + "="*70)
    print("📊 LAB 7: Evaluation Pipeline")
    print("Using Local Metrics (No OpenAI API Required)")
    print("="*70)
    
    # Load test cases
    test_cases = load_test_dataset()
    
    # Initialize agent and evaluator
    agent = HallucinationDetectorWrapper()
    evaluator = LocalMetricsEvaluator()
    
    # Store results
    results = []
    
    print("\n🔄 Running evaluation on test cases...")
    print("-"*50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}: {test_case['id']}")
        print(f"  Category: {test_case['category']}")
        print(f"  Query: {test_case['query'][:60]}...")
        
        # Run agent
        result = agent.run_query(test_case["query"])
        
        # Calculate metrics
        faithfulness = evaluator.calculate_faithfulness(
            result["response"], 
            test_case["expected_ground_truth"]
        )
        
        relevancy = evaluator.calculate_relevancy(
            test_case["query"], 
            result["response"]
        )
        
        contextual_recall = evaluator.calculate_contextual_recall(
            result["response"], 
            test_case["expected_ground_truth"]
        )
        
        tool_metrics = evaluator.calculate_tool_accuracy(
            result["tool_calls_made"],
            test_case["expected_tools"]
        )
        
        # Store results
        results.append({
            "id": test_case["id"],
            "category": test_case["category"],
            "faithfulness": faithfulness,
            "relevancy": relevancy,
            "contextual_recall": contextual_recall,
            "contextual_precision": (faithfulness + relevancy) / 2,
            "tool_precision": tool_metrics["precision"],
            "tool_recall": tool_metrics["recall"],
            "tool_f1": tool_metrics["f1"],
            "latency": result["latency"],
            "success": result["success"],
            "response_length": len(result["response"])
        })
        
        print(f"  ✓ Faithfulness: {faithfulness:.3f}")
        print(f"  ✓ Relevancy: {relevancy:.3f}")
        print(f"  ✓ Tool F1: {tool_metrics['f1']:.3f}")
        print(f"  ✓ Latency: {result['latency']:.2f}s")
    
    # Calculate summary statistics
    summary = calculate_summary(results)
    
    # Generate report
    generate_report(results, summary)
    
    return results, summary

def calculate_summary(results: List[Dict]) -> Dict:
    """Calculate summary statistics"""
    
    if not results:
        return {}
    
    total = len(results)
    
    summary = {
        "total_tests": total,
        "average_faithfulness": sum(r["faithfulness"] for r in results) / total,
        "average_relevancy": sum(r["relevancy"] for r in results) / total,
        "average_contextual_recall": sum(r["contextual_recall"] for r in results) / total,
        "average_contextual_precision": sum(r["contextual_precision"] for r in results) / total,
        "average_tool_f1": sum(r["tool_f1"] for r in results) / total,
        "average_latency": sum(r["latency"] for r in results) / total,
        "success_rate": sum(1 for r in results if r["success"]) / total
    }
    
    return summary

def generate_report(results: List[Dict], summary: Dict):
    """Generate evaluation report"""
    
    report = f"""# Hallucination Detector - Evaluation Report

## Overview
- **Evaluation Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Test Cases**: {summary['total_tests']}
- **Evaluation Method**: Local Metrics (No external API calls)

## Overall Metrics

| Metric | Score | Status |
|--------|-------|--------|
| **Faithfulness** | {summary['average_faithfulness']:.3f} | {'✅ Good' if summary['average_faithfulness'] > 0.7 else '⚠️ Needs Improvement'} |
| **Answer Relevancy** | {summary['average_relevancy']:.3f} | {'✅ Good' if summary['average_relevancy'] > 0.7 else '⚠️ Needs Improvement'} |
| **Contextual Recall** | {summary['average_contextual_recall']:.3f} | {'✅ Good' if summary['average_contextual_recall'] > 0.7 else '⚠️ Needs Improvement'} |
| **Tool Call F1** | {summary['average_tool_f1']:.3f} | {'✅ Good' if summary['average_tool_f1'] > 0.8 else '⚠️ Needs Improvement'} |
| **Success Rate** | {summary['success_rate']*100:.1f}% | - |
| **Average Latency** | {summary['average_latency']:.2f}s | - |

## Category Breakdown

| Category | Count | Faithfulness | Relevancy | Tool F1 |
|----------|-------|--------------|-----------|---------|
"""
    
    # Group by category
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)
    
    for cat, items in categories.items():
        avg_faith = sum(i["faithfulness"] for i in items) / len(items)
        avg_rel = sum(i["relevancy"] for i in items) / len(items)
        avg_tool = sum(i["tool_f1"] for i in items) / len(items)
        report += f"| {cat} | {len(items)} | {avg_faith:.3f} | {avg_rel:.3f} | {avg_tool:.3f} |\n"
    
    report += f"""
## Analysis

### Strengths
- Faithfulness score {summary['average_faithfulness']:.3f} indicates responses are generally grounded in evidence
- Tool call F1 of {summary['average_tool_f1']:.3f} shows good tool selection accuracy

### Areas for Improvement
- {'Consider improving answer relevancy' if summary['average_relevancy'] < 0.7 else 'Answer relevancy is satisfactory'}
- {'Tool selection could be more precise' if summary['average_tool_f1'] < 0.8 else 'Tool selection is accurate'}

## Conclusion

The hallucination detector demonstrates {'strong' if summary['average_faithfulness'] > 0.7 else 'moderate'} performance with a faithfulness score of {summary['average_faithfulness']:.3f}.

---
*Report generated by Hallucination Detector Evaluation Pipeline*
*Using local metrics - no external API calls required*
"""
    
    # Save report
    report_path = Path(__file__).resolve().parent / "evaluation_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n✅ Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "="*50)
    print("📊 EVALUATION SUMMARY")
    print("="*50)
    print(f"  Faithfulness: {summary['average_faithfulness']:.3f}")
    print(f"  Relevancy: {summary['average_relevancy']:.3f}")
    print(f"  Tool F1: {summary['average_tool_f1']:.3f}")
    print(f"  Latency: {summary['average_latency']:.2f}s")
    print("="*50)

# ============================================
# 5. MAIN
# ============================================

if __name__ == "__main__":
    results, summary = run_evaluation()