from orchestrator import execute_plan
from agents.planner import generate_plan
import audit_trail
import os
from dotenv import load_dotenv

# Load from the parent directory's .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# Natural language input — this is what the user actually types
user_prompt = "Load the assembly file and show me properties of entity_1, then move entity_2 by 10 on the x axis"

print("=== GENERATING PLAN ===")
plan = generate_plan(user_prompt)
print(plan)

print("\n=== EXECUTING PLAN ===")
results = execute_plan(plan)
for r in results:
    print(r)

print("\n=== AUDIT TRAIL ===")
audit_trail.export_trail()