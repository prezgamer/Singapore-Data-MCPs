

# Singapore Data.gov MCP Server

A Model Context Protocol (MCP) server that provides seamless access to Singapore's official government data through data.gov.sg APIs. 

## Installation

### Prerequisites
- Python 3.8 or higher
- Claude Desktop application

### Required Python Packages
```bash
pip install requests aiohttp pandas mcp
```

## Carpark Availability MCP Server

This server specializes in carpark information and real-time availability data, enabling Claude to help users find parking in Singapore.

## Features

- 🚗 **Real-time carpark availability** from Singapore's official data.gov.sg API
- 📍 **Comprehensive carpark information** including addresses, pricing, and types
- 🔍 **Smart search capabilities** by area, location, or carpark number
- 📊 **Combined static and live data** for complete parking insights
- 🚀 **No API key required** for basic functionality (optional for enhanced features)
- ⚡ **Efficient caching** to minimize API calls and improve performance
- 🛡️ **Robust error handling** with timeouts and graceful degradation

## Tools

### 1. `get_carpark_info`
Get static information about a specific carpark.

**Required Parameters:**
- `carpark_number` (string) - Carpark identifier (e.g., 'ACB', 'BM29')

**Returns:** Static carpark details including address, carpark type, parking system type, and other fixed information.

### 2. `get_carpark_availability`
Get real-time availability for a specific carpark.

**Required Parameters:**
- `carpark_number` (string) - Carpark identifier (e.g., 'ACB', 'BM29')

**Returns:** Current availability status including available lots, total lots, and last update time.

### 3. `get_complete_carpark_info`
Get both static information and real-time availability for a carpark.

**Required Parameters:**
- `carpark_number` (string) - Carpark identifier (e.g., 'ACB', 'BM29')

**Returns:** Comprehensive carpark data combining static info and live availability.

### 4. `search_carparks_by_area`
Search for carparks in a specific area or location.

**Required Parameters:**
- `area_keyword` (string) - Area keyword to search (e.g., 'Jurong', 'Tampines', 'Orchard')

**Optional Parameters:**
- `include_availability` (boolean) - Include real-time availability data (default: false)
- `max_results` (integer) - Maximum number of results (default: 10)

**Returns:** List of carparks matching the area search with optional availability data.

### 5. `search_carparks_by_name`
Search carparks by carpark number or name pattern.

**Required Parameters:**
- `name_keyword` (string) - Keyword to search in carpark numbers (e.g., 'AC', 'BM', 'TPM')

**Optional Parameters:**
- `include_availability` (boolean) - Include real-time availability data (default: false)
- `max_results` (integer) - Maximum number of results (default: 10)

**Returns:** List of carparks matching the name/number pattern with optional availability data.

### 6. `get_all_carpark_availability`
Get real-time availability for all carparks (performance-optimized).

**Optional Parameters:**
- `max_results` (integer) - Maximum number of carparks to include (default: 50)

**Returns:** Current availability status for multiple carparks, limited for performance.

### Manual Setup

1. Save the server code to a file (e.g., `singapore_carpark_server.py`)

2. Open Claude Desktop settings: **Settings > Developer > Edit Config**

3. Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "singapore-data": {
      "command": "python",
      "args": ["path/to/carpark_availability_MCP.py"]
    }
  }
}
```

4. **Restart Claude Desktop**

### With API Key (Optional)

For enhanced rate limits and features, you can use a data.gov.sg API key:

```python
# Modify the server initialization
carpark_system = SingaporeCarParkSystem(api_key="your_api_key_here")
```

Get your API key from [data.gov.sg](https://data.gov.sg/developer).

## Usage Examples

Once installed, you can ask Claude to:

- *"Find available parking near Orchard Road"*
- *"What's the current availability at carpark ACB?"*
- *"Search for carparks in Jurong with availability"*
- *"Get complete information about carpark BM29"*
- *"Show me all carparks starting with 'TP'"*
- *"Find parking near Marina Bay Sands"*

## Data Sources

This server integrates with Singapore's official government data APIs:

- **Static Carpark Information**: `data.gov.sg/dataset/hdb-carpark-information`
- **Real-time Availability**: `data.gov.sg/dataset/carpark-availability`

## Development

### Running from Source

```bash
# Clone or download the server file
python singapore_carpark_server.py
```

### Testing

```bash
# Test individual functions
python -c "
from singapore_carpark_server import SingaporeCarParkSystem
system = SingaporeCarParkSystem()
print(system.fetch_carpark_info('ACB'))
"
```

### Logging

The server includes comprehensive logging. Set the log level in the code:

```python
logging.basicConfig(level=logging.DEBUG)  # For detailed logs
logging.basicConfig(level=logging.INFO)   # For normal operation
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure MCP is installed: `pip install mcp`
2. **No carpark found**: Check the carpark number format (usually 2-4 uppercase characters)
3. **Timeout errors**: The server includes built-in timeouts; try again or check network
4. **Rate limiting**: Add delays between requests or use an API key

### Performance Tips

- Use `include_availability=false` for faster searches when live data isn't needed
- Limit `max_results` for area searches to improve response times
- Cache frequently accessed carpark numbers in your queries

### Support

For issues related to:
- **Data accuracy**: Contact data.gov.sg
- **Server functionality**: Check the logs for detailed error messages
- **API limits**: Consider registering for an API key at data.gov.sg

## Data Accuracy

- **Static data**: Updated periodically by Singapore's Housing Development Board
- **Availability data**: Updated in real-time (typically every few minutes)
- **Accuracy**: Data sourced directly from official government systems

## License

This server is provided as-is for educational and personal use. Please respect data.gov.sg's terms of service and rate limits.

