"""
Data models and schemas for the Airline Route Optimization application.
Defines data structures for airports, routes, weather data, and API responses.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

@dataclass
class Airport:
    """Represents an airport with its properties."""
    code: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    elevation: Optional[int] = None
    timezone: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'name': self.name,
            'city': self.city,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'elevation': self.elevation,
            'timezone': self.timezone
        }

@dataclass
class Route:
    """Represents a flight route between two airports."""
    flight_id: str
    source_airport: str
    destination_airport: str
    distance: float  # in kilometers
    duration: Optional[int] = None  # in minutes
    aircraft_type: Optional[str] = None
    airline: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'flight_id': self.flight_id,
            'source_airport': self.source_airport,
            'destination_airport': self.destination_airport,
            'distance': self.distance,
            'duration': self.duration,
            'aircraft_type': self.aircraft_type,
            'airline': self.airline
        }

@dataclass
class WeatherData:
    """Represents weather information for an airport."""
    airport_code: str
    timestamp: datetime
    temperature: float  # Celsius
    humidity: int  # Percentage
    wind_speed: float  # km/h
    wind_direction: int  # degrees
    visibility: float  # km
    conditions: str  # e.g., 'clear', 'cloudy', 'rain', 'storm'
    precipitation: float = 0.0  # mm/h
    pressure: float = 1013.25  # hPa
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'airport_code': self.airport_code,
            'timestamp': self.timestamp.isoformat(),
            'temperature': self.temperature,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'visibility': self.visibility,
            'conditions': self.conditions,
            'precipitation': self.precipitation,
            'pressure': self.pressure
        }

@dataclass
class OptimizedRoute:
    """Represents an optimized route with weather considerations."""
    route: Route
    weather_impact_score: float  # 0-100, lower is better
    total_score: float  # Combined optimization score
    waypoints: List[Dict[str, float]] = field(default_factory=list)
    weather_alerts: List[str] = field(default_factory=list)
    estimated_fuel_consumption: Optional[float] = None
    estimated_cost: Optional[float] = None
    alternative_routes: List['OptimizedRoute'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'route': self.route.to_dict(),
            'weather_impact_score': self.weather_impact_score,
            'total_score': self.total_score,
            'waypoints': self.waypoints,
            'weather_alerts': self.weather_alerts,
            'estimated_fuel_consumption': self.estimated_fuel_consumption,
            'estimated_cost': self.estimated_cost,
            'alternative_routes': [route.to_dict() for route in self.alternative_routes]
        }

@dataclass
class SparkJobStatus:
    """Represents the status of a Spark processing job."""
    job_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    start_time: datetime
    end_time: Optional[datetime] = None
    progress: float = 0.0  # 0-100
    description: str = ""
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'status': self.status,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'progress': self.progress,
            'description': self.description,
            'error_message': self.error_message
        }

@dataclass
class APIResponse:
    """Standard API response format."""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'errors': self.errors,
            'metadata': self.metadata
        }

class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

class WeatherAPIError(Exception):
    """Custom exception for weather API errors."""
    pass

class SparkProcessingError(Exception):
    """Custom exception for Spark processing errors."""
    pass

def validate_airport_data(data: Dict[str, Any]) -> Airport:
    """Validates and creates an Airport object from raw data."""
    required_fields = ['code', 'name', 'city', 'country', 'latitude', 'longitude']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            raise DataValidationError(f"Missing required airport field: {field}")
    
    # Validate coordinates
    if not (-90 <= data['latitude'] <= 90):
        raise DataValidationError(f"Invalid latitude: {data['latitude']}")
    if not (-180 <= data['longitude'] <= 180):
        raise DataValidationError(f"Invalid longitude: {data['longitude']}")
    
    return Airport(**data)

def validate_route_data(data: Dict[str, Any]) -> Route:
    """Validates and creates a Route object from raw data."""
    required_fields = ['flight_id', 'source_airport', 'destination_airport', 'distance']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            raise DataValidationError(f"Missing required route field: {field}")
    
    # Validate distance
    if data['distance'] < 0:
        raise DataValidationError(f"Invalid distance: {data['distance']}")
    
    return Route(**data)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great circle distance between two points using the Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r