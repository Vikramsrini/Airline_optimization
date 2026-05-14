"""
Weather service integration for real-time weather data.
Provides weather information for airports and route optimization.
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from models import WeatherData, WeatherAPIError
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    """Service for fetching and managing weather data."""
    
    def __init__(self, api_key: str):
        # Use provided API key or fallback to environment variable
        self.api_key = api_key if api_key and api_key != 'demo_key' else "db0faf973e3bdf7b83ddb99e330e4914"
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.cache = {}
        self.cache_duration = 600  # 10 minutes
        
    def _get_cache_key(self, airport_code: str, lat: float, lon: float) -> str:
        """Generates a cache key for weather data."""
        return f"weather_{airport_code}_{lat}_{lon}"
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """Checks if cached data is still valid."""
        return time.time() - timestamp < self.cache_duration
    
    def get_weather_by_coordinates(self, airport_code: str, lat: float, lon: float) -> Optional[WeatherData]:
        """
        Fetches weather data for given coordinates.
        
        Args:
            airport_code: IATA airport code
            lat: Latitude
            lon: Longitude
            
        Returns:
            WeatherData object or None if fetch fails
        """
        cache_key = self._get_cache_key(airport_code, lat, lon)
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                logger.info(f"Using cached weather data for {airport_code}")
                return cached_data
        
        try:
            # Build API request
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'  # Get temperature in Celsius
            }
            
            logger.info(f"Fetching weather data for {airport_code} ({lat}, {lon})")
            response = requests.get(f"{self.base_url}/weather", params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse weather data
                weather_data = WeatherData(
                    airport_code=airport_code,
                    timestamp=datetime.fromtimestamp(data['dt']),
                    temperature=data['main']['temp'],
                    humidity=data['main']['humidity'],
                    wind_speed=data['wind']['speed'] * 3.6,  # Convert m/s to km/h
                    wind_direction=data['wind'].get('deg', 0),
                    visibility=data.get('visibility', 10000) / 1000,  # Convert to km
                    conditions=data['weather'][0]['main'].lower(),
                    precipitation=0.0,  # Will be updated if rain/snow data exists
                    pressure=data['main']['pressure']
                )
                
                # Add precipitation data if available
                if 'rain' in data:
                    weather_data.precipitation = data['rain'].get('1h', 0.0)
                elif 'snow' in data:
                    weather_data.precipitation = data['snow'].get('1h', 0.0)
                
                # Cache the result
                self.cache[cache_key] = (weather_data, time.time())
                
                logger.info(f"Successfully fetched weather for {airport_code}: {weather_data.conditions}")
                return weather_data
                
            elif response.status_code == 401:
                raise WeatherAPIError("Invalid weather API key")
            elif response.status_code == 429:
                raise WeatherAPIError("Weather API rate limit exceeded")
            else:
                raise WeatherAPIError(f"Weather API error: {response.status_code}")
                
        except requests.RequestException as e:
            logger.error(f"Network error fetching weather for {airport_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing weather data for {airport_code}: {e}")
            return None
    
    def get_weather_forecast(self, airport_code: str, lat: float, lon: float, hours: int = 24) -> Optional[List[WeatherData]]:
        """
        Gets weather forecast for the next specified hours.
        
        Args:
            airport_code: IATA airport code
            lat: Latitude
            lon: Longitude
            hours: Number of hours to forecast (default 24)
            
        Returns:
            List of WeatherData objects or None if fetch fails
        """
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': min(hours, 40)  # API limit
            }
            
            logger.info(f"Fetching weather forecast for {airport_code}")
            response = requests.get(f"{self.base_url}/forecast", params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                forecast = []
                
                for item in data['list']:
                    weather_data = WeatherData(
                        airport_code=airport_code,
                        timestamp=datetime.fromtimestamp(item['dt']),
                        temperature=item['main']['temp'],
                        humidity=item['main']['humidity'],
                        wind_speed=item['wind']['speed'] * 3.6,
                        wind_direction=item['wind'].get('deg', 0),
                        visibility=item.get('visibility', 10000) / 1000,
                        conditions=item['weather'][0]['main'].lower(),
                        pressure=item['main']['pressure']
                    )
                    
                    # Add precipitation data
                    if 'rain' in item:
                        weather_data.precipitation = item['rain'].get('3h', 0.0) / 3  # Convert to hourly
                    elif 'snow' in item:
                        weather_data.precipitation = item['snow'].get('3h', 0.0) / 3
                    
                    forecast.append(weather_data)
                
                return forecast
            else:
                logger.warning(f"Forecast API error for {airport_code}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching forecast for {airport_code}: {e}")
            return None
    
    def calculate_weather_impact(self, weather: WeatherData) -> float:
        """
        Calculates a weather impact score (0-100) where higher means worse conditions.
        
        Args:
            weather: WeatherData object
            
        Returns:
            Weather impact score
        """
        score = 0.0
        
        # Temperature impact (extreme temperatures are worse)
        if weather.temperature < -20 or weather.temperature > 40:
            score += 25
        elif weather.temperature < 0 or weather.temperature > 35:
            score += 15
        elif weather.temperature < 5 or weather.temperature > 30:
            score += 5
        
        # Wind impact
        if weather.wind_speed > 50:  # Very high winds
            score += 30
        elif weather.wind_speed > 30:  # High winds
            score += 20
        elif weather.wind_speed > 15:  # Moderate winds
            score += 10
        
        # Visibility impact
        if weather.visibility < 1:  # Very low visibility
            score += 25
        elif weather.visibility < 3:  # Low visibility
            score += 15
        elif weather.visibility < 5:  # Moderate visibility
            score += 5
        
        # Precipitation impact
        if weather.precipitation > 5:  # Heavy precipitation
            score += 20
        elif weather.precipitation > 2:  # Moderate precipitation
            score += 10
        elif weather.precipitation > 0:  # Light precipitation
            score += 5
        
        # Weather conditions impact
        condition_scores = {
            'thunderstorm': 30,
            'rain': 15,
            'snow': 20,
            'fog': 25,
            'clouds': 5,
            'clear': 0
        }
        
        score += condition_scores.get(weather.conditions, 10)
        
        # Ensure score is between 0 and 100
        return min(score, 100)
    
    def get_flight_conditions_summary(self, weather: WeatherData) -> str:
        """
        Provides a human-readable summary of flight conditions.
        
        Args:
            weather: WeatherData object
            
        Returns:
            Flight conditions summary
        """
        impact_score = self.calculate_weather_impact(weather)
        
        if impact_score >= 70:
            conditions = "Severe - Flight not recommended"
        elif impact_score >= 50:
            conditions = "Poor - Expect significant delays"
        elif impact_score >= 30:
            conditions = "Fair - Some delays possible"
        elif impact_score >= 10:
            conditions = "Good - Minor impacts possible"
        else:
            conditions = "Excellent - Ideal flight conditions"
        
        details = []
        if weather.wind_speed > 30:
            details.append(f"High winds ({weather.wind_speed:.1f} km/h)")
        if weather.visibility < 3:
            details.append(f"Low visibility ({weather.visibility:.1f} km)")
        if weather.precipitation > 2:
            details.append(f"Precipitation ({weather.precipitation:.1f} mm/h)")
        if abs(weather.temperature) > 35:
            details.append(f"Extreme temperature ({weather.temperature:.1f}°C)")
        
        summary = f"{conditions}"
        if details:
            summary += f" - {', '.join(details)}"
        
        return summary
    
    def clear_cache(self):
        """Clears the weather data cache."""
        self.cache.clear()
        logger.info("Weather data cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Returns cache statistics."""
        return {
            'cached_entries': len(self.cache),
            'cache_duration': self.cache_duration,
            'cache_keys': list(self.cache.keys())
        }