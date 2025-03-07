# Surf Forecast API

This is a **FastAPI**-based Surf Forecast API that retrieves real-time surf conditions for different locations using the **Stormglass API**. The application supports location-based caching using **SQLite** to improve performance.

---

## **🚀 Features**
- Fetches **wave height, wind speed, and water temperature** for a given location and date.
- **Geocoding support** via OpenStreetMap to dynamically retrieve latitude/longitude.
- **SQLite caching** for both location coordinates and surf forecasts.
- **Asynchronous support** for improved performance.
- **Auto-retries on failures** and API error handling.

---

## **🔧 Setup & Installation**
### **1️⃣ Clone the Repository**
```bash
# Clone the repository
git clone https://github.com/yourusername/surf-forecast-api.git
cd surf-forecast-api
```

### **2️⃣ Install Dependencies**
Ensure you have **Python 3.9+** installed. Then, set up a virtual environment:
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # For macOS/Linux
venv\Scripts\activate    # For Windows

# Install required dependencies
pip install --upgrade pip
pip install fastapi uvicorn requests aiosqlite geopy python-dotenv
```

### **3️⃣ Set Up API Keys**
You need a **Stormglass API key**. Sign up at [Stormglass.io](https://stormglass.io/) and get an API key.

Create a `.env` file in the project root and add:
```ini
STORMGLASS_API_KEY=your_api_key_here
```

### **4️⃣ Run the Application**
```bash
uvicorn app.main:app --reload
```

### **5️⃣ Test the API**
You can use **cURL** or **Postman** to test the API.

#### **Example Request:**
```bash
curl -X 'POST' 
  'http://127.0.0.1:8000/forecast'   -H 'Content-Type: application/json'   -d '{ "location": "Praia do Rosa, SC, Brazil", "date": "2025-03-10" }'
```

#### **Example Response:**
```json
{
  "location": "Praia do Rosa, SC, Brazil",
  "date": "2025-03-10",
  "latitude": -28.1260,
  "longitude": -48.6436,
  "wave_height": 2.5,
  "wind_speed": 15,
  "water_temperature": 24,
  "meta": { "source": "noaa" }
}
```

---

## **🗄️ Database & Caching**
- **SQLite database (`locations_cache.db`)** is used for caching.
- **Cached data includes:**
  - **Coordinates** (so we don’t re-query OpenStreetMap for the same location).
  - **Surf forecasts** (to reduce external API calls).
- The cache **persists between application restarts**.

If you ever need to **clear the cache**, delete the database:
```bash
rm locations_cache.db
```

---

## **🛠 API Endpoints**
### **📍 `POST /forecast`**
Fetches surf forecast data for a location.
#### **Request Body:**
```json
{
  "location": "Hawaii",
  "date": "2025-03-10"
}
```
#### **Response:**
```json
{
  "location": "Hawaii",
  "date": "2025-03-10",
  "latitude": 21.3069,
  "longitude": -157.8583,
  "wave_height": 2.5,
  "wind_speed": 10,
  "water_temperature": 27,
  "meta": { "source": "noaa" }
}
```

---

## **🎯 Next Improvements**
- 🔹 **Add Redis caching** to further optimize performance.
- 🔹 **Implement automatic cache expiration**.
- 🔹 **Support more surf parameters** (e.g., swell period, tide levels).
- 🔹 **Improve location handling** by integrating a full geolocation API.

---

## **📜 License**
This project is open-source under the **MIT License**.

---

## **👨‍💻 Author**
Developed by **Felipe Kautzmann** 🚀