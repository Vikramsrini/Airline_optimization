/**
 * Airline Route Optimization - Main Frontend Application
 * Handles all interactive components, API communication, and visualization
 */

class RouteOptimizerApp {
    constructor() {
        this.apiBase = '/api';
        this.map = null;
        this.currentRoutes = [];
        this.airports = [];
        this.isLoading = false;
        
        this.init();
    }

    async init() {
        try {
            // Initialize typed text animation
            this.initTypedText();
            
            // Load initial data
            await this.loadAirports();
            
            // Initialize map
            this.initMap();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Check API health
            await this.checkHealth();
            
            console.log('Route Optimizer App initialized successfully');
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Failed to initialize application');
        }
    }

    initTypedText() {
        const typed = new Typed('#typed-text', {
            strings: [
                'real-time weather data',
                'intelligent algorithms',
                'comprehensive analytics',
                'advanced optimization'
            ],
            typeSpeed: 50,
            backSpeed: 30,
            backDelay: 2000,
            loop: true,
            showCursor: true,
            cursorChar: '|'
        });
    }

    async loadAirports() {
        try {
            // Add cache-busting parameter to ensure fresh data after upload
            const timestamp = new Date().getTime();
            const response = await this.apiCall(`/airports?_=${timestamp}`);
            if (response.success) {
                this.airports = response.data;
                console.log(`Loaded ${this.airports.length} airports`);
                this.populateAirportSelects();
            }
        } catch (error) {
            console.error('Failed to load airports:', error);
        }
    }

    populateAirportSelects() {
        const sourceSelect = document.getElementById('source-airport');
        const destSelect = document.getElementById('destination-airport');
        
        // Clear existing options except the first
        sourceSelect.innerHTML = '<option value="">Select source airport...</option>';
        destSelect.innerHTML = '<option value="">Select destination airport...</option>';
        
        // Add airport options
        this.airports.forEach(airport => {
            const option1 = new Option(
                `${airport.code} - ${airport.name}`, 
                airport.code
            );
            const option2 = new Option(
                `${airport.code} - ${airport.name}`, 
                airport.code
            );
            
            sourceSelect.add(option1);
            destSelect.add(option2);
        });
    }

    initMap() {
        // Initialize Google Map
        this.map = new google.maps.Map(document.getElementById('route-map'), {
            center: { lat: 40.6413, lng: -73.7781 },
            zoom: 2,
            styles: [
                {
                    featureType: 'water',
                    elementType: 'geometry',
                    stylers: [{ color: '#e9e9e9' }, { lightness: 17 }]
                },
                {
                    featureType: 'landscape',
                    elementType: 'geometry',
                    stylers: [{ color: '#f5f5f5' }, { lightness: 20 }]
                }
            ],
            mapTypeControl: true,
            streetViewControl: false,
            fullscreenControl: true
        });
        
        // Store markers and polylines for cleanup
        this.mapMarkers = [];
        this.mapPolylines = [];
    }

