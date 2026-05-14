// Configuration file for frontend settings
// Replace with your actual Google Maps API key

const CONFIG = {
    GOOGLE_MAPS_API_KEY: 'YOUR_GOOGLE_MAPS_API_KEY', // Replace this with your valid key
    API_BASE_URL: '/api'
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
