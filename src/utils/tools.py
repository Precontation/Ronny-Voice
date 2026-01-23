import json

def calculate(expression: str) -> str:
    """Execute the calculation"""
    try:
        result = eval(expression)  # Use safe evaluation in production
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# Map function names to implementations
available_functions = {
    "calculate": calculate,
    # Add more tools here as you build them
    # "get_weather": get_weather,
    # "search_database": search_database,
}

def execute_tool_call(tool_call):
    """Parse and execute a single tool call"""
    function_name = tool_call.function.name
    function_to_call = available_functions[function_name]
    function_args = json.loads(tool_call.function.arguments)
    
    # Call the function with unpacked arguments
    return function_to_call(**function_args)