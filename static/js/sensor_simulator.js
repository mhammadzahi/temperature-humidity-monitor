function simulateSensorData() {
    const temperature = (Math.random() * 30 + 15).toFixed(1); // Temperature between 15°C and 45°C
    const humidity = (Math.random() * 60 + 20).toFixed(1); // Humidity between 20% and 80%
    const timestamp = new Date().toLocaleTimeString();

    // Update temperature and humidity variables
    window.temperature = parseFloat(temperature);
    window.humidity = parseFloat(humidity);

    document.getElementById('timestamp').textContent = 'Last updated: ' + timestamp;
}

setInterval(simulateSensorData, 5000); // Update data every 5 seconds

// Call simulateSensorData once to initialize the values
simulateSensorData();
