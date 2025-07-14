import http.client
import json
import requests
from urllib.parse import urlencode
from typing import Optional, Dict, List

# Comprehensive Singapore CarPark System combining static information and real-time availability
class SingaporeCarParkSystem:

    # Initialize the CarPark System
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.dataset_id = "d_23f946fa557947f93a8043bbef41dd09"
        self.carpark_info_cache = {}
    
    # ========== CARPARK INFORMATION METHODS ==========
    
    # Fetch static carpark information (address, type, pricing, etc.)
    def fetch_carpark_info(self, carpark_number: Optional[str] = None) -> Dict:
        url = f"https://data.gov.sg/api/action/datastore_search?resource_id={self.dataset_id}"
        
        try:
            response = requests.get(url)
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
            return {'error': f'Error fetching data: {e}'}
        except json.JSONDecodeError as e:
            return {'error': f'Error parsing JSON response: {e}'}
    
    # Fetch all carpark information records with pagination
    def fetch_all_carpark_info(self) -> List[Dict]:
        base_url = f"https://data.gov.sg/api/action/datastore_search?resource_id={self.dataset_id}"
        all_records = []
        offset = 0
        limit = 100
        
        while True:
            url = f"{base_url}&offset={offset}&limit={limit}"
            
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data['success']:
                    records = data['result']['records']
                    if not records:
                        break
                        
                    all_records.extend(records)
                    offset += limit
                    print(f"Fetched {len(records)} records (Total: {len(all_records)})")
                else:
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data: {e}")
                break
        
        # Cache the results
        for record in all_records:
            self.carpark_info_cache[record['car_park_no']] = record
            
        return all_records
    
    # ========== CARPARK AVAILABILITY METHODS ==========
    
    # Get real-time carpark availability data
    def get_carpark_availability(self, carpark_number: Optional[str] = None, 
                               date_time: Optional[str] = None, timeout: int = 10) -> Dict:
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
                return {'error': f'HTTP {res.status} - {res.reason}'}
                
        except Exception as e:
            return {'error': f'Error fetching availability data: {e}'}
        finally:
            conn.close()
    
    def _filter_carpark_availability(self, json_data: Dict, carpark_number: str) -> Dict:
        """Filter availability data for specific carpark"""
        if not json_data or 'items' not in json_data:
            return {}
        
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
    
    # Get both static information and real-time availability for a carpark
    def get_complete_carpark_info(self, carpark_number: str) -> Dict:
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
    # Search carparks by area/address keyword
    def search_carparks_by_area(self, area_keyword: str, include_availability: bool = False, max_results: int = 10) -> List[Dict]:
        if not self.carpark_info_cache:
            print("Loading carpark database...")
            self.fetch_all_carpark_info()
        
        area_keyword = area_keyword.upper()
        matching_carparks = []
        
        print(f"🔍 Searching for carparks containing '{area_keyword}'...")
        
        for carpark_no, info in self.carpark_info_cache.items():
            if area_keyword in info['address'].upper():
                carpark_data = {'carpark_number': carpark_no, 'static_info': info}
                
                if include_availability:
                    print(f"  Getting availability for {carpark_no}...")
                    try:
                        availability = self.get_carpark_availability(carpark_no, timeout=5)
                        carpark_data['availability_info'] = availability
                    except Exception as e:
                        print(f"    ⚠️  Could not get availability for {carpark_no}: {e}")
                        carpark_data['availability_info'] = {'error': f'Timeout or error: {e}'}
                
                matching_carparks.append(carpark_data)
                
                # Limit results to prevent hanging
                if len(matching_carparks) >= max_results:
                    print(f"  Limiting to first {max_results} results...")
                    break
        
        return matching_carparks
    
    # ========== DISPLAY METHODS ==========
    
    # Print formatted static carpark information
    def print_carpark_static_info(self, carpark_data: Dict):
        if 'error' in carpark_data:
            print(f"❌ {carpark_data['error']}")
            return
        
        print(f"\n🏢 Car Park: {carpark_data['car_park_no']}")
        print(f"📍 Address: {carpark_data['address']}")
        print(f"🏗️ Type: {carpark_data['car_park_type']}")
        print(f"💳 Parking System: {carpark_data['type_of_parking_system']}")
        print(f"⏱️ Short Term Parking: {carpark_data['short_term_parking']}")
        print(f"🆓 Free Parking: {carpark_data['free_parking']}")
        print(f"🌙 Night Parking: {carpark_data['night_parking']}")
        print(f"🏢 Number of Decks: {carpark_data['car_park_decks']}")
        print(f"📏 Gantry Height: {carpark_data['gantry_height']}m")
        print(f"🏠 Basement: {'Yes' if carpark_data['car_park_basement'] == 'Y' else 'No'}")
        print(f"📍 Coordinates: ({carpark_data['x_coord']}, {carpark_data['y_coord']})")
    
    # Print formatted availability information
    def print_carpark_availability(self, availability_data: Dict):
        if 'error' in availability_data:
            print(f"❌ {availability_data['error']}")
            return
        
        if not availability_data:
            print("❌ No availability data")
            return
        
        print(f"\n🅿️  Availability for: {availability_data.get('carpark_number', 'Unknown')}")
        print(f"⏰ Last Updated: {availability_data.get('update_datetime', 'N/A')}")
        
        lot_type_names = {
            'C': '🚗 Car',
            'Y': '🏍️  Motorcycle', 
            'H': '🚛 Heavy Vehicle',
            'M': '🏍️  Motorcycle (Alt)'
        }
        
        total_available = 0
        total_capacity = 0
        
        for info in availability_data.get('carpark_info', []):
            lot_type = info.get('lot_type', 'Unknown')
            total_lots = int(info.get('total_lots', 0))
            lots_available = int(info.get('lots_available', 0))
            
            total_available += lots_available
            total_capacity += total_lots
            
            if total_lots > 0:
                percentage = (lots_available / total_lots) * 100
                status = "🟢" if percentage > 50 else "🟡" if percentage > 20 else "🔴" if percentage > 0 else "❌"
            else:
                percentage = 0
                status = "❓"
            
            lot_name = lot_type_names.get(lot_type, f'🅿️  {lot_type}')
            print(f"{status} {lot_name}: {lots_available}/{total_lots} ({percentage:.1f}% available)")
        
        if total_capacity > 0:
            overall_percentage = (total_available / total_capacity) * 100
            overall_status = "🟢" if overall_percentage > 50 else "🟡" if overall_percentage > 20 else "🔴"
            print(f"\n{overall_status} Overall: {total_available}/{total_capacity} ({overall_percentage:.1f}% available)")
    
    # Print both static and availability information
    def print_complete_carpark_info(self, complete_data: Dict):
        print("=" * 60)
        print(f"🚗 COMPLETE CARPARK INFORMATION: {complete_data['carpark_number']}")
        print("=" * 60)
        
        # Static information
        print("\n📋 STATIC INFORMATION:")
        print("-" * 30)
        self.print_carpark_static_info(complete_data['static_info'])
        
        # Availability information
        print("\n📊 REAL-TIME AVAILABILITY:")
        print("-" * 30)
        self.print_carpark_availability(complete_data['availability_info'])
        
        print("=" * 60)

