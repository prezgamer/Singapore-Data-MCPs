import asyncio
import json
import requests
from mcp.server import Server
import mcp.server.stdio
import mcp.types as types

# Dengue data fetcher functions
def fetch_dengue_data():
    """Fetch raw dengue data from API"""
    try:
        dataset_id = "d_dbfabf16158d1b0e1c420627c0819168"
        url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download"
        
        response = requests.get(url)
        json_data = response.json()
        
        if json_data['code'] != 0:
            return None, f"API Error: {json_data['errMsg']}"
        
        data_url = json_data['data']['url']
        data_response = requests.get(data_url)
        geojson_data = json.loads(data_response.text)
        
        return geojson_data, None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def get_dengue_count():
    """Get count of dengue hotspots"""
    geojson_data, error = fetch_dengue_data()
    if error:
        return error
    
    if geojson_data.get('type') == 'FeatureCollection':
        return len(geojson_data.get('features', []))
    return 1 if geojson_data.get('type') == 'Feature' else 0

def get_dengue_locations():
    """Get locations of all dengue hotspots"""
    geojson_data, error = fetch_dengue_data()
    if error:
        return error
    
    # Extract features
    if geojson_data.get('type') == 'FeatureCollection':
        features = geojson_data.get('features', [])
    elif geojson_data.get('type') == 'Feature':
        features = [geojson_data]
    else:
        features = []
    
    locations = []
    for i, feature in enumerate(features):
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        
        location_info = {
            'id': i + 1,
            'locality': properties.get('LOCALITY', 'Unknown'),
            'case_size': properties.get('CASE_SIZE'),
            'geometry_type': geometry.get('type'),
            'coordinates': geometry.get('coordinates', [])
        }
        locations.append(location_info)
    
    return locations

def get_dengue_coordinates_only():
    """Get just locality names and coordinates"""
    geojson_data, error = fetch_dengue_data()
    if error:
        return error
    
    # Extract features
    if geojson_data.get('type') == 'FeatureCollection':
        features = geojson_data.get('features', [])
    elif geojson_data.get('type') == 'Feature':
        features = [geojson_data]
    else:
        features = []
    
    coordinates_data = []
    for feature in features:
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        
        coord_info = {
            'locality': properties.get('LOCALITY', 'Unknown'),
            'coordinates': geometry.get('coordinates', [])
        }
        coordinates_data.append(coord_info)
    
    return coordinates_data

# Create server
server = Server("dengue-test")

@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="dengue_count",
            description="Get dengue hotspot count",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="dengue_locations",
            description="Get all dengue hotspot locations with details",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="dengue_coordinates",
            description="Get dengue hotspot localities and coordinates only",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "dengue_count":
        count = get_dengue_count()
        return [types.TextContent(type="text", text=f"Dengue hotspots: {count}")]
    
    elif name == "dengue_locations":
        locations = get_dengue_locations()
        if isinstance(locations, str):  # Error message
            return [types.TextContent(type="text", text=locations)]
        
        # Format the locations nicely
        result = f"Total dengue hotspots: {len(locations)}\n\n"
        for location in locations:
            result += f"Hotspot {location['id']}:\n"
            result += f"  Location: {location['locality']}\n"
            result += f"  Case Size: {location['case_size']}\n"
            result += f"  Geometry: {location['geometry_type']}\n"
            
            # Show first few coordinates for polygons
            if location['coordinates'] and location['geometry_type'] == 'Polygon':
                coords = location['coordinates'][0]  # First ring of polygon
                result += f"  Total Points: {len(coords)}\n"
                result += f"  Sample Coordinates:\n"
                for i, point in enumerate(coords[:3]):  # First 3 points
                    result += f"    [{point[0]:.6f}, {point[1]:.6f}]\n"
                if len(coords) > 3:
                    result += f"    ... and {len(coords) - 3} more points\n"
            result += "\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "dengue_coordinates":
        coordinates = get_dengue_coordinates_only()
        if isinstance(coordinates, str):  # Error message
            return [types.TextContent(type="text", text=coordinates)]
        
        # Return as JSON for easy parsing
        result = {
            "total_hotspots": len(coordinates),
            "hotspots": coordinates
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    return [types.TextContent(type="text", text="Unknown tool")]

async def main():
    async with mcp.server.stdio.stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())