import json
from datetime import datetime
from pathlib import Path

LOG_FILE = "feedback_log.json"


def log_interaction(user_input, agent_response, feedback):
    entry = {
        "timestamp": str(datetime.now()),
        "user_input": user_input,
        "agent_response": agent_response,
        "feedback": feedback
    }

    log_path = Path(LOG_FILE)

    # Create file if not exists
    if not log_path.exists():
        with open(log_path, "w") as f:
            json.dump([], f)

    # Load existing logs
    with open(log_path, "r") as f:
        data = json.load(f)

    data.append(entry)

    # Save updated logs
    with open(log_path, "w") as f:
        json.dump(data, f, indent=2)

    print("✅ Feedback logged successfully")