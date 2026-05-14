# Airline Route Optimization Web Application

A sophisticated full-stack web application for intelligent airline route optimization with real-time weather integration, PySpark-powered data processing, and interactive visualization.

## Features

### 🛫 Core Functionality
- **Intelligent Route Optimization**: Advanced algorithms considering distance, weather, and efficiency
- **Real-time Weather Integration**: Live weather data affecting route recommendations
- **Interactive Map Visualization**: Leaflet-powered route mapping with weather overlays
- **Large-scale Data Processing**: PySpark integration for handling extensive route datasets

### 🎨 User Experience
- **Modern Aviation-themed Design**: Professional interface with smooth animations
- **Responsive Layout**: Optimized for desktop, tablet, and mobile devices
- **Interactive Components**: Dynamic airport search, route comparison, and filtering
- **Real-time Feedback**: Live progress tracking and status updates

### 📊 Analytics & Monitoring
- **Spark Web UI Integration**: Real-time monitoring of PySpark jobs and cluster performance
- **Comprehensive Dashboard**: Detailed analytics and performance metrics
- **Weather Impact Analysis**: Visual representation of weather effects on routes
- **Export Functionality**: Download optimized routes and analytics reports

### 🔧 Technical Features
- **CSV Data Upload**: Support for custom route and airport datasets
- **RESTful API**: Clean JSON-based API for frontend-backend communication
- **Error Handling**: Comprehensive error management and user feedback
- **Caching System**: Efficient data caching for improved performance

## Technology Stack

### Backend
- **Python Flask**: Lightweight web framework for REST API
- **PySpark**: Distributed data processing for large datasets
- **NetworkX**: Graph algorithms for route optimization
- **Pandas**: Data manipulation and analysis
- **Requests**: HTTP library for weather API integration

### Frontend
- **HTML5/CSS3**: Modern web standards with responsive design
- **JavaScript ES6+**: Vanilla JavaScript with modern features
- **Leaflet.js**: Interactive mapping and visualization
- **ECharts.js**: Data visualization and analytics charts
- **Anime.js**: Smooth animations and transitions

### External Services
- **OpenWeatherMap API**: Real-time weather data integration
- **Spark Web UI**: Built-in monitoring and debugging interface

## Project Structure

```
Airline_Optimization/
├── backend/                 # Flask backend application
│   ├── app.py              # Main Flask application
│   ├── models.py           # Data models and schemas
│   ├── spark_service.py    # PySpark integration service
│   ├── weather_service.py  # Weather API integration
│   ├── route_optimizer.py  # Route optimization algorithms
│   ├── data_manager.py     # CSV upload and data management
│   ├── requirements.txt    # Python dependencies
│   └── data/               # Backend data directory
│       ├── airports.csv    # Loaded airports data
│       ├── routes.csv      # Loaded routes data
│       └── uploads/        # User uploads (gitignored)
├── data/                   # Root-level CSV copies (optional)
├── frontend/               # Web application frontend
│   ├── index.html          # Main application interface
│   ├── dashboard.html      # Spark monitoring dashboard
│   ├── main.js             # Frontend JavaScript logic
│   └── config.js           # Frontend configuration
├── docs/                   # Documentation
│   ├── interaction.md      # User interaction design
│   └── design.md           # Visual design guide
├── index.html              # Root entry / redirect to app
├── outline.md              # Project outline notes
├── start.sh                # Startup script
└── README.md               # Project documentation
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- Java 8+ (for PySpark)
- Modern web browser
- Internet connection (for weather API)

### Quick Start

Use the provided startup script:
```bash
./start.sh
```

Or follow the manual setup below:

### Backend Setup

1. **Install Python dependencies:**
```bash
cd backend
pip3 install -r requirements.txt
```

2. **Set up environment variables (optional):**
```bash
export WEATHER_API_KEY="your_openweathermap_api_key"
export PORT=5000
export DEBUG=False
```

3. **Run the Flask application:**
```bash
python3 app.py
```

The backend will start on `http://localhost:5000`

### Frontend Setup

The frontend is served directly by the Flask application. No additional setup required.

### Spark Configuration

The application includes automatic Spark session initialization. **Important:** Spark is lazily initialized to save resources.

**To activate Spark Web UI (port 4040):**
1. Ensure Java 8+ is installed
2. Open the main application at `http://localhost:5000`
3. Select airports and click "Find Optimal Routes" to initialize Spark
4. Once Spark starts processing, the Web UI becomes available at `http://localhost:4040`

PySpark will automatically download required dependencies on first run.

## Usage

### Basic Route Optimization

1. **Select Airports:**
   - Choose source and destination airports from dropdown menus
   - Use search functionality to find specific airports

2. **Configure Options:**
   - Set maximum number of stops (0-2)
   - Adjust weather consideration weight (0-70%)
   - Enable alternative route suggestions

3. **Optimize Routes:**
   - Click "Find Optimal Routes" to start optimization
   - Monitor progress with real-time status updates
   - View results with detailed analytics

### Advanced Features

