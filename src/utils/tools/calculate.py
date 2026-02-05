import ast
import numexpr as ne

def calculate(expression: str) -> str:
    """Execute the calculation"""
    try:
        result =  ne.evaluate(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}. Please tell the user the error that occured exactly."

tool_schema = {
  "type": "function",
  "function": {
    "name": "calculate",
    "description": "Evaluate a mathematical expression using the numexpr framework",
    "parameters": {
      "type": "object",
      "properties": {
        "expression": {
          "type": "string",
          "description": "The mathematical expression to evaluate"
        }
      },
      "required": ["expression"]
    }
  }
}