import streamlit as st
import weatherAPI_wrapper as wAPI
import json
from os import name as os_name
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path
from groqAI_wrapper import AI
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Constants
MAIN_PROPORTION = 0.65
AI_PROPORTION = 0.35

HOURLY_CURRENT_OPTIONS = [
    "Temperature", "Relative Humidity", "Apparent Temperature", "Total Cloud Cover", 
    "Precipitation Probability", "Precipitation", "Wind Speed", "Wind Direction"
]

DAILY_OPTIONS = [
    "Max Temperature", "Min Temperature", "Max Apparent Temperature", 
    "Min Apparent Temperature", "Precipitation Sum", "Mean Wind Speed", "Dominant Wind Direction", 
    "Mean Precipitation Probability", "Mean Cloud Cover", "Mean Relative Humidity"
]

CITIES_FILE = 'cities500.json'
COUNTRIES_FILE = 'country_codes.json'
PARAM_FILE = 'param_mapping.json'

def configure_page():
    # Configure Streamlit page settings
    st.set_page_config(
        page_title="World Weather For Dummies",
        page_icon=":sun_behind_rain_cloud:",
        layout="wide"
    )

@st.cache_data(show_spinner="Caching cities for faster lookups...")
def load_cities():
    # Load cities data from JSON file into dictionary
    json_file = Path(__file__).parent / 'config' / CITIES_FILE
    with open(json_file, "r") as f:
        json_list = json.load(f)
    # Combines city name and country code for unique identification
    return {city["name"] + city["country"]: [city["lat"], city["lon"], city["name"]] for city in json_list}

@st.cache_data(show_spinner="Linking country codes to countries...")
def load_countries():
    # Load country codes from JSON file as dictionary object
    json_file = Path(__file__).parent / 'config' / COUNTRIES_FILE
    with open(json_file, "r") as f:
        return json.load(f)

@st.cache_data(show_spinner="Creating mappings...")
def load_mapping():
    # Load Weather API param mapping file into a dictionary
    json_file = Path(__file__).parent / 'config' / PARAM_FILE
    with open(json_file, "r") as f:
        return json.load(f)

def get_cities_for_country(cities, country_code):
    # Get list of cities for country selected
    return sorted([city_info[2] for key, city_info in cities.items() if key.endswith(country_code)])

def create_date_filters(graph_filter):
    # Create date/time input filters based on graph type and return values
    min_date = (date.today() - relativedelta(months=2)).replace(day=1)
    max_date = date.today() + relativedelta(days=15)

    if graph_filter == "Daily":
        date_start = st.date_input(
            "Filter by Start Date",
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY"
        )
        date_end = st.date_input(
            "Filter by End Date",
            min_value=date_start,
            max_value=max_date,
            format="DD/MM/YYYY"
        )
        return date_start.isoformat(), date_end.isoformat()
    elif graph_filter == "Hourly":
        datetime_start = st.datetime_input(
            "Filter by Start Date and Time",
            min_value=min_date,
            max_value=max_date,
            value=datetime.now().replace(minute=0, microsecond=0),
            step=3600,
            format="DD/MM/YYYY"
        )
        datetime_end = st.datetime_input(
            "Filter by End Date and Time",
            min_value=datetime_start,
            max_value=max_date,
            value=datetime_start+relativedelta(hours=1),
            step=3600,
            format="DD/MM/YYYY"
        )
        return datetime_start.isoformat(), datetime_end.isoformat()
    return None, None

def create_data_filters(graph_filter):
    # Create data selection filters based on graph type and return selected values
    if graph_filter in ("Current", "Hourly"):
        return st.multiselect(
            f"Filter for *{graph_filter}* data",
            HOURLY_CURRENT_OPTIONS,
            placeholder="No data chosen"
        ) or HOURLY_CURRENT_OPTIONS
    else:
        return st.multiselect(
            f"Filter for *Daily* data",
            DAILY_OPTIONS,
            placeholder="No data chosen"
        ) or DAILY_OPTIONS

def create_refresh_button():
    # Creates the refresh button in the sidebar
    # Separate function from create_sidebar() to maintain readability of returns and modularity
    with st.sidebar:
        refresh = st.button(
            "Refresh Graphs",
            help="Send the current choices picked by the filters to the Open-meteo API to refresh the data shown by the graphs",
            icon=":material/refresh:"
        )
    return refresh

