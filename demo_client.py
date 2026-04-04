import json
import sys
import urllib.error
import urllib.request

CHAT_URL = "http://localhost:8000/api/v1/tools/chat"


class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


def color(text: str, c: str) -> str:
    return f"{c}{text}{Colors.RESET}"


def heading(title: str) -> None:
    print(color(f"\n--- {title} ---", Colors.CYAN))


def post_chat(prompt: str) -> dict:
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(
        CHAT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def result_summary(result: dict) -> str:
    if not isinstance(result, dict):
        return "No result returned"

    tool = result.get("tool", "unknown_tool")
    ok = result.get("ok", False)

    if tool == "load_and_count":
        load_data = ((result.get("data") or {}).get("load") or {}).get("data") or {}
        count_data = ((result.get("data") or {}).get("count") or {}).get("data") or {}
        load_message = load_data.get("message", "load step completed")
        total = (((count_data.get("data") or {}).get("totalEntities")))
        if total is None:
            total = "unknown"
        return f"Loaded model ({load_message}); total entities: {total}."

    if tool == "load_model":
        data = result.get("data") or {}
        return data.get("message", "Model load finished.")

    if tool == "get_entity_count":
        data = result.get("data") or {}
        total = ((data.get("data") or {}).get("totalEntities"))
        return f"Entity count: {total if total is not None else 'unknown'}."

    if tool == "list_entities":
        data = result.get("data") or {}
        entities = data.get("data") or []
        return f"Listed {len(entities)} entities."

    return f"Tool: {tool}, success: {ok}."


def print_output(prompt: str, response: dict) -> None:
    heading("USER PROMPT")
    print(prompt)

    heading("PARSED COMMAND")
    print(json.dumps(response.get("parsed_command", {}), indent=2))

    heading("EXECUTION STEPS")
    steps = response.get("steps", [])
    if not steps:
        print(color("No execution steps found.", Colors.YELLOW))
    else:
        for idx, step in enumerate(steps, start=1):
            print(color(f"* Step {idx}: {step}", Colors.YELLOW))

    heading("RESULT")
    result = response.get("result", {})
    ok = result.get("ok", False) if isinstance(result, dict) else False
    summary = result_summary(result)
    if ok:
        print(color(summary, Colors.GREEN))
    else:
        print(color(summary, Colors.RED))

    heading("AGENT INSIGHTS")
    agents = response.get("agents", {}) or {}
    print(f"Structural: {agents.get('structural', 'N/A')}")
    print(f"Cost: {agents.get('cost', 'N/A')}")
    print(f"Validation: {agents.get('validation', 'N/A')}")

    heading("AUDIT TRAIL")
    audit = response.get("audit", [])
    if not audit:
        print("1. No audit events found")
    else:
        for idx, item in enumerate(audit, start=1):
            print(f"{idx}. {item}")


def main() -> int:
    print(color("MCP CAD Demo Client", Colors.CYAN))
    prompt = input("Enter prompt: ").strip()

    if not prompt:
        print(color("Error: prompt cannot be empty.", Colors.RED))
        return 1

    try:
        response = post_chat(prompt)
        print_output(prompt, response)
        return 0
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8")
            detail = json.loads(raw)
        except Exception:
            detail = {"detail": str(e)}
        print(color("\nAPI request failed.", Colors.RED))
        print(f"Status: {e.code}")
        print(f"Detail: {json.dumps(detail, indent=2)}")
        return 1
    except urllib.error.URLError as e:
        print(color("\nCould not reach MCP server at http://localhost:8000/api/v1/tools/chat", Colors.RED))
        print(f"Reason: {e.reason}")
        return 1
    except json.JSONDecodeError:
        print(color("\nReceived invalid JSON response from server.", Colors.RED))
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 1
    except Exception as e:
        print(color("\nUnexpected error.", Colors.RED))
        print(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
