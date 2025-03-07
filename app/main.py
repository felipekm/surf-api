import requests
import os
import sqlite3
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
import aiosqlite
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize geocoder
geolocator = Nominatim(user_agent="surf_forecast_api")

# Stormglass API credentials
STORMGLASS_API_KEY = os.getenv("STORMGLASS_API_KEY")
STORMGLASS_API_URL = "https://api.stormglass.io/v2/weather/point"

# SQLite database file
DB_FILE = "locations_cache.db"

# Pydantic model for request validation
class SurfForecastRequest(BaseModel):
    location: str
    date: str  # Format: YYYY-MM-DD

# Create database tables (runs only once)
async def initialize_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS locations (
                location TEXT PRIMARY KEY,
                lat REAL,
                lng REAL
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS forecasts (
                location TEXT,
                date TEXT,
                wave_height REAL,
                wind_speed REAL,
                water_temperature REAL,
                meta TEXT,
                PRIMARY KEY (location, date)
            )"""
        )
        await db.commit()

@app.on_event("startup")
async def startup():
    await initialize_db()

# Function to check if forecast data is cached
async def get_cached_forecast(location: str, date: str):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(
            "SELECT wave_height, wind_speed, water_temperature, meta FROM forecasts WHERE location = ? AND date = ?", 
            (location, date)
        )
        row = await cursor.fetchone()
        return {
            "wave_height": row[0],
            "wind_speed": row[1],
            "water_temperature": row[2],
            "meta": json.loads(row[3])  # Convert JSON string back to dict
        } if row else None

# Function to cache forecast data
async def cache_forecast(location: str, date: str, forecast: dict):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            """INSERT INTO forecasts (location, date, wave_height, wind_speed, water_temperature, meta) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                location, date, 
                forecast["wave_height"], 
                forecast["wind_speed"], 
                forecast["water_temperature"], 
                json.dumps(forecast["meta"])  # Convert dict to JSON string
            )
        )
        await db.commit()

# Function to check the cache before geocoding
async def get_cached_coordinates(location: str):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT lat, lng FROM locations WHERE location = ?", (location,))
        row = await cursor.fetchone()
        return {"lat": row[0], "lng": row[1]} if row else None

# Function to store coordinates in SQLite cache
async def cache_coordinates(location: str, lat: float, lng: float):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT INTO locations (location, lat, lng) VALUES (?, ?, ?)", (location, lat, lng))
        await db.commit()

# Function to fetch coordinates dynamically with caching
async def get_coordinates(location: str):
    cached_result = await get_cached_coordinates(location)
    if cached_result:
        return cached_result  # Return cached value

    try:
        location_data = geolocator.geocode(location)
        if location_data:
            coords = {"lat": location_data.latitude, "lng": location_data.longitude}
            await cache_coordinates(location, coords["lat"], coords["lng"])  # Store in DB
            return coords
        return None
    except Exception:
        return None

@app.post("/forecast")
async def get_forecast(request: SurfForecastRequest):
    # Check if forecast is already cached
    cached_forecast = await get_cached_forecast(request.location, request.date)
    if cached_forecast:
        return {
            "location": request.location,
            "date": request.date,
            "latitude": None,  # Not needed if cached
            "longitude": None,  # Not needed if cached
            **cached_forecast  # Return cached data
        }

    # Fetch coordinates
    coordinates = await get_coordinates(request.location)
    
    if not coordinates:
        raise HTTPException(status_code=400, detail=f"Could not find coordinates for {request.location}")

    params = {
        "lat": coordinates["lat"],
        "lng": coordinates["lng"],
        "params": "waveHeight,windSpeed,waterTemperature",
        "source": "noaa",
    }

    headers = {"Authorization": STORMGLASS_API_KEY}

    try:
        response = requests.get(STORMGLASS_API_URL, params=params, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Stormglass API error: {response.text}")
        
        data = response.json()

        # Structure forecast data
        forecast_data = {
            "wave_height": data["hours"][0]["waveHeight"]["noaa"],
            "wind_speed": data["hours"][0]["windSpeed"]["noaa"],
            "water_temperature": data["hours"][0]["waterTemperature"]["noaa"],
            "meta": data["meta"]
        }

        # Cache the forecast data
        await cache_forecast(request.location, request.date, forecast_data)

        return {
            "location": request.location,
            "date": request.date,
            "latitude": coordinates["lat"],
            "longitude": coordinates["lng"],
            **forecast_data  # Include forecast data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
