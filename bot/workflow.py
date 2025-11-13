import json
from llm import set_llm
from get_metrics import fetch_agent_data
import logging


class CloudBotOrchestrator:
    """
    CloudBotOrchestrator:
    - Lets the LLM interpret the user query.
    - Dynamically decides which agent(s) and data type(s) to fetch.
    - Uses LLM again to produce a structured Markdown response
      (adaptive to any future data you add: metrics, logs, events, etc.).
    """

    def __init__(self, api_key, api_base, model):
        self.llm = set_llm(api_key, api_base, model)

    def decide_parameters(self, query: str):
        """Ask the LLM to determine which agent and data type to fetch."""
        instruction = f"""
        You are CloudBot's reasoning engine.
        Based on the following user query, decide what parameters should be passed
        to the function `fetch_agent_data(agent_name, data_type)`.

        Available agents: "cloudbot-agent-1", "cloudbot-agent-2", or "all"
        Data types: "metrics", "logs", "system-inventory" , "security" or "all"

        Respond **only** with a JSON object like this:
        {{
            "agent_name": "<agent name>",
            "data_type": "<data type>"
        }}

        User query: "{query}"
        """

        response = self.llm.invoke(instruction)

        try:
            params = json.loads(response.content)
            print(params)
            agent_name = params.get("agent_name", "all")
            data_type = params.get("data_type", "all")
        except Exception:
            logging.warning(
                "⚠️ LLM parameter parsing failed — defaulting to ('all', 'all')"
            )
            agent_name, data_type = "all", "all"

        return agent_name, data_type

    def handle_query(self, query: str):
        """
        Main orchestration logic:
        1. Use LLM to interpret what to fetch.
        2. Fetch data from target agent(s).
        3. Ask the LLM to generate a Markdown-formatted response that can include
           summaries, insights, or direct data formatting — without assuming
           specific metric names.
        """
        agent_name, data_type = self.decide_parameters(query)
        results = fetch_agent_data(agent_name, data_type)

        # Generalized markdown prompt (no assumptions about content)
        summary_prompt = f"""
        You are CloudBot, an intelligent DevOps and systems assistant.
        Analyze the following JSON data retrieved from agents.

        Your goals:
        - Present the information in a clean, structured **Markdown (.md)** format.
        - You may include bullet points, sections, or code blocks (```) as needed.
        - Highlight important findings, trends, errors, or insights.
        - Avoid making up data — summarize what’s available.
        - If applicable, categorize data by agent or data type.
        - Be adaptive: The content may include any type of information
          (metrics, logs, configurations, alerts, system info, etc.).
        - Do **not** explain what Markdown is — just output Markdown text directly.

        Data:
        {json.dumps(results, indent=2)}
        """

        summary = self.llm.invoke(summary_prompt).content
        return summary


# ---------- TESTING ----------
if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    api_base = os.getenv("GROQ_API_BASE")
    model = os.getenv("GROQ_MODEL")

    bot = CloudBotOrchestrator(api_key, api_base, model)
    output = bot.handle_query("Give me the latest updates from agent 1.")
    print(output)
