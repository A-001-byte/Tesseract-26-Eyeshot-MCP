import json
from orchestrator import execute_plan
from agents.planner import generate_plan
import audit_trail
from dotenv import load_dotenv

load_dotenv()

user_prompt = "Load the assembly file and show me properties of entity_1, then move entity_2 by 10 on the x axis"

print("=== PLANNER AGENT ===")
plan = generate_plan(user_prompt)
print(json.dumps(plan, indent=2))

print("\n=== EXECUTING PLAN ===")
final = execute_plan(plan, user_prompt=user_prompt)

print("\n=== FINAL RESULTS ===")
for r in final["results"]:
    print(r)

print("\n=== AUDIT TRAIL ===")
audit_trail.export_trail()