def create_sidebar():
    # Create sidebar with filters and return all filter values
    with st.sidebar:
        # If all option unselected by user, use Current data
        graph_filter = st.segmented_control(
            "Filter by Graph Type",
            ["Current", "Hourly", "Daily"],
            default="Current"
        ) or "Current"

        date_start, date_end = create_date_filters(graph_filter)
        selected_data = create_data_filters(graph_filter)
        
    return graph_filter, date_start, date_end, selected_data

def get_city_data(city, country, cities, countries):
    if not city:
        return
        
    city_key = city + countries[country]

    chosen_city = cities[city_key]
    return chosen_city, country

def create_city_selection(cities, countries):
    # Create main dashboard content
    st.title(":orange[World Weather] For Dummies :nerd_face:")
    st.markdown(":grey[This dashboard provides graphs and data for your desired city via the *Open-Meteo* API and summarises the data through a *Groq* AI model]")
    st.divider()
    
    city_col, country_col = st.columns(2, gap="medium")
    
    with country_col:
        country = st.selectbox("Country", countries.keys())
    
    with city_col:
        available_cities = get_cities_for_country(cities, countries[country])
        city = st.selectbox(
            "City",
            available_cities,
            placeholder="Choose a city"
        )
    
    return get_city_data(city, country, cities, countries)

def display_city_graphs(dataframe, graph):
    if graph == "Current":
        display_current_graphs(dataframe)
    elif graph == "Hourly":
        display_hourly_graphs(dataframe)
    else: # Daily
        display_daily_graphs(dataframe)

def display_current_graphs(dataframe):
    # Get available columns
    available_cols = [col for col in dataframe.columns]
    
    # Create 4 columns for each row
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    
    # Second row columns
    col5, col6, col7, col8 = st.columns(4)
    cols.extend([col5, col6, col7, col8])
    
    # Display metrics for available columns only
    for i, col_name in enumerate(available_cols):
        with cols[i]:
            value = dataframe[col_name].iloc[0]
            
            # Add appropriate units
            if 'Temperature' in col_name:
                unit = '°C'
            elif 'Humidity' in col_name or 'Total Cloud Cover' in col_name or 'Precipitation Probability' in col_name:
                unit = '%'
            elif 'Wind Speed' in col_name:
                unit = 'mph'
            elif 'Wind Direction' in col_name:
                unit = '°'
            elif 'Precipitation' in col_name:
                unit = 'mm'
            else:
                unit = ''
            
            st.metric(col_name, f"{value}{unit}", border=True)

