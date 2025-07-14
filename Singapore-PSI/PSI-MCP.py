import asyncio
import json
import requests
from mcp.server import Server
import mcp.server.stdio
import mcp.types as types

# PSI data fetcher functions
def fetch_psi_data():
    """Fetch raw PSI data from Singapore API"""
    try:
        url = "https://api-open.data.gov.sg/v2/real-time/api/psi"
        
        response = requests.get(url)
        json_data = response.json()
        
        if json_data['code'] != 0:
            return None, f"API Error: {json_data['errorMsg']}"
        
        return json_data['data'], None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def get_psi_summary():
    """Get PSI summary for all regions"""
    data, error = fetch_psi_data()
    if error:
        return error
    
    if not data.get('items'):
        return "No PSI data available"
    
    latest_item = data['items'][0]
    psi_readings = latest_item['readings']['psi_twenty_four_hourly']
    
    summary = {
        'timestamp': latest_item['timestamp'],
        'updated': latest_item['updatedTimestamp'],
        'date': latest_item['date'],
        'psi_readings': psi_readings,
        'highest_psi': max(psi_readings.values()),
        'lowest_psi': min(psi_readings.values()),
        'average_psi': round(sum(psi_readings.values()) / len(psi_readings), 1)
    }
    
    return summary

def get_psi_by_region(region=None):
    """Get PSI data for a specific region or all regions"""
    data, error = fetch_psi_data()
    if error:
        return error
    
    if not data.get('items'):
        return "No PSI data available"
    
    latest_item = data['items'][0]
    readings = latest_item['readings']
    
    if region:
        region = region.lower()
        if region not in readings['psi_twenty_four_hourly']:
            return f"Region '{region}' not found. Available regions: {', '.join(readings['psi_twenty_four_hourly'].keys())}"
        
        region_data = {
            'region': region,
            'timestamp': latest_item['timestamp'],
            'psi': readings['psi_twenty_four_hourly'][region],
            'pm25': readings['pm25_twenty_four_hourly'][region],
            'pm10': readings['pm10_twenty_four_hourly'][region],
            'o3': readings['o3_eight_hour_max'][region],
            'no2': readings['no2_one_hour_max'][region],
            'so2': readings['so2_twenty_four_hourly'][region],
            'co': readings['co_eight_hour_max'][region]
        }
        return region_data
    
    # Return all regions
    all_regions = {}
    for region_name in readings['psi_twenty_four_hourly'].keys():
        all_regions[region_name] = {
            'psi': readings['psi_twenty_four_hourly'][region_name],
            'pm25': readings['pm25_twenty_four_hourly'][region_name],
            'pm10': readings['pm10_twenty_four_hourly'][region_name],
            'o3': readings['o3_eight_hour_max'][region_name],
            'no2': readings['no2_one_hour_max'][region_name],
            'so2': readings['so2_twenty_four_hourly'][region_name],
            'co': readings['co_eight_hour_max'][region_name]
        }
    
    return {
        'timestamp': latest_item['timestamp'],
        'regions': all_regions
    }

def get_air_quality_status():
    """Get air quality status with descriptive categories"""
    data, error = fetch_psi_data()
    if error:
        return error
    
    if not data.get('items'):
        return "No PSI data available"
    
    latest_item = data['items'][0]
    psi_readings = latest_item['readings']['psi_twenty_four_hourly']
    
    def get_psi_category(psi_value):
        if psi_value <= 50:
            return "Good"
        elif psi_value <= 100:
            return "Moderate"
        elif psi_value <= 200:
            return "Unhealthy"
        elif psi_value <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    status = {
        'timestamp': latest_item['timestamp'],
        'overall_status': get_psi_category(max(psi_readings.values())),
        'regions': {}
    }
    
    for region, psi_value in psi_readings.items():
        status['regions'][region] = {
            'psi': psi_value,
            'status': get_psi_category(psi_value)
        }
    
    return status

def get_region_metadata():
    """Get metadata about PSI regions including coordinates"""
    data, error = fetch_psi_data()
    if error:
        return error
    
    if not data.get('regionMetadata'):
        return "No region metadata available"
    
    return data['regionMetadata']

# Create server
server = Server("psi-singapore")

