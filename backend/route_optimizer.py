"""
Route optimization algorithms with weather consideration.
Implements various optimization strategies for airline route planning.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from models import Route, Airport, WeatherData, OptimizedRoute
from geopy.distance import geodesic

logger = logging.getLogger(__name__)

class RouteOptimizer:
    """Advanced route optimization with weather and efficiency considerations."""
    
    def __init__(self):
        self.route_graph = nx.DiGraph()
        self.airport_coords = {}
        self.weather_data = {}
        self.optimization_cache = {}
        
    def load_data(self, routes: List[Dict[str, Any]], airports: List[Dict[str, Any]]):
        """
        Loads route and airport data into the optimizer.
        
        Args:
            routes: List of route dictionaries
            airports: List of airport dictionaries
        """
        logger.info("Loading data into route optimizer...")
        
        # Build airport coordinate lookup
        self.airport_coords = {}
        for airport in airports:
            self.airport_coords[airport['code']] = (airport['latitude'], airport['longitude'])
        
        # Build route graph
        self.route_graph.clear()
        
        for route in routes:
            source = route['source_airport']
            dest = route['destination_airport']
            
            # Calculate edge weight based on distance and other factors
            weight = self._calculate_base_weight(route)
            
            self.route_graph.add_edge(
                source, dest,
                flight_id=route['flight_id'],
                distance=route['distance'],
                duration=route.get('duration', 0),
                aircraft_type=route.get('aircraft_type', ''),
                airline=route.get('airline', ''),
                weight=weight
            )
        
        logger.info(f"Loaded {len(airports)} airports and {len(routes)} routes into optimizer")
    
    def update_weather_data(self, weather_data: Dict[str, WeatherData]):
        """
        Updates weather data for optimization.
        
        Args:
            weather_data: Dictionary of weather data by airport code
        """
        self.weather_data = weather_data
        logger.info(f"Updated weather data for {len(weather_data)} airports")
        
        # Clear cache since weather affects optimization
        self.optimization_cache.clear()
    
    def find_optimal_routes(self, source: str, destination: str, 
                          max_stops: int = 2, 
                          weather_weight: float = 0.3,
                          time_preference: str = 'balanced') -> List[OptimizedRoute]:
        """
        Finds optimal routes between source and destination airports.
        
        Args:
            source: Source airport code
            destination: Destination airport code
            max_stops: Maximum number of stops allowed
            weather_weight: Weight given to weather factors (0-1)
            time_preference: 'fastest', 'shortest', or 'balanced'
            
        Returns:
            List of optimized route objects
        """
        source = source.upper()
        destination = destination.upper()
        
        # Check cache first
        cache_key = f"{source}_{destination}_{max_stops}_{weather_weight}_{time_preference}"
        if cache_key in self.optimization_cache:
            logger.info(f"Using cached optimization results for {source} -> {destination}")
            return self.optimization_cache[cache_key]
        
        logger.info(f"Finding optimal routes from {source} to {destination}")
        
        try:
            optimized_routes = []
            
            # Find direct routes
            direct_routes = self._find_direct_routes(source, destination)
            optimized_routes.extend(direct_routes)
            
            # Find one-stop routes if no direct routes or if we want alternatives
            if max_stops >= 1 and len(optimized_routes) < 3:
                one_stop_routes = self._find_one_stop_routes(source, destination, weather_weight)
                optimized_routes.extend(one_stop_routes)
            
            # Find two-stop routes if needed
            if max_stops >= 2 and len(optimized_routes) < 5:
                two_stop_routes = self._find_two_stop_routes(source, destination, weather_weight)
                optimized_routes.extend(two_stop_routes)
            
            # Apply weather optimization
            if self.weather_data:
                optimized_routes = self._apply_weather_optimization(optimized_routes, weather_weight)
            
            # Sort by total score (lower is better)
            optimized_routes.sort(key=lambda x: x.total_score)
            
            # Limit results
            optimized_routes = optimized_routes[:10]
            
            # Cache results
            self.optimization_cache[cache_key] = optimized_routes
            
            logger.info(f"Found {len(optimized_routes)} optimal routes")
            return optimized_routes
            
        except Exception as e:
            logger.error(f"Route optimization failed: {e}")
            return []
    
    def _find_direct_routes(self, source: str, destination: str) -> List[OptimizedRoute]:
        """Finds direct routes between source and destination."""
        routes = []
        
        if self.route_graph.has_edge(source, destination):
            edge_data = self.route_graph[source][destination]
            
            route = Route(
                flight_id=edge_data['flight_id'],
                source_airport=source,
                destination_airport=destination,
                distance=edge_data['distance'],
                duration=edge_data['duration'],
                aircraft_type=edge_data['aircraft_type'],
                airline=edge_data['airline']
            )
            
            # Calculate waypoints (great circle path)
            waypoints = self._generate_waypoints(source, destination)
            
            optimized_route = OptimizedRoute(
                route=route,
                weather_impact_score=0,  # Will be updated later
                total_score=edge_data['weight'],
                waypoints=waypoints,
                estimated_fuel_consumption=self._estimate_fuel_consumption(edge_data['distance']),
                estimated_cost=self._estimate_cost(edge_data['distance'], edge_data['duration'])
            )
            
            routes.append(optimized_route)
        
        return routes
    
    def _find_one_stop_routes(self, source: str, destination: str, weather_weight: float) -> List[OptimizedRoute]:
        """Finds one-stop routes between source and destination."""
        routes = []
        
        # Find all possible intermediate airports
        for intermediate in self.route_graph.nodes():
            if (intermediate != source and intermediate != destination and
                self.route_graph.has_edge(source, intermediate) and
                self.route_graph.has_edge(intermediate, destination)):
                
                first_leg = self.route_graph[source][intermediate]
                second_leg = self.route_graph[intermediate][destination]
                
                total_distance = first_leg['distance'] + second_leg['distance']
                total_duration = first_leg['duration'] + second_leg['duration']
                
                # Create a composite route
                route = Route(
                    flight_id=f"{first_leg['flight_id']}+{second_leg['flight_id']}",
                    source_airport=source,
                    destination_airport=destination,
                    distance=total_distance,
                    duration=total_duration,
                    aircraft_type=f"{first_leg['aircraft_type']}+{second_leg['aircraft_type']}",
                    airline=f"{first_leg['airline']}+{second_leg['airline']}"
                )
                
                # Generate waypoints for both legs
                waypoints = self._generate_waypoints(source, intermediate)
                waypoints.extend(self._generate_waypoints(intermediate, destination)[1:])
                
                optimized_route = OptimizedRoute(
                    route=route,
                    weather_impact_score=0,  # Will be updated later
                    total_score=first_leg['weight'] + second_leg['weight'],
                    waypoints=waypoints,
                    estimated_fuel_consumption=self._estimate_fuel_consumption(total_distance),
                    estimated_cost=self._estimate_cost(total_distance, total_duration)
                )
                
                routes.append(optimized_route)
        
        return routes
    
    def _find_two_stop_routes(self, source: str, destination: str, weather_weight: float) -> List[OptimizedRoute]:
        """Finds two-stop routes using shortest path algorithm."""
        routes = []
        
        try:
            # Use NetworkX shortest path algorithm
            paths = list(nx.all_simple_paths(
                self.route_graph, source, destination, cutoff=3  # Max 3 edges (2 stops)
            ))
            
            for path in paths:
                if len(path) == 3:  # Two stops
                    stop1, stop2 = path[1], path[2]
                    
                    # Build route chain
                    total_distance = 0
                    total_duration = 0
                    total_weight = 0
                    flight_ids = []
                    aircraft_types = []
                    airlines = []
                    waypoints = []
                    
                    current = source
                    for next_airport in path[1:]:
                        edge_data = self.route_graph[current][next_airport]
                        total_distance += edge_data['distance']
                        total_duration += edge_data['duration']
                        total_weight += edge_data['weight']
                        flight_ids.append(edge_data['flight_id'])
                        aircraft_types.append(edge_data['aircraft_type'])
                        airlines.append(edge_data['airline'])
                        
                        # Add waypoints
                        leg_waypoints = self._generate_waypoints(current, next_airport)
                        if waypoints:
                            waypoints.extend(leg_waypoints[1:])
                        else:
                            waypoints.extend(leg_waypoints)
                        
                        current = next_airport
                    
                    route = Route(
                        flight_id='+'.join(flight_ids),
                        source_airport=source,
                        destination_airport=destination,
                        distance=total_distance,
                        duration=total_duration,
                        aircraft_type='+'.join(aircraft_types),
                        airline='+'.join(airlines)
                    )
                    
                    optimized_route = OptimizedRoute(
                        route=route,
                        weather_impact_score=0,
                        total_score=total_weight,
                        waypoints=waypoints,
                        estimated_fuel_consumption=self._estimate_fuel_consumption(total_distance),
                        estimated_cost=self._estimate_cost(total_distance, total_duration)
                    )
                    
                    routes.append(optimized_route)
                    
        except nx.NetworkXNoPath:
            logger.info(f"No two-stop routes found from {source} to {destination}")
        
        return routes
    
    def _apply_weather_optimization(self, routes: List[OptimizedRoute], weather_weight: float) -> List[OptimizedRoute]:
        """Applies weather-based optimization to routes."""
        optimized_routes = []
        
        for route in routes:
            # Calculate weather impact for the route
            weather_impact = self._calculate_route_weather_impact(route)
            route.weather_impact_score = weather_impact
            
            # Update total score with weather consideration
            base_score = route.total_score
            weather_adjusted_score = base_score * (1 + weather_weight * weather_impact / 100)
            route.total_score = weather_adjusted_score
            
            # Generate weather alerts
            route.weather_alerts = self._generate_weather_alerts(route)
            
            optimized_routes.append(route)
        
        return optimized_routes
    
    def _calculate_route_weather_impact(self, route: OptimizedRoute) -> float:
        """Calculates overall weather impact for a route."""
        if not self.weather_data:
            return 0
        
        # Get weather for source and destination
        source_weather = self.weather_data.get(route.route.source_airport)
        dest_weather = self.weather_data.get(route.route.destination_airport)
        
        impacts = []
        if source_weather:
            impacts.append(self._calculate_single_airport_weather_impact(source_weather))
        if dest_weather:
            impacts.append(self._calculate_single_airport_weather_impact(dest_weather))
        
        return sum(impacts) / len(impacts) if impacts else 0
    
    def _calculate_single_airport_weather_impact(self, weather: WeatherData) -> float:
        """Calculates weather impact score for a single airport."""
        score = 0
        
        # Temperature impact
        if weather.temperature < -20 or weather.temperature > 40:
            score += 25
        elif weather.temperature < 0 or weather.temperature > 35:
            score += 15
        
        # Wind impact
        if weather.wind_speed > 50:
            score += 30
        elif weather.wind_speed > 30:
            score += 20
        elif weather.wind_speed > 15:
            score += 10
        
        # Visibility impact
        if weather.visibility < 1:
            score += 25
        elif weather.visibility < 3:
            score += 15
        elif weather.visibility < 5:
            score += 5
        
        # Precipitation impact
        if weather.precipitation > 5:
            score += 20
        elif weather.precipitation > 2:
            score += 10
        elif weather.precipitation > 0:
            score += 5
        
        # Weather conditions
        condition_scores = {
            'thunderstorm': 30,
            'rain': 15,
            'snow': 20,
            'fog': 25,
            'clouds': 5,
            'clear': 0
        }
        score += condition_scores.get(weather.conditions, 10)
        
        return min(score, 100)
    
    def _generate_weather_alerts(self, route: OptimizedRoute) -> List[str]:
        """Generates weather alerts for a route."""
        alerts = []
        
        if not self.weather_data:
            return alerts
        
        # Check source weather
        source_weather = self.weather_data.get(route.route.source_airport)
        if source_weather:
            if source_weather.wind_speed > 40:
                alerts.append(f"High winds at departure ({source_weather.wind_speed:.1f} km/h)")
            if source_weather.visibility < 2:
                alerts.append(f"Low visibility at departure ({source_weather.visibility:.1f} km)")
            if source_weather.precipitation > 3:
                alerts.append(f"Heavy precipitation at departure ({source_weather.precipitation:.1f} mm/h)")
        
        # Check destination weather
        dest_weather = self.weather_data.get(route.route.destination_airport)
        if dest_weather:
            if dest_weather.wind_speed > 40:
                alerts.append(f"High winds at arrival ({dest_weather.wind_speed:.1f} km/h)")
            if dest_weather.visibility < 2:
                alerts.append(f"Low visibility at arrival ({dest_weather.visibility:.1f} km)")
            if dest_weather.precipitation > 3:
                alerts.append(f"Heavy precipitation at arrival ({dest_weather.precipitation:.1f} mm/h)")
        
        return alerts
    
    def _generate_waypoints(self, source: str, destination: str, num_waypoints: int = 10) -> List[Dict[str, float]]:
        """Generates waypoints along a great circle path."""
        if source not in self.airport_coords or destination not in self.airport_coords:
            return []
        
        source_coords = self.airport_coords[source]
        dest_coords = self.airport_coords[destination]
        
        waypoints = []
        
        for i in range(num_waypoints + 1):
            fraction = i / num_waypoints
            
            # Calculate point along great circle
            lat1, lon1 = map(np.radians, source_coords)
            lat2, lon2 = map(np.radians, dest_coords)
            
            # Great circle interpolation
            d = np.arccos(np.sin(lat1) * np.sin(lat2) + np.cos(lat1) * np.cos(lat2) * np.cos(lon2 - lon1))
            
            if d == 0:
                # Same point
                lat, lon = lat1, lon1
            else:
                A = np.sin((1 - fraction) * d) / np.sin(d)
                B = np.sin(fraction * d) / np.sin(d)
                x = A * np.cos(lat1) * np.cos(lon1) + B * np.cos(lat2) * np.cos(lon2)
                y = A * np.cos(lat1) * np.sin(lon1) + B * np.cos(lat2) * np.sin(lon2)
                z = A * np.sin(lat1) + B * np.sin(lat2)
                
                lat = np.arctan2(z, np.sqrt(x * x + y * y))
                lon = np.arctan2(y, x)
            
            waypoints.append({
                'latitude': np.degrees(lat),
                'longitude': np.degrees(lon)
            })
        
        return waypoints
    
    def _calculate_base_weight(self, route: Dict[str, Any]) -> float:
        """Calculates base optimization weight for a route."""
        # Base weight is primarily distance
        distance = route['distance']
        
        # Add some penalty for longer duration
        duration_penalty = route.get('duration', 0) * 0.1
        
        return distance + duration_penalty
    
    def _estimate_fuel_consumption(self, distance: float) -> float:
        """Estimates fuel consumption for a route."""
        # Simplified fuel consumption calculation
        # Average fuel consumption: ~3.5L per 100km per passenger for modern aircraft
        # Assuming 200 passengers average
        fuel_per_km = 3.5 * 200 / 100  # L/km
        return distance * fuel_per_km  # Total liters
    
    def _estimate_cost(self, distance: float, duration: float) -> float:
        """Estimates operational cost for a route."""
        # Simplified cost calculation
        # Fuel cost: ~$0.50 per liter
        fuel_cost = self._estimate_fuel_consumption(distance) * 0.5
        
        # Time-based costs (crew, maintenance, etc.)
        time_cost = duration * 100  # $100 per hour
        
        return fuel_cost + time_cost
    
    def get_route_alternatives(self, optimized_route: OptimizedRoute, num_alternatives: int = 3) -> List[OptimizedRoute]:
        """Generates alternative route suggestions."""
        alternatives = []
        
        # Find routes with similar characteristics but different paths
        all_routes = self.find_optimal_routes(
            optimized_route.route.source_airport,
            optimized_route.route.destination_airport,
            max_stops=2,
            weather_weight=0.3
        )
        
        # Remove the original route and limit alternatives
        alternatives = [r for r in all_routes if r.route.flight_id != optimized_route.route.flight_id]
        
        return alternatives[:num_alternatives]
    
    def get_optimization_insights(self, routes: List[OptimizedRoute]) -> Dict[str, Any]:
        """Provides insights about the optimization results."""
        if not routes:
            return {}
        
        best_route = routes[0]
        
        insights = {
            'total_routes_considered': len(routes),
            'best_route_distance': best_route.route.distance,
            'best_route_duration': best_route.route.duration,
            'best_route_score': best_route.total_score,
            'weather_impact': best_route.weather_impact_score,
            'fuel_estimate': best_route.estimated_fuel_consumption,
            'cost_estimate': best_route.estimated_cost,
            'has_alternatives': len(routes) > 1,
            'weather_alerts': best_route.weather_alerts,
            'optimization_factors': []
        }
        
        # Add optimization factor explanations
        if best_route.weather_impact_score > 20:
            insights['optimization_factors'].append('Weather conditions significantly affect this route')
        
        if len(routes) > 1:
            distance_variance = np.std([r.route.distance for r in routes[:3]])
            if distance_variance > 500:
                insights['optimization_factors'].append('Multiple route options available with varying distances')
        
        return insights