def display_hourly_graphs(dataframe):
    # Display hourly weather data as interactive graphs
    available_cols = [col for col in dataframe.columns if col != 'Date']
    
    # Temperature line graph - shows actual vs feels-like temperature over time
    if 'Temperature' in available_cols or 'Apparent Temperature' in available_cols:
        fig = go.Figure()
        # Add actual temperature line in blue
        if 'Temperature' in available_cols:
            fig.add_trace(go.Scatter(x=dataframe['Date'], y=dataframe['Temperature'], 
                                    mode='lines+markers', name='Temperature', line=dict(color='blue'),
                                    hovertemplate='<b>Temperature:</b> %{y}°C<br><b>Date:</b> %{x}<extra></extra>'))
        # Add apparent temperature line in orange
        if 'Apparent Temperature' in available_cols:
            fig.add_trace(go.Scatter(x=dataframe['Date'], y=dataframe['Apparent Temperature'], 
                                    mode='lines+markers', name='Apparent Temperature', line=dict(color='orange'),
                                    hovertemplate='<b>Apparent Temperature:</b> %{y}°C<br><b>Date:</b> %{x}<extra></extra>'))
        fig.update_layout(title='Temperature & Apparent Temperature', 
                        xaxis_title='Datetime', yaxis_title='Temperature (°C)')
        st.plotly_chart(fig)

    # Precipitation dual-axis bar chart - shows rainfall amount and probability side by side
    if 'Precipitation' in available_cols or 'Precipitation Probability' in available_cols:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        # Add precipitation amount bars (left y-axis)
        if 'Precipitation' in available_cols:
            fig.add_trace(go.Bar(x=dataframe['Date'], y=dataframe['Precipitation'], 
                                name='Precipitation', marker_color='blue',
                                offsetgroup=1,
                                hovertemplate='<b>Precipitation:</b> %{y}mm<br><b>Date:</b> %{x}<extra></extra>'), secondary_y=False)
        # Add precipitation probability bars (right y-axis)
        if 'Precipitation Probability' in available_cols:
            fig.add_trace(go.Bar(x=dataframe['Date'], y=dataframe['Precipitation Probability'], 
                                name='Precipitation Probability', marker_color='orange',
                                offsetgroup=2,
                                hovertemplate='<b>Precipitation Probability:</b> %{y}%<br><b>Date:</b> %{x}<extra></extra>'), secondary_y=True)
        # Configure y-axes with minimum values at 0
        fig.update_yaxes(title_text='Amount of Precipitation (mm)', minallowed=0, secondary_y=False)
        fig.update_yaxes(title_text='Precipitation Probability (%)', minallowed=0, maxallowed=100, secondary_y=True)
        fig.update_layout(title='Precipitation & Precipitation Probability', xaxis_title='Datetime')
        st.plotly_chart(fig)
    
    # Display side-by-side as legend doesn't take up unnecessary UI space
    col1, col2 = st.columns(2)
    
    with col1:
        # Wind Speed Line Graph with Wind Direction given at each point
        if 'Wind Speed' in available_cols:
            fig = go.Figure()
            hover_data = ['Wind Direction'] if 'Wind Direction' in available_cols else []
            fig.add_trace(go.Scatter(x=dataframe['Date'], y=dataframe['Wind Speed'], 
                                   mode='lines+markers', name='Wind Speed',
                                   customdata=dataframe[hover_data] if hover_data else None,
                                   hovertemplate='<b>Wind Speed:</b> %{y} mph<br><b>Date:</b> %{x}<br>' + 
                                               ('<b>Wind Direction:</b> %{customdata[0]:.2f}°<extra></extra>' if hover_data else '<extra></extra>')))
            fig.update_layout(title='Wind Speed & Wind Direction', 
                            xaxis_title='Datetime', yaxis_title='Wind Speed (mph)')
            fig.update_yaxes(minallowed=0)
            st.plotly_chart(fig)
    
    with col2:
        # Relative Humidity metrics with Datetime input
        if 'Relative Humidity' in available_cols:
            st.subheader('Relative Humidity')
            min_date = dataframe['Date'].min()
            max_date = dataframe['Date'].max()
            selected_date = st.datetime_input('Select Date/Time', 
                                            min_value=min_date,
                                            max_value=max_date,
                                            value=min_date,
                                            step=3600,
                                            format="DD/MM/YYYY",
                                            )
            # Convert to Pandas datetime to match DataFrame
            selected_date = pd.to_datetime(selected_date, utc=True)

            humidity_value = dataframe[dataframe['Date'] == selected_date]['Relative Humidity'].iloc[0]
            st.metric('Relative Humidity', f'{humidity_value}%')

    # Total Cloud Cover Line Graph
    if 'Total Cloud Cover' in available_cols:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dataframe['Date'], y=dataframe['Total Cloud Cover'], 
                    mode='lines+markers', name='Total Cloud Cover',
                    hovertemplate='<b>Cloud Cover:</b> %{y}%<br><b>Date:</b> %{x}<extra></extra>'))
        fig.update_layout(title='Total Cloud Cover', xaxis_title='Datetime', yaxis_title='Total Cloud Cover (%)')
        fig.update_yaxes(minallowed=0, maxallowed=100)
        st.plotly_chart(fig)


