from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import requests
import pandas as pd
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
from googletrans import Translator
from collections import defaultdict

# Load KCC dataset
kcc_df = pd.read_csv("cleaned_kcc_dataset.csv", encoding="ISO-8859-1")

# Preprocess dataset: Convert to lowercase and handle NaN values
kcc_df["QueryText"] = kcc_df["QueryText"].astype(str).str.lower().fillna("")
kcc_df["KccAns"] = kcc_df["KccAns"].astype(str).fillna("No information available.")

# TF-IDF Vectorizer for text similarity
vectorizer = TfidfVectorizer(ngram_range=(1, 3))
query_vectors = vectorizer.fit_transform(kcc_df["QueryText"])

translator = Translator()

def translate_to_telugu(text: str) -> str:
    try:
        translation = translator.translate(text, src='en', dest='te')
        return translation.text
    except Exception as e:
        return "(Translation unavailable) " + text


def find_best_match(user_query: str) -> str:
    user_vector = vectorizer.transform([user_query])
    similarities = cosine_similarity(user_vector, query_vectors)
    best_match_index = np.argmax(similarities)
    best_match_score = similarities[0, best_match_index]

    if best_match_score < 0.5:
        max_fuzz_score = 0
        best_fuzz_match = None
        for idx, text in enumerate(kcc_df["QueryText"]):
            fuzz_score = fuzz.partial_ratio(user_query, text)
            if fuzz_score > max_fuzz_score:
                max_fuzz_score = fuzz_score
                best_fuzz_match = idx

        if max_fuzz_score > 50:
            best_match_index = best_fuzz_match
        else:
            return "I'm sorry, I couldn't find an answer to your query. Please try rephrasing or contact the KCC helpline at 1800-180-1551."
    # Get the best answer
    answer = kcc_df.iloc[best_match_index]["KccAns"]
    # Check for vague or missing answers
    if not answer or answer.strip().lower() in ["given as per data", "n/a", "na", ""]:
        return "The answer to your query isn't available at the moment. Please contact the KCC helpline at 1800-180-1551 for more information."
    return answer

class ActionFetchAgricultureInfo(Action):
    def name(self) -> Text:
        return "action_fetch_agriculture_info"
    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_query = tracker.latest_message.get("text", "").lower().strip()
        if not user_query:
            dispatcher.utter_message(text="I couldn't understand your query. Please ask again.")
            return []
        answer = find_best_match(user_query)
        telugu_answer = translate_to_telugu(answer)
        dispatcher.utter_message(text=f"English: {answer}\nTelugu: {telugu_answer}")
        return []

class ActionFetchHorticultureInfo(Action):
    def name(self) -> Text:
        return "action_fetch_horticulture_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        crop = next(tracker.get_latest_entity_values("fruit"), None) or next(
            tracker.get_latest_entity_values("vegetable"), None)
        if not crop:
            dispatcher.utter_message(text="Please specify a fruit or vegetable for horticulture information.")
            return []
        crop = crop.lower()
        user_query = f"{crop} {tracker.latest_message.get('text').lower()}"
        answer = find_best_match(user_query)
        telugu_answer = translate_to_telugu(answer)
        dispatcher.utter_message(text=f"English: {answer}\nTelugu: {telugu_answer}")
        return []