# Quick function to check both info and availability for a carpark
def quick_check(carpark_number: str, api_key: Optional[str] = None):
    system = SingaporeCarParkSystem(api_key)
    complete_data = system.get_complete_carpark_info(carpark_number)
    system.print_complete_carpark_info(complete_data)
    return complete_data

# Search carparks in a specific area
def search_area(area_keyword: str, include_availability: bool = False, max_results: int = 5, api_key: Optional[str] = None):
    system = SingaporeCarParkSystem(api_key)
    results = system.search_carparks_by_area(area_keyword, include_availability, max_results)
    
    print(f"\n🔍 Found {len(results)} carparks in area containing '{area_keyword}':")
    print("=" * 60)
    
    for i, carpark in enumerate(results, 1):
        print(f"\n[{i}] {carpark['carpark_number']} - {carpark['static_info']['address']}")
        if include_availability and 'availability_info' in carpark:
            system.print_carpark_availability(carpark['availability_info'])
        print("-" * 40)
    
    return results

# ========== MAIN DEMO FUNCTION ==========

# Demo function showing all capabilities
def main():
    print("🇸🇬 SINGAPORE CARPARK INFORMATION & AVAILABILITY SYSTEM")
    print("=" * 70)
    
    # Initialize system
    system = SingaporeCarParkSystem()
    
    # Example 1: Quick check of a specific carpark
    print("\n1️⃣ QUICK CHECK - Complete info for carpark ACB:")
    quick_check("ACB")
    
    # Example 2: Search by area (WITHOUT availability to avoid hanging)
    print("\n2️⃣ AREA SEARCH - Carparks in spectific area (static info only):")
    search_results = search_area("mei ling", include_availability=False, max_results=3)
    
    # Example 3: Get availability for one specific carpark
    print("\n3️⃣ AVAILABILITY CHECK - Single carpark:")
    availability = system.get_carpark_availability("ACB")
    system.print_carpark_availability(availability)
    
    # Example 4: Database overview
    print("\n4️⃣ DATABASE OVERVIEW:")
    print(f"✅ Total carparks in cache: {len(system.carpark_info_cache)}")
    
    print("\n💡 TIP: Use quick_check('CARPARK_NO') for individual carpark checks")
    print("💡 TIP: Use search_area('AREA', include_availability=True, max_results=2) for small searches with availability")

if __name__ == "__main__":
    main()