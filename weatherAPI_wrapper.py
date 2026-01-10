import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

# Setup a session with caching and retry on error to improve speed of grabbing data
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Configures the parameters sent to API according to what is chosen in dashboard
def set_config(call_API=False, **kwargs):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": kwargs['latitude'],
        "longitude": kwargs['longitude'],
        "timezone": "auto",
        "wind_speed_unit": "mph",
    }
    
    if kwargs['daily']:
        params['daily'] = kwargs['daily']
        params['start_date'] = kwargs['date_start']
        params['end_date'] = kwargs['date_end']
    elif kwargs['hourly']:
        params['hourly'] = kwargs['hourly']
        params['start_hour'] = kwargs['datetime_start']
        params['end_hour'] = kwargs['datetime_end']
    else:
        params['current'] = kwargs['current']
    
    if call_API:
        # Get first location from API call
        response = (openmeteo.weather_api(url, params=params))[0]
        return response

# Process current data into DataFrame for graphs in dashboard
def get_current_data(response, choices):
    current = response.Current()
    data = {}
    
    # Creates a dictionary linking data to a suitable name for AI model to understand
    # 'choices' argument would be the options chosen on the dashboard
    for pos, data_name in enumerate(choices):
        data[data_name] = round(current.Variables(pos).Value(), 2)
    
    return pd.DataFrame(data, index=[0])

# Process hourly data into DataFrame for graphs in dashboard
def get_hourly_data(response, choices):
    hourly = response.Hourly()
    
    # Creates a Pandas DatetimeIndex for timed data
    data = {"Date": pd.date_range(
        start=pd.to_datetime(hourly.Time() + response.UtcOffsetSeconds(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd() + response.UtcOffsetSeconds(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    
    for pos, data_name in enumerate(choices):
        data[data_name] = hourly.Variables(pos).ValuesAsNumpy().round(2)
    
    return pd.DataFrame(data)

# Process daily data into DataFrame for graphs in dashboard
def get_daily_data(response, choices):
    daily = response.Daily()
    
    data = {"Date": pd.date_range(
        start=pd.to_datetime(daily.Time() + response.UtcOffsetSeconds(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd() + response.UtcOffsetSeconds(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )}
    
    # To account for the list nature of Precipitation Sum, I account for their pos and adjust the pos if it occurs in the choices list
    pos = 0
    for data_name in choices:
        if data_name == "Precipitation Sum":
            data['Rain Sum'] = daily.Variables(pos).ValuesAsNumpy().round(2)
            data['Showers Sum'] = daily.Variables(pos+1).ValuesAsNumpy().round(2)
            data['Snowfall Sum'] = daily.Variables(pos+2).ValuesAsNumpy().round(2)
            pos += 3
        else:
            data[data_name] = daily.Variables(pos).ValuesAsNumpy().round(2)
            pos += 1
    
    return pd.DataFrame(data)