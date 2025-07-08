import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlencode
import aiohttp
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data.gov.sg API configuration
BASE_URL = "https://data.gov.sg/api/action/datastore_search"
DATASET_ID = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"

class HDBResaleServer:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def fetch_data(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch data from data.gov.sg API with optional filters"""
        session = await self.get_session()
        all_records = []
        offset = 0
        
        while True:
            params = {
                "resource_id": DATASET_ID,
                "limit": limit,
                "offset": offset
            }
            
            if filters:
                params["filters"] = json.dumps(filters)
            
            try:
                async with session.get(BASE_URL, params=params) as response:
                    data = await response.json()
                    
                    if not data.get("success", False):
                        raise Exception(f"API error: {data}")
                    
                    records = data["result"]["records"]
                    if not records:
                        break
                    
                    all_records.extend(records)
                    
                    # Check if we have more data
                    if len(records) < limit:
                        break
                    
                    offset += limit
                    
            except Exception as e:
                logger.error(f"Error fetching data: {str(e)}")
                raise
        
        return all_records
    
    async def get_highest_price(self, flat_type: str = None, town: str = None, year: str = None) -> Dict[str, Any]:
        """Get the highest recorded price for a flat"""
        filters = {}
        
        if flat_type:
            filters["flat_type"] = flat_type
        if town:
            filters["town"] = town
        
        records = await self.fetch_data(filters)
        
        # Filter by year if specified (client-side since API doesn't support year range filtering)
        if year:
            records = [r for r in records if r["month"].startswith(year)]
        
        if not records:
            return {"error": "No records found with the specified filters"}
        
        # Convert resale_price to int for comparison
        max_record = max(records, key=lambda x: int(x["resale_price"]))
        
        return {
            "highest_price": int(max_record["resale_price"]),
            "details": max_record
        }
    
    async def get_lowest_price(self, flat_type: str = None, town: str = None, year: str = None) -> Dict[str, Any]:
        """Get the lowest recorded price for a flat"""
        filters = {}
        
        if flat_type:
            filters["flat_type"] = flat_type
        if town:
            filters["town"] = town
        
        records = await self.fetch_data(filters)
        
        # Filter by year if specified (client-side since API doesn't support year range filtering)
        if year:
            records = [r for r in records if r["month"].startswith(year)]
        
        if not records:
            return {"error": "No records found with the specified filters"}
        
        # Convert resale_price to int for comparison
        min_record = min(records, key=lambda x: int(x["resale_price"]))
        
        return {
            "lowest_price": int(min_record["resale_price"]),
            "details": min_record
        }
    
    async def get_highest_transaction_areas(self, year: str, limit: int = 10) -> Dict[str, Any]:
        """Get areas with the highest number of transactions in a year"""
        # Fetch all records (we need to filter by year client-side)
        records = await self.fetch_data()
        
        # Filter by year
        year_records = [r for r in records if r["month"].startswith(year)]
        
        if not year_records:
            return {"error": f"No records found for year {year}"}
        
        # Count transactions by town
        town_counts = {}
        for record in year_records:
            town = record["town"]
            town_counts[town] = town_counts.get(town, 0) + 1
        
        # Sort by transaction count (descending)
        sorted_towns = sorted(town_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "year": year,
            "total_transactions": len(year_records),
            "highest_transaction_areas": [
                {"town": town, "transaction_count": count}
                for town, count in sorted_towns[:limit]
            ]
        }
    
    async def get_lowest_transaction_areas(self, year: str, limit: int = 10) -> Dict[str, Any]:
        """Get areas with the lowest number of transactions in a year"""
        # Fetch all records (we need to filter by year client-side)
        records = await self.fetch_data()
        
        # Filter by year
        year_records = [r for r in records if r["month"].startswith(year)]
        
        if not year_records:
            return {"error": f"No records found for year {year}"}
        
        # Count transactions by town
        town_counts = {}
        for record in year_records:
            town = record["town"]
            town_counts[town] = town_counts.get(town, 0) + 1
        
        # Sort by transaction count (ascending)
        sorted_towns = sorted(town_counts.items(), key=lambda x: x[1])
        
        return {
            "year": year,
            "total_transactions": len(year_records),
            "lowest_transaction_areas": [
                {"town": town, "transaction_count": count}
                for town, count in sorted_towns[:limit]
            ]
        }
    
    async def get_highest_avg_price_areas(self, year: str, limit: int = 10, flat_type: str = None) -> Dict[str, Any]:
        """Get areas with the highest average transaction prices in a year"""
        # Build filters for more efficient API calls
        filters = {}
        if flat_type:
            filters["flat_type"] = flat_type
        
        records = await self.fetch_data(filters)
        
        # Filter by year (client-side since API doesn't support year range filtering)
        year_records = [r for r in records if r["month"].startswith(year)]
        
        if not year_records:
            return {"error": f"No records found for year {year}" + (f" and flat type {flat_type}" if flat_type else "")}
        
        # Calculate average prices by town
        town_data = {}
        for record in year_records:
            town = record["town"]
            price = int(record["resale_price"])
            
            if town not in town_data:
                town_data[town] = {"total_price": 0, "count": 0}
            
            town_data[town]["total_price"] += price
            town_data[town]["count"] += 1
        
        # Calculate averages and sort
        town_averages = []
        for town, data in town_data.items():
            avg_price = data["total_price"] / data["count"]
            town_averages.append({
                "town": town,
                "average_price": round(avg_price, 2),
                "transaction_count": data["count"],
                "total_value": data["total_price"]
            })
        
        town_averages.sort(key=lambda x: x["average_price"], reverse=True)
        
        return {
            "year": year,
            "flat_type": flat_type or "All types",
            "total_transactions": len(year_records),
            "total_areas": len(town_data),
            "highest_avg_price_areas": town_averages[:limit]
        }
    
    async def get_lowest_avg_price_areas(self, year: str, limit: int = 10, flat_type: str = None) -> Dict[str, Any]:
        """Get areas with the lowest average transaction prices in a year"""
        # Build filters for more efficient API calls
        filters = {}
        if flat_type:
            filters["flat_type"] = flat_type
        
        records = await self.fetch_data(filters)
        
        # Filter by year (client-side since API doesn't support year range filtering)
        year_records = [r for r in records if r["month"].startswith(year)]
        
        if not year_records:
            return {"error": f"No records found for year {year}" + (f" and flat type {flat_type}" if flat_type else "")}
        
        # Calculate average prices by town
        town_data = {}
        for record in year_records:
            town = record["town"]
            price = int(record["resale_price"])
            
            if town not in town_data:
                town_data[town] = {"total_price": 0, "count": 0}
            
            town_data[town]["total_price"] += price
            town_data[town]["count"] += 1
        
        # Calculate averages and sort
        town_averages = []
        for town, data in town_data.items():
            avg_price = data["total_price"] / data["count"]
            town_averages.append({
                "town": town,
                "average_price": round(avg_price, 2),
                "transaction_count": data["count"],
                "total_value": data["total_price"]
            })
        
        town_averages.sort(key=lambda x: x["average_price"])
        
        return {
            "year": year,
            "flat_type": flat_type or "All types",
            "total_transactions": len(year_records),
            "total_areas": len(town_data),
            "lowest_avg_price_areas": town_averages[:limit]
        }
    
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP messages"""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "hdb-resale-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "notifications/initialized":
                return None  # No response needed
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [
                            {
                                "name": "get_highest_price",
                                "description": "Get the highest recorded price for a flat",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "flat_type": {"type": "string", "enum": ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]},
                                        "town": {"type": "string"},
                                        "year": {"type": "string"}
                                    },
                                    "additionalProperties": False
                                }
                            },
                            {
                                "name": "get_lowest_price",
                                "description": "Get the lowest recorded price for a flat",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "flat_type": {"type": "string", "enum": ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]},
                                        "town": {"type": "string"},
                                        "year": {"type": "string"}
                                    },
                                    "additionalProperties": False
                                }
                            },
                            {
                                "name": "get_highest_transaction_areas",
                                "description": "Get areas with the highest number of transactions in a year",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "year": {"type": "string", "pattern": "^[0-9]{4}$"},
                                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                                    },
                                    "required": ["year"],
                                    "additionalProperties": False
                                }
                            },
                            {
                                "name": "get_lowest_transaction_areas",
                                "description": "Get areas with the lowest number of transactions in a year",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "year": {"type": "string", "pattern": "^[0-9]{4}$"},
                                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                                    },
                                    "required": ["year"],
                                    "additionalProperties": False
                                }
                            },
                            {
                                "name": "get_highest_avg_price_areas",
                                "description": "Get areas with the highest average transaction prices in a year",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "year": {"type": "string", "pattern": "^[0-9]{4}$"},
                                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                                        "flat_type": {"type": "string", "enum": ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]}
                                    },
                                    "required": ["year"],
                                    "additionalProperties": False
                                }
                            },
                            {
                                "name": "get_lowest_avg_price_areas",
                                "description": "Get areas with the lowest average transaction prices in a year",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "year": {"type": "string", "pattern": "^[0-9]{4}$"},
                                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                                        "flat_type": {"type": "string", "enum": ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]}
                                    },
                                    "required": ["year"],
                                    "additionalProperties": False
                                }
                            }
                        ]
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "get_highest_price":
                    result = await self.get_highest_price(**arguments)
                elif tool_name == "get_lowest_price":
                    result = await self.get_lowest_price(**arguments)
                elif tool_name == "get_highest_transaction_areas":
                    result = await self.get_highest_transaction_areas(**arguments)
                elif tool_name == "get_lowest_transaction_areas":
                    result = await self.get_lowest_transaction_areas(**arguments)
                elif tool_name == "get_highest_avg_price_areas":
                    result = await self.get_highest_avg_price_areas(**arguments)
                elif tool_name == "get_lowest_avg_price_areas":
                    result = await self.get_lowest_avg_price_areas(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2, ensure_ascii=False)
                            }
                        ]
                    }
                }
            
            else:
                raise ValueError(f"Unknown method: {method}")
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            # Only return error response if there's a valid message ID
            if msg_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
            return None
    
    async def run(self):
        """Run the MCP server"""
        try:
            while True:
                try:
                    # Read from stdin
                    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                    if not line:
                        break
                    
                    # Parse JSON-RPC message
                    try:
                        message = json.loads(line.strip())
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON: {line.strip()}")
                        continue
                    
                    # Skip if no method (likely malformed)
                    if "method" not in message:
                        logger.error(f"No method in message: {message}")
                        continue
                    
                    # Handle message
                    response = await self.handle_message(message)
                    
                    # Send response if needed
                    if response:
                        print(json.dumps(response, ensure_ascii=False))
                        sys.stdout.flush()
                
                except Exception as e:
                    logger.error(f"Error in main loop: {str(e)}")
                    continue
        
        finally:
            if self.session:
                await self.session.close()

async def main():
    """Main entry point"""
    server = HDBResaleServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())