## Disclaimer

This is an unofficial tool that interfaces with Singapore's official data.gov.sg APIs. The authors are not affiliated with the Singapore government. Please verify critical information through official channels.

---

# Singapore GES Survey MCP Server

This server enables Claude to analyze graduate employment statistics, salary trends, and career outcomes across universities, degrees, and years.

## Features

- 📊 **Graduate Employment Statistics** from Singapore's official GES data
- 💰 **Comprehensive Salary Analysis** including mean, median, and percentile data
- 🎓 **Multi-University Comparison** across NUS, NTU, SMU, and other institutions
- 📈 **Year-over-Year Trend Analysis** to track employment and salary changes
- 🔍 **Advanced Search Capabilities** by degree, university, school, or employment metrics
- 📋 **Complete Employment Metrics** including overall and full-time permanent rates
- 🏆 **Ranking and Comparison Tools** for best/worst performing degrees
- ⚡ **Efficient Data Processing** with intelligent caching and pagination

## Tools

### Year Analysis Tools

#### 1. `get_available_years`
Get all available years in the GES dataset.

**Returns:** List of all years with available graduate employment data.

#### 2. `get_highest_paid_degree_by_year`
Find the highest paying degree for a specific year.

**Required Parameters:**
- `year` (string) - Year to analyze (e.g., '2022')

**Returns:** Complete degree information with all salary and employment metrics.

#### 3. `get_lowest_paid_degree_by_year`
Find the lowest paying degree for a specific year.

**Required Parameters:**
- `year` (string) - Year to analyze (e.g., '2022')

**Returns:** Complete degree information with all salary and employment metrics.

#### 4. `get_top_degrees_by_year`
Get top N degrees for a specific year by any metric.

**Required Parameters:**
- `year` (string) - Year to analyze (e.g., '2022')

**Optional Parameters:**
- `metric` (string) - Sorting metric (default: 'gross_monthly_median')
- `limit` (integer) - Number of results (default: 10)

**Available Metrics:**
- `gross_monthly_median` - Gross monthly median salary
- `gross_monthly_mean` - Gross monthly mean salary
- `employment_rate_overall` - Overall employment rate
- `employment_rate_ft_perm` - Full-time permanent employment rate

### Search Tools

#### 5. `search_by_degree_name`
Search for degrees by keyword in degree name.

**Required Parameters:**
- `degree_keyword` (string) - Keyword to search (e.g., 'computer', 'business', 'engineering')

**Optional Parameters:**
- `year` (string) - Filter by specific year

**Returns:** List of matching degrees with complete employment and salary data.

#### 6. `search_by_university`
Search for degrees by university name.

**Required Parameters:**
- `university_keyword` (string) - University keyword (e.g., 'National', 'Nanyang', 'SMU')

**Optional Parameters:**
- `year` (string) - Filter by specific year

**Returns:** List of degrees from matching universities.

#### 7. `search_by_school`
Search for degrees by school/faculty name.

**Required Parameters:**
- `school_keyword` (string) - School/faculty keyword (e.g., 'Engineering', 'Business', 'Medicine')

**Optional Parameters:**
- `year` (string) - Filter by specific year

**Returns:** List of degrees from matching schools/faculties.

#### 8. `compare_degree_across_years`
Compare a specific degree across multiple years.

**Required Parameters:**
- `degree_keyword` (string) - Degree keyword to search
- `years` (array) - List of years to compare (e.g., ['2020', '2021', '2022'])

**Returns:** Year-over-year comparison with employment and salary trends.

### Analysis Tools

#### 9. `get_highest_paid_degree_gross_median`
Get the degree with highest gross monthly median salary.

**Optional Parameters:**
- `year` (string) - Filter by specific year

**Returns:** Complete degree information with all metrics.

#### 10. `get_lowest_paid_degree_gross_median`
Get the degree with lowest gross monthly median salary.

**Optional Parameters:**
- `year` (string) - Filter by specific year

**Returns:** Complete degree information with all metrics.

#### 11. `get_highest_employment_overall`
Get the degree with highest overall employment rate.

**Optional Parameters:**
- `year` (string) - Filter by specific year

**Returns:** Complete degree information with all metrics.

#### 12. `get_lowest_employment_overall`
Get the degree with lowest overall employment rate.

**Optional Parameters:**
- `year` (string) - Filter by specific year

**Returns:** Complete degree information with all metrics.

#### 13. `get_highest_graduate_count`
Get degrees with highest estimated number of graduates.

**Optional Parameters:**
- `year` (string) - Filter by specific year

**Returns:** List of degrees ranked by estimated graduate count.

#### 14. `get_best_salary_distribution`
Get degrees with best salary distribution (percentile analysis).

**Optional Parameters:**
- `year` (string) - Filter by specific year

**Returns:** Degrees ranked by salary distribution quality (25th-75th percentile analysis).

#### 15. `get_total_graduates_by_degree`
Get total estimated graduates for each degree across all years.

**Returns:** Comprehensive summary of graduate counts, universities offering each degree, and average metrics.

### Manual Setup

1. Save the server code to a file (e.g., `GES_Survey_MCP.py`)

2. Open Claude Desktop settings: **Settings > Developer > Edit Config**

3. Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ges-survey": {
      "command": "python",
      "args": ["path/to/GES_Survey_MCP.py"]
    }
  }
}
```

4. **Restart Claude Desktop**

## Usage Examples

Once installed, you can ask Claude to:

### General Queries
- *"What are the highest paying degrees in Singapore?"*
- *"Show me employment rates for computer science degrees"*
- *"Compare engineering salaries across different universities"*

### Year-Specific Analysis
- *"What were the top 10 highest paying degrees in 2022?"*
- *"Show me the best employment rates for 2023 graduates"*
- *"Compare business degree salaries between 2020 and 2022"*

### University Comparisons
- *"Compare computer science programs at NUS vs NTU"*
- *"What are the salary differences between local universities?"*
- *"Show me all engineering programs and their employment rates"*

### Trend Analysis
- *"How have computer science salaries changed over the years?"*
- *"Track employment rates for business degrees from 2018 to 2022"*
- *"Show salary trends for medical degrees"*

### Specific Searches
- *"Find all degrees with 'data' in the name"*
- *"Search for programs from the School of Engineering"*
- *"What degrees have the best salary distribution?"*

## Data Metrics Explained

### Employment Rates
- **Overall Employment Rate**: Percentage of graduates employed within 6 months
- **Full-Time Permanent Employment Rate**: Percentage in full-time permanent positions

### Salary Metrics
- **Basic Monthly Mean/Median**: Basic salary without bonuses
- **Gross Monthly Mean/Median**: Total compensation including bonuses
- **25th/75th Percentile**: Salary range distribution indicators

### Distribution Score
A composite score considering:
- 25th percentile salary (40% weight)
- Median salary (40% weight)  
- 75th percentile salary (20% weight)

## Data Sources

This server integrates with Singapore's official Graduate Employment Survey data:

- **Source**: data.gov.sg/dataset/graduate-employment-survey
- **Coverage**: All major universities in Singapore
- **Update Frequency**: Annually
- **Survey Timing**: 6 months post-graduation

## Development

### Running from Source

```bash
# Run the MCP server
python ges_survey_server.py
```

### Testing Standalone

```bash
# Test without MCP (built-in test mode)
python -c "
from ges_survey_server import GraduateStatsService
service = GraduateStatsService()

# Test available years
years = service.get_available_years()
print(f'Available years: {years}')

# Test search
results = service.search_by_degree_name('computer')
print(f'Computer degrees found: {len(results)}')
"
```

### Logging

The server includes comprehensive logging:

```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure MCP is installed: `pip install mcp`
2. **No data returned**: Check parameter spelling and format
3. **Year format**: Use 4-digit year strings (e.g., '2022', not 2022)
4. **Empty results**: Try broader search keywords

### Performance Tips

- Use specific years when possible to reduce data processing
- Limit results for large searches to improve response times
- Cache frequently accessed degree names for repeated queries
- Use broad keywords first, then narrow down searches

### Data Quality Notes

- Some degrees may have 'na' values for certain metrics
- Graduate count estimates are algorithmic approximations
- Salary data reflects 6-month post-graduation surveys
- Employment rates may vary by economic conditions

## License

This server is provided for educational and research purposes. Please respect data.gov.sg's terms of service and cite the Graduate Employment Survey when using this data.

## Disclaimer

This is an unofficial tool that interfaces with Singapore's official Graduate Employment Survey data. The authors are not affiliated with the Singapore government or participating universities. Please verify critical decisions through official university channels and career counseling services.

---

# Singapore Air Temperature MCP Server

This server enables Claude to access real-time air temperature data from Singapore's weather monitoring stations across the island.

## Features

- 🌡️ **Real-Time Temperature Data** from Singapore's official weather stations
- 📍 **Island-Wide Coverage** with multiple monitoring stations
- 🔍 **Temperature Analysis** including highest and lowest readings
- 📊 **Station Information** with geographic coordinates
- ⚡ **Live Data Feed** updated regularly from data.gov.sg
- 🏝️ **Comprehensive Coverage** across all regions of Singapore

## Tools

### Temperature Analysis Tools

#### 1. `get_all_air_temperatures`
Get current air temperature readings from all weather stations in Singapore.

**Returns:** Complete list of all temperature readings with station details, coordinates, and timestamp.

#### 2. `get_highest_temperature`
Get the weather station currently recording the highest temperature.

**Returns:** Station details with the highest temperature reading, including location coordinates and timestamp.

#### 3. `get_lowest_temperature`
Get the weather station currently recording the lowest temperature.

**Returns:** Station details with the lowest temperature reading, including location coordinates and timestamp.

### Manual Setup

1. Save the server code to a file (e.g., `airtemp_MCP.py`)

2. Open Claude Desktop settings: **Settings > Developer > Edit Config**

3. Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "air-temperature": {
      "command": "python",
      "args": ["path/to/airtemp_MCP.py"]
    }
  }
}
```

4. **Restart Claude Desktop**

## Usage Examples

Once installed, you can ask Claude to:

### General Queries
- *"What's the current temperature in Singapore?"*
- *"Show me all temperature readings across Singapore"*
- *"What are the temperature variations across the island?"*

### Specific Analysis
- *"Which area has the highest temperature right now?"*
- *"Where is it coolest in Singapore currently?"*
- *"Show me the temperature difference between hottest and coolest areas"*

### Location-Based Queries
- *"What's the temperature near my location?"*
- *"Compare temperatures between different regions"*
- *"Which weather stations are recording extreme temperatures?"*

### Weather Monitoring
- *"Is there a heat island effect visible in the data?"*
- *"What's the temperature spread across Singapore?"*
- *"Show me current weather conditions island-wide"*

## Data Metrics Explained

### Temperature Readings
- **Temperature Value**: Current air temperature in degrees Celsius
- **Station ID**: Unique identifier for each weather monitoring station
- **Station Name**: Descriptive name of the weather station location
- **Coordinates**: Latitude and longitude of the station
- **Timestamp**: When the reading was recorded

### Coverage Areas
Singapore's weather stations are strategically located across:
- **Urban Centers**: City areas and commercial districts
- **Residential Areas**: HDB estates and private housing
- **Industrial Zones**: Manufacturing and port areas
- **Green Spaces**: Parks and nature reserves
- **Coastal Areas**: Waterfront and island locations

## Data Sources

This server integrates with Singapore's official weather monitoring system:

- **Source**: api-open.data.gov.sg/v2/real-time/api/air-temperature
- **Coverage**: Island-wide weather station network
- **Update Frequency**: Real-time (typically every few minutes)
- **Data Quality**: Official meteorological measurements

## Development

### Running from Source

```bash
# Run the MCP server
python air_temperature_server.py
```

### Testing Standalone

```bash
# Test without MCP (built-in test mode)
python -c "
from air_temperature_server import AirTempService
service = AirTempService()