def display_daily_graphs(dataframe):
    available_cols = [col for col in dataframe.columns if col != 'Date']
    
    # Graph 1: Max/Min Temperature Chart
    if any(temp in available_cols for temp in ('Max Temperature', 'Min Temperature', 'Max Apparent Temperature', 'Min Apparent Temperature')):
        fig = go.Figure()
        zero_pad_removal = '-' if os_name == 'posix' else '#'

        temp_configs = [
            ('Max Temperature', 'Min Temperature', 'blue', 'Temperature', -1),
            ('Max Apparent Temperature', 'Min Apparent Temperature', 'orange', 'Apparent Temperature', 1)
        ]

        for max_col, min_col, colour, name, offset_hours in temp_configs:
            # Add markers for the max and min points
            if max_col in available_cols and min_col not in available_cols:
                fig.add_trace(go.Scatter(x=dataframe['Date'], y=dataframe[max_col], 
                                    mode='markers', name=max_col, marker=dict(color=colour),
                                    hovertemplate=f'<b>{max_col}:</b> %{{y:.2f}}°C<br><b>Date:</b> %{{x}}<extra></extra>'))
            
            elif min_col in available_cols and max_col not in available_cols:
                fig.add_trace(go.Scatter(x=dataframe['Date'], y=dataframe[min_col], 
                                    mode='markers', name=min_col, marker=dict(color=colour),
                                    hovertemplate=f'<b>{min_col}:</b> %{{y:.2f}}°C<br><b>Date:</b> %{{x}}<extra></extra>'))
            
            # Add Max/Min Temperature and Apparent Temperature lines
            elif max_col in available_cols and min_col in available_cols:
                # Using offset of time to trick scatter plot into displaying the data side-by-side
                offset = pd.Timedelta(hours=offset_hours)
                for i, date in enumerate(dataframe['Date']):
                    max_temp = dataframe[max_col].iloc[i]
                    min_temp = dataframe[min_col].iloc[i]
                    fig.add_trace(go.Scatter(x=[date+offset, date+offset], y=[min_temp, max_temp], 
                                        mode='lines+markers', name=name if i == 0 else None,
                                        line=dict(color=colour), showlegend=(i == 0),
                                        hovertemplate=f'<b>{max_col}:</b> {max_temp:.2f}°C<br><b>{min_col}:</b> {min_temp:.2f}°C<br><b>Date:</b> {date.strftime(f"%b %{zero_pad_removal}d, %Y")}<extra></extra>')) 

        # xaxis_tickformat doesn't require same os check as date.strftime as it uses d3 formatting
        # xaxis dtick is set to 86400000ms (1 day) to ensure that time offset is not visible on the graph
        fig.update_layout(title='Max/Min Temperatures', xaxis_title='Dates', yaxis_title='Temperature (°C)', xaxis_tickformat="%b %-d, %Y", xaxis=dict(dtick=86400000))
        st.plotly_chart(fig)
    
    # Display side-by-side as legend doesn't take up unnecessary UI space
    col1, col2 = st.columns(2)

    with col1:
        # Graph 2: Precipitation Pie Chart with date selector
        if any(precip in available_cols for precip in ('Rain Sum', 'Showers Sum', 'Snowfall Sum')):
            st.subheader('Sum of Precipitation')
            
            # Date selector
            min_date = dataframe['Date'].dt.date.min()
            max_date = dataframe['Date'].dt.date.max()
            selected_date = st.date_input('Select Date for Precipitation', 
                                        min_value=min_date, max_value=max_date, value=min_date, format="DD/MM/YYYY")
            
            # Filter data for selected date
            selected_row = dataframe[dataframe['Date'].dt.date == selected_date]
            if not selected_row.empty:
                rain = selected_row['Rain Sum'].iloc[0] if 'Rain Sum' in available_cols else 0
                showers = selected_row['Showers Sum'].iloc[0] if 'Showers Sum' in available_cols else 0
                snowfall = selected_row['Snowfall Sum'].iloc[0] if 'Snowfall Sum' in available_cols else 0
                
                # Create pie chart
                values = [rain, showers, snowfall]
                labels = ['Total Rainfall (mm)', 'Total Showers (mm)', 'Total Snowfall (cm)']
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3,
                                             hovertemplate='<b>%{label}</b><br>%{value:.2f}<br>%{percent}<extra></extra>')])
                fig.update_layout(title=f'Precipitation for {selected_date.strftime('%d/%m/%Y')}')
                st.plotly_chart(fig)
                
                # Total precipitation caption
                total = rain + showers + (snowfall/7)
                st.markdown(f'*Total Precipitation: {total:.2f}mm*')
    
    with col2:
        # Graph 3: Wind Speed and Direction Metrics
        if 'Mean Wind Speed' in available_cols or 'Dominant Wind Direction' in available_cols:
            st.subheader('Mean Wind Speed and Dominant Direction')
            
            # Date selector for wind data
            selected_wind_date = st.date_input('Select Date for Wind Data', 
                                             min_value=min_date, max_value=max_date, value=min_date, format="DD/MM/YYYY")
            
            selected_wind_row = dataframe[dataframe['Date'].dt.date == selected_wind_date]
            if not selected_wind_row.empty:
                wind_speed = selected_wind_row['Mean Wind Speed'].iloc[0] if 'Mean Wind Speed' in available_cols else None
                wind_direction = selected_wind_row['Dominant Wind Direction'].iloc[0] if 'Dominant Wind Direction' in available_cols else None
                
                col_a, col_b = st.columns(2)
                if wind_speed and wind_direction:
                    with col_a:
                        st.metric('Mean Wind Speed', f'{wind_speed:.2f} mph')
                    with col_b:
                        st.metric('Dominant Wind Direction', f'{wind_direction:.2f}°')
                elif wind_speed:
                    with col_a:
                        st.metric('Mean Wind Speed', f'{wind_speed:.2f} mph')
                else: # wind_direction
                    with col_a:
                        st.metric('Dominant Wind Direction', f'{wind_direction:.2f}°')
    
    # Graph 4: Mean Cloud Cover and Precipitation Probability
    if 'Mean Precipitation Probability' in available_cols or 'Mean Cloud Cover' in available_cols:
        fig = go.Figure()
        
        if 'Mean Precipitation Probability' in available_cols:
            fig.add_trace(go.Scatter(x=dataframe['Date'], y=dataframe['Mean Precipitation Probability'], 
                                    mode='lines+markers', name='Mean Precipitation Probability', line=dict(color='blue'),
                                    hovertemplate='<b>Precipitation Probability:</b> %{y}%<br><b>Date:</b> %{x}<extra></extra>'))
        
        if 'Mean Cloud Cover' in available_cols:
            fig.add_trace(go.Scatter(x=dataframe['Date'], y=dataframe['Mean Cloud Cover'], 
                                    mode='lines+markers', name='Mean Cloud Cover', line=dict(color='orange'),
                                    hovertemplate='<b>Cloud Cover:</b> %{y}%<br><b>Date:</b> %{x}<extra></extra>'))
        
        fig.update_layout(title='Mean Cloud Cover and Mean Precipitation Likelihood', 
                        xaxis_title='Dates', yaxis_title='%')
        fig.update_yaxes(minallowed=0, maxallowed=100)
        st.plotly_chart(fig)

    # Graph 5: Mean Relative Humidity
    if 'Mean Relative Humidity' in available_cols:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dataframe['Date'], y=dataframe['Mean Relative Humidity'], 
                                mode='lines+markers', name='Mean Relative Humidity',
                                hovertemplate='<b>Mean Relative Humidity:</b> %{y}%<br><b>Date:</b> %{x}<extra></extra>'))
        fig.update_layout(title='Mean Relative Humidity', 
                        xaxis_title='Dates', yaxis_title='Mean Relative Humidity (%)')
        fig.update_yaxes(minallowed=0, maxallowed=100)
        st.plotly_chart(fig)

