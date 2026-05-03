import json
import sys
from evaluation import run_evaluation

# Load thresholds from config
with open("eval_thresholds.json") as f:
    THRESHOLDS = json.load(f)

def main():
    results = run_evaluation()

    avg_faith = sum(r["faithfulness"] for r in results) / len(results)
    avg_rel = sum(r["relevancy"] for r in results) / len(results)

    passed = (
        avg_faith >= THRESHOLDS["faithfulness"]
        and avg_rel >= THRESHOLDS["relevancy"]
    )

    output = {
        "faithfulness": avg_faith,
        "relevancy": avg_rel,
        "thresholds": THRESHOLDS,
        "pass": passed
    }

    with open("eval_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(output, indent=2))

    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()