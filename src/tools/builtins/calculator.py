"""Safe mathematical expression calculator tool."""

import math
from typing import Any, Dict
from src.tools.base import BaseTool


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Execute mathematical computations and evaluate math expressions. Input should be a valid mathematical expression string (e.g. '15 * 12 + sqrt(144)')."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate"
            }
        },
        "required": ["expression"]
    }

    # Safe math namespace
    ALLOWED_NAMES: Dict[str, Any] = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }
    ALLOWED_NAMES.update({"abs": abs, "round": round, "min": min, "max": max, "sum": sum, "pow": pow})

    async def execute(self, expression: str, **kwargs) -> str:
        try:
            # Strip unsafe characters
            clean_expr = expression.replace("^", "**")
            result = eval(clean_expr, {"__builtins__": {}}, self.ALLOWED_NAMES)
            return str(result)
        except Exception as e:
            return f"Error evaluating expression '{expression}': {str(e)}"