def create_ai_panel(refresh, city, country, dataframe):
    # Create AI summary panel
    st.header("AI Summary :brain:")
    st.markdown(":grey[This summary panel is used to display the AI output after receiving the data given by the graphs]")
    st.markdown(":small[:grey[**NOTE:** The chat board will clear every 4 messages to avoid the page becoming too long and will NOT remember previous prompts]]")
    st.markdown(f":blue[:small[The model you are currently using is: _{AI.get_model()}_]]")
    st.divider()

    display_chat_boards(refresh, city, country, dataframe)

def display_chat_boards(refresh, city, country, dataframe):
    # Display the summary through chat messages (similar to that of ChatGPT)
    message_board = st.container()
    chat_board = st.container()

    check_disabled(refresh)

    # Display previous messages with st.session_state.chat
    with message_board:
        display_prev_messages()
    
    # Clarify details to user about the AI panel
    chat_board.markdown("**Why do you want to use this dashboard?**")
    chat_board.markdown("Please be as detailed as possible")
    chat_board.caption(":small[e.g. I want to see how the weather will affect my train journey at 8am on the Elizabeth Line from Romford to Liverpool Street to work]")
    chat_board.prompt = st.chat_input("Give AI context", disabled=st.session_state.disabled, on_submit=check_disabled, args=(refresh,))

    if chat_board.prompt:
        with message_board:
            with st.chat_message('user'):
                st.write(chat_board.prompt)
            st.session_state.chat.append({"role": "user", "content": chat_board.prompt})
            
            with st.chat_message('ai'):
                response = AI.call_API(message=chat_board.prompt,
                                       city=city,
                                       country=country,
                                       dataframe=dataframe)
                st.write(response)
            st.session_state.chat.append({"role": "ai", "content": response})

