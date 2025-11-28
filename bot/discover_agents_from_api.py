import requests
import json

# ===== CONFIG =====
AGENT_IPS = ["44.211.32.144", "3.239.82.168"]
PORT = 8000
TIMEOUT = 5  # seconds


def discover_agents(region: str = "us-east-1"):
    agents = []

    for i, ip in enumerate(AGENT_IPS, start=1):
        name = f"cloudbot-agent-{i}"
        base = f"http://{ip}:{PORT}"
        print(f"🔍 Discovering {name} ({ip})...")

        try:
            # Fetch system inventory (contains region + running services)
            resp = requests.get(f"{base}/system-inventory", timeout=TIMEOUT)
            resp.raise_for_status()
            inventory = resp.json()

            region = inventory.get("region", region)
            services = inventory.get("running_services", [])

            # Determine role from running services
            if any("prometheus" in s for s in services):
                role = "monitoring"
            elif any("docker" in s for s in services):
                role = "container"
            elif any("nginx" in s for s in services):
                role = "web"
            elif any("grafana" in s for s in services):
                role = "visualization"
            elif any("postgres" in s or "mysql" in s for s in services):
                role = "database"
            else:
                role = "generic"

            agents.append({"name": name, "ip": ip, "role": role, "region": region})

        except Exception as e:
            print(f"⚠️ Could not reach {ip}: {e}")
            agents.append(
                {"name": name, "ip": ip, "role": "unknown", "region": "unknown"}
            )

    # Save agents.json
    with open("bot/agents.json", "w") as f:
        json.dump({"agents": agents}, f, indent=2)

    print("\n✅ agents.json created successfully!\n")
    print(json.dumps({"agents": agents}, indent=2))


if __name__ == "__main__":
    discover_agents()
