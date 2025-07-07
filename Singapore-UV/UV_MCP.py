import asyncio
import json
import requests
from mcp.server import Server
import mcp.server.stdio
import mcp.types as types
from datetime import datetime

# UV Index data fetcher functions
def fetch_uv_data():
    """Fetch raw UV index data from Singapore API"""
    try:
        url = "https://api-open.data.gov.sg/v2/real-time/api/uv"
        
        response = requests.get(url)
        json_data = response.json()
        
        if json_data['code'] != 0:
            return None, f"API Error: {json_data.get('errorMsg', 'Unknown error')}"
        
        return json_data['data'], None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def get_uv_current():
    """Get current UV index reading"""
    data, error = fetch_uv_data()
    if error:
        return error
    
    if not data.get('records'):
        return "No UV data available"
    
    latest_record = data['records'][0]
    
    def get_uv_risk_level(uv_index):
        if uv_index <= 2:
            return "Low"
        elif uv_index <= 5:
            return "Moderate"
        elif uv_index <= 7:
            return "High"
        elif uv_index <= 10:
            return "Very High"
        else:
            return "Extreme"
    
    def get_uv_recommendation(uv_index):
        if uv_index <= 2:
            return "No protection needed. You can safely enjoy being outside."
        elif uv_index <= 5:
            return "Some protection required. Seek shade during midday hours, wear sun protective clothing, wide-brimmed hat and UV-blocking sunglasses."
        elif uv_index <= 7:
            return "Protection required. Reduce time in sun between 10am-4pm. Wear sun protective clothing, wide-brimmed hat, UV-blocking sunglasses and broad spectrum SPF30+ sunscreen."
        elif uv_index <= 10:
            return "Extra protection required. Avoid sun between 10am-4pm. Seek shade, wear sun protective clothing, wide-brimmed hat, UV-blocking sunglasses and broad spectrum SPF30+ sunscreen."
        else:
            return "Extreme protection required. Avoid sun between 10am-4pm. Seek shade, wear full body covering including sun protective clothing, wide-brimmed hat, UV-blocking sunglasses and broad spectrum SPF50+ sunscreen."
    
    # Get current UV index (most recent hour)
    current_uv = latest_record['index'][0]['value']
    
    current_data = {
        'date': latest_record['date'],
        'timestamp': latest_record['timestamp'],
        'updated_timestamp': latest_record['updatedTimestamp'],
        'current_uv_index': current_uv,
        'risk_level': get_uv_risk_level(current_uv),
        'recommendation': get_uv_recommendation(current_uv)
    }
    
    return current_data

def get_uv_hourly():
    """Get hourly UV index forecast"""
    data, error = fetch_uv_data()
    if error:
        return error
    
    if not data.get('records'):
        return "No UV data available"
    
    latest_record = data['records'][0]
    
    def get_uv_risk_level(uv_index):
        if uv_index <= 2:
            return "Low"
        elif uv_index <= 5:
            return "Moderate"
        elif uv_index <= 7:
            return "High"
        elif uv_index <= 10:
            return "Very High"
        else:
            return "Extreme"
    
    hourly_data = {
        'date': latest_record['date'],
        'updated_timestamp': latest_record['updatedTimestamp'],
        'hourly_forecast': []
    }
    
    for reading in latest_record['index']:
        hourly_data['hourly_forecast'].append({
            'hour': reading['hour'],
            'uv_index': reading['value'],
            'risk_level': get_uv_risk_level(reading['value'])
        })
    
    return hourly_data

