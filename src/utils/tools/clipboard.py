import pyperclip

def get_clipboard() -> str:
    """Return the clipboard"""
    try:
      clipboard = pyperclip.paste()
      if (clipboard):
        return "Clipboard content: " + clipboard
      
      return "Clipboard either not available or is empty!";
    except:
      return "Clipboard either not available or is empty!";

tool_schema = {
  "type": "function",
  "function": {
    "name": "get_clipboard",
    "description": "Get the user's clipboard, if available.",
  }
}

get_clipboard()