# **Cloudmind: AI-Driven Cloud Monitoring and Autonomous Configuration Framework**

CloudBot is an AI-assisted cloud orchestration framework that integrates FastAPI agents, Terraform-based provisioning, Ansible automation, and an LLM-powered orchestrator for intelligent cloud monitoring and autonomous configuration management. The system deploys lightweight CloudBot Agents across EC2 instances and enables natural-language interaction through a Streamlit interface.

---

## **1. Features**

* Distributed FastAPI agents for metrics, logs, inventory, and security insights
* Terraform-based provisioning of AWS EC2 agent nodes
* Automated configuration using Ansible playbooks
* LLM-powered CloudBot Orchestrator for intelligent query interpretation
* Streamlit conversational dashboard for monitoring and analysis
* Fully agent-driven architecture with real-time data retrieval

---

## **2. System Architecture**

CloudBot follows a multi-layered architecture:

1. **Infrastructure Layer**
   Terraform provision EC2 instances and networking resources.

2. **Configuration Layer**
   Ansible installs Python, FastAPI, dependencies, systemd services, and deploys CloudBot Agent.

3. **Agent Layer**
   FastAPI Agents expose endpoints:
   `/metrics`, `/logs`, `/system-inventory`, `/security`.

4. **Orchestration Layer**
   An LLM interprets user queries, selects agents, fetches data, and generates structured Markdown summaries.

5. **Interaction Layer**
   Streamlit dashboard provides conversational monitoring and data visualization.

---

## **3. Prerequisites**

Install the following:

* **Terraform** (≥ 1.3)
* **Ansible**
* **AWS CLI**
* **Python 3.10+**
* **pip / virtualenv**
* **SSH keypair** (`~/.ssh/id_rsa` and `~/.ssh/id_rsa.pub`)
* AWS account with programmatic IAM access

---

## **4. AWS Setup**

1. Configure AWS credentials locally:

   ```bash
   aws configure
   ```
2. Provide:

   * AWS Access Key ID
   * AWS Secret Access Key
   * Region (e.g., `us-east-1`)

---

## **5. Deployment Workflow**

### **Step 1: Clone the Repository**

```bash
git clone <repo-url>
cd <repo-folder>
```

---

### **Step 2: Provision Infrastructure (Terraform)**

Navigate to the Terraform directory:

```bash
cd terraform
terraform init
terraform validate
terraform plan
terraform apply
terraform output inventory > cloudmin/ansible/inventories/host.ini
```

Terraform will:

* Create SSH key pairs
* Create a security group
* Provision two EC2 instances
* Output their public IPs
* Generate dynamic Ansible inventory

---

### **Step 3: Deploy CloudBot Agents (Ansible)**

From the project root:

```bash
ansible-playbook -i inventories/hosts.ini deploy-agent.yml
```

Ansible will:

* Install Python, FastAPI, Uvicorn, Psutil
* Copy `app.py` to `/opt/agent/` on each instance
* Install a systemd service for continuous execution
* Start the CloudBot Agent on port **8000**

---

### **Step 4: Verify Agent Endpoints**

Use curl or browser:

```bash
curl http://<agent-ip>:8000/
curl http://<agent-ip>:8000/metrics
curl http://<agent-ip>:8000/system-inventory
curl http://<agent-ip>:8000/security
```

Each agent should return real-time system data.

---

### **Step 5: Start the CloudBot Orchestrator UI**

Install dependencies:

```bash
pip install -r requirements.txt
```

Set agents info file

```bash
python -m bot.discover_agents_from_api
```

Run Streamlit:

```bash
streamlit run app.py
```

The UI will:

* Load `agents.json`
* Allow natural-language queries
* Communicate with the LLM orchestrator
* Fetch metrics/logs from agents
* Render Markdown-based insights in real time

---

## **6. How the System Works**

1. User enters a query (e.g., *“Show CPU usage of both agents”*).
2. LLM interprets intent and determines which endpoints to query.
3. Orchestrator fetches data via FastAPI endpoints from distributed agents.
4. Results are aggregated and passed back to the LLM.
5. LLM generates a Markdown summary displayed in Streamlit.
6. Agents run continuously in the background using systemd.

---

## **7. Repository Structure**

```
/terraform           → Infrastructure (EC2, SG, keypairs)
/ansible             → Playbooks for deploying CloudBot agent
/agent_app           → FastAPI agent source code
/streamlit_ui        → CloudBot LLM-based orchestration UI
agents.json          → Discovered agent list
```

---

## **8. Technologies Used**

* **FastAPI** – Lightweight monitoring agents
* **Terraform** – Infrastructure as Code
* **Ansible** – Automated configuration management
* **Streamlit** – Conversational UI
* **LLM (OpenAI/Groq)** – Intelligent orchestration
* **AWS EC2** – Cloud execution environment
* **systemd** – Service management on agents

---

## **9. Future Enhancements**

* Automated remediation and self-healing operations
* Predictive analytics with ML anomaly detection
* Multi-cloud deployment (GCP, Azure)
* Kubernetes and container monitoring support
* Security event correlation and threat scoring

---

## **10. License**

MIT License (or your preferred license)


