import pyperclip

def get_clipboard() -> str:
    """Return the clipboard"""
    clipboard = pyperclip.paste()
    return clipboard

tool_schema = {
  "type": "function",
  "function": {
    "name": "get_clipboard",
    "description": "Get the user's clipboard, if available.",
  }
}

get_clipboard()