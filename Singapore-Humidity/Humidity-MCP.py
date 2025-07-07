import asyncio
import json
import requests
from mcp.server import Server
import mcp.server.stdio
import mcp.types as types
from datetime import datetime

# Relative Humidity data fetcher functions
def fetch_humidity_data():
    """Fetch raw relative humidity data from Singapore API"""
    try:
        url = "https://api-open.data.gov.sg/v2/real-time/api/relative-humidity"
        
        response = requests.get(url)
        json_data = response.json()
        
        if json_data['code'] != 0:
            return None, f"API Error: {json_data.get('errorMsg', 'Unknown error')}"
        
        return json_data['data'], None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def get_humidity_summary():
    """Get humidity summary for all stations"""
    data, error = fetch_humidity_data()
    if error:
        return error
    
    if not data.get('readings'):
        return "No humidity data available"
    
    latest_reading = data['readings'][0]
    stations = {station['id']: station for station in data['stations']}
    
    # Extract humidity values
    humidity_values = []
    station_data = {}
    
    for reading in latest_reading['data']:
        station_id = reading['stationId']
        value = reading['value']
        humidity_values.append(value)
        
        if station_id in stations:
            station_data[station_id] = {
                'name': stations[station_id]['name'],
                'value': value,
                'location': stations[station_id]['location']
            }
    
    if not humidity_values:
        return "No humidity readings available"
    
    summary = {
        'timestamp': latest_reading['timestamp'],
        'reading_type': data['readingType'],
        'unit': data['readingUnit'],
        'total_stations': len(humidity_values),
        'highest_humidity': max(humidity_values),
        'lowest_humidity': min(humidity_values),
        'average_humidity': round(sum(humidity_values) / len(humidity_values), 1),
        'stations': station_data
    }
    
    return summary

def get_humidity_by_station(station_id=None):
    """Get humidity data for a specific station or all stations"""
    data, error = fetch_humidity_data()
    if error:
        return error
    
    if not data.get('readings'):
        return "No humidity data available"
    
    latest_reading = data['readings'][0]
    stations = {station['id']: station for station in data['stations']}
    
    if station_id:
        station_id = station_id.upper()
        # Find the specific station reading
        station_reading = None
        for reading in latest_reading['data']:
            if reading['stationId'] == station_id:
                station_reading = reading
                break
        
        if not station_reading:
            available_stations = [s['id'] for s in data['stations']]
            return f"Station '{station_id}' not found. Available stations: {', '.join(available_stations)}"
        
        if station_id not in stations:
            return f"Station metadata not found for '{station_id}'"
        
        station_info = stations[station_id]
        station_data = {
            'station_id': station_id,
            'name': station_info['name'],
            'timestamp': latest_reading['timestamp'],
            'humidity': station_reading['value'],
            'unit': data['readingUnit'],
            'reading_type': data['readingType'],
            'location': station_info['location']
        }
        return station_data
    
    # Return all stations
    all_stations = {}
    for reading in latest_reading['data']:
        station_id = reading['stationId']
        if station_id in stations:
            all_stations[station_id] = {
                'name': stations[station_id]['name'],
                'humidity': reading['value'],
                'location': stations[station_id]['location']
            }
    
    return {
        'timestamp': latest_reading['timestamp'],
        'reading_type': data['readingType'],
        'unit': data['readingUnit'],
        'stations': all_stations
    }

