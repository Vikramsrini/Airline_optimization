"""
PySpark service for large-scale data processing and route optimization.
Handles distributed computing for airline route analysis.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, when, lit, sqrt, pow, radians, sin, cos, atan2
from pyspark.sql.types import DoubleType, StringType, BooleanType, ArrayType, StructType, StructField
import json
import logging
import os
import re
import subprocess
import glob
from typing import List, Dict, Any, Optional, Tuple
from models import Route, Airport, SparkJobStatus, SparkProcessingError
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class SparkService:
    """Service for PySpark data processing and route optimization."""
    
    def __init__(self, app_name: str = "AirlineRouteOptimizer"):
        self.app_name = app_name
        self.spark = None
        self.active_jobs = {}
        self.initialized = False
        
    def initialize_spark(self) -> bool:
        """
        Initializes the Spark session with appropriate configuration.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing Spark session...")
            # Try to ensure we are running with a Java version compatible with Hadoop 3.3.x (JDK 11/17)
            self._ensure_java_compat()
            
            # Prefer local mode for desktop usage and reduce Hadoop auth issues
            # Also enable native access to suppress JDK warning with Hadoop libs
            java_opts = os.environ.get("JAVA_TOOL_OPTIONS", "")
            if "--enable-native-access=ALL-UNNAMED" not in java_opts:
                # Do not overwrite existing options; append safely for current process
                os.environ["JAVA_TOOL_OPTIONS"] = (java_opts + " --enable-native-access=ALL-UNNAMED").strip()

            # Build Spark session in local mode with safer Hadoop settings
            self.spark = (
                SparkSession.builder
                .master("local[*]")
                .appName(self.app_name)
                .config("spark.sql.adaptive.enabled", "true")
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
                .config("spark.sql.shuffle.partitions", "200")
                .config("spark.default.parallelism", "4")
                .config("spark.driver.memory", "2g")
                .config("spark.executor.memory", "2g")
                .config("spark.driver.extraJavaOptions", "--enable-native-access=ALL-UNNAMED")
                .config("spark.executor.extraJavaOptions", "--enable-native-access=ALL-UNNAMED")
                .config("spark.hadoop.security.authentication", "simple")
                .config("spark.hadoop.security.authorization", "false")
                .config("spark.ui.port", "4040")
                .getOrCreate()
            )
            
            # Set log level
            self.spark.sparkContext.setLogLevel("WARN")
            
            self.initialized = True
            logger.info(f"Spark session initialized successfully. Web UI available at: {self.spark.sparkContext.uiWebUrl}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark session: {e}")
            # Provide actionable guidance for common JDK/Hadoop mismatch
            logger.error("Hint: Use JDK 17 for PySpark/Hadoop 3.3.x, and ensure '--enable-native-access=ALL-UNNAMED'.")
            logger.error("You can export JAVA_HOME to a JDK 17 installation and re-run.")
            return False

    def _ensure_java_compat(self):
        """Ensure a compatible JDK (prefer 17) is used when launching Spark.
        If JDK 21+ is active, attempt to switch to a local JDK 17 on macOS.
        """
        try:
            proc = subprocess.run(["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out = proc.stderr or proc.stdout
            m = re.search(r'version\s+"([^"]+)"', out)
            version = m.group(1) if m else ""
            major = None
            if version.startswith("1."):
                # e.g., 1.8.0_402 -> 8
                parts = version.split(".")
                if len(parts) > 1:
                    major = int(parts[1])
            else:
                try:
                    major = int(version.split(".")[0])
                except Exception:
                    major = None

            if major is not None and major >= 21:
                # Attempt macOS JDK 17 discovery
                for jdk_home in glob.glob("/Library/Java/JavaVirtualMachines/*17*.jdk/Contents/Home"):
                    if os.path.isdir(jdk_home) and os.path.exists(os.path.join(jdk_home, "bin", "java")):
                        os.environ["JAVA_HOME"] = jdk_home
                        os.environ["PATH"] = f"{jdk_home}/bin:" + os.environ.get("PATH", "")
                        logger.warning("Detected Java %s; switching JAVA_HOME to JDK 17 at %s for Spark compatibility.", major, jdk_home)
                        break
        except Exception as _e:
            # Best-effort; continue with existing Java if detection fails
            pass
    
    def create_route_dataframe(self, routes_data: List[Dict[str, Any]]) -> Any:
        """
        Creates a Spark DataFrame from route data.
        
        Args:
            routes_data: List of route dictionaries
            
        Returns:
            Spark DataFrame or None if creation fails
        """
        if not self.initialized:
            if not self.initialize_spark():
                return None
        
        try:
            # Create DataFrame
            df = self.spark.createDataFrame(routes_data)
            
            # Register as temporary view for SQL queries
            df.createOrReplaceTempView("routes")
            
            logger.info(f"Created route DataFrame with {df.count()} records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to create route DataFrame: {e}")
            return None
    
    def create_airport_dataframe(self, airports_data: List[Dict[str, Any]]) -> Any:
        """
        Creates a Spark DataFrame from airport data.
        
        Args:
            airports_data: List of airport dictionaries
            
        Returns:
            Spark DataFrame or None if creation fails
        """
        if not self.initialized:
            if not self.initialize_spark():
                return None
        
        try:
            df = self.spark.createDataFrame(airports_data)
            df.createOrReplaceTempView("airports")
            
            logger.info(f"Created airport DataFrame with {df.count()} records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to create airport DataFrame: {e}")
            return None
    
    def register_haversine_udf(self):
        """Registers the haversine distance calculation as a UDF."""
        if not self.initialized or not self.spark:
            return
        
        def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """Calculates great circle distance using haversine formula."""
            from math import radians, sin, cos, sqrt, atan2
            
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            # Earth's radius in km
            r = 6371
            return c * r
        
        # Register UDF
        self.spark.udf.register("haversine_distance", haversine_distance, DoubleType())
    
    def process_routes_dataset(self, routes_df: Any, airports_df: Any) -> Dict[str, Any]:
        """
        Processes the routes dataset to extract insights and prepare for optimization.
        
        Args:
            routes_df: Spark DataFrame containing route data
            airports_df: Spark DataFrame containing airport data
            
        Returns:
            Dictionary with processing results and statistics
        """
        job_id = f"route_processing_{int(time.time())}"
        job_status = SparkJobStatus(
            job_id=job_id,
            status="running",
            start_time=datetime.now(),
            description="Processing airline routes dataset"
        )
        self.active_jobs[job_id] = job_status
        
        try:
            logger.info(f"Starting route dataset processing (Job ID: {job_id})")
            
            # Basic statistics
            total_routes = routes_df.count()
            unique_airports = routes_df.select("source_airport").union(
                routes_df.select("destination_airport")
            ).distinct().count()
            
            job_status.progress = 25
            
            # Route distance statistics
            distance_stats = routes_df.describe("distance").collect()
            distance_summary = {row['summary']: row['distance'] for row in distance_stats}
            
            job_status.progress = 50
            
            # Popular routes (most connections)
            popular_routes = routes_df.groupBy("source_airport", "destination_airport") \
                .count().orderBy(col("count").desc()).limit(10).collect()
            
            job_status.progress = 75
            
            # Airport connectivity analysis
            airport_connections = routes_df.groupBy("source_airport") \
                .agg({"destination_airport": "count"}) \
                .withColumnRenamed("count(destination_airport)", "outbound_connections") \
                .orderBy(col("outbound_connections").desc()).limit(20).collect()
            
            job_status.progress = 90
            
            # Prepare results
            results = {
                'total_routes': total_routes,
                'unique_airports': unique_airports,
                'distance_summary': distance_summary,
                'popular_routes': [row.asDict() for row in popular_routes],
                'airport_connectivity': [row.asDict() for row in airport_connections],
                'processing_time': (datetime.now() - job_status.start_time).total_seconds()
            }
            
            job_status.progress = 100
            job_status.status = "completed"
            job_status.end_time = datetime.now()
            
            logger.info(f"Route processing completed successfully. Processed {total_routes} routes.")
            return results
            
        except Exception as e:
            job_status.status = "failed"
            job_status.error_message = str(e)
            job_status.end_time = datetime.now()
            logger.error(f"Route processing failed: {e}")
            raise SparkProcessingError(f"Failed to process routes dataset: {e}")
    
    def find_optimal_routes(self, source_airport: str, destination_airport: str, 
                          routes_df: Any, airports_df: Any, 
                          weather_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Finds optimal routes between two airports using graph algorithms.
        
        Args:
            source_airport: Source airport code
            destination_airport: Destination airport code
            routes_df: Spark DataFrame with route data
            airports_df: Spark DataFrame with airport data
            weather_data: Dictionary of weather data by airport
            
        Returns:
            List of optimized route dictionaries
        """
        job_id = f"route_optimization_{int(time.time())}"
        job_status = SparkJobStatus(
            job_id=job_id,
            status="running",
            start_time=datetime.now(),
            description=f"Finding optimal routes from {source_airport} to {destination_airport}"
        )
        self.active_jobs[job_id] = job_status
        
        try:
            logger.info(f"Starting route optimization from {source_airport} to {destination_airport}")
            
            # Filter relevant routes (all routes that could be part of the path)
            relevant_routes = routes_df.filter(
                (col("source_airport") == source_airport) |
                (col("destination_airport") == destination_airport) |
                (col("source_airport") == destination_airport) |
                (col("destination_airport") == source_airport)
            ).cache()
            
            # Get airport coordinates
            airports_list = airports_df.collect()
            airport_coords = {row['code']: (row['latitude'], row['longitude']) for row in airports_list}
            
            job_status.progress = 25
            
            # Find direct routes
            direct_routes = relevant_routes.filter(
                (col("source_airport") == source_airport) & 
                (col("destination_airport") == destination_airport)
            ).collect()
            
            job_status.progress = 50
            
            # Find one-stop routes
            one_stop_routes = []
            if len(direct_routes) == 0:
                # Find routes from source to intermediate airports
                first_legs = relevant_routes.filter(col("source_airport") == source_airport).collect()
                
                # Find routes from intermediate airports to destination
                for first_leg in first_legs:
                    intermediate_airport = first_leg['destination_airport']
                    second_legs = relevant_routes.filter(
                        (col("source_airport") == intermediate_airport) & 
                        (col("destination_airport") == destination_airport)
                    ).collect()
                    
                    for second_leg in second_legs:
                        one_stop_routes.append({
                            'route_type': 'one_stop',
                            'first_leg': first_leg.asDict(),
                            'second_leg': second_leg.asDict(),
                            'total_distance': first_leg['distance'] + second_leg['distance'],
                            'intermediate_airport': intermediate_airport
                        })
            
            job_status.progress = 75
            
            # Calculate weather impact scores
            optimized_routes = []
            
            # Process direct routes
            for route in direct_routes:
                route_dict = route.asDict()
                route_dict['route_type'] = 'direct'
                route_dict['weather_impact'] = self._calculate_route_weather_impact(
                    route_dict, weather_data
                )
                route_dict['total_score'] = self._calculate_optimization_score(route_dict)
                optimized_routes.append(route_dict)
            
            # Process one-stop routes
            for route in one_stop_routes:
                route['weather_impact'] = (
                    self._calculate_route_weather_impact(route['first_leg'], weather_data) +
                    self._calculate_route_weather_impact(route['second_leg'], weather_data)
                ) / 2
                route['total_score'] = self._calculate_optimization_score(route)
                optimized_routes.append(route)
            
            job_status.progress = 90
            
            # Sort by total score (lower is better)
            optimized_routes.sort(key=lambda x: x['total_score'])
            
            # Limit results
            optimized_routes = optimized_routes[:10]
            
            job_status.progress = 100
            job_status.status = "completed"
            job_status.end_time = datetime.now()
            
            logger.info(f"Route optimization completed. Found {len(optimized_routes)} optimal routes.")
            return optimized_routes
            
        except Exception as e:
            job_status.status = "failed"
            job_status.error_message = str(e)
            job_status.end_time = datetime.now()
            logger.error(f"Route optimization failed: {e}")
            raise SparkProcessingError(f"Failed to find optimal routes: {e}")
    
    def _calculate_route_weather_impact(self, route: Dict[str, Any], weather_data: Dict[str, Dict[str, Any]]) -> float:
        """Calculates weather impact score for a route."""
        source_weather = weather_data.get(route['source_airport'], {})
        dest_weather = weather_data.get(route['destination_airport'], {})
        
        # Get impact scores from weather data or use defaults
        source_impact = source_weather.get('impact_score', 0) if source_weather else 0
        dest_impact = dest_weather.get('impact_score', 0) if dest_weather else 0
        
        # Average the impact scores
        return (source_impact + dest_impact) / 2
    
    def _calculate_optimization_score(self, route: Dict[str, Any]) -> float:
        """Calculates overall optimization score for a route."""
        # Base score is distance (lower is better)
        distance_score = route.get('distance', route.get('total_distance', 0))
        
        # Add weather impact
        weather_impact = route.get('weather_impact', 0)
        
        # Combine scores (weather has 30% weight)
        total_score = distance_score * 0.7 + weather_impact * 100 * 0.3
        
        return total_score
    
    def get_job_status(self, job_id: str) -> Optional[SparkJobStatus]:
        """Gets the status of a Spark job."""
        return self.active_jobs.get(job_id)
    
    def get_all_jobs(self) -> List[SparkJobStatus]:
        """Gets all active and recent Spark jobs."""
        return list(self.active_jobs.values())
    
    def cleanup_jobs(self, max_age_hours: int = 24):
        """Cleans up old completed jobs."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if job.status in ['completed', 'failed'] and job.end_time and job.end_time < cutoff_time:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
        
        logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
    
    def get_spark_ui_url(self) -> Optional[str]:
        """Gets the Spark Web UI URL."""
        if self.initialized and self.spark:
            return self.spark.sparkContext.uiWebUrl
        return None
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Gets information about the Spark cluster."""
        if not self.initialized:
            return {'status': 'not_initialized'}
        
        try:
            sc = self.spark.sparkContext
            status = sc.statusTracker()

            # Active stages via PySpark API if available
            active_stages_count = 0
            try:
                if hasattr(status, 'getActiveStageIds'):
                    active_stages = status.getActiveStageIds()
                    # Some versions return a list-like JavaObject; cast to list safely
                    active_stages_count = len(list(active_stages))
            except Exception:
                active_stages_count = 0

            # Active jobs: track via our service's job registry to avoid API differences
            active_jobs_count = sum(1 for j in self.active_jobs.values() if getattr(j, 'status', '') == 'running')

            return {
                'status': 'active',
                'app_name': sc.appName,
                'spark_version': self.spark.version,
                'spark_context_version': sc.version,
                'default_parallelism': sc.defaultParallelism,
                'ui_web_url': sc.uiWebUrl,
                'active_jobs': active_jobs_count,
                'active_stages': active_stages_count,
            }
        except Exception as e:
            logger.error(f"Failed to get cluster info: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def stop_spark(self):
        """Stops the Spark session."""
        if self.spark:
            self.spark.stop()
            self.initialized = False
            logger.info("Spark session stopped")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, 'spark') and self.spark:
            self.spark.stop()