#### Data Upload
- Upload custom CSV files for routes and airports
- Support for drag-and-drop file upload
- Automatic data validation and processing

#### Weather Integration
- Real-time weather data for departure and arrival airports
- Weather impact scoring and route recommendations
- Visual weather alerts and warnings

#### Spark Monitoring
- Access Spark Web UI for detailed job monitoring
- View real-time job progress and cluster metrics
- Analyze performance and optimization insights

### Sample Data

The application includes comprehensive sample data:
- **15+ major international airports** including JFK, LAX, LHR, CDG, NRT, SIN, DXB, and more
- **400+ airline routes** with realistic distances and durations
- **Multiple aircraft types** (Boeing 737, 777, 787, Airbus A320, A330, A380, etc.) and airlines
- **Global coverage** including North America, Europe, Asia, Australia, and South America

## API Endpoints

### Core Endpoints

- `GET /api/health` - Application health check
- `GET /api/airports` - Get all airports
- `GET /api/airports/search` - Search airports
- `GET /api/routes` - Get all routes (paginated)
- `POST /api/routes/optimize` - Optimize routes between airports

### Weather Endpoints

- `GET /api/weather` - Get weather data for airport

### Data Management

- `POST /api/data/upload` - Upload CSV data files
- `GET /api/data/summary` - Get data summary statistics
- `GET /api/export` - Export data in various formats

### Spark Monitoring

- `GET /api/spark/status` - Get Spark cluster status
- `GET /api/spark/jobs` - Get Spark job information
- `GET /api/spark/ui` - Get Spark Web UI URL

## Configuration

### Weather API

To enable real-time weather data:

1. Sign up for a free account at [OpenWeatherMap](https://openweathermap.org/)
2. Get your API key from the dashboard
3. Set the environment variable:
   ```bash
   export WEATHER_API_KEY="your_api_key_here"
   ```

Without an API key, the application will use demo weather data.

### Spark Configuration

The application automatically configures Spark with optimized settings:

```python
spark = SparkSession.builder \
    .appName("AirlineRouteOptimizer") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.shuffle.partitions", "200") \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "2g") \
    .getOrCreate()
```

## Performance Optimization

### Backend Optimizations
- **PySpark Caching**: Automatic caching of frequently accessed data
- **Weather API Caching**: 10-minute cache for weather data
- **Route Optimization Caching**: Cached results for identical queries
- **Connection Pooling**: Efficient database connections

### Frontend Optimizations
- **Lazy Loading**: Progressive loading of route results
- **Map Optimization**: Efficient rendering of flight paths
- **Animation Performance**: Hardware-accelerated CSS animations
- **Responsive Images**: Optimized images for different screen sizes

## Troubleshooting

### Common Issues

1. **Spark Web UI Not Available (Port 4040)**
   - Spark UI only starts after running route optimization
   - Go to main app → select airports → click "Find Optimal Routes"
   - Once Spark initializes, UI will be at `http://localhost:4040`
   - Ensure Java 8+ is installed
   - Check firewall settings for port 4040 if still not accessible

2. **Weather API Not Working**
   - Check API key validity
   - Verify internet connectivity
   - Check API rate limits

3. **Route Optimization Slow**
   - Increase Spark memory allocation
   - Reduce weather weight for faster processing
   - Limit maximum stops parameter

### Debug Mode

Enable debug logging:
```bash
export DEBUG=True
python3 app.py
```

## Development

### Adding New Features

1. **Backend Changes:**
   - Update models in `models.py`
   - Add API endpoints in `app.py`
   - Implement logic in appropriate service files

2. **Frontend Changes:**
   - Update HTML templates
   - Add JavaScript functionality in `main.js`
   - Style with CSS in HTML files

### Testing

Run basic functionality tests:
```bash
# Test API health
curl http://localhost:5000/api/health

# Test airport listing
curl http://localhost:5000/api/airports

# Test route optimization
curl -X POST http://localhost:5000/api/routes/optimize \
  -H "Content-Type: application/json" \
  -d '{"source": "JFK", "destination": "LAX"}'
```

## Deployment

### Production Considerations

1. **Security:**
   - Use environment variables for sensitive data
   - Implement proper authentication
   - Use HTTPS for production

2. **Performance:**
   - Configure proper Spark cluster settings
   - Set up load balancing
   - Use production-grade web server (Gunicorn, uWSGI)

3. **Monitoring:**
   - Set up application monitoring
   - Configure logging and alerts
   - Monitor Spark cluster health

### Docker Deployment

Create a Dockerfile:
```dockerfile
FROM python:3.9
WORKDIR /app
COPY backend/requirements.txt ./backend/
RUN pip install -r backend/requirements.txt
COPY . .
EXPOSE 5000
CMD ["python3", "backend/app.py"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Feel free to use, modify, and distribute according to your needs.

## Support

For issues, questions, or contributions:
- Check the troubleshooting section
- Review the inline API documentation in `backend/app.py`
- Consult the interaction and design docs in the `docs/` folder

---

**Built with ❤️ using modern web technologies and intelligent algorithms**