def get_humidity_categories():
    """Get humidity data with comfort level categories"""
    data, error = fetch_humidity_data()
    if error:
        return error
    
    if not data.get('readings'):
        return "No humidity data available"
    
    latest_reading = data['readings'][0]
    stations = {station['id']: station for station in data['stations']}
    
    def get_comfort_level(humidity):
        if humidity < 30:
            return "Very Dry"
        elif humidity < 40:
            return "Dry"
        elif humidity < 60:
            return "Comfortable"
        elif humidity < 70:
            return "Slightly Humid"
        elif humidity < 80:
            return "Humid"
        else:
            return "Very Humid"
    
    categorized_data = {
        'timestamp': latest_reading['timestamp'],
        'reading_type': data['readingType'],
        'unit': data['readingUnit'],
        'stations': {}
    }
    
    for reading in latest_reading['data']:
        station_id = reading['stationId']
        humidity = reading['value']
        
        if station_id in stations:
            categorized_data['stations'][station_id] = {
                'name': stations[station_id]['name'],
                'humidity': humidity,
                'comfort_level': get_comfort_level(humidity),
                'location': stations[station_id]['location']
            }
    
    return categorized_data

def get_station_locations():
    """Get all humidity monitoring station locations"""
    data, error = fetch_humidity_data()
    if error:
        return error
    
    if not data.get('stations'):
        return "No station data available"
    
    locations = []
    for station in data['stations']:
        locations.append({
            'station_id': station['id'],
            'name': station['name'],
            'device_id': station['deviceId'],
            'latitude': station['location']['latitude'],
            'longitude': station['location']['longitude']
        })
    
    return {
        'total_stations': len(locations),
        'stations': locations
    }

def get_humidity_extremes():
    """Get stations with highest and lowest humidity"""
    data, error = fetch_humidity_data()
    if error:
        return error
    
    if not data.get('readings'):
        return "No humidity data available"
    
    latest_reading = data['readings'][0]
    stations = {station['id']: station for station in data['stations']}
    
    station_readings = []
    for reading in latest_reading['data']:
        station_id = reading['stationId']
        if station_id in stations:
            station_readings.append({
                'station_id': station_id,
                'name': stations[station_id]['name'],
                'humidity': reading['value'],
                'location': stations[station_id]['location']
            })
    
    if not station_readings:
        return "No station readings available"
    
    # Sort by humidity
    station_readings.sort(key=lambda x: x['humidity'])
    
    return {
        'timestamp': latest_reading['timestamp'],
        'lowest_humidity': station_readings[0],
        'highest_humidity': station_readings[-1],
        'all_readings': station_readings
    }

# Create server
server = Server("humidity-singapore")

