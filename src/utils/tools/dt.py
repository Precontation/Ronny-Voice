from datetime import datetime, timezone

def get_datetime():
    utc_dt = datetime.now(timezone.utc) # UTC time
    dt = utc_dt.astimezone() # local time
    return f"It is {dt.ctime()} ({dt.tzinfo}). Only give the user the info they asked for."

tool_schema = {
  "type": "function",
  "function": {
    "name": "get_datetime",
    "description": "Get the current user's date and time based on their time zone.",
  }
}