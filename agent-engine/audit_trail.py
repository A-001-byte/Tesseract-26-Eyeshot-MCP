import json
import datetime

audit_log = []

def log(agent: str, action: str, input_data: dict, output_data: dict, status: str = "ok"):
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "agent": agent,
        "action": action,
        "input": input_data,
        "output": output_data,
        "status": status
    }
    audit_log.append(entry)
    print(f"[AUDIT] {entry['timestamp']} | {agent} | {action} | {status}")

def get_trail():
    return audit_log

def export_trail(path="audit_trail.json"):
    with open(path, "w") as f:
        json.dump(audit_log, f, indent=2)