import asyncio
import http.client
import json
import requests
from urllib.parse import urlencode
from typing import Optional, Dict, List
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from mcp.server import Server
    import mcp.server.stdio
    import mcp.types as types
except ImportError as e:
    logger.error(f"Failed to import MCP: {e}")
    logger.error("Please install MCP: pip install mcp")
    sys.exit(1)

class SingaporeCarParkSystem:
    """
    Comprehensive Singapore CarPark System combining static information and real-time availability
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CarPark System
        
        Args:
            api_key (str, optional): Your data.gov.sg API key for higher rate limits
        """
        self.api_key = api_key
        self.dataset_id = "d_23f946fa557947f93a8043bbef41dd09"
        self.carpark_info_cache = {}
    
    # ========== CARPARK INFORMATION METHODS ==========
    
    def fetch_carpark_info(self, carpark_number: Optional[str] = None) -> Dict:
        """
        Fetch static carpark information (address, type, pricing, etc.)
        
        Args:
            carpark_number (str, optional): Specific carpark to search for
            
        Returns:
            dict: Carpark information data
        """
        url = f"https://data.gov.sg/api/action/datastore_search?resource_id={self.dataset_id}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data['success']:
                records = data['result']['records']
                
                # If specific carpark requested, filter
                if carpark_number:
                    carpark_number = carpark_number.upper()
                    for record in records:
                        if record['car_park_no'] == carpark_number:
                            return record
                    return {'error': f'Carpark {carpark_number} not found in static data'}
                else:
                    return {'records': records, 'total': len(records)}
            else:
                return {'error': 'API request was not successful'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching carpark info: {e}")
            return {'error': f'Error fetching data: {e}'}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {'error': f'Error parsing JSON response: {e}'}
    
    def fetch_all_carpark_info(self) -> List[Dict]:
        """
        Fetch all carpark information records with pagination
        
        Returns:
            list: List of all carpark information records
        """
        base_url = f"https://data.gov.sg/api/action/datastore_search?resource_id={self.dataset_id}"
        all_records = []
        offset = 0
        limit = 100
        
        logger.info("Starting to fetch all carpark information...")
        
        while True:
            url = f"{base_url}&offset={offset}&limit={limit}"
            
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if data['success']:
                    records = data['result']['records']
                    if not records:
                        break
                        
                    all_records.extend(records)
                    offset += limit
                    logger.info(f"Fetched {len(records)} records (Total: {len(all_records)})")
                else:
                    logger.error("API request unsuccessful")
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching data: {e}")
                break
        
        # Cache the results
        for record in all_records:
            self.carpark_info_cache[record['car_park_no']] = record
            
        logger.info(f"Completed fetching all carpark info. Total: {len(all_records)}")
        return all_records
    
    # ========== CARPARK AVAILABILITY METHODS ==========
    
    def get_carpark_availability(self, carpark_number: Optional[str] = None, 
                               date_time: Optional[str] = None, timeout: int = 15) -> Dict:
        """
        Get real-time carpark availability data
        
        Args:
            carpark_number (str, optional): Specific carpark number to search for
            date_time (str, optional): ISO format datetime string
            timeout (int): Request timeout in seconds
            
        Returns:
            dict: API response data
        """
        conn = http.client.HTTPSConnection("api.data.gov.sg", timeout=timeout)
        
        params = {}
        if date_time:
            params['date_time'] = date_time
        
        url = "/v1/transport/carpark-availability"
        if params:
            url += "?" + urlencode(params)
        
        headers = {}
        if self.api_key:
            headers['X-API-KEY'] = self.api_key
        
        try:
            conn.request("GET", url, headers=headers)
            res = conn.getresponse()
            
            if res.status == 200:
                data = res.read()
                json_data = json.loads(data.decode("utf-8"))
                
                if carpark_number:
                    return self._filter_carpark_availability(json_data, carpark_number.upper())
                else:
                    return json_data
            else:
                logger.error(f"HTTP error: {res.status} - {res.reason}")
                return {'error': f'HTTP {res.status} - {res.reason}'}
                
        except Exception as e:
            logger.error(f"Error fetching availability data: {e}")
            return {'error': f'Error fetching availability data: {e}'}
        finally:
            try:
                conn.close()
            except:
                pass
    
    def _filter_carpark_availability(self, json_data: Dict, carpark_number: str) -> Dict:
        """Filter availability data for specific carpark"""
        if not json_data or 'items' not in json_data:
            return {'error': 'No data available'}
        
        for item in json_data['items']:
            if 'carpark_data' in item:
                for carpark in item['carpark_data']:
                    if carpark.get('carpark_number') == carpark_number:
                        return {
                            'timestamp': item.get('timestamp'),
                            'carpark_number': carpark.get('carpark_number'),
                            'carpark_info': carpark.get('carpark_info', []),
                            'update_datetime': carpark.get('update_datetime')
                        }
        
        return {'error': f'Carpark {carpark_number} not found in availability data'}
    
    # ========== COMBINED METHODS ==========
    
    def get_complete_carpark_info(self, carpark_number: str) -> Dict:
        """
        Get both static information and real-time availability for a carpark
        
        Args:
            carpark_number (str): Carpark number
            
        Returns:
            dict: Combined carpark data
        """
        carpark_number = carpark_number.upper()
        
        # Get static information
        static_info = self.fetch_carpark_info(carpark_number)
        
        # Get availability
        availability_info = self.get_carpark_availability(carpark_number)
        
        return {
            'carpark_number': carpark_number,
            'static_info': static_info,
            'availability_info': availability_info
        }
    
    def search_carparks_by_area(self, area_keyword: str, include_availability: bool = False, max_results: int = 10) -> List[Dict]:
        """
        Search carparks by area/address keyword
        
        Args:
            area_keyword (str): Keyword to search in address
            include_availability (bool): Whether to include real-time availability
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of matching carparks
        """
        # Load cache if empty
        if not self.carpark_info_cache:
            logger.info("Loading carpark database...")
            self.fetch_all_carpark_info()
        
        area_keyword = area_keyword.upper()
        matching_carparks = []
        
        logger.info(f"Searching for carparks containing '{area_keyword}'...")
        
        for carpark_no, info in self.carpark_info_cache.items():
            if area_keyword in info['address'].upper():
                carpark_data = {'carpark_number': carpark_no, 'static_info': info}
                
                if include_availability:
                    logger.info(f"Getting availability for {carpark_no}...")
                    try:
                        availability = self.get_carpark_availability(carpark_no, timeout=5)
                        carpark_data['availability_info'] = availability
                    except Exception as e:
                        logger.warning(f"Could not get availability for {carpark_no}: {e}")
                        carpark_data['availability_info'] = {'error': f'Timeout or error: {e}'}
                
                matching_carparks.append(carpark_data)
                
                # Limit results to prevent hanging
                if len(matching_carparks) >= max_results:
                    logger.info(f"Limiting to first {max_results} results...")
                    break
        
        return matching_carparks
    
    def search_carparks_by_name(self, name_keyword: str, include_availability: bool = False, max_results: int = 10) -> List[Dict]:
        """
        Search carparks by carpark number or name pattern
        
        Args:
            name_keyword (str): Keyword to search in carpark number
            include_availability (bool): Whether to include real-time availability
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of matching carparks
        """
        # Load cache if empty
        if not self.carpark_info_cache:
            logger.info("Loading carpark database...")
            self.fetch_all_carpark_info()
        
        name_keyword = name_keyword.upper()
        matching_carparks = []
        
        logger.info(f"Searching for carparks with name/number containing '{name_keyword}'...")
        
        for carpark_no, info in self.carpark_info_cache.items():
            if name_keyword in carpark_no.upper():
                carpark_data = {'carpark_number': carpark_no, 'static_info': info}
                
                if include_availability:
                    logger.info(f"Getting availability for {carpark_no}...")
                    try:
                        availability = self.get_carpark_availability(carpark_no, timeout=5)
                        carpark_data['availability_info'] = availability
                    except Exception as e:
                        logger.warning(f"Could not get availability for {carpark_no}: {e}")
                        carpark_data['availability_info'] = {'error': f'Timeout or error: {e}'}
                
                matching_carparks.append(carpark_data)
                
                # Limit results to prevent hanging
                if len(matching_carparks) >= max_results:
                    logger.info(f"Limiting to first {max_results} results...")
                    break
        
        return matching_carparks
    
    def get_all_carpark_availability(self, max_results: int = 50) -> Dict:
        """
        Get availability for all carparks (limited to prevent timeout)
        
        Args:
            max_results (int): Maximum number of carparks to include
            
        Returns:
            dict: All availability data
        """
        try:
            availability_data = self.get_carpark_availability()
            
            if 'error' in availability_data:
                return availability_data
            
            # Limit results if requested
            if max_results and 'items' in availability_data:
                for item in availability_data['items']:
                    if 'carpark_data' in item and len(item['carpark_data']) > max_results:
                        item['carpark_data'] = item['carpark_data'][:max_results]
                        item['note'] = f'Limited to first {max_results} carparks'
            
            return availability_data
            
        except Exception as e:
            logger.error(f"Error fetching all availability: {e}")
            return {'error': str(e)}

# Initialize system
carpark_system = SingaporeCarParkSystem()

# Create MCP server
server = Server("singapore-carpark")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="get_carpark_info",
            description="Get static information about a specific carpark by number",
            inputSchema={
                "type": "object",
                "properties": {
                    "carpark_number": {
                        "type": "string",
                        "description": "Carpark number (e.g., 'ACB', 'BM29')"
                    }
                },
                "required": ["carpark_number"]
            }
        ),
        types.Tool(
            name="get_carpark_availability", 
            description="Get real-time availability for a specific carpark",
            inputSchema={
                "type": "object",
                "properties": {
                    "carpark_number": {
                        "type": "string",
                        "description": "Carpark number (e.g., 'ACB', 'BM29')"
                    }
                },
                "required": ["carpark_number"]
            }
        ),
        types.Tool(
            name="get_complete_carpark_info",
            description="Get both static info and real-time availability for a specific carpark",
            inputSchema={
                "type": "object", 
                "properties": {
                    "carpark_number": {
                        "type": "string",
                        "description": "Carpark number (e.g., 'ACB', 'BM29')"
                    }
                },
                "required": ["carpark_number"]
            }
        ),
        types.Tool(
            name="search_carparks_by_area",
            description="Search carparks in a specific area or location by address keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "area_keyword": {
                        "type": "string", 
                        "description": "Area keyword to search in addresses (e.g., 'Jurong', 'Tampines', 'Orchard')"
                    },
                    "include_availability": {
                        "type": "boolean",
                        "description": "Whether to include real-time availability data",
                        "default": False
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["area_keyword"]
            }
        ),
        types.Tool(
            name="search_carparks_by_name",
            description="Search carparks by carpark number or name pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "name_keyword": {
                        "type": "string", 
                        "description": "Keyword to search in carpark numbers/names (e.g., 'AC', 'BM', 'TPM')"
                    },
                    "include_availability": {
                        "type": "boolean",
                        "description": "Whether to include real-time availability data",
                        "default": False
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["name_keyword"]
            }
        ),
        types.Tool(
            name="get_all_carpark_availability",
            description="Get real-time availability for all carparks (limited for performance)",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of carparks to include",
                        "default": 50
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    try:
        logger.info(f"Tool call: {name} with args: {arguments}")
        
        if name == "get_carpark_info":
            carpark_number = arguments.get("carpark_number")
            if not carpark_number:
                return [types.TextContent(type="text", text="Error: carpark_number required")]
            
            result = carpark_system.fetch_carpark_info(carpark_number)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_carpark_availability":
            carpark_number = arguments.get("carpark_number")
            if not carpark_number:
                return [types.TextContent(type="text", text="Error: carpark_number required")]
            
            result = carpark_system.get_carpark_availability(carpark_number)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_complete_carpark_info":
            carpark_number = arguments.get("carpark_number")
            if not carpark_number:
                return [types.TextContent(type="text", text="Error: carpark_number required")]
            
            result = carpark_system.get_complete_carpark_info(carpark_number)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "search_carparks_by_area":
            area_keyword = arguments.get("area_keyword")
            include_availability = arguments.get("include_availability", False)
            max_results = arguments.get("max_results", 10)
            
            if not area_keyword:
                return [types.TextContent(type="text", text="Error: area_keyword required")]
            
            result = carpark_system.search_carparks_by_area(area_keyword, include_availability, max_results)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "search_carparks_by_name":
            name_keyword = arguments.get("name_keyword")
            include_availability = arguments.get("include_availability", False)
            max_results = arguments.get("max_results", 10)
            
            if not name_keyword:
                return [types.TextContent(type="text", text="Error: name_keyword required")]
            
            result = carpark_system.search_carparks_by_name(name_keyword, include_availability, max_results)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_all_carpark_availability":
            max_results = arguments.get("max_results", 50)
            
            result = carpark_system.get_all_carpark_availability(max_results)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Tool error in {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Run the MCP server"""
    logger.info("Starting Enhanced Singapore Carpark MCP Server...")
    
    try:
        # Use the stdio server properly
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Connected to stdio streams")
            
            # Run the server
            await server.run(
                read_stream, 
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)