import mysql.connector
import bcrypt
import requests
import sys
import argparse
from getpass import getpass
from datetime import datetime, timedelta
import pickle
import os

# Database credentials
DB_USER = 'sss_assignment_sep24'
DB_PASSWORD = 'doitnow'
DB_NAME = 'weather_db'
DB_HOST = 'localhost'

# OpenWeatherMap API credentials
API_KEY = 'API_KEY_HERE'

# File to store user sessions
SESSION_FILE = 'user_sessions.pkl'

# Connect to the MySQL database
def connect_db():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        sys.exit(1)



# Register a new user
def register():
    conn = connect_db()
    cursor = conn.cursor()

    username = input("Enter username: ").strip()
    if not username:
        print("Error: Username cannot be empty.")
        return

    password = getpass("Enter password: ")
    if not password:
        print("Error: Password cannot be empty.")
        return

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password.decode('utf-8')))
        conn.commit()
        print("Registration successful!")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()


# User login
def login():
    conn = connect_db()
    cursor = conn.cursor()

    username = input("Enter username: ").strip()
    if not username:
        print("Error: Username cannot be empty.")
        return None

    password = getpass("Enter password: ")
    if not password:
        print("Error: Password cannot be empty.")
        return None

    try:
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            print("Login successful!")
            store_session(username)
            return username
        else:
            print("Invalid username or password.")
            return None
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


# Store user session and clear previous sessions
def store_session(username):
    try:
        sessions = {username: datetime.now()}
        with open(SESSION_FILE, 'wb') as f:
            pickle.dump(sessions, f)
    except Exception as e:
        print(f"Error storing session: {e}")



# Load user sessions
def load_sessions():
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'rb') as f:
                return pickle.load(f)
        else:
            return {}
    except Exception as e:
        print(f"Error loading sessions: {e}")
        return {}



# Check if the user's session is still valid
def is_session_valid(username):
    try:
        sessions = load_sessions()
        if username not in sessions:
            return False
        session_start_time = sessions[username]
        if datetime.now() - session_start_time > timedelta(minutes=5):
            print("Session expired. Please log in again.")
            del sessions[username]
            with open(SESSION_FILE, 'wb') as f:
                pickle.dump(sessions, f)
            return False
        return True
    except Exception as e:
        print(f"Error checking session validity: {e}")
        return False



# Save search history
def save_search_history(username, location, weather_data):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_id = cursor.fetchone()

        if user_id:
            user_id = user_id[0]
            weather_data_str = format_weather_data(weather_data)
            cursor.execute(
                "INSERT INTO search_history (user_id, location, weather_data) VALUES (%s, %s, %s)",
                (user_id, location, weather_data_str)
            )
            conn.commit()
            print("Search history saved!")
        else:
            print("User not found.")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()



# Format weather data
def format_weather_data(data):
    try:
        temp = data['main']['temp'] - 273.15
        humidity = data['main']['humidity']
        weather_desc = data['weather'][0]['description']
        wind_speed = data['wind']['speed']
        return (f"Temperature: {temp:.2f}°C, "
                f"Humidity: {humidity}%, "
                f"Weather: {weather_desc.capitalize()}, "
                f"Wind Speed: {wind_speed} m/s")
    except KeyError as e:
        print(f"Error formatting weather data: {e}")
        return "Data format error"



# Fetch weather data using OpenWeatherMap API
def fetch_weather(username, location):
    if not is_session_valid(username):
        print("You need to log in first.")
        return

    try:
        response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}")
        if response.status_code == 429:
            print("API rate limit exceeded. Please try again later.")
            return
        elif response.status_code == 200:
            data = response.json()
            print_weather(data)
            save_search_history(username, location, data)
        else:
            data = response.json()
            print(f"Error fetching weather data: {data.get('message', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")




# Print weather data
def print_weather(data):
    try:
        temp = data['main']['temp'] - 273.15
        humidity = data['main']['humidity']
        weather_desc = data['weather'][0]['description']
        wind_speed = data['wind']['speed']

        print(f"Temperature: {temp:.2f}°C")
        print(f"Humidity: {humidity}%")
        print(f"Weather: {weather_desc.capitalize()}")
        print(f"Wind Speed: {wind_speed} m/s")
    except KeyError as e:
        print(f"Error printing weather data: {e}")



# Show search history
def show_search_history(username):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_id = cursor.fetchone()

        if user_id:
            user_id = user_id[0]
            cursor.execute("SELECT timestamp, location, weather_data FROM search_history WHERE user_id = %s", (user_id,))
            history = cursor.fetchall()
            if history:
                for entry in history:
                    timestamp, location, weather_data = entry
                    print(f"Date: {timestamp}, Location: {location}, Weather Data: {weather_data}")
            else:
                print("No search history found.")
        else:
            print("User not found.")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()



# Update user data
def update_user(username):
    conn = connect_db()
    cursor = conn.cursor()

    if not is_session_valid(username):
        print("Session expired or invalid. Please log in again.")
        return

    new_password = getpass("Enter new password: ")
    if not new_password:
        print("Error: Password cannot be empty.")
        return

    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_password.decode('utf-8'), username))
        conn.commit()
        print("Password updated successfully!")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# CLI logic
def main():
    parser = argparse.ArgumentParser(description="Weather CLI Application")
    parser.add_argument('--register', action='store_true', help="Register a new user")
    parser.add_argument('--login', action='store_true', help="Login an existing user")
    parser.add_argument('--weather', type=str, help="Fetch weather data for a location")
    parser.add_argument('--history', action='store_true', help="Show search history for the logged-in user")
    parser.add_argument('--update', action='store_true', help="Update user password")
    args = parser.parse_args()

    if args.register:
        register()
    elif args.login:
        username = login()
        if username:
            print(f"Welcome {username}!")
    elif args.weather:
        sessions = load_sessions()
        logged_in_users = [user for user in sessions if is_session_valid(user)]
        if logged_in_users:
            username = logged_in_users[0]
            fetch_weather(username, args.weather)
        else:
            print("No valid session found. Please log in first.")
    elif args.history:
        sessions = load_sessions()
        logged_in_users = [user for user in sessions if is_session_valid(user)]
        if logged_in_users:
            username = logged_in_users[0]
            show_search_history(username)
        else:
            print("No valid session found. Please log in first.")
    elif args.update:
        sessions = load_sessions()
        logged_in_users = [user for user in sessions if is_session_valid(user)]
        if logged_in_users:
            username = logged_in_users[0]
            update_user(username)
        else:
            print("No valid session found. Please log in first.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
