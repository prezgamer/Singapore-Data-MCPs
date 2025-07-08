#!/usr/bin/env python3
"""
HDB Resale Data Analyzer

This script provides comprehensive analysis and sorting of Singapore HDB resale flat data.
It can sort by price, calculate averages, and filter by various criteria.
"""

import requests
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics

class HDBDataAnalyzer:
    def __init__(self):
        self.base_url = "https://data.gov.sg/api/action/datastore_search"
        self.dataset_id = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
        self.data = []
    
    def fetch_all_data(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fetch all data from the API with optional filters"""
        all_records = []
        offset = 0
        limit = 100
        
        print("Fetching data from API...")
        while True:
            params = {
                "resource_id": self.dataset_id,
                "limit": limit,
                "offset": offset
            }
            
            if filters:
                params["filters"] = json.dumps(filters)
            
            try:
                response = requests.get(self.base_url, params=params)
                data = response.json()
                
                if not data.get("success", False):
                    print(f"API error: {data}")
                    break
                
                records = data["result"]["records"]
                if not records:
                    break
                
                all_records.extend(records)
                print(f"Fetched {len(all_records)} records...")
                
                # Check if we have more data
                if len(records) < limit:
                    break
                
                offset += limit
                
            except Exception as e:
                print(f"Error fetching data: {str(e)}")
                break
        
        # Convert resale_price and floor_area_sqm to appropriate numeric types
        for record in all_records:
            # Convert price to float first (in case of decimals), then round to int
            record['resale_price'] = int(float(record['resale_price']))
            # Convert floor area to float first (in case of decimals), then round to int
            record['floor_area_sqm'] = int(float(record['floor_area_sqm']))
        
        self.data = all_records
        print(f"Total records fetched: {len(all_records)}")
        return all_records
    
    def filter_data(self, 
                   flat_type: str = None, 
                   town: str = None, 
                   year: str = None,
                   min_price: int = None,
                   max_price: int = None,
                   min_area: int = None,
                   max_area: int = None) -> List[Dict[str, Any]]:
        """Filter data based on various criteria"""
        filtered_data = self.data.copy()
        
        if flat_type:
            filtered_data = [r for r in filtered_data if r['flat_type'] == flat_type]
        
        if town:
            filtered_data = [r for r in filtered_data if r['town'] == town]
        
        if year:
            filtered_data = [r for r in filtered_data if r['month'].startswith(year)]
        
        if min_price:
            filtered_data = [r for r in filtered_data if r['resale_price'] >= min_price]
        
        if max_price:
            filtered_data = [r for r in filtered_data if r['resale_price'] <= max_price]
        
        if min_area:
            filtered_data = [r for r in filtered_data if r['floor_area_sqm'] >= min_area]
        
        if max_area:
            filtered_data = [r for r in filtered_data if r['floor_area_sqm'] <= max_area]
        
        return filtered_data
    
    def sort_by_price(self, data: List[Dict[str, Any]], ascending: bool = True) -> List[Dict[str, Any]]:
        """Sort data by resale price"""
        return sorted(data, key=lambda x: x['resale_price'], reverse=not ascending)
    
    def sort_by_price_per_sqm(self, data: List[Dict[str, Any]], ascending: bool = True) -> List[Dict[str, Any]]:
        """Sort data by price per square meter"""
        for record in data:
            record['price_per_sqm'] = record['resale_price'] / record['floor_area_sqm']
        
        return sorted(data, key=lambda x: x['price_per_sqm'], reverse=not ascending)
    
    def get_highest_priced_flats(self, data: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get the highest priced flats"""
        sorted_data = self.sort_by_price(data, ascending=False)
        return sorted_data[:limit]
    
    def get_lowest_priced_flats(self, data: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get the lowest priced flats"""
        sorted_data = self.sort_by_price(data, ascending=True)
        return sorted_data[:limit]
    
    def calculate_average_prices_by_town(self, data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate average prices grouped by town"""
        town_data = defaultdict(list)
        
        for record in data:
            town = record['town']
            town_data[town].append(record['resale_price'])
        
        result = {}
        for town, prices in town_data.items():
            result[town] = {
                'average_price': round(statistics.mean(prices), 2),
                'median_price': round(statistics.median(prices), 2),
                'min_price': min(prices),
                'max_price': max(prices),
                'transaction_count': len(prices),
                'total_value': sum(prices)
            }
        
        return result
    
    def calculate_average_prices_by_flat_type(self, data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate average prices grouped by flat type"""
        flat_type_data = defaultdict(list)
        
        for record in data:
            flat_type = record['flat_type']
            flat_type_data[flat_type].append(record['resale_price'])
        
        result = {}
        for flat_type, prices in flat_type_data.items():
            result[flat_type] = {
                'average_price': round(statistics.mean(prices), 2),
                'median_price': round(statistics.median(prices), 2),
                'min_price': min(prices),
                'max_price': max(prices),
                'transaction_count': len(prices)
            }
        
        return result
    
    def get_highest_avg_price_towns(self, data: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get towns with highest average prices"""
        town_averages = self.calculate_average_prices_by_town(data)
        
        sorted_towns = sorted(
            town_averages.items(), 
            key=lambda x: x[1]['average_price'], 
            reverse=True
        )
        
        result = []
        for town, stats in sorted_towns[:limit]:
            result.append({
                'town': town,
                **stats
            })
        
        return result
    
    def get_lowest_avg_price_towns(self, data: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get towns with lowest average prices"""
        town_averages = self.calculate_average_prices_by_town(data)
        
        sorted_towns = sorted(
            town_averages.items(), 
            key=lambda x: x[1]['average_price']
        )
        
        result = []
        for town, stats in sorted_towns[:limit]:
            result.append({
                'town': town,
                **stats
            })
        
        return result
    
    def get_transaction_volume_by_town(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get transaction volume by town, sorted by count"""
        town_counts = defaultdict(int)
        
        for record in data:
            town = record['town']
            town_counts[town] += 1
        
        sorted_towns = sorted(town_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{'town': town, 'transaction_count': count} for town, count in sorted_towns]
    
    def price_analysis_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get comprehensive price analysis summary"""
        if not data:
            return {"error": "No data available"}
        
        prices = [record['resale_price'] for record in data]
        
        return {
            'total_transactions': len(data),
            'average_price': round(statistics.mean(prices), 2),
            'median_price': round(statistics.median(prices), 2),
            'min_price': min(prices),
            'max_price': max(prices),
            'price_std_dev': round(statistics.stdev(prices) if len(prices) > 1 else 0, 2),
            'price_range': max(prices) - min(prices)
        }
    
    def print_analysis_results(self, data: List[Dict[str, Any]], title: str = "Analysis Results"):
        """Print formatted analysis results"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        
        # Summary statistics
        summary = self.price_analysis_summary(data)
        print(f"\nSUMMARY STATISTICS:")
        print(f"Total Transactions: {summary['total_transactions']:,}")
        print(f"Average Price: ${summary['average_price']:,.2f}")
        print(f"Median Price: ${summary['median_price']:,.2f}")
        print(f"Price Range: ${summary['min_price']:,} - ${summary['max_price']:,}")
        print(f"Standard Deviation: ${summary['price_std_dev']:,.2f}")
        
        # Top 5 highest prices
        print(f"\nTOP 5 HIGHEST PRICED FLATS:")
        highest = self.get_highest_priced_flats(data, 5)
        for i, flat in enumerate(highest, 1):
            print(f"{i}. ${flat['resale_price']:,} - {flat['flat_type']} in {flat['town']} "
                  f"({flat['floor_area_sqm']}sqm, {flat['month']})")
        
        # Top 5 lowest prices
        print(f"\nTOP 5 LOWEST PRICED FLATS:")
        lowest = self.get_lowest_priced_flats(data, 5)
        for i, flat in enumerate(lowest, 1):
            print(f"{i}. ${flat['resale_price']:,} - {flat['flat_type']} in {flat['town']} "
                  f"({flat['floor_area_sqm']}sqm, {flat['month']})")
        
        # Top 5 towns by average price
        print(f"\nTOP 5 TOWNS BY AVERAGE PRICE:")
        top_towns = self.get_highest_avg_price_towns(data, 5)
        for i, town_data in enumerate(top_towns, 1):
            print(f"{i}. {town_data['town']}: ${town_data['average_price']:,.2f} "
                  f"({town_data['transaction_count']} transactions)")
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str):
        """Save data to CSV file"""
        if not data:
            print("No data to save")
            return
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

# Example usage and demonstration
def main():
    analyzer = HDBDataAnalyzer()
    
    # Fetch all data
    print("Fetching HDB resale data...")
    all_data = analyzer.fetch_all_data()
    
    if not all_data:
        print("No data fetched. Exiting.")
        return
    
    # Overall analysis
    analyzer.print_analysis_results(all_data, "OVERALL HDB RESALE DATA ANALYSIS")
    
    # Analysis by year
    print("\n" + "="*60)
    print("YEAR-BY-YEAR ANALYSIS")
    print("="*60)
    
    years = ['2017', '2018', '2019', '2020']  # Add more years as needed
    for year in years:
        year_data = analyzer.filter_data(year=year)
        if year_data:
            print(f"\n--- {year} ---")
            summary = analyzer.price_analysis_summary(year_data)
            print(f"Transactions: {summary['total_transactions']:,}")
            print(f"Average Price: ${summary['average_price']:,.2f}")
            print(f"Median Price: ${summary['median_price']:,.2f}")
    
    # Analysis by flat type
    print("\n" + "="*60)
    print("FLAT TYPE ANALYSIS")
    print("="*60)
    
    flat_types = ['2 ROOM', '3 ROOM', '4 ROOM', '5 ROOM', 'EXECUTIVE']
    for flat_type in flat_types:
        flat_data = analyzer.filter_data(flat_type=flat_type)
        if flat_data:
            print(f"\n--- {flat_type} ---")
            summary = analyzer.price_analysis_summary(flat_data)
            print(f"Transactions: {summary['total_transactions']:,}")
            print(f"Average Price: ${summary['average_price']:,.2f}")
            print(f"Price Range: ${summary['min_price']:,} - ${summary['max_price']:,}")
    
    # Custom analysis example
    print("\n" + "="*60)
    print("CUSTOM ANALYSIS: 4-ROOM FLATS IN 2017")
    print("="*60)
    
    custom_data = analyzer.filter_data(flat_type='4 ROOM', year='2017')
    if custom_data:
        analyzer.print_analysis_results(custom_data, "4-ROOM FLATS IN 2017")
        
        # Save to CSV
        analyzer.save_to_csv(custom_data, '4room_flats_2017.csv')
    
    # Town comparison
    print("\n" + "="*60)
    print("TOWN COMPARISON (TOP 10 BY AVERAGE PRICE)")
    print("="*60)
    
    top_towns = analyzer.get_highest_avg_price_towns(all_data, 10)
    for i, town_data in enumerate(top_towns, 1):
        print(f"{i:2d}. {town_data['town']:15} | "
              f"Avg: ${town_data['average_price']:>8,.0f} | "
              f"Transactions: {town_data['transaction_count']:>4}")

if __name__ == "__main__":
    main()