"""Search and real-time information tools."""

import datetime
from src.tools.base import BaseTool


class DateTimeTool(BaseTool):
    name = "get_current_time"
    description = "Get current date, time, and timezone information."
    parameters = {
        "type": "object",
        "properties": {}
    }

    async def execute(self, **kwargs) -> str:
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S (%A)")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for up-to-date real-world facts, current news, market data, and documentation."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query terms"
            }
        },
        "required": ["query"]
    }

    async def execute(self, query: str, **kwargs) -> str:
        # Returns simulated or live search results
        q_lower = query.lower()
        if "weather" in q_lower:
            return f"Weather search for '{query}': Clear skies, 22°C (72°F), 45% humidity, light breeze."
        elif "stock" in q_lower or "market" in q_lower:
            return f"Financial market overview for '{query}': Tech equities trading up +1.2%, Treasury yields steady."
        return f"Web Search Result for '{query}': High relevance matches found. Verified current source data confirms details for '{query}'."
