import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry
import geocoder

# Setup thing
g = geocoder.ipinfo('me')

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session) # pyright: ignore[reportArgumentType]

def get_weather_now():
  # Make sure all required weather variables are listed here
  # The order of variables in hourly or daily is important to assign them correctly below
  url = "https://api.open-meteo.com/v1/forecast"
  params = {
    "latitude": g.latlng[0],
    "longitude": g.latlng[1],
    "current": ["precipitation", "temperature_2m"],
    "temperature_unit": "fahrenheit",
  }
  responses = openmeteo.weather_api(url, params=params)

  # Process first location. Add a for-loop for multiple locations or weather models
  response = responses[0]

  # Process current data. The order of variables needs to be the same as requested.
  current = response.Current()
  
  if not current:
    return
  
  currentZero = current.Variables(0)
  currentOne = current.Variables(1)

  if not currentZero or not currentOne:
    return
  
  current_precipitation = currentZero.Value()
  current_temperature_2m = currentOne.Value()

  return f"Current time: {current.Time()}\nCurrent precipitation: {current_precipitation}\nCurrent temperature_2m: {current_temperature_2m}"

def get_weather_today():
  # Make sure all required weather variables are listed here
  # The order of variables in hourly or daily is important to assign them correctly below
  url = "https://api.open-meteo.com/v1/forecast"
  params = {
    "latitude": g.latlng[0],
    "longitude": g.latlng[1],
    "hourly": ["temperature_2m", "precipitation_probability"],
    "forecast_days": 1,
    "temperature_unit": "fahrenheit",
  }
  
  responses = openmeteo.weather_api(url, params=params)

  # Process first location. Add a for-loop for multiple locations or weather models
  response = responses[0]

  # Process hourly data. The order of variables needs to be the same as requested.
  hourly = response.Hourly()
  if not hourly:
    return

  hourlyZero = hourly.Variables(0)
  hourlyOne = hourly.Variables(1)

  if not hourlyZero or not hourlyOne:
    return
  
  hourly_temperature_2m = hourlyZero.ValuesAsNumpy()
  hourly_precipitation_probability = hourlyOne.ValuesAsNumpy()

  hourly_data = {"date": pd.date_range(
    start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    freq = pd.Timedelta(seconds = hourly.Interval()),
    inclusive = "left"
  )}

  hourly_data["temperature_2m"] = hourly_temperature_2m # pyright: ignore[reportArgumentType]
  hourly_data["precipitation_probability"] = hourly_precipitation_probability # pyright: ignore[reportArgumentType]

  hourly_dataframe = pd.DataFrame(data = hourly_data)
  return "Hourly data\n", hourly_dataframe

def get_weather_forecast():
  # Make sure all required weather variables are listed here
  # The order of variables in hourly or daily is important to assign them correctly below
  url = "https://api.open-meteo.com/v1/forecast"
  params = {
    "latitude": g.latlng[0],
    "longitude": g.latlng[1],
    "daily": ["temperature_2m_max", "temperature_2m_min"],
    "temperature_unit": "fahrenheit",
  }
  responses = openmeteo.weather_api(url, params=params)

  # Process first location. Add a for-loop for multiple locations or weather models
  response = responses[0]

  # Process daily data. The order of variables needs to be the same as requested.
  daily = response.Daily()
  if not daily:
    return
  
  dailyZero = daily.Variables(0)
  dailyOne = daily.Variables(1)

  if not dailyZero or not dailyOne:
    return
  
  daily_temperature_2m_max = dailyZero.ValuesAsNumpy()
  daily_temperature_2m_min = dailyOne.ValuesAsNumpy()

  daily_data = {"date": pd.date_range(
    start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
    end =  pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
    freq = pd.Timedelta(seconds = daily.Interval()),
    inclusive = "left"
  )}

  daily_data["temperature_2m_max"] = daily_temperature_2m_max # pyright: ignore[reportArgumentType]
  daily_data["temperature_2m_min"] = daily_temperature_2m_min # pyright: ignore[reportArgumentType]

  daily_dataframe = pd.DataFrame(data = daily_data)
  return "Daily data\n", daily_dataframe

now_tool_schema = {
  "type": "function",
  "function": {
    "name": "get_weather_now",
    "description": "Get the current weather at the exact moment, using the user's estimated location",
  }
}

today_tool_schema = {
  "type": "function",
  "function": {
    "name": "get_weather_today",
    "description": "Get the weather for the rest of the day, hourly, using the user's estimated location",
  }
}

forcast_tool_schema = {
  "type": "function",
  "function": {
    "name": "get_forcast",
    "description": "Get the next 7 days forcast, using the user's estimated location",
  }
}