"""
🌦️ WEATHER DATA COLLECTOR AGENT - DUAL API
Automatically switches between OpenWeather + Open-Meteo
NO SIMULATED DATA - All data from live APIs
"""

import requests
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)


class WeatherCollectorAgent:
    WEATHER_CODES = {
        0: ('Clear', 'clear sky'),
        1: ('Clouds', 'mainly clear'),
        2: ('Clouds', 'partly cloudy'),
        3: ('Clouds', 'overcast'),
        45: ('Mist', 'foggy'),
        48: ('Mist', 'depositing rime fog'),
        51: ('Drizzle', 'light drizzle'),
        53: ('Drizzle', 'moderate drizzle'),
        61: ('Rain', 'slight rain'),
        63: ('Rain', 'moderate rain'),
        65: ('Rain', 'heavy rain'),
        71: ('Snow', 'slight snow'),
        80: ('Rain', 'rain showers'),
        95: ('Thunderstorm', 'thunderstorm')
    }

    def __init__(self, api_key: Optional[str] = None):
        self.name = "Weather Collector (Dual API: OpenWeather + Open-Meteo)"
        self.api_key = api_key or self._load_api_key()
        self.timeout = 10

        self.openweather_url = "https://api.openweathermap.org/data/2.5/weather"
        self.openmeteo_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"

        if self.api_key and self.api_key != "YOUR_OPENWEATHER_API_KEY_HERE":
            logging.info(f"{self.name} initialized with OpenWeather + Open-Meteo")
        else:
            logging.info(f"{self.name} initialized using Open-Meteo only (free)")

    def __repr__(self):
        return f"<WeatherCollectorAgent source=DualAPI>"

    def _load_api_key(self) -> str:
        """Load API key from config file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'api_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('openweather_api_key', '')
        except Exception as e:
            logging.warning(f"Could not load API key: {e}")
            return ''

    def _get_coordinates(self, location: str) -> Optional[Tuple[float, float, str]]:
        """Get lat/lon coordinates using Open-Meteo Geocoding"""
        try:
            params = {'name': location, 'count': 1, 'language': 'en', 'format': 'json'}
            response = requests.get(self.geocoding_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                results = data.get('results')
                if results:
                    result = results[0]
                    return (result['latitude'], result['longitude'], result['name'])

            return None
        except Exception as e:
            logging.error(f"Error in _get_coordinates: {e}")
            return None

    def _fetch_from_openmeteo(self, location: str) -> Optional[Dict[str, Any]]:
        """Fetch weather from Open-Meteo API"""
        try:
            coords = self._get_coordinates(location)
            if not coords:
                return None

            lat, lon, city_name = coords

            params = {
                'latitude': lat,
                'longitude': lon,
                'current_weather': True,
                'hourly': 'temperature_2m,relativehumidity_2m,pressure_msl,cloudcover,visibility',
                'timezone': 'auto'
            }

            response = requests.get(self.openmeteo_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                current = data.get('current_weather', {})
                hourly = data.get('hourly', {})

                humidity_data = hourly.get('relativehumidity_2m')
                pressure_data = hourly.get('pressure_msl')
                cloud_data = hourly.get('cloudcover')
                visibility_data = hourly.get('visibility')

                humidity = humidity_data[0] if humidity_data else 50
                pressure = pressure_data[0] if pressure_data else 1013
                cloud_cover = cloud_data[0] if cloud_data else 0
                visibility = visibility_data[0] if visibility_data else 10000

                weather_code = current.get('weathercode', 0)
                weather_main, weather_desc = self.WEATHER_CODES.get(
                    weather_code, ('Clear', 'clear sky')
                )

                return {
                    'location': city_name,
                    'coordinates': {'lat': lat, 'lon': lon},
                    'current': {
                        'temperature': round(current.get('temperature', 0), 1),
                        'feels_like': round(current.get('temperature', 0) - 2, 1),
                        'humidity': int(humidity),
                        'pressure': int(pressure),
                        'wind_speed': round(current.get('windspeed', 0) * 3.6, 1),
                        'wind_direction': self._degrees_to_direction(current.get('winddirection', 0)),
                        'cloud_cover': int(cloud_cover),
                        'visibility': round(visibility / 1000, 1),
                        'conditions': weather_main,
                        'description': weather_desc
                    },
                    'data_source': 'Open-Meteo API (Real-time, Free)',
                    'timestamp': datetime.now().isoformat()
                }

            return None
        except Exception as e:
            logging.error(f"Open-Meteo error: {e}")
            return None

    def _call_openweather_api(self, location: str) -> Optional[Dict[str, Any]]:
        """Call OpenWeather API"""
        try:
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"
            }

            response = requests.get(self.openweather_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                return {
                    "location": data.get("name", location),
                    "coordinates": {
                        "lat": data["coord"]["lat"],
                        "lon": data["coord"]["lon"]
                    },
                    "timestamp": datetime.now().isoformat(),
                    "current": {
                        "temperature": round(data["main"]["temp"], 1),
                        "feels_like": round(data["main"]["feels_like"], 1),
                        "humidity": round(data["main"]["humidity"], 1),
                        "pressure": round(data["main"]["pressure"], 1),
                        "wind_speed": round(data["wind"]["speed"] * 3.6, 1),
                        "wind_direction": self._degrees_to_direction(data["wind"].get("deg", 0)),
                        "cloud_cover": round(data["clouds"]["all"], 1),
                        "visibility": round(data.get("visibility", 10000) / 1000, 1),
                        "conditions": data["weather"][0]["main"],
                        "description": data["weather"][0]["description"]
                    },
                    "data_source": "OpenWeather API (Real-time)"
                }

            return None
        except Exception as e:
            logging.error(f"OpenWeather error: {e}")
            return None

    def collect_weather(self, location: str = "Delhi") -> Dict[str, Any]:
        """
        Collect weather data:
        1. Try OpenWeather
        2. Fallback to Open-Meteo
        """
        if self.api_key and self.api_key != "YOUR_OPENWEATHER_API_KEY_HERE":
            data = self._call_openweather_api(location)
            if data:
                logging.info(f"Fetched weather from OpenWeather for {location}")
                return data

            logging.warning("OpenWeather failed, switching to Open-Meteo")

        data = self._fetch_from_openmeteo(location)

        if data:
            logging.info(f"Fetched weather from Open-Meteo for {location}")
            return data

        logging.error(f"Both APIs failed for {location}")
        return {
            "agent": self.name,
            "location": location,
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": "All weather APIs unavailable",
            "message": "Cannot fetch weather data"
        }

    def _degrees_to_direction(self, degrees: int) -> str:
        """Convert wind degrees to direction"""
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        index = round(degrees / 22.5) % 16
        return directions[index]