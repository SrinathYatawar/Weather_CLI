# Weather CLI Application

The Weather CLI Application is a command-line tool that allows users to register, log in, fetch weather data for specific locations, view their search history, and update their passwords. The application interacts with a MySQL database to manage user information and search history.

## Prerequisites

- Python 3.8 or higher
- MySQL Server
- Required Python packages

## Setting Up the Environment

1. **Install Python Packages:**
   ```sh
   pip install mysql-connector-python bcrypt requests
#Set Up MySQL Database:

CREATE USER 'sss_assignment_sep24'@'localhost' IDENTIFIED BY 'doitnow';
GRANT ALL PRIVILEGES ON weather_db.* TO 'sss_assignment_sep24'@'localhost';
FLUSH PRIVILEGES;

Create Database & Tables:

CREATE DATABASE weather_db;
USE weather_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location VARCHAR(100),
    weather_data TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
API Key

API_KEY = 'your_openweathermap_api_key_here'
