import http.client
import json
from urllib.parse import urlencode
from typing import Optional, Dict, List

# Get carpark availability data from Singapore's data.gov.sg API
def get_carpark_availability(carpark_number: Optional[str] = None, 
                           date_time: Optional[str] = None,
                           api_key: Optional[str] = None) -> Dict:
    conn = http.client.HTTPSConnection("api.data.gov.sg")
    
    # Build query parameters
    params = {}
    if date_time:
        params['date_time'] = date_time
    
    # Build URL with parameters
    url = "/v1/transport/carpark-availability"
    if params:
        url += "?" + urlencode(params)
    
    # Set headers
    headers = {}
    if api_key:
        headers['X-API-KEY'] = api_key
    
    try:
        # Make the request
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
        
        if res.status == 200:
            data = res.read()
            json_data = json.loads(data.decode("utf-8"))
            
            # If specific carpark requested, filter the results
            if carpark_number:
                return filter_carpark_data(json_data, carpark_number.upper())
            else:
                return json_data
        else:
            print(f"Error: HTTP {res.status} - {res.reason}")
            return {}
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}
    finally:
        conn.close()

# Filter the API response to return only the specified carpark data
def filter_carpark_data(json_data: Dict, carpark_number: str) -> Dict:
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
    
    return {'error': f'Carpark {carpark_number} not found'}

# Print a formatted summary of carpark availability
def print_carpark_summary(carpark_data: Dict):
    if 'error' in carpark_data:
        print(f"❌ {carpark_data['error']}")
        return
    
    if not carpark_data:
        print("❌ No carpark data available")
        return
    
    print(f"\n🅿️  Carpark: {carpark_data.get('carpark_number', 'Unknown')}")
    print(f"⏰ Last Updated: {carpark_data.get('update_datetime', 'N/A')}")
    print("=" * 50)
    
    # Lot type mapping for better display
    lot_type_names = {
        'C': '🚗 Car',
        'Y': '🏍️  Motorcycle', 
        'H': '🚛 Heavy Vehicle',
        'M': '🚗 Motorcycle (Alt)'
    }
    
    total_available = 0
    total_capacity = 0
    
    for info in carpark_data.get('carpark_info', []):
        lot_type = info.get('lot_type', 'Unknown')
        total_lots = int(info.get('total_lots', 0))
        lots_available = int(info.get('lots_available', 0))
        
        total_available += lots_available
        total_capacity += total_lots
        
        # Calculate percentage
        if total_lots > 0:
            percentage = (lots_available / total_lots) * 100
            if percentage > 50:
                status = "🟢"
            elif percentage > 20:
                status = "🟡"
            elif percentage > 0:
                status = "🔴"
            else:
                status = "❌"
        else:
            percentage = 0
            status = "❓"
        
        lot_name = lot_type_names.get(lot_type, f'🅿️  {lot_type}')
        print(f"{status} {lot_name}: {lots_available}/{total_lots} ({percentage:.1f}% available)")
    
    if total_capacity > 0:
        overall_percentage = (total_available / total_capacity) * 100
        overall_status = "🟢" if overall_percentage > 50 else "🟡" if overall_percentage > 20 else "🔴"
        print(f"\n{overall_status} Overall: {total_available}/{total_capacity} ({overall_percentage:.1f}% available)")

# Get availability data for multiple carparks
def get_multiple_carparks(carpark_numbers: List[str], 
                         date_time: Optional[str] = None,
                         api_key: Optional[str] = None) -> List[Dict]:
    # Get all data once
    all_data = get_carpark_availability(date_time=date_time, api_key=api_key)
    results = []
    
    if not all_data or 'items' not in all_data:
        return results
    
    # Convert to uppercase for comparison
    target_numbers = [num.upper() for num in carpark_numbers]
    
    for item in all_data['items']:
        if 'carpark_data' in item:
            for carpark in item['carpark_data']:
                if carpark.get('carpark_number') in target_numbers:
                    results.append({
                        'timestamp': item.get('timestamp'),
                        'carpark_number': carpark.get('carpark_number'),
                        'carpark_info': carpark.get('carpark_info', []),
                        'update_datetime': carpark.get('update_datetime')
                    })
    
    return results

# Example usage functions
def main():
    print("🚗 Singapore Carpark Availability Checker")
    print("=" * 50)
    
    # Example 1: Get all carpark data (your original code enhanced)
    print("\n1️⃣ Getting all carpark data...")
    all_data = get_carpark_availability()
    if all_data:
        total_carparks = sum(len(item.get('carpark_data', [])) for item in all_data.get('items', []))
        print(f"✅ Retrieved data for {total_carparks} carparks")
        print(f"📅 Timestamp: {all_data.get('items', [{}])[0].get('timestamp', 'N/A')}")
    
    # Example 2: Get specific carpark
    print("\n2️⃣ Getting specific carpark data...")
    carpark_number = "AM22"  # Using TB6 from your example data
    carpark_data = get_carpark_availability(carpark_number=carpark_number)
    print_carpark_summary(carpark_data)
    
    # Example 3: Get multiple carparks
    print("\n3️⃣ Getting multiple carparks...")
    carpark_numbers = ["TB6", "TB7", "ACB"]  # Using TB6, TB7 from your example
    multiple_data = get_multiple_carparks(carpark_numbers)
    
    for data in multiple_data:
        print_carpark_summary(data)
    
    # Example 4: Raw JSON output (similar to your original code)
    print("\n4️⃣ Raw JSON for specific carpark...")
    raw_data = get_carpark_availability(carpark_number="TB6")
    if raw_data:
        print(json.dumps(raw_data, indent=2))

# Simple function to quickly check a carpark (most common use case)
def check_carpark(carpark_number: str, api_key: Optional[str] = None):
    print(f"🔍 Checking carpark {carpark_number.upper()}...")
    data = get_carpark_availability(carpark_number=carpark_number, api_key=api_key)
    print_carpark_summary(data)
    return data

if __name__ == "__main__":
    main()