@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="psi_summary",
            description="Get PSI summary for all regions in Singapore",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="psi_by_region",
            description="Get detailed PSI data for a specific region or all regions",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Region name (west, east, central, south, north). Leave empty for all regions.",
                        "enum": ["west", "east", "central", "south", "north"]
                    }
                }
            }
        ),
        types.Tool(
            name="air_quality_status",
            description="Get air quality status with descriptive categories for all regions",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="region_metadata",
            description="Get metadata about PSI regions including coordinates",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "psi_summary":
        summary = get_psi_summary()
        if isinstance(summary, str):  # Error message
            return [types.TextContent(type="text", text=summary)]
        
        result = f"PSI Summary for Singapore\n"
        result += f"Date: {summary['date']}\n"
        result += f"Last Updated: {summary['updated']}\n\n"
        result += f"PSI Readings by Region:\n"
        for region, psi in summary['psi_readings'].items():
            result += f"  {region.capitalize()}: {psi}\n"
        result += f"\nOverall Statistics:\n"
        result += f"  Highest PSI: {summary['highest_psi']}\n"
        result += f"  Lowest PSI: {summary['lowest_psi']}\n"
        result += f"  Average PSI: {summary['average_psi']}\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "psi_by_region":
        region = arguments.get("region")
        data = get_psi_by_region(region)
        
        if isinstance(data, str):  # Error message
            return [types.TextContent(type="text", text=data)]
        
        if region:
            # Single region data
            result = f"PSI Data for {data['region'].capitalize()} Region\n"
            result += f"Timestamp: {data['timestamp']}\n\n"
            result += f"Pollutant Readings:\n"
            result += f"  PSI (24-hour): {data['psi']}\n"
            result += f"  PM2.5 (24-hour): {data['pm25']} μg/m³\n"
            result += f"  PM10 (24-hour): {data['pm10']} μg/m³\n"
            result += f"  O3 (8-hour max): {data['o3']} μg/m³\n"
            result += f"  NO2 (1-hour max): {data['no2']} μg/m³\n"
            result += f"  SO2 (24-hour): {data['so2']} μg/m³\n"
            result += f"  CO (8-hour max): {data['co']} mg/m³\n"
        else:
            # All regions data
            result = f"PSI Data for All Regions\n"
            result += f"Timestamp: {data['timestamp']}\n\n"
            for region_name, readings in data['regions'].items():
                result += f"{region_name.capitalize()} Region:\n"
                result += f"  PSI: {readings['psi']}\n"
                result += f"  PM2.5: {readings['pm25']} μg/m³\n"
                result += f"  PM10: {readings['pm10']} μg/m³\n"
                result += f"  O3: {readings['o3']} μg/m³\n"
                result += f"  NO2: {readings['no2']} μg/m³\n"
                result += f"  SO2: {readings['so2']} μg/m³\n"
                result += f"  CO: {readings['co']} mg/m³\n\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "air_quality_status":
        status = get_air_quality_status()
        if isinstance(status, str):  # Error message
            return [types.TextContent(type="text", text=status)]
        
        result = f"Air Quality Status for Singapore\n"
        result += f"Timestamp: {status['timestamp']}\n"
        result += f"Overall Status: {status['overall_status']}\n\n"
        result += f"Regional Status:\n"
        for region, info in status['regions'].items():
            result += f"  {region.capitalize()}: {info['status']} (PSI: {info['psi']})\n"
        
        result += f"\nPSI Categories:\n"
        result += f"  0-50: Good\n"
        result += f"  51-100: Moderate\n"
        result += f"  101-200: Unhealthy\n"
        result += f"  201-300: Very Unhealthy\n"
        result += f"  301+: Hazardous\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "region_metadata":
        metadata = get_region_metadata()
        if isinstance(metadata, str):  # Error message
            return [types.TextContent(type="text", text=metadata)]
        
        result = f"Singapore PSI Regions Metadata\n\n"
        for region in metadata:
            result += f"Region: {region['name'].capitalize()}\n"
            result += f"  Latitude: {region['labelLocation']['latitude']}\n"
            result += f"  Longitude: {region['labelLocation']['longitude']}\n\n"
        
        return [types.TextContent(type="text", text=result)]
    
    return [types.TextContent(type="text", text="Unknown tool")]

async def main():
    async with mcp.server.stdio.stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())