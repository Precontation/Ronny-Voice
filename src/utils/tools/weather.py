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
    "current": ["temperature_2m", "precipitation", "rain", "weather_code"],
    "temperature_unit": "fahrenheit",
  }
  responses = openmeteo.weather_api(url, params=params)

  # Process first location. Add a for-loop for multiple locations or weather models
  response = responses[0]

  # Process current data. The order of variables needs to be the same as requested.
  current = response.Current()
  
  # Assign by index based on the list above
  temp = current.Variables(0).Value() # type: ignore
  precip = current.Variables(1).Value() # type: ignore
  rain = current.Variables(2).Value() # type: ignore
  code = current.Variables(3).Value() # type: ignore

  return (
    f"Temp: {temp}°F\n"
    f"Precipitation: {precip}mm\n"
    f"Rain: {rain}mm\n"
    f"WMO Code: {code}"
  )

def get_weather_today():
  # Make sure all required weather variables are listed here
  # The order of variables in hourly or daily is important to assign them correctly below
  url = "https://api.open-meteo.com/v1/forecast"
  params = {
    "latitude": g.latlng[0],
    "longitude": g.latlng[1],
    "hourly": ["temperature_2m", "precipitation", "rain", "weather_code"],
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

  hourlyTemperature = hourly.Variables(0)
  hourlyPrecipitation = hourly.Variables(1)
  hourlyRain = hourly.Variables(2)
  hourlyWeather = hourly.Variables(3)
  
  temp = hourlyTemperature.ValuesAsNumpy() # type: ignore
  precip = hourlyPrecipitation.ValuesAsNumpy() # type: ignore
  rain = hourlyRain.ValuesAsNumpy() # type: ignore
  code = hourlyWeather.ValuesAsNumpy() # type: ignore

  hourly_data = {"date": pd.date_range(
    start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    freq = pd.Timedelta(seconds = hourly.Interval()),
    inclusive = "left"
  )}

  hourly_data["temperature_2m"] = temp # type: ignore
  hourly_data["precipitation"] = precip # type: ignore
  hourly_data["rain"] = rain # type: ignore
  hourly_data["weather_code"] = code # type: ignore

  hourly_dataframe = pd.DataFrame(data = hourly_data)
  return "Hourly data\n", hourly_dataframe

def get_weather_forecast():
  # Make sure all required weather variables are listed here
  # The order of variables in hourly or daily is important to assign them correctly below
  url = "https://api.open-meteo.com/v1/forecast"
  params = {
    "latitude": g.latlng[0],
    "longitude": g.latlng[1],
    "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "rain_sum", "weather_code"],
    "temperature_unit": "fahrenheit",
  }
  responses = openmeteo.weather_api(url, params=params)

  # Process first location. Add a for-loop for multiple locations or weather models
  response = responses[0]

  # Process daily data. The order of variables needs to be the same as requested.
  daily = response.Daily()
  if not daily:
    return
  
  dailyTemperatureMin = daily.Variables(0)
  dailyTemperatureMax = daily.Variables(0)
  dailyPrecipitation = daily.Variables(1)
  dailyRain = daily.Variables(2)
  dailyWeather = daily.Variables(3)
  
  tempMin = dailyTemperatureMin.ValuesAsNumpy() # type: ignore
  tempMax = dailyTemperatureMax.ValuesAsNumpy() # type: ignore
  precip = dailyPrecipitation.ValuesAsNumpy() # type: ignore
  rain = dailyRain.ValuesAsNumpy() # type: ignore
  code = dailyWeather.ValuesAsNumpy() # type: ignore

  daily_data = {"date": pd.date_range(
    start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
    end =  pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
    freq = pd.Timedelta(seconds = daily.Interval()),
    inclusive = "left"
  )}

  daily_data["temperature_2m_min"] = tempMin # type: ignore
  daily_data["temperature_2m_max"] = tempMax # type: ignore
  daily_data["precipitation"] = precip # type: ignore
  daily_data["rain"] = rain # type: ignore
  daily_data["weather_code"] = code # type: ignore

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