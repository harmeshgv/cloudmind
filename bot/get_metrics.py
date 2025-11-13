import requests
import json


# === Load JSON file ===
with open("agents.json", "r") as file:
    data = json.load(file)
print(data)

# === Create {agent_name: ip} mapping ===
AGENTS = {agent["name"]: agent["ip"] for agent in data["agents"]}


# === CORE FUNCTION ===
def fetch_agent_data(agent_name: str, data_type: str):
    results = {}

    # Pick which agents to query
    targets = (
        AGENTS if agent_name.lower() == "all" else {agent_name: AGENTS.get(agent_name)}
    )

    for name, ip in targets.items():
        if not ip:
            results[name] = {"error": "Unknown agent name"}
            continue

        agent_result = {}
        base_url = f"http://{ip}:8000"

        # Fetch metrics
        if data_type in ["metrics", "all"]:
            try:
                res = requests.get(f"{base_url}/metrics", timeout=5)
                res.raise_for_status()
                agent_result["metrics"] = res.json()
            except Exception as e:
                agent_result["metrics_error"] = str(e)

        # Fetch logs
        if data_type in ["logs", "all"]:
            try:
                res = requests.get(f"{base_url}/logs", timeout=5)
                res.raise_for_status()
                agent_result["logs"] = res.json()
            except Exception as e:
                agent_result["logs_error"] = str(e)

        if data_type in ["system-inventory", "all"]:
            try:
                res = requests.get(f"{base_url}/system-inventory", timeout=5)
                res.raise_for_status()
                agent_result["system-inventory"] = res.json()
            except Exception as e:
                agent_result["system-inventory_error"] = str(e)

        if data_type in ["security", "all"]:
            try:
                res = requests.get(f"{base_url}/security", timeout=5)
                res.raise_for_status()
                agent_result["security"] = res.json()
            except Exception as e:
                agent_result["security_error"] = str(e)

        results[name] = agent_result

    return results


# === MAIN ===
if __name__ == "__main__":
    agent_name = input("Enter agent name (agent1, agent2, or all): ").strip()
    data_type = input(
        "Enter data type (metrics, logs, system-inventory or all): "
    ).strip()

    print(f"\n🔍 Fetching '{data_type}' from '{agent_name}'...\n")

    data = fetch_agent_data(agent_name, data_type)

    print("📊 Results (JSON):")
    print(json.dumps(data, indent=2))