    setupEventListeners() {
        // Optimize button
        document.getElementById('optimize-btn').addEventListener('click', () => {
            this.optimizeRoutes();
        });
        
        // Clear button
        document.getElementById('clear-btn').addEventListener('click', () => {
            this.clearResults();
        });
        
        // Upload button
        document.getElementById('upload-btn').addEventListener('click', () => {
            this.toggleUploadSection();
        });
        
        // File upload
        const fileInput = document.getElementById('file-input');
        const uploadArea = document.getElementById('upload-area');
        
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
        
        // Navigation links: only intercept hash links for smooth scroll
        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href') || '';
                if (href.startsWith('#')) {
                    e.preventDefault();
                    if (href === '#dashboard') {
                        // Open dashboard page
                        window.open('dashboard.html', '_blank');
                        return;
                    }
                    const element = document.querySelector(href);
                    if (element) {
                        element.scrollIntoView({ behavior: 'smooth' });
                    }
                }
                // Non-hash links fall through to default navigation (e.g., dashboard.html)
            });
        });
    }

    async checkHealth() {
        try {
            const response = await this.apiCall('/health');
            if (response.success) {
                console.log('API Health:', response.data);
            }
        } catch (error) {
            console.warn('Health check failed:', error);
        }
    }

    async optimizeRoutes() {
        if (this.isLoading) return;
        
        const source = document.getElementById('source-airport').value;
        const destination = document.getElementById('destination-airport').value;
        
        if (!source || !destination) {
            this.showError('Please select both source and destination airports');
            return;
        }
        
        if (source === destination) {
            this.showError('Source and destination airports cannot be the same');
            return;
        }
        
        this.setLoading(true);
        
        try {
            const params = {
                source: source,
                destination: destination,
                max_stops: parseInt(document.getElementById('max-stops').value),
                weather_weight: parseFloat(document.getElementById('weather-weight').value),
                include_alternatives: document.getElementById('include-alternatives').checked
            };
            
            const response = await this.apiCall('/routes/optimize', 'POST', params);
            
            if (response.success) {
                this.displayResults(response.data, source, destination);
            } else {
                this.showError(response.message || 'Failed to optimize routes');
            }
        } catch (error) {
            console.error('Route optimization failed:', error);
            this.showError('Failed to optimize routes. Please try again.');
        } finally {
            this.setLoading(false);
        }
    }

    displayResults(routes, source, destination) {
        this.currentRoutes = routes;
        
        // Show results section
        const resultsSection = document.getElementById('results');
        resultsSection.classList.add('active');
        
        // Update header
        const resultsTitle = document.querySelector('.results-title');
        resultsTitle.textContent = `Optimized Routes: ${source} → ${destination}`;
        
        // Fetch and display weather for both airports
        this.displayWeatherInfo(source, destination);
        
        // Clear existing route cards
        const routesGrid = document.getElementById('routes-grid');
        routesGrid.innerHTML = '';
        
        // Create route cards
        routes.forEach((route, index) => {
            const routeCard = this.createRouteCard(route, index);
            routesGrid.appendChild(routeCard);
        });
        
        // Update map
        this.updateMap(routes, source, destination);

        // Update chart visualization
        this.updateChart(routes);
        
        // Animate cards
        anime({
            targets: '.route-card',
            opacity: [0, 1],
            translateY: [30, 0],
            delay: anime.stagger(100),
            duration: 600,
            easing: 'easeOutQuart'
        });
    }

    updateChart(routes) {
        const chartDom = document.getElementById('route-chart');
        if (!chartDom || !window.echarts) return;

        const chart = echarts.getInstanceByDom(chartDom) || echarts.init(chartDom);
        
        // Prepare data
        const labels = routes.map((_, idx) => `Route ${idx + 1}`);
        const distances = routes.map(r => r.route.distance || 0);
        const weatherImpact = routes.map(r => (typeof r.weather_impact_score === 'number' ? r.weather_impact_score : 0));
        const fuelConsumption = routes.map(r => (r.estimated_fuel_consumption || 0) / 1000); // Convert to thousands
        const costs = routes.map(r => (r.estimated_cost || 0) / 1000); // Convert to thousands

        chart.setOption({
            title: {
                text: 'Route Comparison',
                left: 'center',
                textStyle: {
                    color: '#2C3E50',
                    fontSize: 18,
                    fontWeight: 600
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'shadow'
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: '#BDC3C7',
                borderWidth: 1,
                textStyle: {
                    color: '#2C3E50'
                },
                formatter: function(params) {
                    let result = `<strong>${params[0].axisValue}</strong><br/>`;
                    params.forEach(item => {
                        let value = item.value;
                        let unit = '';
                        if (item.seriesName === 'Distance') {
                            unit = ' km';
                        } else if (item.seriesName === 'Weather Impact') {
                            unit = '/100';
                        } else if (item.seriesName === 'Fuel') {
                            value = (value * 1000).toFixed(0);
                            unit = ' L';
                        } else if (item.seriesName === 'Cost') {
                            value = '$' + (value * 1000).toFixed(0);
                            unit = '';
                        }
                        result += `${item.marker} ${item.seriesName}: <strong>${typeof value === 'number' ? value.toFixed(1) : value}${unit}</strong><br/>`;
                    });
                    return result;
                }
            },
            legend: {
                data: ['Distance', 'Weather Impact', 'Fuel', 'Cost'],
                top: '35',
                textStyle: {
                    color: '#2C3E50',
                    fontSize: 12
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '5%',
                top: '80',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: labels,
                axisLabel: {
                    color: '#7F8C8D',
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#BDC3C7'
                    }
                }
            },
            yAxis: [
                {
                    type: 'value',
                    name: 'Distance (km) / Fuel (k L) / Cost (k $)',
                    nameTextStyle: {
                        color: '#7F8C8D',
                        fontSize: 11
                    },
                    axisLabel: {
                        color: '#7F8C8D',
                        fontSize: 11,
                        formatter: function(value) {
                            if (value >= 1000) {
                                return (value / 1000).toFixed(1) + 'k';
                            }
                            return value.toFixed(0);
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            color: '#ECF0F1'
                        }
                    }
                },
                {
                    type: 'value',
                    name: 'Weather Impact (0-100)',
                    nameTextStyle: {
                        color: '#7F8C8D',
                        fontSize: 11
                    },
                    max: 100,
                    axisLabel: {
                        color: '#7F8C8D',
                        fontSize: 11
                    },
                    splitLine: {
                        show: false
                    }
                }
            ],
            series: [
                {
                    name: 'Distance',
                    type: 'bar',
                    data: distances,
                    itemStyle: {
                        color: '#4A90E2',
                        borderRadius: [4, 4, 0, 0]
                    },
                    emphasis: {
                        itemStyle: {
                            color: '#3A7BC8'
                        }
                    }
                },
                {
                    name: 'Fuel',
                    type: 'bar',
                    data: fuelConsumption,
                    itemStyle: {
                        color: '#27AE60',
                        borderRadius: [4, 4, 0, 0]
                    },
                    emphasis: {
                        itemStyle: {
                            color: '#229954'
                        }
                    }
                },
                {
                    name: 'Cost',
                    type: 'bar',
                    data: costs,
                    itemStyle: {
                        color: '#9B59B6',
                        borderRadius: [4, 4, 0, 0]
                    },
                    emphasis: {
                        itemStyle: {
                            color: '#8E44AD'
                        }
                    }
                },
                {
                    name: 'Weather Impact',
                    type: 'line',
                    yAxisIndex: 1,
                    data: weatherImpact,
                    smooth: true,
                    lineStyle: {
                        color: '#F39C12',
                        width: 3
                    },
                    itemStyle: {
                        color: '#F39C12'
                    },
                    areaStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                { offset: 0, color: 'rgba(243, 156, 18, 0.3)' },
                                { offset: 1, color: 'rgba(243, 156, 18, 0.05)' }
                            ]
                        }
                    },
                    emphasis: {
                        itemStyle: {
                            color: '#E67E22'
                        }
                    },
                    symbolSize: 8
                }
            ]
        });
        
        // Make chart responsive
        window.addEventListener('resize', () => {
            chart.resize();
        });
    }

    createRouteCard(route, index) {
        const card = document.createElement('div');
        card.className = `route-card ${index === 0 ? 'best-route' : ''}`;
        
        const isDirect = route.route_type === 'direct';
        const isOneStop = route.route_type === 'one_stop';
        
        // Determine route type display
        let routeTypeDisplay = 'Direct';
        if (isOneStop) routeTypeDisplay = '1 Stop';
        else if (!isDirect) routeTypeDisplay = 'Multi-stop';
        
        // Calculate score colors
        const totalScoreColor = this.getScoreColor(route.total_score, 1000);
        const weatherScoreColor = this.getWeatherScoreColor(route.weather_impact_score);
        
        card.innerHTML = `
            <div class="route-header">
                <div class="route-airports">
                    <span class="airport-code">${route.route.source_airport}</span>
                    <i class="fas fa-arrow-right route-arrow"></i>
                    <span class="airport-code">${route.route.destination_airport}</span>
                </div>
                <span class="route-type">${routeTypeDisplay}</span>
            </div>
            
            <div class="route-details">
                <div class="detail-item">
                    <div class="detail-value">${route.route.distance.toLocaleString()}</div>
                    <div class="detail-label">Distance (km)</div>
                </div>
                <div class="detail-item">
                    <div class="detail-value">${this.formatDuration(route.route.duration)}</div>
                    <div class="detail-label">Duration</div>
                </div>
                <div class="detail-item">
                    <div class="detail-value">${route.route.aircraft_type}</div>
                    <div class="detail-label">Aircraft</div>
                </div>
                <div class="detail-item">
                    <div class="detail-value">${route.route.airline}</div>
                    <div class="detail-label">Airline</div>
                </div>
            </div>
            
            <div class="route-score">
                <div class="score-item">
                    <div class="score-value ${totalScoreColor}">${route.total_score.toFixed(1)}</div>
                    <div class="score-label">Total Score</div>
                </div>
                <div class="score-item">
                    <div class="score-value ${weatherScoreColor}">${route.weather_impact_score.toFixed(1)}</div>
                    <div class="score-label">Weather Impact</div>
                </div>
                <div class="score-item">
                    <div class="score-value">${route.estimated_fuel_consumption?.toLocaleString() || 'N/A'}</div>
                    <div class="score-label">Fuel (L)</div>
                </div>
                <div class="score-item">
                    <div class="score-value">$${route.estimated_cost?.toLocaleString() || 'N/A'}</div>
                    <div class="score-label">Est. Cost</div>
                </div>
            </div>
            
            ${route.weather_alerts && route.weather_alerts.length > 0 ? `
                <div class="weather-alerts">
                    ${route.weather_alerts.map(alert => `
                        <div class="alert-item">
                            <i class="fas fa-exclamation-triangle alert-icon"></i>
                            <span>${alert}</span>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            <div class="route-actions">
                <button class="btn btn-primary btn-small" onclick="app.viewRouteOnMap(${index})">
                    <i class="fas fa-map"></i> View on Map
                </button>
                <button class="btn btn-secondary btn-small" onclick="app.exportRoute(${index})">
                    <i class="fas fa-download"></i> Export
                </button>
            </div>
        `;
        
        return card;
    }

    getScoreColor(score, threshold) {
        if (score < threshold * 0.3) return 'good';
        if (score < threshold * 0.7) return 'fair';
        return 'poor';
    }

    getWeatherScoreColor(score) {
        if (score < 20) return 'good';
        if (score < 50) return 'fair';
        return 'poor';
    }

    formatDuration(minutes) {
        if (!minutes) return 'N/A';
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
    }

    updateMap(routes, source, destination) {
        // Clear existing markers and polylines
        this.mapMarkers.forEach(marker => marker.setMap(null));
        this.mapPolylines.forEach(polyline => polyline.setMap(null));
        this.mapMarkers = [];
        this.mapPolylines = [];
        
        // Get airport coordinates
        const sourceAirport = this.airports.find(a => a.code === source);
        const destAirport = this.airports.find(a => a.code === destination);
        
        if (!sourceAirport || !destAirport) return;
        
        const bounds = new google.maps.LatLngBounds();
        
        // Add airport markers
        const sourceMarker = new google.maps.Marker({
            position: { lat: sourceAirport.latitude, lng: sourceAirport.longitude },
            map: this.map,
            title: sourceAirport.code,
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 8,
                fillColor: '#4A90E2',
                fillOpacity: 1,
                strokeColor: '#fff',
                strokeWeight: 2
            }
        });
        
        const sourceInfoWindow = new google.maps.InfoWindow({
            content: `<b>${sourceAirport.code}</b><br>${sourceAirport.name}`
        });
        sourceMarker.addListener('click', () => sourceInfoWindow.open(this.map, sourceMarker));
        this.mapMarkers.push(sourceMarker);
        bounds.extend(sourceMarker.position);
        
        const destMarker = new google.maps.Marker({
            position: { lat: destAirport.latitude, lng: destAirport.longitude },
            map: this.map,
            title: destAirport.code,
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 8,
                fillColor: '#E74C3C',
                fillOpacity: 1,
                strokeColor: '#fff',
                strokeWeight: 2
            }
        });
        
        const destInfoWindow = new google.maps.InfoWindow({
            content: `<b>${destAirport.code}</b><br>${destAirport.name}`
        });
        destMarker.addListener('click', () => destInfoWindow.open(this.map, destMarker));
        this.mapMarkers.push(destMarker);
        bounds.extend(destMarker.position);
        
        // Add route paths
        routes.forEach((route, index) => {
            if (route.waypoints && route.waypoints.length > 0) {
                const path = route.waypoints.map(wp => ({ lat: wp.latitude, lng: wp.longitude }));
                
                const color = index === 0 ? '#27AE60' : '#4A90E2';
                const weight = index === 0 ? 4 : 2;
                const opacity = index === 0 ? 0.9 : 0.6;
                
                const polyline = new google.maps.Polyline({
                    path: path,
                    geodesic: true,
                    strokeColor: color,
                    strokeOpacity: opacity,
                    strokeWeight: weight,
                    map: this.map
                });
                
                this.mapPolylines.push(polyline);
                
                // Extend bounds to include all waypoints
                path.forEach(point => bounds.extend(point));
            }
        });
        
        // Fit map to show all routes
        this.map.fitBounds(bounds);
        
        // Ensure minimum zoom level
        const listener = google.maps.event.addListenerOnce(this.map, 'bounds_changed', () => {
            if (this.map.getZoom() > 15) {
                this.map.setZoom(15);
            }
        });
    }

    viewRouteOnMap(routeIndex) {
        const route = this.currentRoutes[routeIndex];
        if (!route || !route.waypoints) return;
        
        // Clear existing polylines (keep markers)
        this.mapPolylines.forEach(polyline => polyline.setMap(null));
        this.mapPolylines = [];
        
        // Add selected route with highlight color
        const path = route.waypoints.map(wp => ({ lat: wp.latitude, lng: wp.longitude }));
        const polyline = new google.maps.Polyline({
            path: path,
            geodesic: true,
            strokeColor: '#F39C12',
            strokeOpacity: 1,
            strokeWeight: 5,
            map: this.map
        });
        
        this.mapPolylines.push(polyline);
        
        // Fit map to selected route
        const bounds = new google.maps.LatLngBounds();
        path.forEach(point => bounds.extend(point));
        this.map.fitBounds(bounds);
        
        // Add some padding
        const listener = google.maps.event.addListenerOnce(this.map, 'bounds_changed', () => {
            const currentZoom = this.map.getZoom();
            this.map.setZoom(currentZoom - 0.5);
        });
        
        // Scroll to map
        document.querySelector('.map-container').scrollIntoView({ behavior: 'smooth' });
    }

    exportRoute(routeIndex) {
        const route = this.currentRoutes[routeIndex];
        if (!route) return;
        
        const data = {
            route: route,
            exported_at: new Date().toISOString(),
            source: 'Airline Route Optimizer'
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `route_${route.route.source_airport}_${route.route.destination_airport}_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
    }

    clearResults() {
        // Clear form
        document.getElementById('source-airport').value = '';
        document.getElementById('destination-airport').value = '';
        document.getElementById('max-stops').value = '1';
        document.getElementById('weather-weight').value = '0.3';
        document.getElementById('include-alternatives').checked = false;
        
        // Hide results
        document.getElementById('results').classList.remove('active');
        
        // Clear map markers and polylines
        this.mapMarkers.forEach(marker => marker.setMap(null));
        this.mapPolylines.forEach(polyline => polyline.setMap(null));
        this.mapMarkers = [];
        this.mapPolylines = [];
        
        // Reset map view
        this.map.setCenter({ lat: 40.6413, lng: -73.7781 });
        this.map.setZoom(2);
        
        this.currentRoutes = [];
    }

    toggleUploadSection() {
        const uploadSection = document.getElementById('upload-section');
        const isVisible = uploadSection.style.display !== 'none';
        
        uploadSection.style.display = isVisible ? 'none' : 'block';
        
        if (!isVisible) {
            uploadSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    async handleFileUpload(file) {
        if (!file.name.endsWith('.csv')) {
            this.showError('Please upload a CSV file');
            return;
        }
        
        try {
            const content = await this.readFileContent(file);
            const dataType = file.name.includes('airport') ? 'airports' : 'routes';
            
            const formData = new FormData();
            formData.append('file', new Blob([content], { type: 'text/csv' }), file.name);
            formData.append('type', dataType);
            
            const response = await fetch('/api/data/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Reload airports data to refresh dropdowns
                await this.loadAirports();
                this.showSuccess(`${result.message}. Loaded ${this.airports.length} airports.`);
            } else {
                this.showError(result.message || 'Upload failed');
            }
        } catch (error) {
            console.error('File upload failed:', error);
            this.showError('Failed to upload file');
        }
    }

    readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }

    setLoading(loading) {
        this.isLoading = loading;
        const loadingElement = document.getElementById('loading');
        const optimizeBtn = document.getElementById('optimize-btn');
        
        if (loading) {
            loadingElement.classList.add('active');
            optimizeBtn.disabled = true;
            optimizeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Optimizing...';
        } else {
            loadingElement.classList.remove('active');
            optimizeBtn.disabled = false;
            optimizeBtn.innerHTML = '<i class="fas fa-search"></i> Find Optimal Routes';
        }
    }

    async apiCall(endpoint, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${this.apiBase}${endpoint}`, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    async displayWeatherInfo(source, destination) {
        try {
            // Fetch weather for both airports
            const [sourceWeather, destWeather] = await Promise.all([
                this.apiCall(`/weather?airport=${source}`),
                this.apiCall(`/weather?airport=${destination}`)
            ]);
            
            // Create or update weather container
            let weatherContainer = document.getElementById('weather-info');
            if (!weatherContainer) {
                weatherContainer = document.createElement('div');
                weatherContainer.id = 'weather-info';
                weatherContainer.className = 'weather-info fade-in';
                document.querySelector('.results-header').after(weatherContainer);
            }
            
            weatherContainer.innerHTML = `
                <div class="weather-cards">
                    ${this.createWeatherCard(source, sourceWeather.data, 'departure')}
                    ${this.createWeatherCard(destination, destWeather.data, 'arrival')}
                </div>
            `;
        } catch (error) {
            console.error('Failed to fetch weather data:', error);
        }
    }
    
    createWeatherCard(airportCode, weather, type) {
        const isDeparture = type === 'departure';
        const icon = this.getWeatherIcon(weather.conditions);
        const conditionColor = this.getWeatherConditionColor(weather.conditions);
        
        return `
            <div class="weather-card ${type}">
                <div class="weather-header">
                    <div class="weather-airport">
                        <i class="fas ${isDeparture ? 'fa-plane-departure' : 'fa-plane-arrival'}"></i>
                        <span class="weather-airport-code">${airportCode}</span>
                    </div>
                    <div class="weather-label">${isDeparture ? 'Departure' : 'Arrival'}</div>
                </div>
                <div class="weather-main">
                    <div class="weather-icon-large">
                        <i class="fas ${icon}" style="color: ${conditionColor}"></i>
                    </div>
                    <div class="weather-temp">${Math.round(weather.temperature)}°C</div>
                    <div class="weather-condition">${weather.conditions.charAt(0).toUpperCase() + weather.conditions.slice(1)}</div>
                </div>
                <div class="weather-details">
                    <div class="weather-detail-item">
                        <i class="fas fa-wind"></i>
                        <span>${Math.round(weather.wind_speed)} km/h</span>
                    </div>
                    <div class="weather-detail-item">
                        <i class="fas fa-tint"></i>
                        <span>${weather.humidity}%</span>
                    </div>
                    <div class="weather-detail-item">
                        <i class="fas fa-eye"></i>
                        <span>${weather.visibility} km</span>
                    </div>
                    <div class="weather-detail-item">
                        <i class="fas fa-compress-arrows-alt"></i>
                        <span>${weather.pressure} hPa</span>
                    </div>
                </div>
                ${weather.precipitation > 0 ? `
                    <div class="weather-alert">
                        <i class="fas fa-cloud-rain"></i>
                        <span>Precipitation: ${weather.precipitation.toFixed(1)} mm/h</span>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    getWeatherIcon(condition) {
        const icons = {
            'clear': 'fa-sun',
            'clouds': 'fa-cloud',
            'rain': 'fa-cloud-rain',
            'drizzle': 'fa-cloud-rain',
            'thunderstorm': 'fa-bolt',
            'snow': 'fa-snowflake',
            'mist': 'fa-smog',
            'fog': 'fa-smog',
            'haze': 'fa-smog'
        };
        return icons[condition.toLowerCase()] || 'fa-cloud';
    }
    
    getWeatherConditionColor(condition) {
        const colors = {
            'clear': '#F39C12',
            'clouds': '#95A5A6',
            'rain': '#3498DB',
            'drizzle': '#3498DB',
            'thunderstorm': '#9B59B6',
            'snow': '#ECF0F1',
            'mist': '#BDC3C7',
            'fog': '#BDC3C7',
            'haze': '#BDC3C7'
        };
        return colors[condition.toLowerCase()] || '#95A5A6';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${type === 'error' ? '#E74C3C' : type === 'success' ? '#27AE60' : '#4A90E2'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
            z-index: 10000;
            max-width: 400px;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    }
}

// Initialize the application
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new RouteOptimizerApp();
    // Expose globally after initialization for button handlers
    window.app = app;
});

// Handle page visibility changes for performance
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Pause animations when page is hidden
        console.log('Page hidden - pausing animations');
    } else {
        // Resume animations when page is visible
        console.log('Page visible - resuming animations');
    }
});

// Handle window resize for responsive design
window.addEventListener('resize', () => {
    if (app && app.map) {
        google.maps.event.trigger(app.map, 'resize');
    }
});

// Export for global access (assigned after DOMContentLoaded above)