import json
from collections import Counter
from pathlib import Path

FEEDBACK_FILE = Path("feedback_log.json")

def analyze_feedback():

    if not FEEDBACK_FILE.exists():
        print("❌ feedback_log.json not found")
        return

    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    total_responses = len(logs)

    negative_feedback = [
        log for log in logs
        if log["feedback"].lower() == "bad"
    ]

    negative_count = len(negative_feedback)

    failed_queries = [
        log["user_input"]
        for log in negative_feedback
    ]

    top_failed = Counter(failed_queries).most_common(3)

    print("\n==============================")
    print("📊 FEEDBACK ANALYSIS REPORT")
    print("==============================")

    print(f"\nTotal Responses: {total_responses}")

    print(f"Negative Feedback Count: {negative_count}")

    print("\nTop 3 Failed Queries:")

    if top_failed:
        for idx, (query, count) in enumerate(top_failed, 1):
            print(f"{idx}. {query} ({count} times)")
    else:
        print("No failed queries found.")

if __name__ == "__main__":
    analyze_feedback()