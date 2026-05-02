import json

HIGH_RISK_TOOLS = ["fetch_paper_metadata"]

def request_human_approval(tool_name, tool_args):

    print("\n================ HUMAN APPROVAL REQUIRED ================")
    print(f"Tool: {tool_name}")
    print("Arguments:")
    print(json.dumps(tool_args, indent=2))
    print("==========================================================")

    print("Options:")
    print("1 Approve")
    print("2 Modify Arguments")
    print("3 Cancel")

    choice = input("Enter choice: ")

    if choice == "1":
        return tool_args

    if choice == "2":
        new_args = input("Enter new arguments as JSON: ")

        try:
            edited = json.loads(new_args)
            return edited
        except:
            print("Invalid JSON. Cancelling.")
            return None

    return None