# Test temperature readings
result = service.get_all_temperatures()
if isinstance(result, dict):
    print(f'Total stations: {result[\"total_stations\"]}')
    print(f'Latest reading: {result[\"timestamp\"]}')
else:
    print(f'Error: {result}')
"
```

### Logging

The server includes basic error handling and can be enhanced with logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure MCP is installed: `pip install mcp`
2. **No data returned**: Check internet connection and API availability
3. **API errors**: The service will display specific error messages from data.gov.sg
4. **Connection timeouts**: Try again as this may be a temporary network issue

### Performance Tips

- Temperature data is fetched in real-time, so slight delays are normal
- The API provides the most recent readings available
- All stations are queried simultaneously for efficiency
- Data is fresh and reflects current conditions

### Data Quality Notes

- Readings are from official weather monitoring equipment
- Timestamps indicate when measurements were taken
- Some stations may occasionally be offline for maintenance
- Temperature variations across the island are normal due to geography

## Sample Queries

```
"What's the current temperature across Singapore?"
"Show me the hottest and coolest spots right now"
"How much temperature variation is there across the island?"
```

## Technical Details

### API Integration
- **Real-time data**: Direct connection to Singapore's weather API
- **Error handling**: Graceful handling of API errors and timeouts
- **Data processing**: Automatic parsing and formatting of weather data
- **Station mapping**: Links temperature readings to station information

### Data Structure
Each temperature reading includes:
- Station identification and name
- Current temperature value
- Geographic coordinates
- Measurement timestamp
- Temperature unit (Celsius)

## License

This server is provided for educational and informational purposes. Please respect data.gov.sg's terms of service when using this weather data.

## Disclaimer

This is an unofficial tool that interfaces with Singapore's official weather monitoring APIs. The authors are not affiliated with the Singapore government or meteorological services. For official weather forecasts and warnings, please consult the National Environment Agency (NEA).

---

# Singapore Dengue Hotspots MCP Server

This server enables Claude to access real-time dengue hotspot data from Singapore's health monitoring system, providing current outbreak locations and case information.

## Features

- 🦟 **Real-Time Dengue Hotspots** from Singapore's official health surveillance
- 📍 **Geographic Coverage** with precise coordinates and locality information
- 📊 **Case Size Data** indicating severity of each hotspot
- 🗺️ **Polygon Boundaries** defining exact affected areas
- ⚡ **Live Health Data** updated regularly from data.gov.sg
- 🏥 **Public Health Monitoring** for disease prevention and awareness

## Tools

### Dengue Monitoring Tools

#### 1. `dengue_count`
Get the current total number of dengue hotspots in Singapore.

**Returns:** Simple count of active dengue hotspots across the island.

#### 2. `dengue_locations`
Get detailed information about all current dengue hotspots.

**Returns:** Complete list of hotspots with locality names, case sizes, geometry types, and coordinate boundaries.

#### 3. `dengue_coordinates`
Get locality names and coordinates for all dengue hotspots in JSON format.

**Returns:** Structured JSON data with hotspot locations and their geographic coordinates for mapping and analysis.

### Manual Setup

1. Save the server code to a file (e.g., `dengue_MCP.py`)

2. Open Claude Desktop settings: **Settings > Developer > Edit Config**

3. Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dengue-hotspots": {
      "command": "python",
      "args": ["path/to/dengue_MCP.py"]
    }
  }
}
```

4. **Restart Claude Desktop**

## Usage Examples

Once installed, you can ask Claude to:

### General Health Queries
- *"How many dengue hotspots are there in Singapore right now?"*
- *"Show me all current dengue outbreak locations"*
- *"What areas should I avoid due to dengue?"*

### Location-Based Analysis
- *"Are there any dengue hotspots near my area?"*
- *"Which neighborhoods have dengue outbreaks?"*
- *"Show me the geographic distribution of dengue cases"*

## Data Metrics Explained

### Hotspot Information
- **Locality**: Specific area or neighborhood name where outbreak is occurring
- **Case Size**: Number indicating the severity/size of the outbreak
- **Geometry Type**: Geographic shape (usually Polygon for area boundaries)
- **Coordinates**: Precise latitude/longitude points defining the affected area

### Geographic Data
- **Polygon Boundaries**: Exact area boundaries where dengue cases are concentrated
- **Coordinate Points**: Multiple lat/lng pairs defining the perimeter of each hotspot
- **Area Coverage**: Specific neighborhoods, streets, or districts affected

## Data Sources

This server integrates with Singapore's official health monitoring system:

- **Source**: api-open.data.gov.sg (Ministry of Health dengue surveillance)
- **Coverage**: Island-wide health monitoring network
- **Update Frequency**: Regular updates as new cases are confirmed
- **Data Quality**: Official epidemiological surveillance data

## Development

### Running from Source

```bash
# Run the MCP server
python dengue_server.py
```

### Testing Standalone