def check_disabled(*args):
    if args[0]:
        st.session_state.disabled = False
    else:
        st.session_state.disabled = True

def display_prev_messages():
    # Limit chat to 4 messages total to avoid page becoming too long
    if len(st.session_state.chat) >= 4:
        st.session_state.chat.clear()
    for message in st.session_state.chat:
        with st.chat_message(message["role"]):
            st.write(message["content"])

def get_weatherAPI_response(data, city, graph_type, mapping, start=None, end=None):
    lat, long = city[0], city[1]
    
    # Build weather parameters based on graph type
    if graph_type in ("Current", "Hourly"):
        weather_params = [mapping['hourly_current'][element] for element in data]
    else:  # Daily
        weather_params = []
        for element in data:
            daily_param = mapping['daily'][element]
            weather_params.extend(daily_param if isinstance(daily_param, list) else [daily_param])
    
    # Configure API call based on graph type
    config = {
        "latitude": lat,
        "longitude": long,
        "daily": None,
        "hourly": None,
        "current": None,
        "call_API": True
    }
    
    if graph_type == "Current":
        config["current"] = weather_params
    elif graph_type == "Hourly":
        config.update({
            "hourly": weather_params,
            "datetime_start": start,
            "datetime_end": end
        })
    else:  # Daily
        config.update({
            "daily": weather_params,
            "date_start": start,
            "date_end": end
        })
    
    # Unpacks the dictionary to corresponding parameters
    response = wAPI.set_config(**config)

    if graph_type == "Current":
        return wAPI.get_current_data(response, data), graph_type
    elif graph_type == "Hourly":
        return wAPI.get_hourly_data(response, data), graph_type
    else: # Daily
        return wAPI.get_daily_data(response, data), graph_type

def main():
    # Loads main functions to build the dashboard
    configure_page()
    
    if "disabled" not in st.session_state:
        st.session_state.disabled = True
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if "dataset" not in st.session_state:
        st.session_state.dataset = None
    if "graph" not in st.session_state:
        st.session_state.graph = None
    if "city" not in st.session_state:
        st.session_state.city = None
    if "country" not in st.session_state:
        st.session_state.country = None

    cities = load_cities()
    countries = load_countries()
    mapping = load_mapping()
    
    main_col, ai_col = st.columns([MAIN_PROPORTION, AI_PROPORTION], border=True)
    
    # Get values from sidebar
    graph_filter, start, end, selected_data = create_sidebar()
    refresh = create_refresh_button()
    
    with main_col:
        chosen_city, chosen_country = create_city_selection(cities, countries)
        
        # Only fetch new data when refresh is clicked and city is selected
        if refresh and chosen_city:
            st.session_state.city = chosen_city
            st.session_state.country = chosen_country

            st.session_state.dataset, st.session_state.graph = get_weatherAPI_response(
                data=selected_data,
                city=chosen_city,
                graph_type=graph_filter,
                mapping=mapping,
                start=start,
                end=end
            )
        
        # Display the cached dataset
        if st.session_state.dataset is not None:
            display_city_graphs(st.session_state.dataset, st.session_state.graph)
    
    with ai_col:
        create_ai_panel(refresh, st.session_state.city, st.session_state.country, st.session_state.dataset)
    
if __name__ == "__main__":
    main()