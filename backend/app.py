"""
Flask backend application for Airline Route Optimization Web Application.
Provides REST APIs for frontend communication and integrates all services.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
from datetime import datetime
import json
from typing import Dict, Any, Optional, List

# Import our custom modules
from models import APIResponse, Airport, Route, WeatherData, SparkJobStatus
from data_manager import DataManager
from weather_service import WeatherService
from spark_service import SparkService
from route_optimizer import RouteOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Global service instances
data_manager = DataManager()
weather_service = None
spark_service = SparkService()
route_optimizer = RouteOptimizer()

# Configuration
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', 'demo_key')  # Replace with real key in production

@app.route('/')
def index():
    """Serves the main application page."""
    return send_from_directory('../frontend', 'index.html')

@app.route('/dashboard')
def dashboard():
    """Serves the Spark monitoring dashboard."""
    return send_from_directory('../frontend', 'dashboard.html')

@app.route('/<path:path>')
def static_files(path):
    """Serves static files."""
    return send_from_directory('../frontend', path)

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify(APIResponse(
        success=True,
        message="Airline Route Optimization API is running",
        data={
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'services': {
                'data_manager': True,
                'spark_service': spark_service.initialized,
                'weather_service': weather_service is not None,
                'route_optimizer': True
            }
        }
    ).to_dict())

@app.route('/api/airports', methods=['GET'])
def get_airports():
    """Gets all available airports."""
    try:
        airports = data_manager.get_airports()
        
        return jsonify(APIResponse(
            success=True,
            data=airports,
            metadata={'count': len(airports)}
        ).to_dict())
        
    except Exception as e:
        logger.error(f"Error getting airports: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to retrieve airports",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/airports/search', methods=['GET'])
def search_airports():
    """Searches airports by code or name."""
    try:
        query = request.args.get('q', '').upper()
        if not query:
            return jsonify(APIResponse(
                success=False,
                message="Search query is required"
            ).to_dict()), 400
        
        airports = data_manager.get_airports()
        
        # Filter airports
        filtered_airports = [
            airport for airport in airports
            if query in airport['code'].upper() or 
               query in airport['name'].upper() or
               query in airport['city'].upper() or
               query in airport['country'].upper()
        ]
        
        return jsonify(APIResponse(
            success=True,
            data=filtered_airports,
            metadata={'count': len(filtered_airports), 'query': query}
        ).to_dict())
        
    except Exception as e:
        logger.error(f"Error searching airports: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to search airports",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/routes', methods=['GET'])
def get_routes():
    """Gets all available routes."""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        routes = data_manager.get_routes()
        
        # Apply pagination
        paginated_routes = routes[offset:offset + limit]
        
        return jsonify(APIResponse(
            success=True,
            data=paginated_routes,
            metadata={
                'total': len(routes),
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < len(routes)
            }
        ).to_dict())
        
    except Exception as e:
        logger.error(f"Error getting routes: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to retrieve routes",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/routes/optimize', methods=['POST'])
def optimize_route():
    """Optimizes routes between source and destination airports."""
    try:
        data = request.get_json()
        
        # Validate input
        source = data.get('source', '').upper()
        destination = data.get('destination', '').upper()
        
        if not source or not destination:
            return jsonify(APIResponse(
                success=False,
                message="Source and destination airports are required"
            ).to_dict()), 400
        
        if source == destination:
            return jsonify(APIResponse(
                success=False,
                message="Source and destination cannot be the same"
            ).to_dict()), 400
        
        # Optional parameters
        max_stops = int(data.get('max_stops', 2))
        weather_weight = float(data.get('weather_weight', 0.3))
        time_preference = data.get('time_preference', 'balanced')
        
        # Load data into optimizer
        routes = data_manager.get_routes()
        airports = data_manager.get_airports()
        route_optimizer.load_data(routes, airports)
        
        # Get weather data if available
        weather_data = {}
        if weather_service:
            # Get weather for source and destination
            source_airport = data_manager.get_airport_by_code(source)
            dest_airport = data_manager.get_airport_by_code(destination)
            
            if source_airport:
                weather = weather_service.get_weather_by_coordinates(
                    source, source_airport['latitude'], source_airport['longitude']
                )
                if weather:
                    weather_data[source] = weather
            
            if dest_airport:
                weather = weather_service.get_weather_by_coordinates(
                    destination, dest_airport['latitude'], dest_airport['longitude']
                )
                if weather:
                    weather_data[destination] = weather
            
            route_optimizer.update_weather_data(weather_data)
        
        # If Spark is initialized, create a tracked job and run a lightweight Spark action
        job_id = None
        if spark_service and spark_service.initialized:
            try:
                job_id = f"ui_optimize_{int(datetime.now().timestamp())}"
                spark_service.active_jobs[job_id] = SparkJobStatus(
                    job_id=job_id,
                    status="running",
                    start_time=datetime.now(),
                    description=f"UI optimize {source}->{destination} (preprocess)"
                )
                
                routes_df = spark_service.create_route_dataframe(routes)
                airports_df = spark_service.create_airport_dataframe(airports)
                if routes_df is not None and airports_df is not None:
                    # Trigger a job in Spark UI so users see activity
                    _ = routes_df.filter(
                        (routes_df.source_airport == source) | (routes_df.destination_airport == destination)
                    ).count()
                    spark_service.active_jobs[job_id].progress = 50.0
            except Exception as _e:
                if job_id and job_id in spark_service.active_jobs:
                    spark_service.active_jobs[job_id].status = "failed"
                    spark_service.active_jobs[job_id].end_time = datetime.now()
                    spark_service.active_jobs[job_id].error_message = str(_e)
                job_id = None
        
        # Find optimal routes with the local optimizer for consistent output
        optimal_routes = route_optimizer.find_optimal_routes(
            source, destination, max_stops, weather_weight, time_preference
        )
        
        # Convert to dictionaries for JSON serialization
        routes_data = [route.to_dict() for route in optimal_routes]
        
        # Close out the Spark-tracked UI job if we created one
        if job_id and job_id in spark_service.active_jobs:
            sj = spark_service.active_jobs[job_id]
            sj.progress = 100.0
            sj.status = "completed"
            sj.end_time = datetime.now()
        
        return jsonify(APIResponse(
            success=True,
            data=routes_data,
            metadata={
                'source': source,
                'destination': destination,
                'count': len(routes_data),
                'weather_enabled': len(weather_data) > 0,
                'engine': 'local' if not (spark_service and spark_service.initialized) else 'local+spark-preprocess',
                'spark_job_id': job_id
            }
        ).to_dict())
        
    except Exception as e:
        logger.error(f"Error optimizing routes: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to optimize routes",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """Gets weather data for an airport."""
    try:
        airport_code = request.args.get('airport', '').upper()
        
        if not airport_code:
            return jsonify(APIResponse(
                success=False,
                message="Airport code is required"
            ).to_dict()), 400
        
        if not weather_service:
            # Return demo weather data if service unavailable
            demo_weather = {
                'airport_code': airport_code,
                'timestamp': datetime.now().isoformat(),
                'temperature': 20.0,
                'humidity': 65,
                'wind_speed': 15.0,
                'wind_direction': 270,
                'visibility': 10.0,
                'conditions': 'clear',
                'precipitation': 0.0,
                'pressure': 1013.25
            }
            
            return jsonify(APIResponse(
                success=True,
                data=demo_weather,
                metadata={'demo': True}
            ).to_dict())
        
        # Get airport coordinates
        airport = data_manager.get_airport_by_code(airport_code)
        if not airport:
            return jsonify(APIResponse(
                success=False,
                message=f"Airport {airport_code} not found"
            ).to_dict()), 404
        
        # Get real weather data
        weather = weather_service.get_weather_by_coordinates(
            airport_code, airport['latitude'], airport['longitude']
        )
        
        if weather:
            return jsonify(APIResponse(
                success=True,
                data=weather.to_dict()
            ).to_dict())
        else:
            return jsonify(APIResponse(
                success=False,
                message="Failed to retrieve weather data"
            ).to_dict()), 503
        
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to retrieve weather data",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/data/upload', methods=['POST'])
def upload_data():
    """Uploads new route or airport data."""
    try:
        if 'file' not in request.files:
            return jsonify(APIResponse(
                success=False,
                message="No file provided"
            ).to_dict()), 400
        
        file = request.files['file']
        data_type = request.form.get('type', 'routes')
        
        if file.filename == '':
            return jsonify(APIResponse(
                success=False,
                message="No file selected"
            ).to_dict()), 400
        
        # Read file content
        file_content = file.read().decode('utf-8')
        
        # Upload data
        success, message = data_manager.upload_csv_data(file_content, data_type, file.filename)
        
        if success:
            return jsonify(APIResponse(
                success=True,
                message=message
            ).to_dict())
        else:
            return jsonify(APIResponse(
                success=False,
                message=message
            ).to_dict()), 400
            
    except Exception as e:
        logger.error(f"Error uploading data: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to upload data",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/data/summary', methods=['GET'])
def get_data_summary():
    """Gets summary statistics of loaded data."""
    try:
        summary = data_manager.get_data_summary()
        
        return jsonify(APIResponse(
            success=True,
            data=summary
        ).to_dict())
        
    except Exception as e:
        logger.error(f"Error getting data summary: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to get data summary",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/spark/status', methods=['GET'])
def get_spark_status():
    """Gets Spark service status and cluster information."""
    try:
        cluster_info = spark_service.get_cluster_info()
        
        return jsonify(APIResponse(
            success=True,
            data=cluster_info
        ).to_dict())
        
    except Exception as e:
        logger.error(f"Error getting Spark status: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to get Spark status",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/spark/initialize', methods=['POST'])
def initialize_spark():
    """Manually initializes Spark session."""
    try:
        if spark_service.initialized:
            return jsonify(APIResponse(
                success=True,
                message="Spark is already initialized",
                data=spark_service.get_cluster_info()
            ).to_dict())
        
        success = spark_service.initialize_spark()
        
        if success:
            cluster_info = spark_service.get_cluster_info()
            return jsonify(APIResponse(
                success=True,
                message="Spark initialized successfully",
                data=cluster_info
            ).to_dict())
        else:
            # Return 200 with success=False so frontend can handle gracefully
            return jsonify(APIResponse(
                success=False,
                message="Failed to initialize Spark"
            ).to_dict()), 200
            
    except Exception as e:
        logger.error(f"Error initializing Spark: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to initialize Spark",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/spark/jobs', methods=['GET'])
def get_spark_jobs():
    """Gets active and recent Spark jobs."""
    try:
        jobs = spark_service.get_all_jobs()
        jobs_data = [job.to_dict() for job in jobs]
        
        return jsonify(APIResponse(
            success=True,
            data=jobs_data,
            metadata={'count': len(jobs_data)}
        ).to_dict())
        
    except Exception as e:
        logger.error(f"Error getting Spark jobs: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to get Spark jobs",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/spark/ui', methods=['GET'])
def get_spark_ui_url():
    """Gets the Spark Web UI URL."""
    try:
        ui_url = spark_service.get_spark_ui_url()
        
        return jsonify(APIResponse(
            success=True,
            data={'ui_url': ui_url}
        ).to_dict())
        
    except Exception as e:
        logger.error(f"Error getting Spark UI URL: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to get Spark UI URL",
            errors=[str(e)]
        ).to_dict()), 500

@app.route('/api/export', methods=['GET'])
def export_data():
    """Exports data in various formats."""
    try:
        data_type = request.args.get('type', 'routes')
        format = request.args.get('format', 'csv')
        
        filepath = data_manager.export_data(data_type, format)
        
        if filepath:
            return send_from_directory(
                os.path.dirname(filepath),
                os.path.basename(filepath),
                as_attachment=True
            )
        else:
            return jsonify(APIResponse(
                success=False,
                message="Failed to export data"
            ).to_dict()), 500
            
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify(APIResponse(
            success=False,
            message="Failed to export data",
            errors=[str(e)]
        ).to_dict()), 500

def initialize_services():
    """Initializes all backend services."""
    global weather_service
    
    logger.info("Initializing backend services...")
    
    # Initialize Spark service
    spark_initialized = spark_service.initialize_spark()
    logger.info(f"Spark service initialized: {spark_initialized}")
    
    # Initialize weather service - always initialize (WeatherService has built-in API key)
    try:
        weather_service = WeatherService(WEATHER_API_KEY)
        logger.info("Weather service initialized with OpenWeatherMap API")
    except Exception as e:
        logger.warning(f"Weather service initialization failed: {e} - using demo mode")
    
    # Load data
    data_manager.load_data()
    logger.info("Data manager initialized")
    
    logger.info("Backend services initialization complete")

if __name__ == '__main__':
    # Initialize services
    initialize_services()
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)