```bash
# Test dengue data fetching
python -c "
from dengue_server import get_dengue_count, get_dengue_locations
count = get_dengue_count()
print(f'Current hotspots: {count}')

locations = get_dengue_locations()
if isinstance(locations, list):
    print(f'Found {len(locations)} hotspot details')
else:
    print(f'Error: {locations}')
"
```

### API Integration

```python
# Example of accessing the raw data
from dengue_server import fetch_dengue_data

geojson_data, error = fetch_dengue_data()
if not error:
    print("Successfully fetched dengue GeoJSON data")
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure MCP is installed: `pip install mcp`
2. **No data returned**: Check internet connection and API availability
3. **API errors**: The service will display specific error messages from data.gov.sg
4. **GeoJSON parsing issues**: Data format may vary; the server handles this gracefully

### Performance Tips

- Dengue data is fetched in real-time from health surveillance systems
- The API provides the most current outbreak information available
- GeoJSON data includes detailed polygon boundaries for precise mapping
- Data reflects official health department classifications

### Data Quality Notes

- Hotspot data comes from official health surveillance
- Case sizes indicate relative outbreak severity
- Geographic boundaries are precisely mapped
- Information is updated as health authorities confirm new cases

## License

This server is provided for public health awareness and educational purposes. Please respect data.gov.sg's terms of service when using this health surveillance data.

## Disclaimer

This is an unofficial tool that interfaces with Singapore's official health monitoring APIs. The authors are not affiliated with the Ministry of Health or health authorities. For official health advisories and medical guidance, please consult the Ministry of Health (MOH) and seek professional medical advice.

---

# Singapore HDB Resale MCP Server

This server enables Claude to access comprehensive HDB resale transaction data (2017 Onwards) from Singapore's official housing database, providing insights into property prices, market trends, and lease information.

## Features

- 🏠 **HDB Resale Transaction Data** from Singapore's official housing records
- 💰 **Price Analysis Tools** including highest, lowest, and average pricing by area
- 📊 **Market Activity Tracking** with transaction volume analysis by location
- 🗓️ **Year-over-Year Comparisons** for market trend analysis
- 📍 **Location-Based Filtering** by town, flat type, and other criteria
- ⏰ **Lease Remaining Analysis** for investment and purchase decisions
- 🔍 **Advanced Search Capabilities** with multiple filter combinations
- ⚡ **Optimized Performance** with intelligent caching and data fetching strategies

## Tools

### Price Analysis Tools

#### 1. `get_highest_price`
Get the highest recorded resale price for HDB flats.

**Optional Parameters:**
- `flat_type` (string) - Flat type filter ("2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE")
- `town` (string) - Town/area filter
- `year` (string) - Year in YYYY format (defaults to current year)

**Returns:** Highest price record with complete transaction details and search statistics.

#### 2. `get_lowest_price`
Get the lowest recorded resale price for HDB flats.

**Optional Parameters:**
- `flat_type` (string) - Flat type filter
- `town` (string) - Town/area filter  
- `year` (string) - Year in YYYY format (defaults to current year)

**Returns:** Lowest price record with complete transaction details and search statistics.

#### 3. `get_highest_avg_price_areas`
Get areas with the highest average transaction prices.

**Required Parameters:**
- `year` (string) - Year in YYYY format

**Optional Parameters:**
- `limit` (integer) - Number of results (default: 10, max: 50)
- `flat_type` (string) - Flat type filter

**Returns:** Ranked list of areas by average price with transaction counts and total values.

#### 4. `get_lowest_avg_price_areas`
Get areas with the lowest average transaction prices.

**Required Parameters:**
- `year` (string) - Year in YYYY format

**Optional Parameters:**
- `limit` (integer) - Number of results (default: 10, max: 50)
- `flat_type` (string) - Flat type filter

**Returns:** Ranked list of areas by average price with transaction counts and total values.

### Market Activity Tools

#### 5. `get_highest_transaction_areas`
Get areas with the highest number of resale transactions.

**Required Parameters:**
- `year` (string) - Year in YYYY format

**Optional Parameters:**
- `limit` (integer) - Number of results (default: 10, max: 50)

**Returns:** Areas ranked by transaction volume with counts and market activity indicators.

#### 6. `get_lowest_transaction_areas`
Get areas with the lowest number of resale transactions.

**Required Parameters:**
- `year` (string) - Year in YYYY format

**Optional Parameters:**
- `limit` (integer) - Number of results (default: 10, max: 50)

**Returns:** Areas ranked by transaction volume with counts and market activity indicators.

### Lease Analysis Tools

#### 7. `get_flats_by_lease_remaining`
Find flats with specified minimum lease remaining years.

**Optional Parameters:**
- `min_lease_years` (integer) - Minimum lease remaining (default: 90, range: 1-99)
- `year` (string) - Year in YYYY format (defaults to current year)
- `flat_type` (string) - Flat type filter
- `town` (string) - Town/area filter
- `limit` (integer) - Number of results (default: 50, max: 200)

**Returns:** List of qualifying flats with lease details, locations, and pricing information.

#### 8. `get_lease_statistics`
Get comprehensive statistics about lease remaining across different ranges.

**Optional Parameters:**
- `year` (string) - Year in YYYY format (defaults to current year)
- `flat_type` (string) - Flat type filter
- `town` (string) - Town/area filter

**Returns:** Distribution of flats across lease ranges with statistical summaries.

### System Tools

#### 9. `health_check`
Check server health and performance status.

**Returns:** Server status, cache information, and performance metrics.

### Manual Setup

1. Save the server code to a file (e.g., `HDB-Resale-Price-MCP.py`)

2. Open Claude Desktop settings: **Settings > Developer > Edit Config**

3. Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "HDB-Resale-Price": {
      "command": "python",
      "args": ["path/to/HDB-Resale-Price-MCP.py"]
    }
  }
}
```

