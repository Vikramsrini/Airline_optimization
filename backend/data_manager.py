"""
Data management service for handling CSV uploads, validation, and storage.
Manages airport and route datasets for the optimization system.
"""

import pandas as pd
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from models import Route, Airport, DataValidationError, validate_route_data, validate_airport_data
import csv
import io

logger = logging.getLogger(__name__)

class DataManager:
    """Manages airline route and airport datasets."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.routes_file = os.path.join(data_dir, "routes.csv")
        self.airports_file = os.path.join(data_dir, "airports.csv")
        self.uploads_dir = os.path.join(data_dir, "uploads")
        
        # Create directories if they don't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.uploads_dir, exist_ok=True)
        
        # In-memory storage
        self.routes_cache = []
        self.airports_cache = []
        self.loaded = False
        
        # Load sample data if no existing data
        self._ensure_sample_data()
    
    def _ensure_sample_data(self):
        """Creates sample data if no existing datasets are found."""
        if not os.path.exists(self.routes_file) or not os.path.exists(self.airports_file):
            logger.info("Creating sample datasets...")
            self._create_sample_data()
    
    def _create_sample_data(self):
        """Creates comprehensive sample airline route data."""
        
        # Load sample data from JSON file
        sample_data_file = os.path.join(os.path.dirname(__file__), 'data', 'sample_data.json')
        
        try:
            with open(sample_data_file, 'r') as f:
                sample_data = json.load(f)
            
            sample_airports = sample_data['airports']
            airlines = sample_data['airlines']
        except FileNotFoundError:
            logger.warning(f"Sample data file not found: {sample_data_file}, using fallback data")
            # Fallback to minimal data if JSON file not found
            sample_airports = [
                {
                    "code": "JFK", "name": "John F. Kennedy International Airport",
                    "city": "New York", "country": "USA",
                    "latitude": 40.6413, "longitude": -73.7781,
                    "elevation": 13, "timezone": "America/New_York"
                },
                {
                    "code": "LAX", "name": "Los Angeles International Airport",
                    "city": "Los Angeles", "country": "USA",
                    "latitude": 33.9425, "longitude": -118.4081,
                    "elevation": 38, "timezone": "America/Los_Angeles"
                }
            ]
            airlines = ["American Airlines", "Delta Air Lines", "United Airlines"]
        
        # Save airports data
        airports_df = pd.DataFrame(sample_airports)
        airports_df.to_csv(self.airports_file, index=False)
        
        # Generate comprehensive route network
        sample_routes = []
        flight_id_counter = 1000
        
        # Major hub connections (hub-to-hub routes)
        major_hubs = ["JFK", "LAX", "ORD", "DFW", "LHR", "CDG", "FRA", "AMS", "NRT", "PEK", "SIN", "DXB"]
        
        for i, source in enumerate(major_hubs):
            for j, dest in enumerate(major_hubs):
                if i != j:
                    # Calculate approximate distance (simplified)
                    source_airport = next(a for a in sample_airports if a["code"] == source)
                    dest_airport = next(a for a in sample_airports if a["code"] == dest)
                    
                    # Simplified distance calculation
                    distance = self._calculate_approximate_distance(
                        source_airport["latitude"], source_airport["longitude"],
                        dest_airport["latitude"], dest_airport["longitude"]
                    )
                    
                    # Generate multiple flights per route
                    for flight_num in range(1, 4):  # 3 flights per route
                        sample_routes.append({
                            "flight_id": f"FL{flight_id_counter}",
                            "source_airport": source,
                            "destination_airport": dest,
                            "distance": round(distance, 1),
                            "duration": self._estimate_flight_duration(distance),
                            "aircraft_type": self._get_aircraft_type(distance),
                            "airline": self._get_random_airline()
                        })
                        flight_id_counter += 1
        
        # Regional connections (from hubs to smaller airports)
        regional_connections = [
            ("JFK", "SFO", 4150), ("LAX", "SFO", 540), ("ORD", "SFO", 2950),
            ("LHR", "CDG", 340), ("LHR", "FRA", 650), ("CDG", "AMS", 430),
            ("NRT", "PEK", 2100), ("PEK", "SIN", 4400), ("SIN", "DXB", 5800),
            ("DXB", "LHR", 5500), ("LAX", "SYD", 12200), ("GRU", "MIA", 6500)
        ]
        
        for source, dest, distance in regional_connections:
            if any(r["source_airport"] == source and r["destination_airport"] == dest for r in sample_routes):
                continue  # Skip if already exists
                
            sample_routes.append({
                "flight_id": f"FL{flight_id_counter}",
                "source_airport": source,
                "destination_airport": dest,
                "distance": distance,
                "duration": self._estimate_flight_duration(distance),
                "aircraft_type": self._get_aircraft_type(distance),
                "airline": self._get_random_airline()
            })
            flight_id_counter += 1
        
        # Save routes data
        routes_df = pd.DataFrame(sample_routes)
        routes_df.to_csv(self.routes_file, index=False)
        
        logger.info(f"Created sample dataset with {len(sample_airports)} airports and {len(sample_routes)} routes")
    
    def _calculate_approximate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Simplified distance calculation for sample data."""
        # Simplified equirectangular approximation
        from math import radians, cos, sqrt
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        x = (lon2 - lon1) * cos(0.5 * (lat1 + lat2))
        y = lat2 - lat1
        return 6371 * sqrt(x*x + y*y)
    
    def _estimate_flight_duration(self, distance: float) -> int:
        """Estimates flight duration based on distance."""
        # Average speed ~850 km/h for jets, ~600 km/h for turboprops
        if distance > 2000:
            duration_hours = distance / 850 + 0.5  # Add taxi time
        else:
            duration_hours = distance / 600 + 0.5
        
        return int(duration_hours * 60)  # Return minutes
    
    def _get_aircraft_type(self, distance: float) -> str:
        """Determines aircraft type based on route distance."""
        # Load aircraft types from JSON file if available
        sample_data_file = os.path.join(os.path.dirname(__file__), 'data', 'sample_data.json')
        
        try:
            with open(sample_data_file, 'r') as f:
                sample_data = json.load(f)
            aircraft_types = sample_data['aircraft_types']
            
            import random
            if distance > 5000:
                return random.choice(aircraft_types['long_haul'])
            elif distance > 3000:
                return random.choice(aircraft_types['medium_haul'])
            elif distance > 500:
                return random.choice(aircraft_types['short_haul'])
            else:
                return random.choice(aircraft_types['regional'])
        except (FileNotFoundError, KeyError):
            # Fallback to simple mapping
            if distance > 5000:
                return "Boeing 777"
            elif distance > 3000:
                return "Boeing 787"
            elif distance > 1500:
                return "Airbus A330"
            elif distance > 500:
                return "Boeing 737"
            else:
                return "ATR 72"
    
    def _get_random_airline(self) -> str:
        """Returns a random airline from major carriers."""
        # Load airlines from JSON file if available
        sample_data_file = os.path.join(os.path.dirname(__file__), 'data', 'sample_data.json')
        
        try:
            with open(sample_data_file, 'r') as f:
                sample_data = json.load(f)
            airlines = sample_data['airlines']
        except (FileNotFoundError, KeyError):
            airlines = [
                "American Airlines", "Delta Air Lines", "United Airlines", 
                "Lufthansa", "British Airways", "Air France", "KLM",
                "Singapore Airlines", "Emirates", "Qatar Airways"
            ]
        
        import random
        return random.choice(airlines)
    
    def load_data(self) -> bool:
        """Loads data from CSV files into memory."""
        try:
            # Load airports
            if os.path.exists(self.airports_file):
                airports_df = pd.read_csv(self.airports_file)
                self.airports_cache = airports_df.to_dict('records')
                logger.info(f"Loaded {len(self.airports_cache)} airports")
            
            # Load routes
            if os.path.exists(self.routes_file):
                routes_df = pd.read_csv(self.routes_file)
                self.routes_cache = routes_df.to_dict('records')
                logger.info(f"Loaded {len(self.routes_cache)} routes")
            
            self.loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False
    
    def get_airports(self) -> List[Dict[str, Any]]:
        """Returns all airports."""
        if not self.loaded:
            self.load_data()
        return self.airports_cache
    
    def get_routes(self) -> List[Dict[str, Any]]:
        """Returns all routes."""
        if not self.loaded:
            self.load_data()
        return self.routes_cache
    
    def get_airport_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Finds airport by IATA code."""
        airports = self.get_airports()
        return next((airport for airport in airports if airport['code'] == code.upper()), None)
    
    def get_routes_from_airport(self, airport_code: str) -> List[Dict[str, Any]]:
        """Gets all routes departing from specified airport."""
        routes = self.get_routes()
        return [route for route in routes if route['source_airport'] == airport_code.upper()]
    
    def get_routes_to_airport(self, airport_code: str) -> List[Dict[str, Any]]:
        """Gets all routes arriving at specified airport."""
        routes = self.get_routes()
        return [route for route in routes if route['destination_airport'] == airport_code.upper()]
    
    def validate_csv_data(self, file_content: str, data_type: str) -> Tuple[bool, List[str]]:
        """
        Validates uploaded CSV data.
        
        Args:
            file_content: CSV file content as string
            data_type: 'routes' or 'airports'
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(file_content))
            rows = list(csv_reader)
            
            if not rows:
                errors.append("CSV file is empty")
                return False, errors
            
            if data_type == 'routes':
                required_fields = ['flight_id', 'source_airport', 'destination_airport', 'distance']
                for field in required_fields:
                    if field not in csv_reader.fieldnames:
                        errors.append(f"Missing required field: {field}")
                
                # Validate each row
                for i, row in enumerate(rows):
                    try:
                        # Check required fields
                        for field in required_fields:
                            if not row.get(field):
                                errors.append(f"Row {i+1}: Missing {field}")
                        
                        # Validate distance
                        if row.get('distance'):
                            try:
                                distance = float(row['distance'])
                                if distance <= 0:
                                    errors.append(f"Row {i+1}: Invalid distance {distance}")
                            except ValueError:
                                errors.append(f"Row {i+1}: Distance must be a number")
                        
                        # Validate airport codes
                        if row.get('source_airport') and len(row['source_airport']) != 3:
                            errors.append(f"Row {i+1}: Invalid source airport code")
                        if row.get('destination_airport') and len(row['destination_airport']) != 3:
                            errors.append(f"Row {i+1}: Invalid destination airport code")
                            
                    except Exception as e:
                        errors.append(f"Row {i+1}: {str(e)}")
            
            elif data_type == 'airports':
                required_fields = ['code', 'name', 'city', 'country', 'latitude', 'longitude']
                for field in required_fields:
                    if field not in csv_reader.fieldnames:
                        errors.append(f"Missing required field: {field}")
                
                # Validate each row
                for i, row in enumerate(rows):
                    try:
                        # Check required fields
                        for field in required_fields:
                            if not row.get(field):
                                errors.append(f"Row {i+1}: Missing {field}")
                        
                        # Validate coordinates
                        if row.get('latitude'):
                            try:
                                lat = float(row['latitude'])
                                if not -90 <= lat <= 90:
                                    errors.append(f"Row {i+1}: Invalid latitude {lat}")
                            except ValueError:
                                errors.append(f"Row {i+1}: Latitude must be a number")
                        
                        if row.get('longitude'):
                            try:
                                lon = float(row['longitude'])
                                if not -180 <= lon <= 180:
                                    errors.append(f"Row {i+1}: Invalid longitude {lon}")
                            except ValueError:
                                errors.append(f"Row {i+1}: Longitude must be a number")
                        
                        # Validate airport code
                        if row.get('code') and len(row['code']) != 3:
                            errors.append(f"Row {i+1}: Invalid airport code")
                            
                    except Exception as e:
                        errors.append(f"Row {i+1}: {str(e)}")
            
            else:
                errors.append(f"Invalid data type: {data_type}")
                return False, errors
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Failed to parse CSV: {str(e)}")
            return False, errors
    
    def upload_csv_data(self, file_content: str, data_type: str, filename: str) -> Tuple[bool, str]:
        """
        Uploads and saves CSV data.
        
        Args:
            file_content: CSV file content as string
            data_type: 'routes' or 'airports'
            filename: Original filename
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate data
            is_valid, errors = self.validate_csv_data(file_content, data_type)
            if not is_valid:
                return False, f"Validation failed: {'; '.join(errors)}"
            
            # Save uploaded file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            uploaded_file = os.path.join(self.uploads_dir, f"{data_type}_{timestamp}_{filename}")
            
            with open(uploaded_file, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # Update main data file
            if data_type == 'routes':
                self.routes_file = uploaded_file
            elif data_type == 'airports':
                self.airports_file = uploaded_file
            
            # Reload data
            self.loaded = False
            self.load_data()
            
            return True, f"Successfully uploaded {data_type} data"
            
        except Exception as e:
            return False, f"Upload failed: {str(e)}"
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Returns summary statistics of loaded data."""
        if not self.loaded:
            self.load_data()
        
        return {
            'total_airports': len(self.airports_cache),
            'total_routes': len(self.routes_cache),
            'unique_source_airports': len(set(r['source_airport'] for r in self.routes_cache)),
            'unique_destination_airports': len(set(r['destination_airport'] for r in self.routes_cache)),
            'total_distance_km': sum(r['distance'] for r in self.routes_cache),
            'avg_route_distance': sum(r['distance'] for r in self.routes_cache) / len(self.routes_cache) if self.routes_cache else 0
        }
    
    def export_data(self, data_type: str, format: str = 'csv') -> Optional[str]:
        """
        Exports data in specified format.
        
        Args:
            data_type: 'routes' or 'airports'
            format: Export format ('csv', 'json')
            
        Returns:
            File path of exported data or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if data_type == 'routes':
                data = self.get_routes()
                filename = f"routes_export_{timestamp}.{format}"
            elif data_type == 'airports':
                data = self.get_airports()
                filename = f"airports_export_{timestamp}.{format}"
            else:
                return None
            
            filepath = os.path.join(self.data_dir, filename)
            
            if format == 'csv':
                df = pd.DataFrame(data)
                df.to_csv(filepath, index=False)
            elif format == 'json':
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                return None
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return None