def get_uv_summary():
    """Get UV index summary for the day"""
    data, error = fetch_uv_data()
    if error:
        return error
    
    if not data.get('records'):
        return "No UV data available"
    
    latest_record = data['records'][0]
    
    uv_values = [reading['value'] for reading in latest_record['index']]
    
    if not uv_values:
        return "No UV readings available"
    
    # Find peak UV time
    max_uv = max(uv_values)
    peak_times = []
    for reading in latest_record['index']:
        if reading['value'] == max_uv:
            peak_times.append(reading['hour'])
    
    def get_uv_risk_level(uv_index):
        if uv_index <= 2:
            return "Low"
        elif uv_index <= 5:
            return "Moderate"
        elif uv_index <= 7:
            return "High"
        elif uv_index <= 10:
            return "Very High"
        else:
            return "Extreme"
    
    summary = {
        'date': latest_record['date'],
        'updated_timestamp': latest_record['updatedTimestamp'],
        'current_uv_index': uv_values[0],  # Most recent reading
        'peak_uv_index': max_uv,
        'peak_uv_times': peak_times,
        'peak_risk_level': get_uv_risk_level(max_uv),
        'minimum_uv_index': min(uv_values),
        'average_uv_index': round(sum(uv_values) / len(uv_values), 1),
        'total_readings': len(uv_values)
    }
    
    return summary

def get_uv_peak_times():
    """Get times when UV index is at dangerous levels (7+)"""
    data, error = fetch_uv_data()
    if error:
        return error
    
    if not data.get('records'):
        return "No UV data available"
    
    latest_record = data['records'][0]
    
    dangerous_times = []
    very_high_times = []
    extreme_times = []
    
    for reading in latest_record['index']:
        uv_value = reading['value']
        if uv_value >= 11:
            extreme_times.append({
                'hour': reading['hour'],
                'uv_index': uv_value,
                'risk_level': 'Extreme'
            })
        elif uv_value >= 8:
            very_high_times.append({
                'hour': reading['hour'],
                'uv_index': uv_value,
                'risk_level': 'Very High'
            })
        elif uv_value >= 7:
            dangerous_times.append({
                'hour': reading['hour'],
                'uv_index': uv_value,
                'risk_level': 'High'
            })
    
    return {
        'date': latest_record['date'],
        'updated_timestamp': latest_record['updatedTimestamp'],
        'high_uv_times': dangerous_times,
        'very_high_uv_times': very_high_times,
        'extreme_uv_times': extreme_times,
        'total_dangerous_hours': len(dangerous_times) + len(very_high_times) + len(extreme_times)
    }

def get_uv_protection_schedule():
    """Get recommended protection schedule based on UV levels"""
    data, error = fetch_uv_data()
    if error:
        return error
    
    if not data.get('records'):
        return "No UV data available"
    
    latest_record = data['records'][0]
    
    def get_protection_level(uv_index):
        if uv_index <= 2:
            return "No protection needed"
        elif uv_index <= 5:
            return "Basic protection (hat, sunglasses)"
        elif uv_index <= 7:
            return "Standard protection (SPF30+, hat, sunglasses, shade)"
        elif uv_index <= 10:
            return "High protection (avoid sun 10am-4pm, SPF30+, full coverage)"
        else:
            return "Maximum protection (avoid sun, SPF50+, full body coverage)"
    
    schedule = {
        'date': latest_record['date'],
        'updated_timestamp': latest_record['updatedTimestamp'],
        'protection_schedule': []
    }
    
    for reading in latest_record['index']:
        schedule['protection_schedule'].append({
            'hour': reading['hour'],
            'uv_index': reading['value'],
            'protection_needed': get_protection_level(reading['value'])
        })
    
    return schedule

# Create server
server = Server("uv-singapore")