## Usage Examples

Once installed, you can ask Claude to:

### Price Analysis Queries
- *"What's the highest HDB resale price recorded this year?"*
- *"Show me the most expensive 4-room flats sold in 2023"*
- *"Which areas have the highest average HDB prices?"*
- *"Compare average prices between Tampines and Jurong"*

### Market Activity Analysis
- *"Which towns had the most HDB transactions last year?"*
- *"Show me areas with low transaction volumes in 2023"*
- *"What's the market activity like in different regions?"*
- *"Find the most and least active HDB markets"*

### Investment and Purchase Planning
- *"Find HDB flats with at least 90 years lease remaining"*
- *"Show me 5-room flats in Bishan with long leases"*
- *"What's the lease situation for HDB flats in 2024?"*
- *"Compare lease remaining statistics across different flat types"*

### Year-over-Year Comparisons
- *"How did HDB prices change from 2022 to 2023?"*
- *"Compare transaction volumes between different years"*
- *"Show me price trends for executive flats over time"*
- *"What areas saw the biggest price increases?"*

## Data Metrics Explained

### Transaction Details
- **Resale Price**: Final transaction amount in SGD
- **Flat Type**: 2-room, 3-room, 4-room, 5-room, or Executive
- **Floor Area**: Size in square meters
- **Storey Range**: Floor level range (e.g., "10 TO 12")
- **Flat Model**: HDB flat design model
- **Lease Commence Date**: Year the original lease started

### Lease Information
- **Lease Remaining**: Years left on the 99-year lease
- **Lease Ranges**: Categorized into 90+, 80-89, 70-79, 60-69, 50-59, and <50 years
- **Lease Statistics**: Average, median, minimum, and maximum lease remaining

### Market Metrics
- **Transaction Count**: Number of resale transactions in a period
- **Average Price**: Mean transaction price for an area/type
- **Total Value**: Sum of all transactions in a category
- **Market Activity**: Relative transaction volume indicators

## Data Sources

This server integrates with Singapore's official HDB resale transaction database:

- **Source**: data.gov.sg HDB resale flat prices dataset
- **Coverage**: All HDB resale transactions island-wide
- **Update Frequency**: Regular updates from HDB
- **Historical Data**: Multi-year transaction records available (From 2017 Onwards)

## Data Quality Notes

- **Official Records**: All data sourced from official HDB transaction records
- **Comprehensive Coverage**: Includes all HDB resale transactions (excluding new sales)
- **Regular Updates**: Data updated according to HDB's reporting schedule
- **Validation**: Built-in data validation and error handling for data quality
- **Historical Accuracy**: Multi-year historical data for trend analysis

## License

This server is provided for research, analysis, and informational purposes. Please respect data.gov.sg's terms of service when using this housing market data.

## Disclaimer

This is an unofficial tool that interfaces with Singapore's official HDB resale transaction data. The authors are not affiliated with HDB or government housing agencies. For official housing policies, eligibility criteria, and purchase procedures, please consult the Housing & Development Board (HDB) directly.

---

# Singapore Humidity MCP Server

This server enables Claude to access real-time relative humidity data from Singapore's weather monitoring stations, providing current moisture levels and comfort assessments across the island.

## Features

- 💧 **Real-Time Humidity Data** from Singapore's official weather monitoring network
- 📊 **Comprehensive Station Coverage** across all regions of Singapore
- 🌡️ **Comfort Level Analysis** with humidity categorization for wellness planning
- 📍 **Geographic Distribution** with precise station coordinates
- 📈 **Statistical Analysis** including averages, extremes, and comparisons
- 🏝️ **Island-Wide Monitoring** for complete humidity picture
- ⚡ **Live Data Feed** updated regularly from data.gov.sg

## Tools

### Humidity Analysis Tools

#### 1. `humidity_summary`
Get comprehensive humidity summary for all weather stations in Singapore.

**Returns:** Overall statistics including highest, lowest, and average humidity levels with all station readings.

#### 2. `humidity_by_station`
Get humidity data for a specific station or all stations.

**Optional Parameters:**
- `station_id` (string) - Specific station ID (e.g., "S111"). Leave empty for all stations.

**Returns:** Detailed humidity readings for the specified station or all stations with location data.

#### 3. `humidity_categories`
Get humidity data with comfort level categories for wellness assessment.

**Returns:** All station readings categorized by comfort levels (Very Dry, Dry, Comfortable, Slightly Humid, Humid, Very Humid).

#### 4. `station_locations`
Get locations and metadata of all humidity monitoring stations.

**Returns:** Complete list of monitoring stations with coordinates, device IDs, and location information.

#### 5. `humidity_extremes`
Get stations with the highest and lowest humidity readings.

**Returns:** Extreme humidity readings with station details and complete sorted list of all readings.


### Manual Setup

1. Save the server code to a file (e.g., `Humidity-MCP.py`)

2. Open Claude Desktop settings: **Settings > Developer > Edit Config**

3. Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "HDB-Resale-Price": {
      "command": "python",
      "args": ["path/to/Humidity-MCP.py"]
    }
  }
}
```

## Usage Examples

Once installed, you can ask Claude to:

### General Humidity Queries
- *"What's the current humidity level in Singapore?"*
- *"Show me humidity readings from all weather stations"*
- *"What are the humidity conditions across Singapore right now?"*

### Comfort and Wellness Planning
- *"Which areas have comfortable humidity levels for outdoor activities?"*
- *"Where is it least humid in Singapore right now?"*
- *"Show me humidity comfort levels across different locations"*
- *"What areas should I avoid due to high humidity?"*

### Location-Specific Analysis
- *"What's the humidity at station S111?"*
- *"Show me humidity readings near my location"*
- *"Compare humidity levels between different regions"*
- *"Which weather station has the most comfortable conditions?"*

### Weather Pattern Analysis
- *"What's the humidity range across Singapore today?"*
- *"Show me the most and least humid areas on the island"*
- *"What's the average humidity level right now?"*
- *"Map out humidity distribution across Singapore"*

## Data Metrics Explained

### Humidity Measurements
- **Relative Humidity**: Percentage of moisture in the air relative to maximum capacity
- **Reading Unit**: Percentage (%) indicating moisture saturation level
- **Timestamp**: When the measurement was recorded
- **Station Coverage**: Multiple monitoring points across Singapore

### Comfort Level Categories
- **Very Dry** (< 30%): Uncomfortably low moisture, potential skin/respiratory irritation
- **Dry** (30-39%): Below optimal comfort, may cause minor discomfort
- **Comfortable** (40-59%): Ideal humidity range for human comfort
- **Slightly Humid** (60-69%): Above optimal but generally tolerable
- **Humid** (70-79%): Noticeably humid, may feel uncomfortable
- **Very Humid** (80%+): Uncomfortably high moisture, potential health concerns

### Geographic Data
- **Station Locations**: Precise latitude/longitude coordinates
- **Device IDs**: Unique identifiers for monitoring equipment
- **Regional Coverage**: Stations distributed across urban, suburban, and coastal areas
- **Network Density**: Comprehensive monitoring for accurate island-wide data

## Data Sources

This server integrates with Singapore's official weather monitoring system:

- **Source**: api-open.data.gov.sg/v2/real-time/api/relative-humidity
- **Coverage**: Island-wide weather monitoring network
- **Update Frequency**: Real-time updates (typically every few minutes)
- **Data Quality**: Official meteorological measurements from calibrated instruments

## License

This server is provided for weather monitoring, health planning, and educational purposes. Please respect data.gov.sg's terms of service when using this meteorological data.

## Disclaimer

This is an unofficial tool that interfaces with Singapore's official weather monitoring APIs. The authors are not affiliated with the Meteorological Service Singapore or government weather agencies. For official weather forecasts, warnings, and health advisories, please consult the National Environment Agency (NEA) and seek professional medical advice for health-related concerns.

---

# Singapore PSI MCP Server

This server enables Claude to access real-time Pollutant Standards Index (PSI) and air quality data from Singapore's environmental monitoring system, providing current air pollution levels and health advisories across all regions.

## Features

- 🌫️ **Real-Time PSI Data** from Singapore's official air quality monitoring network
- 🗺️ **Regional Coverage** across West, East, Central, South, and North Singapore
- 🏥 **Health Status Categories** with air quality classifications for safety planning
- 📊 **Comprehensive Pollutant Data** including PM2.5, PM10, O3, NO2, SO2, and CO
- 📍 **Geographic Monitoring** with precise regional coordinates
- ⚠️ **Safety Assessments** for outdoor activity planning and health protection
- ⚡ **Live Environmental Data** updated regularly from data.gov.sg

## Tools

### Air Quality Analysis Tools

#### 1. `psi_summary`
Get comprehensive PSI summary for all regions in Singapore.

**Returns:** Overall PSI statistics including highest, lowest, and average readings across all regions with timestamp information.

#### 2. `psi_by_region`
Get detailed PSI and pollutant data for a specific region or all regions.

**Optional Parameters:**
- `region` (string) - Region name: "west", "east", "central", "south", or "north". Leave empty for all regions.

**Returns:** Complete pollutant breakdown including PSI, PM2.5, PM10, O3, NO2, SO2, and CO levels for specified region(s).

#### 3. `air_quality_status`
Get air quality status with descriptive health categories for all regions.

**Returns:** Health-based air quality classifications (Good, Moderate, Unhealthy, Very Unhealthy, Hazardous) for each region.

#### 4. `region_metadata`
Get metadata about PSI monitoring regions including coordinates.

**Returns:** Geographic information and coordinates for all PSI monitoring regions across Singapore.

### Manual Setup

1. Save the server code to a file (e.g., `PSI-MCP.py`)

2. Open Claude Desktop settings: **Settings > Developer > Edit Config**

3. Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "HDB-Resale-Price": {
      "command": "python",
      "args": ["path/to/PSI-MCP.py"]
    }
  }
}
```

## Usage Examples

Once installed, you can ask Claude to:

### General Air Quality Queries
- *"What's the current air quality in Singapore?"*
- *"Show me PSI readings from all regions"*
- *"Is the air safe for outdoor activities today?"*

### Health and Safety Planning
- *"Which areas have unhealthy air quality right now?"*
- *"Is it safe to exercise outdoors in the Central region?"*
- *"Show me air quality status for planning my outdoor event"*
- *"Which region has the cleanest air today?"*

### Regional Analysis
- *"What's the PSI in the West region?"*
- *"Compare air quality between East and West Singapore"*
- *"Show me detailed pollutant levels for the North region"*
- *"Which region should I avoid due to poor air quality?"*

### Environmental Monitoring
- *"What's the range of PSI values across Singapore?"*
- *"Show me all pollutant measurements for today"*
- *"Map out air quality conditions across different regions"*
- *"What are the PM2.5 levels in each area?"*

## Data Metrics Explained

### PSI (Pollutant Standards Index)
- **PSI Value**: 24-hour average pollutant concentration index
- **Health Categories**:
  - **Good** (0-50): Air quality is satisfactory for most people
  - **Moderate** (51-100): Acceptable for most, some sensitive individuals may experience minor issues
  - **Unhealthy** (101-200): Everyone may experience health effects, sensitive groups more severely
  - **Very Unhealthy** (201-300): Health warnings for everyone, serious health effects possible
  - **Hazardous** (301+): Emergency conditions, entire population at risk

