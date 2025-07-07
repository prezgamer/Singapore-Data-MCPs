import requests
import json

def fetch_and_display_carpark_data():
    dataset_id = "d_23f946fa557947f93a8043bbef41dd09"
    url = f"https://data.gov.sg/api/action/datastore_search?resource_id={dataset_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        data = response.json()
        
        if data['success']:
            records = data['result']['records']
            total_records = len(records)
            
            print(f"=== Singapore Car Park Information ===")
            print(f"Total car parks found: {total_records}")
            print("=" * 50)
            
            for i, record in enumerate(records, 1):
                print(f"\n[{i}] Car Park: {record['car_park_no']}")
                print(f"    Address: {record['address']}")
                print(f"    Type: {record['car_park_type']}")
                print(f"    Parking System: {record['type_of_parking_system']}")
                print(f"    Short Term Parking: {record['short_term_parking']}")
                print(f"    Free Parking: {record['free_parking']}")
                print(f"    Night Parking: {record['night_parking']}")
                print(f"    Number of Decks: {record['car_park_decks']}")
                print(f"    Gantry Height: {record['gantry_height']}m")
                print(f"    Basement: {'Yes' if record['car_park_basement'] == 'Y' else 'No'}")
                print(f"    Coordinates: ({record['x_coord']}, {record['y_coord']})")
                print("-" * 50)
        else:
            print("Error: API request was not successful")
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
    except KeyError as e:
        print(f"Error: Missing expected key in response: {e}")

def fetch_all_records():
    """Fetch all records with pagination"""
    dataset_id = "d_23f946fa557947f93a8043bbef41dd09"
    base_url = f"https://data.gov.sg/api/action/datastore_search?resource_id={dataset_id}"
    
    all_records = []
    offset = 0
    limit = 100  # Default API limit
    
    while True:
        url = f"{base_url}&offset={offset}&limit={limit}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data['success']:
                records = data['result']['records']
                if not records:  # No more records
                    break
                    
                all_records.extend(records)
                offset += limit
                
                print(f"Fetched {len(records)} records (Total: {len(all_records)})")
            else:
                print("Error: API request was not successful")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            break
    
    return all_records

if __name__ == "__main__":
    # Display first batch of records in readable format
    fetch_and_display_carpark_data()
    
    print("\n" + "=" * 70)
    