@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="humidity_summary",
            description="Get humidity summary for all weather stations in Singapore",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="humidity_by_station",
            description="Get humidity data for a specific station or all stations",
            inputSchema={
                "type": "object",
                "properties": {
                    "station_id": {
                        "type": "string",
                        "description": "Station ID (e.g., S111). Leave empty for all stations."
                    }
                }
            }
        ),
        types.Tool(
            name="humidity_categories",
            description="Get humidity data with comfort level categories",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="station_locations",
            description="Get locations and metadata of all humidity monitoring stations",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="humidity_extremes",
            description="Get stations with highest and lowest humidity readings",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "humidity_summary":
        summary = get_humidity_summary()
        if isinstance(summary, str):  # Error message
            return [types.TextContent(type="text", text=summary)]
        
        result = f"Humidity Summary for Singapore\n"
        result += f"Timestamp: {summary['timestamp']}\n"
        result += f"Reading Type: {summary['reading_type']}\n"
        result += f"Unit: {summary['unit']}\n\n"
        result += f"Overall Statistics:\n"
        result += f"  Total Stations: {summary['total_stations']}\n"
        result += f"  Highest Humidity: {summary['highest_humidity']}%\n"
        result += f"  Lowest Humidity: {summary['lowest_humidity']}%\n"
        result += f"  Average Humidity: {summary['average_humidity']}%\n\n"
        result += f"Station Readings:\n"
        for station_id, info in summary['stations'].items():
            result += f"  {info['name']} ({station_id}): {info['value']}%\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "humidity_by_station":
        station_id = arguments.get("station_id")
        data = get_humidity_by_station(station_id)
        
        if isinstance(data, str):  # Error message
            return [types.TextContent(type="text", text=data)]
        
        if station_id:
            # Single station data
            result = f"Humidity Data for {data['name']} ({data['station_id']})\n"
            result += f"Timestamp: {data['timestamp']}\n"
            result += f"Reading Type: {data['reading_type']}\n\n"
            result += f"Current Reading:\n"
            result += f"  Humidity: {data['humidity']}{data['unit']}\n\n"
            result += f"Location:\n"
            result += f"  Latitude: {data['location']['latitude']}\n"
            result += f"  Longitude: {data['location']['longitude']}\n"
        else:
            # All stations data
            result = f"Humidity Data for All Stations\n"
            result += f"Timestamp: {data['timestamp']}\n"
            result += f"Reading Type: {data['reading_type']}\n"
            result += f"Unit: {data['unit']}\n\n"
            result += f"Station Readings:\n"
            for station_id, info in data['stations'].items():
                result += f"  {info['name']} ({station_id}): {info['humidity']}%\n"
                result += f"    Location: {info['location']['latitude']}, {info['location']['longitude']}\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "humidity_categories":
        categories = get_humidity_categories()
        if isinstance(categories, str):  # Error message
            return [types.TextContent(type="text", text=categories)]
        
        result = f"Humidity Comfort Levels for Singapore\n"
        result += f"Timestamp: {categories['timestamp']}\n"
        result += f"Reading Type: {categories['reading_type']}\n\n"
        result += f"Station Comfort Levels:\n"
        for station_id, info in categories['stations'].items():
            result += f"  {info['name']} ({station_id}):\n"
            result += f"    Humidity: {info['humidity']}%\n"
            result += f"    Comfort Level: {info['comfort_level']}\n"
            result += f"    Location: {info['location']['latitude']}, {info['location']['longitude']}\n\n"
        
        result += f"Comfort Level Categories:\n"
        result += f"  < 30%: Very Dry\n"
        result += f"  30-39%: Dry\n"
        result += f"  40-59%: Comfortable\n"
        result += f"  60-69%: Slightly Humid\n"
        result += f"  70-79%: Humid\n"
        result += f"  80%+: Very Humid\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "station_locations":
        locations = get_station_locations()
        if isinstance(locations, str):  # Error message
            return [types.TextContent(type="text", text=locations)]
        
        result = f"Humidity Monitoring Stations in Singapore\n"
        result += f"Total Stations: {locations['total_stations']}\n\n"
        for station in locations['stations']:
            result += f"Station: {station['name']} ({station['station_id']})\n"
            result += f"  Device ID: {station['device_id']}\n"
            result += f"  Latitude: {station['latitude']}\n"
            result += f"  Longitude: {station['longitude']}\n\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "humidity_extremes":
        extremes = get_humidity_extremes()
        if isinstance(extremes, str):  # Error message
            return [types.TextContent(type="text", text=extremes)]
        
        result = f"Humidity Extremes in Singapore\n"
        result += f"Timestamp: {extremes['timestamp']}\n\n"
        result += f"Lowest Humidity:\n"
        low = extremes['lowest_humidity']
        result += f"  {low['name']} ({low['station_id']}): {low['humidity']}%\n"
        result += f"  Location: {low['location']['latitude']}, {low['location']['longitude']}\n\n"
        result += f"Highest Humidity:\n"
        high = extremes['highest_humidity']
        result += f"  {high['name']} ({high['station_id']}): {high['humidity']}%\n"
        result += f"  Location: {high['location']['latitude']}, {high['location']['longitude']}\n\n"
        result += f"All Readings (sorted by humidity):\n"
        for reading in extremes['all_readings']:
            result += f"  {reading['name']} ({reading['station_id']}): {reading['humidity']}%\n"
        
        return [types.TextContent(type="text", text=result)]
    
    return [types.TextContent(type="text", text="Unknown tool")]

async def main():
    async with mcp.server.stdio.stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())