import tomllib, requests
from pathlib import Path
from threading import Timer

class AI:
    # Protected class attributeswhat
    # This looks for the TOML file with the name provided in the cwd/config dir and opens it
    with (Path(__file__).parent / 'config' / 'groq_API_key.toml').open('rb') as f:
        _API_FILE = tomllib.load(f)
    
    # Constants of the class
    _DAILY_LIMIT_REACHED = "You have reached your daily rate limit of AI responses.\nFor more summaries, please return in 24 hours."
    _MIN_LIMIT_REACHED = "You have reached your minute rate limit of AI responses.\nFor more summaries, please wait 1 minute and then refresh."
    _UNRESOLVABLE_ISSUE = "Sorry! There are currently issues with the Groq API, and so a summary could not be provided."
    _MODEL_CHANGE = True
    _FALLBACK_MODEL = "llama-3.1-8b-instant"
    _NORMAL_MODEL = "llama-3.3-70b-versatile"
    _CURRENT_MODEL = _NORMAL_MODEL

    # Returns the current model in use so user can know what AI they're using
    @classmethod
    def get_model(cls):
        return cls._CURRENT_MODEL

    # Returns appropriate response after error-checking API response
    @staticmethod
    def get_response(response):
        if response.ok:
            return response.json()['output'][1]['content'][0]['text']
        elif response.status_code == 429:
            if any(error in response.json()['error']['message'] for error in ('(RPM)', '(TPM)')):
                if AI._CURRENT_MODEL == AI._NORMAL_MODEL:
                    AI._CURRENT_MODEL = AI._FALLBACK_MODEL
                    Timer(60, AI.reset_model).start()
                    return AI._MODEL_CHANGE
                else:
                    return AI._MIN_LIMIT_REACHED
            else:
                return AI._DAILY_LIMIT_REACHED
        else:
            return AI._UNRESOLVABLE_ISSUE

    # Method called on separate thread when requests per min (RPM) or token per min (TPM) are maxed for normal model
    @staticmethod
    def reset_model():
        AI._CURRENT_MODEL = AI._NORMAL_MODEL

    # Sends message to Groq API
    @staticmethod
    def call_API(message, city, country, dataframe):
        url = "https://api.groq.com/openai/v1/responses"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AI._API_FILE['GROQ_API_KEY']}"
        }
        # input is the message sent to the AI on behalf of the user
        # instructions are the prior details sent to the AI to set its tone for the user and what it needs to do
        json_data = {
            "model": AI._CURRENT_MODEL,
            "input": f'Country: {country}, City: {city}\nContext: {message}\nData:\n\n{dataframe.to_string()}',
            "instructions": "You are a weather forecast analyst that summarises data in Python Pandas DataFrames to the common person. This person will provide the data in the message (wind speed in mph and snowfall in cm) as well as the: city, country and context for their personalised summary. You should not ask any further questions and only provide a personalised summary with the data given."
        }

        response = requests.post(url, headers=headers, json=json_data)

        result = AI.get_response(response)
    
        # If model changed due to rate limits, retry with new model
        if result == AI._MODEL_CHANGE:
            json_data["model"] = AI._CURRENT_MODEL  # Update to fallback model
            response = requests.post(url, headers=headers, json=json_data)
            return AI.get_response(response)
        
        return result