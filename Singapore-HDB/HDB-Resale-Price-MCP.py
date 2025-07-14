import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import aiohttp
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data.gov.sg API configuration
BASE_URL = "https://data.gov.sg/api/action/datastore_search"
DATASET_ID = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"

# Default year (current year)
DEFAULT_YEAR = str(datetime.now().year)

class HDBResaleServer:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, List[Dict[str, Any]]] = {}  # Simple in-memory cache
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with timeout"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)  # 30s total, 10s connect
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    def _generate_cache_key(self, year: str, filters: Dict[str, Any] = None) -> str:
        """Generate cache key for storing results"""
        filter_str = json.dumps(filters or {}, sort_keys=True)
        return f"{year}_{filter_str}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Simple health check to verify server is responsive"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cache_size": len(self.cache),
            "session_active": self.session is not None and not (self.session.closed if self.session else True)
        }
    
    async def fetch_data_by_year_optimized(self, year: str, filters: Dict[str, Any] = None, max_records: int = 50000) -> List[Dict[str, Any]]:
        """Optimized data fetching with multiple strategies"""
        cache_key = self._generate_cache_key(year, filters)
        
        # Check cache first
        if cache_key in self.cache:
            logger.info(f"Using cached data for {year}")
            return self.cache[cache_key]
        
        session = await self.get_session()
        all_records = []
        
        # Strategy 1: Try to use filters to reduce data at API level
        try:
            logger.info(f"Fetching data for year {year} with filters {filters}")
            all_records = await self._fetch_with_api_filters(session, year, filters, max_records)
            
            if all_records:
                logger.info(f"Successfully fetched {len(all_records)} records using API filters")
                self.cache[cache_key] = all_records
                return all_records
        except Exception as e:
            logger.warning(f"API filter strategy failed: {e}")
        
        # Strategy 2: Fetch in small chunks and filter client-side
        try:
            logger.info(f"Falling back to chunked fetching for year {year}")
            all_records = await self._fetch_chunked_with_year_filter(session, year, filters, max_records)
            
            if all_records:
                logger.info(f"Successfully fetched {len(all_records)} records using chunked approach")
                self.cache[cache_key] = all_records
                return all_records
        except Exception as e:
            logger.error(f"Chunked fetch strategy failed: {e}")
        
        # Strategy 3: Last resort - very limited fetch
        try:
            logger.info(f"Using limited fetch strategy for year {year}")
            all_records = await self._fetch_limited(session, year, filters)
            
            if all_records:
                logger.info(f"Limited fetch returned {len(all_records)} records")
                self.cache[cache_key] = all_records
                return all_records
        except Exception as e:
            logger.error(f"Limited fetch strategy failed: {e}")
        
        return []
    
    async def _fetch_with_api_filters(self, session: aiohttp.ClientSession, year: str, filters: Dict[str, Any], max_records: int) -> List[Dict[str, Any]]:
        """Try to use API-level filtering"""
        all_records = []
        offset = 0
        limit = 1000
        
        # Build comprehensive filters
        api_filters = filters.copy() if filters else {}
        
        while len(all_records) < max_records:
            params = {
                "resource_id": DATASET_ID,
                "limit": limit,
                "offset": offset
            }
            
            if api_filters:
                params["filters"] = json.dumps(api_filters)
            
            async with session.get(BASE_URL, params=params) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                data = await response.json()
                
                if not data.get("success", False):
                    raise Exception(f"API error: {data}")
                
                records = data["result"]["records"]
                if not records:
                    break
                
                # Filter by year client-side as backup
                year_records = [r for r in records if r.get("month", "").startswith(year)]
                all_records.extend(year_records)
                
                if len(records) < limit:
                    break
                
                offset += limit
                
                # Add small delay to avoid overwhelming the API
                await asyncio.sleep(0.1)
        
        return all_records
    
    async def _fetch_chunked_with_year_filter(self, session: aiohttp.ClientSession, year: str, filters: Dict[str, Any], max_records: int) -> List[Dict[str, Any]]:
        """Fetch in small chunks and filter by year"""
        all_records = []
        offset = 0
        limit = 500  # Smaller chunks for faster response
        consecutive_empty_chunks = 0
        max_empty_chunks = 5
        
        base_filters = filters or {}
        
        while len(all_records) < max_records and consecutive_empty_chunks < max_empty_chunks:
            params = {
                "resource_id": DATASET_ID,
                "limit": limit,
                "offset": offset
            }
            
            if base_filters:
                params["filters"] = json.dumps(base_filters)
            
            try:
                async with session.get(BASE_URL, params=params) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} at offset {offset}")
                        break
                    
                    data = await response.json()
                    
                    if not data.get("success", False):
                        logger.warning(f"API error at offset {offset}: {data}")
                        break
                    
                    records = data["result"]["records"]
                    if not records:
                        consecutive_empty_chunks += 1
                        offset += limit
                        continue
                    
                    # Filter by year
                    year_records = [r for r in records if r.get("month", "").startswith(year)]
                    
                    if year_records:
                        all_records.extend(year_records)
                        consecutive_empty_chunks = 0
                    else:
                        consecutive_empty_chunks += 1
                    
                    # Stop if we got fewer records than requested (likely end of data)
                    if len(records) < limit:
                        break
                    
                    offset += limit
                    
                    # Add delay and log progress
                    await asyncio.sleep(0.05)
                    if offset % 5000 == 0:
                        logger.info(f"Processed {offset} records, found {len(all_records)} for year {year}")
            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout at offset {offset}")
                break
            except Exception as e:
                logger.warning(f"Error at offset {offset}: {e}")
                consecutive_empty_chunks += 1
                offset += limit
        
        return all_records
    
    async def _fetch_limited(self, session: aiohttp.ClientSession, year: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Last resort: fetch only a limited amount of recent data"""
        all_records = []
        limit = 1000
        max_attempts = 10
        
        for attempt in range(max_attempts):
            offset = attempt * limit
            
            params = {
                "resource_id": DATASET_ID,
                "limit": limit,
                "offset": offset
            }
            
            if filters:
                params["filters"] = json.dumps(filters)
            
            try:
                async with session.get(BASE_URL, params=params) as response:
                    if response.status != 200:
                        continue
                    
                    data = await response.json()
                    if not data.get("success", False):
                        continue
                    
                    records = data["result"]["records"]
                    if not records:
                        break
                    
                    # Filter by year
                    year_records = [r for r in records if r.get("month", "").startswith(year)]
                    all_records.extend(year_records)
                    
                    # If we found some records for the year, that's good enough
                    if year_records and len(all_records) >= 100:
                        break
                        
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.warning(f"Limited fetch attempt {attempt} failed: {e}")
                continue
        
        return all_records
    
    async def get_highest_price(self, flat_type: str = None, town: str = None, year: str = None) -> Dict[str, Any]:
        """Get the highest recorded price for a flat"""
        filters = {}
        
        if flat_type:
            filters["flat_type"] = flat_type
        if town:
            filters["town"] = town
        
        # Use current year as default if no year specified
        year = year or DEFAULT_YEAR
        
        try:
            records = await self.fetch_data_by_year_optimized(year, filters, max_records=10000)
            
            if not records:
                return {"error": f"No records found with the specified filters for year {year}"}
            
            # Convert resale_price to float for comparison
            max_record = max(records, key=lambda x: float(x["resale_price"]))
            
            return {
                "highest_price": float(max_record["resale_price"]),
                "details": max_record,
                "year_searched": year,
                "total_records_found": len(records)
            }
        except Exception as e:
            logger.error(f"Error in get_highest_price: {e}")
            return {"error": f"Failed to retrieve data: {str(e)}"}
    
    async def get_lowest_price(self, flat_type: str = None, town: str = None, year: str = None) -> Dict[str, Any]:
        """Get the lowest recorded price for a flat"""
        filters = {}
        
        if flat_type:
            filters["flat_type"] = flat_type
        if town:
            filters["town"] = town
        
        # Use current year as default if no year specified
        year = year or DEFAULT_YEAR
        
        try:
            records = await self.fetch_data_by_year_optimized(year, filters, max_records=10000)
            
            if not records:
                return {"error": f"No records found with the specified filters for year {year}"}
            
            # Convert resale_price to float for comparison
            min_record = min(records, key=lambda x: float(x["resale_price"]))
            
            return {
                "lowest_price": float(min_record["resale_price"]),
                "details": min_record,
                "year_searched": year,
                "total_records_found": len(records)
            }
        except Exception as e:
            logger.error(f"Error in get_lowest_price: {e}")
            return {"error": f"Failed to retrieve data: {str(e)}"}
    
    async def get_highest_transaction_areas(self, year: str, limit: int = 10) -> Dict[str, Any]:
        """Get areas with the highest number of transactions in a year"""
        try:
            # Fetch records for the specific year only
            records = await self.fetch_data_by_year_optimized(year, max_records=30000)
            
            if not records:
                return {"error": f"No records found for year {year}"}
            
            # Count transactions by town
            town_counts = {}
            for record in records:
                town = record.get("town", "Unknown")
                town_counts[town] = town_counts.get(town, 0) + 1
            
            # Sort by transaction count (descending)
            sorted_towns = sorted(town_counts.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "year": year,
                "total_transactions": len(records),
                "highest_transaction_areas": [
                    {"town": town, "transaction_count": count}
                    for town, count in sorted_towns[:limit]
                ]
            }
        except Exception as e:
            logger.error(f"Error in get_highest_transaction_areas: {e}")
            return {"error": f"Failed to retrieve data: {str(e)}"}
    
    async def get_lowest_transaction_areas(self, year: str, limit: int = 10) -> Dict[str, Any]:
        """Get areas with the lowest number of transactions in a year"""
        try:
            # Fetch records for the specific year only
            records = await self.fetch_data_by_year_optimized(year, max_records=30000)
            
            if not records:
                return {"error": f"No records found for year {year}"}
            
            # Count transactions by town
            town_counts = {}
            for record in records:
                town = record.get("town", "Unknown")
                town_counts[town] = town_counts.get(town, 0) + 1
            
            # Sort by transaction count (ascending)
            sorted_towns = sorted(town_counts.items(), key=lambda x: x[1])
            
            return {
                "year": year,
                "total_transactions": len(records),
                "lowest_transaction_areas": [
                    {"town": town, "transaction_count": count}
                    for town, count in sorted_towns[:limit]
                ]
            }
        except Exception as e:
            logger.error(f"Error in get_lowest_transaction_areas: {e}")
            return {"error": f"Failed to retrieve data: {str(e)}"}
    
    async def get_highest_avg_price_areas(self, year: str, limit: int = 10, flat_type: str = None) -> Dict[str, Any]:
        """Get areas with the highest average transaction prices in a year"""
        try:
            # Build filters for more efficient API calls
            filters = {}
            if flat_type:
                filters["flat_type"] = flat_type
            
            # Fetch records for the specific year only
            records = await self.fetch_data_by_year_optimized(year, filters, max_records=30000)
            
            if not records:
                return {"error": f"No records found for year {year}" + (f" and flat type {flat_type}" if flat_type else "")}
            
            # Calculate average prices by town
            town_data = {}
            for record in records:
                town = record.get("town", "Unknown")
                try:
                    price = float(record.get("resale_price", 0))
                    if price > 0:  # Valid price
                        if town not in town_data:
                            town_data[town] = {"total_price": 0, "count": 0}
                        
                        town_data[town]["total_price"] += price
                        town_data[town]["count"] += 1
                except (ValueError, TypeError):
                    continue  # Skip invalid prices
            
            # Calculate averages and sort
            town_averages = []
            for town, data in town_data.items():
                if data["count"] > 0:
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
                "total_transactions": len(records),
                "total_areas": len(town_data),
                "highest_avg_price_areas": town_averages[:limit]
            }
        except Exception as e:
            logger.error(f"Error in get_highest_avg_price_areas: {e}")
            return {"error": f"Failed to retrieve data: {str(e)}"}
    
    async def get_lowest_avg_price_areas(self, year: str, limit: int = 10, flat_type: str = None) -> Dict[str, Any]:
        """Get areas with the lowest average transaction prices in a year"""
        try:
            # Build filters for more efficient API calls
            filters = {}
            if flat_type:
                filters["flat_type"] = flat_type
            
            # Fetch records for the specific year only
            records = await self.fetch_data_by_year_optimized(year, filters, max_records=30000)
            
            if not records:
                return {"error": f"No records found for year {year}" + (f" and flat type {flat_type}" if flat_type else "")}
            
            # Calculate average prices by town
            town_data = {}
            for record in records:
                town = record.get("town", "Unknown")
                try:
                    price = float(record.get("resale_price", 0))
                    if price > 0:  # Valid price
                        if town not in town_data:
                            town_data[town] = {"total_price": 0, "count": 0}
                        
                        town_data[town]["total_price"] += price
                        town_data[town]["count"] += 1
                except (ValueError, TypeError):
                    continue  # Skip invalid prices
            
            # Calculate averages and sort
            town_averages = []
            for town, data in town_data.items():
                if data["count"] > 0:
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
                "total_transactions": len(records),
                "total_areas": len(town_data),
                "lowest_avg_price_areas": town_averages[:limit]
            }
        except Exception as e:
            logger.error(f"Error in get_lowest_avg_price_areas: {e}")
            return {"error": f"Failed to retrieve data: {str(e)}"}
    
    async def get_flats_by_lease_remaining(self, min_lease_years: int = 90, year: str = None, flat_type: str = None, town: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get flats with specified minimum lease remaining years"""
        try:
            logger.info(f"Starting lease search: min_lease={min_lease_years}, year={year}, flat_type={flat_type}, town={town}")
            
            filters = {}
            
            if flat_type:
                filters["flat_type"] = flat_type
            if town:
                filters["town"] = town
            
            # Use current year as default if no year specified
            year = year or DEFAULT_YEAR
            
            # Validate year is a valid integer
            try:
                current_year = int(year)
            except (ValueError, TypeError):
                return {"error": f"Invalid year format: {year}. Please use YYYY format."}
            
            # Validate min_lease_years
            if not isinstance(min_lease_years, int) or min_lease_years < 1 or min_lease_years > 99:
                return {"error": f"Invalid min_lease_years: {min_lease_years}. Must be between 1 and 99."}
            
            logger.info(f"Fetching data for lease analysis...")
            records = await self.fetch_data_by_year_optimized(year, filters, max_records=20000)  # Reduced limit
            
            if not records:
                return {"error": f"No records found with the specified filters for year {year}"}
            
            logger.info(f"Analyzing {len(records)} records for lease remaining...")
            
            # Filter by lease remaining and calculate lease info
            qualifying_flats = []
            processed_count = 0
            error_count = 0
            
            for record in records:
                processed_count += 1
                
                # Log progress every 1000 records
                if processed_count % 1000 == 0:
                    logger.info(f"Processed {processed_count}/{len(records)} records, found {len(qualifying_flats)} qualifying flats")
                
                try:
                    # Safely get lease_commence_date
                    lease_commence_raw = record.get("lease_commence_date")
                    if not lease_commence_raw:
                        error_count += 1
                        continue
                    
                    # Try to convert to int
                    lease_commence_year = int(float(str(lease_commence_raw)))  # Handle string/float conversion
                    
                    if lease_commence_year <= 0 or lease_commence_year > current_year:
                        error_count += 1
                        continue
                    
                    # HDB leases are typically 99 years
                    lease_remaining = 99 - (current_year - lease_commence_year)
                    
                    # Skip if lease remaining is negative or unrealistic
                    if lease_remaining < 0 or lease_remaining > 99:
                        error_count += 1
                        continue
                    
                    if lease_remaining >= min_lease_years:
                        # Safely get price
                        try:
                            price = float(record.get("resale_price", 0))
                        except (ValueError, TypeError):
                            price = 0.0
                        
                        flat_info = {
                            "town": str(record.get("town", "Unknown")),
                            "flat_type": str(record.get("flat_type", "Unknown")),
                            "block": str(record.get("block", "Unknown")),
                            "street_name": str(record.get("street_name", "Unknown")),
                            "storey_range": str(record.get("storey_range", "Unknown")),
                            "floor_area_sqm": str(record.get("floor_area_sqm", "Unknown")),
                            "flat_model": str(record.get("flat_model", "Unknown")),
                            "lease_commence_date": lease_commence_year,
                            "lease_remaining_years": lease_remaining,
                            "resale_price": price,
                            "month": str(record.get("month", "Unknown"))
                        }
                        qualifying_flats.append(flat_info)
                
                except Exception as e:
                    error_count += 1
                    # Log detailed error for debugging
                    if error_count <= 5:  # Only log first 5 errors to avoid spam
                        logger.warning(f"Error processing record {processed_count}: {e}")
                    continue
            
            logger.info(f"Lease analysis complete: {len(qualifying_flats)} qualifying flats found, {error_count} records had errors")
            
            # Sort by lease remaining (descending - most lease remaining first)
            try:
                qualifying_flats.sort(key=lambda x: x["lease_remaining_years"], reverse=True)
            except Exception as e:
                logger.warning(f"Error sorting results: {e}")
                # If sorting fails, return unsorted results
            
            return {
                "search_criteria": {
                    "min_lease_years": min_lease_years,
                    "year": year,
                    "flat_type": flat_type or "All types",
                    "town": town or "All towns"
                },
                "total_qualifying_flats": len(qualifying_flats),
                "total_records_searched": len(records),
                "records_with_errors": error_count,
                "flats": qualifying_flats[:limit]
            }
            
        except Exception as e:
            logger.error(f"Critical error in get_flats_by_lease_remaining: {e}")
            return {"error": f"Failed to retrieve lease data: {str(e)}. Please try again or contact support."}
    
    async def get_lease_statistics(self, year: str = None, flat_type: str = None, town: str = None) -> Dict[str, Any]:
        """Get statistics about lease remaining across different ranges"""
        filters = {}
        
        if flat_type:
            filters["flat_type"] = flat_type
        if town:
            filters["town"] = town
        
        # Use current year as default if no year specified
        year = year or DEFAULT_YEAR
        current_year = int(year)
        
        try:
            records = await self.fetch_data_by_year_optimized(year, filters, max_records=30000)
            
            if not records:
                return {"error": f"No records found with the specified filters for year {year}"}
            
            # Define lease ranges
            lease_ranges = {
                "90+ years": 0,
                "80-89 years": 0,
                "70-79 years": 0,
                "60-69 years": 0,
                "50-59 years": 0,
                "Less than 50 years": 0
            }
            
            valid_records = 0
            total_lease_remaining = 0
            lease_data = []
            
            for record in records:
                try:
                    lease_commence_year = int(record.get("lease_commence_date", 0))
                    if lease_commence_year > 0:
                        lease_remaining = 99 - (current_year - lease_commence_year)
                        
                        # Categorize into ranges
                        if lease_remaining >= 90:
                            lease_ranges["90+ years"] += 1
                        elif lease_remaining >= 80:
                            lease_ranges["80-89 years"] += 1
                        elif lease_remaining >= 70:
                            lease_ranges["70-79 years"] += 1
                        elif lease_remaining >= 60:
                            lease_ranges["60-69 years"] += 1
                        elif lease_remaining >= 50:
                            lease_ranges["50-59 years"] += 1
                        else:
                            lease_ranges["Less than 50 years"] += 1
                        
                        valid_records += 1
                        total_lease_remaining += lease_remaining
                        lease_data.append(lease_remaining)
                
                except (ValueError, TypeError):
                    continue
            
            # Calculate statistics
            if valid_records > 0:
                avg_lease_remaining = total_lease_remaining / valid_records
                lease_data.sort()
                median_lease = lease_data[valid_records // 2] if valid_records > 0 else 0
                min_lease = min(lease_data) if lease_data else 0
                max_lease = max(lease_data) if lease_data else 0
            else:
                avg_lease_remaining = median_lease = min_lease = max_lease = 0
            
            return {
                "search_criteria": {
                    "year": year,
                    "flat_type": flat_type or "All types",
                    "town": town or "All towns"
                },
                "total_records": len(records),
                "valid_lease_records": valid_records,
                "lease_distribution": lease_ranges,
                "statistics": {
                    "average_lease_remaining": round(avg_lease_remaining, 1),
                    "median_lease_remaining": median_lease,
                    "min_lease_remaining": min_lease,
                    "max_lease_remaining": max_lease
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_lease_statistics: {e}")
            return {"error": f"Failed to retrieve data: {str(e)}"}
    
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP messages"""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        try:
            logger.info(f"Received message: {method}")
            
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
                logger.info("Server initialized successfully")
                return None  # No response needed
            
            elif method == "tools/list":
                logger.info("Listing available tools")
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [
                            {
                                "name": "health_check",
                                "description": "Check if the server is healthy and responsive",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": False
                                }
                            },
                            {
                                "name": "get_highest_price",
                                "description": "Get the highest recorded price for a flat (defaults to current year if year not specified)",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "flat_type": {"type": "string", "enum": ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]},
                                        "town": {"type": "string"},
                                        "year": {"type": "string", "description": f"Year (YYYY format) - defaults to {DEFAULT_YEAR} if not specified"}
                                    },
                                    "additionalProperties": False
                                }
                            },
                            {
                                "name": "get_lowest_price",
                                "description": "Get the lowest recorded price for a flat (defaults to current year if year not specified)",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "flat_type": {"type": "string", "enum": ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]},
                                        "town": {"type": "string"},
                                        "year": {"type": "string", "description": f"Year (YYYY format) - defaults to {DEFAULT_YEAR} if not specified"}
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
                            },
                            {
                                "name": "get_flats_by_lease_remaining",
                                "description": "Find flats with specified minimum lease remaining years (e.g., 90+ years)",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "min_lease_years": {"type": "integer", "default": 90, "minimum": 1, "maximum": 99, "description": "Minimum lease remaining years"},
                                        "year": {"type": "string", "description": f"Year (YYYY format) - defaults to {DEFAULT_YEAR} if not specified"},
                                        "flat_type": {"type": "string", "enum": ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]},
                                        "town": {"type": "string"},
                                        "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 200}
                                    },
                                    "additionalProperties": False
                                }
                            },
                            {
                                "name": "get_lease_statistics",
                                "description": "Get statistics about lease remaining across different ranges",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "year": {"type": "string", "description": f"Year (YYYY format) - defaults to {DEFAULT_YEAR} if not specified"},
                                        "flat_type": {"type": "string", "enum": ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]},
                                        "town": {"type": "string"}
                                    },
                                    "additionalProperties": False
                                }
                            }
                        ]
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")
                
                try:
                    if tool_name == "health_check":
                        result = await self.health_check()
                    elif tool_name == "get_highest_price":
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
                    elif tool_name == "get_flats_by_lease_remaining":
                        # Extra safety for the problematic function
                        try:
                            logger.info("Starting lease remaining search with extra safety...")
                            result = await asyncio.wait_for(
                                self.get_flats_by_lease_remaining(**arguments), 
                                timeout=60.0  # 60 second timeout
                            )
                        except asyncio.TimeoutError:
                            logger.error("Lease search timed out after 60 seconds")
                            result = {"error": "Search timed out. Please try with more specific filters (town/flat_type) or a more recent year."}
                        except Exception as e:
                            logger.error(f"Lease search failed with error: {e}")
                            result = {"error": f"Lease search failed: {str(e)}"}
                    elif tool_name == "get_lease_statistics":
                        result = await self.get_lease_statistics(**arguments)
                    else:
                        raise ValueError(f"Unknown tool: {tool_name}")
                    
                    logger.info(f"Tool {tool_name} completed successfully")
                    
                except Exception as tool_error:
                    logger.error(f"Tool {tool_name} failed: {tool_error}")
                    result = {"error": f"Tool execution failed: {str(tool_error)}"}
                
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
        """Run the MCP server with automatic restart capability"""
        logger.info("Starting HDB Resale MCP Server...")
        restart_count = 0
        max_restarts = 5
        
        while restart_count < max_restarts:
            try:
                await self._run_server_loop()
                # If we get here, server exited normally
                break
                
            except Exception as e:
                restart_count += 1
                logger.error(f"Server crashed (attempt {restart_count}/{max_restarts}): {e}")
                
                if restart_count < max_restarts:
                    logger.info(f"Restarting server in 2 seconds... (attempt {restart_count + 1})")
                    
                    # Clean up resources before restart
                    try:
                        if self.session and not self.session.closed:
                            await self.session.close()
                        self.session = None
                        # Clear cache on restart to free memory
                        self.cache.clear()
                    except Exception as cleanup_error:
                        logger.warning(f"Error during cleanup: {cleanup_error}")
                    
                    await asyncio.sleep(2)  # Wait 2 seconds before restart
                else:
                    logger.error("Max restart attempts reached. Server shutting down.")
                    break
        
        logger.info("Server shutdown complete")
    
    async def _run_server_loop(self):
        """Main server loop - separated for restart capability"""
        try:
            while True:
                try:
                    # Read from stdin with timeout to prevent hanging
                    line = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline),
                        timeout=None  # No timeout for stdin reads
                    )
                    
                    if not line:
                        logger.info("EOF received, shutting down...")
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse JSON-RPC message
                    try:
                        message = json.loads(line)
                        logger.debug(f"Parsed message: {message}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON: {line} - Error: {e}")
                        continue
                    
                    # Skip if no method (likely malformed)
                    if "method" not in message:
                        logger.error(f"No method in message: {message}")
                        continue
                    
                    # Handle message with timeout to prevent hanging
                    try:
                        response = await asyncio.wait_for(
                            self.handle_message(message), 
                            timeout=120.0  # 2 minute timeout for any message
                        )
                    except asyncio.TimeoutError:
                        logger.error("Message handling timed out")
                        # Send error response for timed out requests
                        if message.get("id") is not None:
                            error_response = {
                                "jsonrpc": "2.0",
                                "id": message["id"],
                                "error": {
                                    "code": -32603,
                                    "message": "Request timed out"
                                }
                            }
                            print(json.dumps(error_response, ensure_ascii=False))
                            sys.stdout.flush()
                        continue
                    
                    # Send response if needed
                    if response:
                        response_json = json.dumps(response, ensure_ascii=False)
                        print(response_json)
                        sys.stdout.flush()
                        logger.debug(f"Sent response: {response_json}")
                
                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt...")
                    raise  # Re-raise to exit cleanly
                except Exception as e:
                    logger.error(f"Error in message processing: {str(e)}")
                    continue  # Continue processing other messages
        
        finally:
            logger.info("Cleaning up server resources...")
            if self.session and not self.session.closed:
                await self.session.close()

async def main():
    """Main entry point"""
    server = HDBResaleServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())