class ActionFetchWeatherInfo(Action):
    def name(self) -> Text:
        return "action_fetch_weather_info"

    async def run(self, dispatcher: CollectingDispatcher, tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        location = next(tracker.get_latest_entity_values("location"), None)
        if not location:
            dispatcher.utter_message(text="Please provide a location to fetch weather information.")
            return []

        api_key = "777ec233b2d64a5790f54d794e8ec7f9"

        city_aliases = {
            "vizag": "visakhapatnam",
            "benares": "varanasi",
            "banglore": "bengaluru",
            "bombay": "mumbai",
            "madras": "chennai",
        }
        location = city_aliases.get(location.lower(), location)

        validation_url = f"https://api.openweathermap.org/data/2.5/weather?q={location},IN&appid={api_key}"
        validation_response = requests.get(validation_url).json()
        if validation_response.get("cod") != 200:
            dispatcher.utter_message(text="Sorry, I couldn't find that city. Please check the spelling and try again.")
            return []

        current_url = f"https://api.openweathermap.org/data/2.5/weather?q={location},IN&appid={api_key}&units=metric"
        current_response = requests.get(current_url).json()
        temp = current_response["main"]["temp"]
        weather_desc = current_response["weather"][0]["description"]
        message = f"🌡️ Current temperature in **{location}** is **{temp}°C** with **{weather_desc}**."

        lat = current_response["coord"]["lat"]
        lon = current_response["coord"]["lon"]

        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        forecast_response = requests.get(forecast_url).json()

        next_5_hours = []
        for forecast in forecast_response["list"][:5]:
            time = forecast["dt_txt"]
            temp = forecast["main"]["temp"]
            condition = forecast["weather"][0]["description"]
            next_5_hours.append(f"{time}: **{temp}°C**, {condition}")

        three_day_forecast = defaultdict(list)
        for forecast in forecast_response["list"]:
            date = forecast["dt_txt"].split(" ")[0]
            temp = forecast["main"]["temp"]
            three_day_forecast[date].append(temp)

        forecast_message = "\n📅 **Next 3 Days Forecast:**\n"
        for i, (date, temps) in enumerate(three_day_forecast.items()):
            if i == 3:
                break
            avg_temp = sum(temps) / len(temps)
            forecast_message += f"{date}: Avg Temp: **{avg_temp:.1f}°C**\n"

        rain_forecast = "🌧️ No rain expected in the next 7 days."
        for forecast in forecast_response["list"]:
            if "rain" in forecast:
                rain_time = forecast["dt_txt"]
                rain_forecast = f"🌧️ Rain expected on **{rain_time}**."
                break

        cloud_forecast = "☀️ Mostly clear skies."
        for forecast in forecast_response["list"]:
            if "clouds" in forecast["weather"][0]["description"]:
                cloud_forecast = f"☁️ Cloudy on **{forecast['dt_txt']}**."
                break

        message += f"\n📍 **Next 5 Hours Forecast:**\n" + "\n".join(next_5_hours)
        message += forecast_message
        message += f"\n{rain_forecast}\n{cloud_forecast}"

        # Translate to Telugu
        telugu_message = translate_to_telugu(message)

        # Final Output
        dispatcher.utter_message(text=f"**English:**\n{message}\n\n**Telugu:**\n{telugu_message}")
        return []

class ActionFetchCropRecommendation(Action):
    def name(self) -> Text:
        return "action_fetch_crop_recommendation"
    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_query = tracker.latest_message.get("text", "").strip().lower()
        if not user_query:
            dispatcher.utter_message(text="I couldn't understand your query. Please ask again.")
            return []
        answer = find_best_match(user_query)
        telugu_answer = translate_to_telugu(answer)
        dispatcher.utter_message(text=f"English: {answer}\nTelugu: {telugu_answer}")
        return []

class ActionFetchSoilRecommendation(Action):
    def name(self) -> Text:
        return "action_fetch_soil_recommendation"
    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_query = tracker.latest_message.get("text", "").strip().lower()
        if not user_query:
            dispatcher.utter_message(text="I couldn't understand your query. Please ask again.")
            return []
        answer = find_best_match(user_query)
        telugu_answer = translate_to_telugu(answer)
        dispatcher.utter_message(text=f"English: {answer}\nTelugu: {telugu_answer}")
        return []


class ActionFetchFertilizerRecommendation(Action):
    def name(self) -> Text:
        return "action_fetch_fertilizer_recommendation"
    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[
        Dict[Text, Any]]:
        crop = next(tracker.get_latest_entity_values("crop"), None) or \
               next(tracker.get_latest_entity_values("fruit"), None) or \
               next(tracker.get_latest_entity_values("vegetable"), None)
        if crop:
            crop = crop.lower()
            user_query = f"fertilizer recommendation for {crop}"
        else:
            user_query = tracker.latest_message.get("text", "").strip().lower()
        if not user_query:
            dispatcher.utter_message(text="I couldn't understand your query. Please ask again.")
            return []
        answer = find_best_match(user_query)
        telugu_answer = translate_to_telugu(answer)
        dispatcher.utter_message(text=f"English: {answer}\nTelugu: {telugu_answer}")
        return []


class ActionKccHelpline(Action):
    def name(self) -> Text:
        return "action_kcc_helpline"
    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = "I'm sorry, but I couldn't find relevant information for your query. If you need further assistance, please call the KCC Toll-Free Number: 1800-180-1551."
        dispatcher.utter_message(text=message)
        return []

class ActionOutOfScope(Action):
    def name(self) -> Text:
        return "action_out_of_scope"
    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = "I'm specialized in agriculture and weather-related topics. Please consult an appropriate source for other inquiries."
        dispatcher.utter_message(text=message)
        return []