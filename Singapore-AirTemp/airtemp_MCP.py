import asyncio
import json
import requests
from mcp.server import Server
import mcp.server.stdio
import mcp.types as types

class AirTempService:
    """Service to fetch and process air temperature data from Singapore's data.gov.sg"""
    
    def __init__(self):
        self.url = "https://api-open.data.gov.sg/v2/real-time/api/air-temperature"
    
    def fetch_air_temp_data(self):
        """Fetch air temperature data from the API"""
        try:
            response = requests.get(self.url)
            data = response.json()
            
            if data['code'] != 0:
                return None, f"API Error: {data['errorMsg']}"
            
            return data['data'], None
            
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def get_all_temperatures(self):
        """Get all air temperature readings with station details"""
        data, error = self.fetch_air_temp_data()
        if error:
            return error
        
        stations = {station['id']: station for station in data['stations']}
        readings = data['readings'][0]['data'] if data['readings'] else []
        
        all_temps = []
        for reading in readings:
            station_id = reading['stationId']
            station_info = stations.get(station_id, {})
            
            temp_info = {
                'station_id': station_id,
                'station_name': station_info.get('name', 'Unknown'),
                'temperature': reading['value'],
                'location': station_info.get('location', {}),
                'unit': data.get('readingUnit', 'deg C')
            }
            all_temps.append(temp_info)
        
        return {
            'timestamp': data['readings'][0]['timestamp'] if data['readings'] else None,
            'reading_type': data.get('readingType', 'Unknown'),
            'total_stations': len(all_temps),
            'temperatures': all_temps
        }
    
    def get_highest_temperature(self):
        """Get the station with the highest temperature"""
        data, error = self.fetch_air_temp_data()
        if error:
            return error
        
        stations = {station['id']: station for station in data['stations']}
        readings = data['readings'][0]['data'] if data['readings'] else []
        
        if not readings:
            return "No temperature readings available"
        
        # Find highest temperature
        highest_reading = max(readings, key=lambda x: x['value'])
        station_info = stations.get(highest_reading['stationId'], {})
        
        return {
            'station_id': highest_reading['stationId'],
            'station_name': station_info.get('name', 'Unknown'),
            'temperature': highest_reading['value'],
            'location': station_info.get('location', {}),
            'unit': data.get('readingUnit', 'deg C'),
            'timestamp': data['readings'][0]['timestamp']
        }
    
    def get_lowest_temperature(self):
        """Get the station with the lowest temperature"""
        data, error = self.fetch_air_temp_data()
        if error:
            return error
        
        stations = {station['id']: station for station in data['stations']}
        readings = data['readings'][0]['data'] if data['readings'] else []
        
        if not readings:
            return "No temperature readings available"
        
        # Find lowest temperature
        lowest_reading = min(readings, key=lambda x: x['value'])
        station_info = stations.get(lowest_reading['stationId'], {})
        
        return {
            'station_id': lowest_reading['stationId'],
            'station_name': station_info.get('name', 'Unknown'),
            'temperature': lowest_reading['value'],
            'location': station_info.get('location', {}),
            'unit': data.get('readingUnit', 'deg C'),
            'timestamp': data['readings'][0]['timestamp']
        }

# Create server
server = Server("air-temperature")

@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="get_all_air_temperatures",
            description="Get all current air temperature readings from all stations in Singapore",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_highest_temperature",
            description="Get the station with the highest current air temperature",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_lowest_temperature",
            description="Get the station with the lowest current air temperature",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    service = AirTempService()
    
    if name == "get_all_air_temperatures":
        result = service.get_all_temperatures()
        
        if isinstance(result, str):  # Error message
            return [types.TextContent(type="text", text=result)]
        
        # Format the output nicely
        output = f"Air Temperature Readings\n"
        output += f"========================\n"
        output += f"Timestamp: {result['timestamp']}\n"
        output += f"Reading Type: {result['reading_type']}\n"
        output += f"Total Stations: {result['total_stations']}\n\n"
        
        for temp in result['temperatures']:
            output += f"Station: {temp['station_name']} ({temp['station_id']})\n"
            output += f"  Temperature: {temp['temperature']}°{temp['unit']}\n"
            if temp['location']:
                output += f"  Location: {temp['location']['latitude']}, {temp['location']['longitude']}\n"
            output += "\n"
        
        return [types.TextContent(type="text", text=output)]
    
    elif name == "get_highest_temperature":
        result = service.get_highest_temperature()
        
        if isinstance(result, str):  # Error message
            return [types.TextContent(type="text", text=result)]
        
        output = f"Highest Temperature Reading\n"
        output += f"==========================\n"
        output += f"Station: {result['station_name']} ({result['station_id']})\n"
        output += f"Temperature: {result['temperature']}°{result['unit']}\n"
        if result['location']:
            output += f"Location: {result['location']['latitude']}, {result['location']['longitude']}\n"
        output += f"Timestamp: {result['timestamp']}\n"
        
        return [types.TextContent(type="text", text=output)]
    
    elif name == "get_lowest_temperature":
        result = service.get_lowest_temperature()
        
        if isinstance(result, str):  # Error message
            return [types.TextContent(type="text", text=result)]
        
        output = f"Lowest Temperature Reading\n"
        output += f"=========================\n"
        output += f"Station: {result['station_name']} ({result['station_id']})\n"
        output += f"Temperature: {result['temperature']}°{result['unit']}\n"
        if result['location']:
            output += f"Location: {result['location']['latitude']}, {result['location']['longitude']}\n"
        output += f"Timestamp: {result['timestamp']}\n"
        
        return [types.TextContent(type="text", text=output)]
    
    return [types.TextContent(type="text", text="Unknown tool")]

async def main():
    async with mcp.server.stdio.stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

# Test function for standalone mode
def test_standalone():
    """Test the air temperature service without MCP"""
    service = AirTempService()
    
    print("=== Testing Air Temperature Service ===")
    
    try:
        # Test 1: Get all temperatures
        all_temps = service.get_all_temperatures()
        if isinstance(all_temps, str):
            print(f"Error: {all_temps}")
            return
        
        print(f"Total stations: {all_temps['total_stations']}")
        print(f"Timestamp: {all_temps['timestamp']}")
        print(f"First few temperatures:")
        for temp in all_temps['temperatures'][:3]:
            print(f"  {temp['station_name']}: {temp['temperature']}°C")
        
        # Test 2: Get highest temperature
        highest = service.get_highest_temperature()
        if not isinstance(highest, str):
            print(f"\nHighest: {highest['station_name']} - {highest['temperature']}°C")
        
        # Test 3: Get lowest temperature
        lowest = service.get_lowest_temperature()
        if not isinstance(lowest, str):
            print(f"Lowest: {lowest['station_name']} - {lowest['temperature']}°C")
            
    except Exception as e:
        print(f"Error testing service: {e}")

if __name__ == "__main__":
    # Try to run as MCP server, fallback to standalone test
    try:
        asyncio.run(main())
    except ImportError:
        print("MCP not available, running standalone test...")
        test_standalone()
    except KeyboardInterrupt:
        print("Server stopped")
    except Exception as e:
        print(f"Error running server: {e}")
        print("Running standalone test instead...")
        test_standalone()