### Pollutant Measurements
- **PM2.5**: Fine particulate matter (≤2.5 micrometers) - measured in μg/m³
- **PM10**: Coarse particulate matter (≤10 micrometers) - measured in μg/m³
- **O3**: Ground-level ozone (8-hour maximum) - measured in μg/m³
- **NO2**: Nitrogen dioxide (1-hour maximum) - measured in μg/m³
- **SO2**: Sulfur dioxide (24-hour average) - measured in μg/m³
- **CO**: Carbon monoxide (8-hour maximum) - measured in mg/m³

### Regional Coverage
- **West Region**: Jurong area and western Singapore
- **East Region**: Changi area and eastern Singapore  
- **Central Region**: City center and central Singapore
- **South Region**: Southern Singapore including port areas
- **North Region**: Northern Singapore including Woodlands area

## Data Sources

This server integrates with Singapore's official environmental monitoring system:

- **Source**: api-open.data.gov.sg/v2/real-time/api/psi
- **Coverage**: Island-wide air quality monitoring network
- **Update Frequency**: Regular updates throughout the day
- **Data Quality**: Official measurements from National Environment Agency (NEA)

## License

This server is provided for environmental awareness, health planning, and educational purposes. Please respect data.gov.sg's terms of service when using this environmental monitoring data.

## Disclaimer

This is an unofficial tool that interfaces with Singapore's official air quality monitoring APIs. The authors are not affiliated with the National Environment Agency (NEA) or government environmental agencies. For official air quality advisories, health warnings, and emergency notifications, please consult the National Environment Agency (NEA) and seek professional medical advice for health-related concerns.

---

# Singapore UV Index MCP Server

This server enables Claude to access real-time UV Index data from Singapore's environmental monitoring system, providing current and hourly UV radiation levels with comprehensive sun protection guidance.

## Features

- ☀️ **Real-Time UV Index Data** from Singapore's official environmental monitoring
- 📅 **Hourly UV Forecasts** for complete daily sun exposure planning
- 🛡️ **Sun Protection Recommendations** with detailed safety guidelines for different UV levels
- ⚠️ **Dangerous UV Alerts** identifying peak exposure times requiring extra caution
- 📊 **Daily UV Statistics** including peak times, averages, and risk assessments
- 🕐 **Protection Scheduling** with hour-by-hour safety recommendations
- ⚡ **Live Environmental Data** updated regularly from data.gov.sg

## Tools

### UV Monitoring Tools

#### 1. `uv_current`
Get current UV index reading with risk level and detailed recommendations.

**Returns:** Current UV index, risk classification, and specific sun protection advice for immediate outdoor planning.

#### 2. `uv_hourly`
Get hourly UV index forecast for the entire day.

**Returns:** Complete hourly breakdown of UV levels with risk classifications for daily activity planning.

#### 3. `uv_summary`
Get comprehensive UV index summary including peak times and daily statistics.

**Returns:** Daily UV statistics including current, peak, minimum, and average UV levels with peak exposure times.

#### 4. `uv_peak_times`
Get specific times when UV index reaches dangerous levels (7+).

**Returns:** Detailed breakdown of high-risk periods requiring maximum sun protection, categorized by severity.

#### 5. `uv_protection_schedule`
Get recommended sun protection schedule based on hourly UV levels.

**Returns:** Hour-by-hour protection guide with specific safety measures needed throughout the day.

### Manual Setup

1. Save the server code to a file (e.g., `UV_MCP.py`)

2. Open Claude Desktop settings: **Settings > Developer > Edit Config**

3. Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "HDB-Resale-Price": {
      "command": "python",
      "args": ["path/to/UV_MCP.py"]
    }
  }
}
```

## Usage Examples

Once installed, you can ask Claude to:

### Daily Sun Safety Planning
- *"What's the current UV level and what protection do I need?"*
- *"Show me the UV forecast for today's outdoor activities"*
- *"When are the dangerous UV times I should avoid being outside?"*

### Activity Planning
- *"Is it safe to go for a run at 2 PM?"*
- *"What time should I schedule my outdoor event to avoid high UV?"*
- *"Show me the best times for outdoor activities today"*

## Data Metrics Explained

### UV Index Scale
- **Low (0-2)**: Minimal risk, no protection needed for most people
- **Moderate (3-5)**: Low risk, basic protection recommended during midday
- **High (6-7)**: Moderate risk, protection required, seek shade during peak hours
- **Very High (8-10)**: High risk, extra protection required, avoid sun 10am-4pm
- **Extreme (11+)**: Very high risk, maximum protection essential, minimize outdoor exposure

## Data Sources

This server integrates with Singapore's official environmental monitoring system:

- **Source**: api-open.data.gov.sg/v2/real-time/api/uv
- **Coverage**: Island-wide UV radiation monitoring
- **Update Frequency**: Regular hourly updates throughout the day
- **Data Quality**: Official measurements from National Environment Agency (NEA)

## License

This server is provided for sun safety, health planning, and educational purposes. Please respect data.gov.sg's terms of service when using this UV monitoring data.

## Disclaimer

This is an unofficial tool that interfaces with Singapore's official UV monitoring APIs. The authors are not affiliated with the National Environment Agency (NEA) or government environmental agencies. For official UV advisories, health warnings, and medical guidance, please consult the National Environment Agency (NEA) and seek professional medical advice for skin health concerns.

---

README is assisted with Generative AI (Claude.AI) 