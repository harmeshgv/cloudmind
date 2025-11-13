# app.py
import os
import json
import requests
from dotenv import load_dotenv
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="🤖 CloudBot AI", layout="centered")
load_dotenv()

# ---------- ENV VARIABLES (validate) ----------
api_key = os.getenv("GROQ_API_KEY") or ""
api_base = os.getenv("GROQ_API_BASE") or ""
model = os.getenv("GROQ_MODEL") or ""

if not api_key or not api_base or not model:
    st.warning(
        "GROQ API environment variables not fully set. "
        "Set GROQ_API_KEY, GROQ_API_BASE and GROQ_MODEL in your .env or environment."
    )

# ---------- AGENTS FILE ----------
AGENT_FILE = os.path.join("agents.json")


def load_agents():
    """Load agents.json safely and return list of agents."""
    if not os.path.exists(AGENT_FILE):
        return []
    try:
        with open(AGENT_FILE, "r") as f:
            data = json.load(f)
            return data.get("agents", [])
    except json.JSONDecodeError as e:
        st.sidebar.error(f"agents.json is invalid JSON: {e}")
        return []
    except Exception as e:
        st.sidebar.error(f"Failed to load agents.json: {e}")
        return []


# ---------- SESSION STATE ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# CloudBotOrchestrator instantiation: lazy import to avoid import-time issues
if "agent" not in st.session_state:
    try:
        from workflow import CloudBotOrchestrator

        # instantiate the orchestrator with API info (class should handle missing keys gracefully)
        st.session_state.agent = CloudBotOrchestrator(api_key, api_base, model)
    except Exception as e:
        # keep app usable even if orchestrator import fails
        st.session_state.agent = None
        st.sidebar.error(f"Could not create CloudBotOrchestrator: {e}")

agents = load_agents()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🌐 Connected Agents")

    # Refresh controls
    col1, col2 = st.columns([1, 1])
    with col1:
        refresh = st.button("🔄 Refresh Now")
    with col2:
        refresh_rate = st.selectbox(
            "Auto Refresh",
            options=[0, 2, 5, 10, 20, 40, 60],
            format_func=lambda x: "⏸️ Off" if x == 0 else f"{x}s",
            index=3,
        )

    if refresh_rate > 0:
        # refresh sidebar content periodically
        st_autorefresh(interval=refresh_rate * 1000, key="sidebar-refresh")
        st.caption(f"🔁 Auto-refreshing every **{refresh_rate}s**")

    if refresh:
        st.experimental_rerun()

    # Agents container
    agent_box = st.container()
    session = requests.Session()
    session.headers.update({"User-Agent": "CloudBot/1.0"})

    with agent_box:
        if not agents:
            st.warning("No agents found in agents.json")
        else:
            for agent in agents:
                name = agent.get("name", "unknown").capitalize()
                ip = agent.get("ip", "unknown")
                role = agent.get("role", "n/a")
                region = agent.get("region", "n/a")
                base_url = f"http://{ip}:8000"

                status = "🔴 Offline"
                cpu_percent = "N/A"
                memory_percent = "N/A"

                try:
                    # quick health check
                    res = session.get(base_url + "/", timeout=2)
                    if res.status_code == 200:
                        status = "🟢 Online"
                    else:
                        status = "🟡 Unreachable"

                    # metrics endpoint (optional)
                    metrics_res = session.get(base_url + "/metrics", timeout=3)
                    if metrics_res.ok:
                        metrics = metrics_res.json()
                        cpu_percent = metrics.get("cpu_percent", "N/A")
                        memory_percent = metrics.get("memory", {}).get("percent", "N/A")
                except requests.RequestException:
                    status = "🔴 Offline"
                except Exception:
                    status = "🔴 Offline"

                st.markdown(
                    f"""
                    <div style="font-family: monospace; font-size: 15px; line-height: 1.6; padding:6px">
                        <b>{name}</b> — {status}<br>
                        <span style="opacity:0.9">
                        IP: {ip}<br>
                        Role: {role}<br>
                        Region: {region}<br>
                        CPU: {cpu_percent} % | RAM: {memory_percent} %
                        </span>
                    </div>
                    <hr style="margin:4px 0; border:0.5px solid #ddd">
                    """,
                    unsafe_allow_html=True,
                )

# ---------- STYLES & HEADER ----------
st.markdown(
    """
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp {font-family: 'Inter', sans-serif;}
    .main-title {
        text-align: center;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: white;
        padding: 16px 0;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        margin-bottom: 10px;
    }
    .main-title h1 { font-size: 26px; margin-bottom: 6px; }
    .main-title p { font-size: 14px; opacity: 0.9; margin: 0; }
    .markdown-content { color: #e4e4e7; background: transparent; font-family: 'Inter', sans-serif; line-height: 1.7; }
    .markdown-content pre { background-color: rgba(255,255,255,0.05); border-radius:8px; padding:12px; overflow-x:auto; color:#e5e7eb; }
    </style>
    <div class="main-title">
        <h1>🤖 CloudBot AI Assistant</h1>
        <p>AI-powered system intelligence with Markdown-style reporting</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- INITIAL MESSAGE ----------
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "👋 **Hey, I’m CloudBot!**\n\nAsk me anything about your agents — metrics, logs, issues, or system state. I’ll generate a structured, Markdown-style summary."
        )

# ---------- DISPLAY CHAT HISTORY ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(
            f"<div class='markdown-content'>{msg['content']}</div>",
            unsafe_allow_html=True,
        )

# ---------- CHAT INPUT ----------
if prompt := st.chat_input("Ask CloudBot something..."):
    # persist user input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # handle the query using orchestrator if available
    with st.chat_message("assistant"):
        try:
            with st.spinner("💭 CloudBot is thinking..."):
                orchestrator = st.session_state.agent
                if orchestrator is None:
                    answer = "_⚠️ CloudBot backend not available (CloudBotOrchestrator not initialized)._"
                else:
                    # handle_query is expected to return a markdown string
                    answer = orchestrator.handle_query(prompt)
                    if not answer or len(answer.strip()) < 10:
                        answer = (
                            "_⚠️ Sorry, I couldn’t generate a proper Markdown response._"
                        )

        except Exception as e:
            answer = f"❌ **Error:** {e}"

        # Display & save assistant response
        st.markdown(
            f"<div class='markdown-content'>{answer}</div>", unsafe_allow_html=True
        )
        st.session_state.messages.append({"role": "assistant", "content": answer})
