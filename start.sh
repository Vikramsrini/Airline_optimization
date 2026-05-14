#!/bin/bash

# Airline Route Optimization Web Application Startup Script

echo "🛫 Starting Airline Route Optimization Web Application..."
echo "======================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

# Check if Java is installed (required for PySpark)
if ! command -v java &> /dev/null; then
        echo "⚠️  Java is not installed. PySpark requires Java 8 or higher."
        echo "Please install Java to enable full functionality."
        echo ""
else
        java_version=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}')
        echo "✅ Java detected: $java_version"
fi

# Ensure a compatible JDK (17) for Hadoop 3.3.x to avoid JAAS getSubject error on JDK 21+
ensure_jdk_17() {
    # Extract major version from possible formats: 1.8.x, 11.x, 17.x, 21.x
    local raw
    raw=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}')
    local major
    if [[ "$raw" == 1.* ]]; then
        major=8
    else
        major=$(echo "$raw" | cut -d. -f1)
    fi

    if [[ "$major" -ge 21 || -z "$major" ]]; then
        echo "⚠️  Detected Java $major; attempting to switch to JDK 17 for PySpark compatibility..."
        # Common macOS JDK 17 locations (Temurin/Adoptium or Oracle)
        for jdk in /Library/Java/JavaVirtualMachines/*17*.jdk/Contents/Home; do
            if [[ -d "$jdk" ]]; then
                export JAVA_HOME="$jdk"
                export PATH="$JAVA_HOME/bin:$PATH"
                echo "✅ Switched JAVA_HOME to: $JAVA_HOME"
                java -version 2>&1 | sed 's/^/   /'
                break
            fi
        done
        if [[ -z "$JAVA_HOME" || ! -x "$JAVA_HOME/bin/java" ]]; then
            echo "❌ Could not find a local JDK 17 under /Library/Java/JavaVirtualMachines."
            echo "   Please install Temurin 17 (LTS) and re-run this script."
        fi
    fi
}

ensure_jdk_17

# Silence native access warnings on newer JDKs
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS} --enable-native-access=ALL-UNNAMED"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ Dependencies installed successfully"
    else
        echo "❌ Failed to install dependencies"
        exit 1
    fi
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export PORT=5000

# Create data directory if it doesn't exist
mkdir -p ../data

# Copy sample data if needed
if [ ! -f "../data/routes.csv" ]; then
    echo "📋 Copying sample route data..."
    cp ../data/sample_routes.csv ../data/routes.csv
fi

if [ ! -f "../data/airports.csv" ]; then
    echo "📋 Copying sample airport data..."
    cp ../data/sample_airports.csv ../data/airports.csv
fi

echo ""
echo "🚀 Starting Flask application..."
echo ""
echo "Application will be available at:"
echo "  • Main App: http://localhost:5000"
echo "  • Spark UI: http://localhost:4040 (when Spark is running)"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Start the Flask application
python3 app.py