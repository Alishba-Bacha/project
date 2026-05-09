import json
from collections import Counter

LOG_FILE = "feedback_log.json"


def analyze_feedback():
    with open(LOG_FILE, "r") as f:
        data = json.load(f)

    total = len(data)

    negative = [
        item for item in data
        if item["feedback"].lower() == "bad"
    ]

    negative_count = len(negative)

    failed_queries = [
        item["user_input"]
        for item in negative
    ]

    top_failed = Counter(failed_queries).most_common(3)

    print("=" * 50)
    print("FEEDBACK ANALYSIS")
    print("=" * 50)

    print(f"Total Responses: {total}")
    print(f"Negative Feedback Count: {negative_count}")

    print("\nTop 3 Failed Queries:")

    for query, count in top_failed:
        print(f"- {query} ({count} times)")


if __name__ == "__main__":
    analyze_feedback()