@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="uv_current",
            description="Get current UV index reading with risk level and recommendations",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="uv_hourly",
            description="Get hourly UV index forecast for the day",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="uv_summary",
            description="Get UV index summary including peak times and averages",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="uv_peak_times",
            description="Get times when UV index is at dangerous levels (7+)",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="uv_protection_schedule",
            description="Get recommended sun protection schedule based on UV levels",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "uv_current":
        current = get_uv_current()
        if isinstance(current, str):  # Error message
            return [types.TextContent(type="text", text=current)]
        
        result = f"Current UV Index for Singapore\n"
        result += f"Date: {current['date']}\n"
        result += f"Last Updated: {current['updated_timestamp']}\n\n"
        result += f"Current UV Index: {current['current_uv_index']}\n"
        result += f"Risk Level: {current['risk_level']}\n\n"
        result += f"Recommendation:\n{current['recommendation']}\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "uv_hourly":
        hourly = get_uv_hourly()
        if isinstance(hourly, str):  # Error message
            return [types.TextContent(type="text", text=hourly)]
        
        result = f"Hourly UV Index Forecast for Singapore\n"
        result += f"Date: {hourly['date']}\n"
        result += f"Last Updated: {hourly['updated_timestamp']}\n\n"
        result += f"Hourly Forecast:\n"
        
        for forecast in hourly['hourly_forecast']:
            hour_time = forecast['hour'].split('T')[1][:5]  # Extract HH:MM
            result += f"  {hour_time}: UV {forecast['uv_index']} ({forecast['risk_level']})\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "uv_summary":
        summary = get_uv_summary()
        if isinstance(summary, str):  # Error message
            return [types.TextContent(type="text", text=summary)]
        
        result = f"UV Index Summary for Singapore\n"
        result += f"Date: {summary['date']}\n"
        result += f"Last Updated: {summary['updated_timestamp']}\n\n"
        result += f"Current UV Index: {summary['current_uv_index']}\n"
        result += f"Peak UV Index: {summary['peak_uv_index']} ({summary['peak_risk_level']})\n"
        result += f"Peak Times: {', '.join([time.split('T')[1][:5] for time in summary['peak_uv_times']])}\n"
        result += f"Minimum UV Index: {summary['minimum_uv_index']}\n"
        result += f"Average UV Index: {summary['average_uv_index']}\n"
        result += f"Total Readings: {summary['total_readings']}\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "uv_peak_times":
        peaks = get_uv_peak_times()
        if isinstance(peaks, str):  # Error message
            return [types.TextContent(type="text", text=peaks)]
        
        result = f"Dangerous UV Times for Singapore\n"
        result += f"Date: {peaks['date']}\n"
        result += f"Last Updated: {peaks['updated_timestamp']}\n"
        result += f"Total Dangerous Hours: {peaks['total_dangerous_hours']}\n\n"
        
        if peaks['extreme_uv_times']:
            result += f"Extreme UV Times (11+):\n"
            for time in peaks['extreme_uv_times']:
                hour_time = time['hour'].split('T')[1][:5]
                result += f"  {hour_time}: UV {time['uv_index']} ({time['risk_level']})\n"
            result += "\n"
        
        if peaks['very_high_uv_times']:
            result += f"Very High UV Times (8-10):\n"
            for time in peaks['very_high_uv_times']:
                hour_time = time['hour'].split('T')[1][:5]
                result += f"  {hour_time}: UV {time['uv_index']} ({time['risk_level']})\n"
            result += "\n"
        
        if peaks['high_uv_times']:
            result += f"High UV Times (7):\n"
            for time in peaks['high_uv_times']:
                hour_time = time['hour'].split('T')[1][:5]
                result += f"  {hour_time}: UV {time['uv_index']} ({time['risk_level']})\n"
            result += "\n"
        
        if not peaks['extreme_uv_times'] and not peaks['very_high_uv_times'] and not peaks['high_uv_times']:
            result += "No dangerous UV levels detected today.\n"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "uv_protection_schedule":
        schedule = get_uv_protection_schedule()
        if isinstance(schedule, str):  # Error message
            return [types.TextContent(type="text", text=schedule)]
        
        result = f"Sun Protection Schedule for Singapore\n"
        result += f"Date: {schedule['date']}\n"
        result += f"Last Updated: {schedule['updated_timestamp']}\n\n"
        result += f"Hourly Protection Guide:\n"
        
        for protection in schedule['protection_schedule']:
            hour_time = protection['hour'].split('T')[1][:5]
            result += f"  {hour_time}: UV {protection['uv_index']} - {protection['protection_needed']}\n"
        
        result += f"\nUV Risk Levels:\n"
        result += f"  0-2: Low\n"
        result += f"  3-5: Moderate\n"
        result += f"  6-7: High\n"
        result += f"  8-10: Very High\n"
        result += f"  11+: Extreme\n"
        
        return [types.TextContent(type="text", text=result)]
    
    return [types.TextContent(type="text", text="Unknown tool")]

async def main():
    async with mcp.server.stdio.stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())