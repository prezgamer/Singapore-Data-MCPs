import requests
import json
import csv
from typing import Dict, List, Any
from collections import defaultdict
import os
from datetime import datetime

class GraduateDataSeparator:
    """Class to fetch and separate graduate employment data by various fields"""
    
    def __init__(self):
        self.dataset_id = "d_3c55210de27fcccda2ed0c63fdd2b352"
        self.base_url = "https://data.gov.sg/api/action/datastore_search"
        self.all_data = []
        
    def fetch_all_data(self) -> List[Dict]:
        """Fetch all data with pagination"""
        all_records = []
        offset = 0
        limit = 100
        
        print("Fetching all graduate employment data...")
        
        while True:
            try:
                url = f"{self.base_url}?resource_id={self.dataset_id}&offset={offset}&limit={limit}"
                response = requests.get(url)
                data = response.json()
                
                if not data.get('success'):
                    break
                
                records = data['result']['records']
                if not records:
                    break
                    
                all_records.extend(records)
                offset += limit
                print(f"Fetched {len(records)} records (Total: {len(all_records)})")
                
                # Check if we've got all records
                if len(records) < limit:
                    break
                    
            except Exception as e:
                print(f"Error fetching data: {e}")
                break
        
        self.all_data = all_records
        print(f"✅ Total records fetched: {len(all_records)}")
        return all_records
    
    def separate_by_year(self) -> Dict[str, List[Dict]]:
        """Separate data by year"""
        year_data = defaultdict(list)
        
        for record in self.all_data:
            year = record.get('year')
            if year:
                year_data[year].append(record)
        
        # Convert to regular dict and sort by year
        sorted_years = dict(sorted(year_data.items()))
        
        print(f"\n📅 DATA BY YEAR:")
        print("=" * 50)
        for year, records in sorted_years.items():
            print(f"Year {year}: {len(records)} records")
        
        return sorted_years
    
    def separate_by_university(self) -> Dict[str, List[Dict]]:
        """Separate data by university"""
        uni_data = defaultdict(list)
        
        for record in self.all_data:
            university = record.get('university')
            if university:
                uni_data[university].append(record)
        
        # Sort by university name
        sorted_unis = dict(sorted(uni_data.items()))
        
        print(f"\n🏫 DATA BY UNIVERSITY:")
        print("=" * 50)
        for uni, records in sorted_unis.items():
            print(f"{uni}: {len(records)} records")
        
        return sorted_unis
    
    def separate_by_school(self) -> Dict[str, List[Dict]]:
        """Separate data by school/faculty"""
        school_data = defaultdict(list)
        
        for record in self.all_data:
            school = record.get('school')
            if school:
                school_data[school].append(record)
        
        # Sort by school name
        sorted_schools = dict(sorted(school_data.items()))
        
        print(f"\n🏛️ DATA BY SCHOOL/FACULTY:")
        print("=" * 50)
        for school, records in sorted_schools.items():
            print(f"{school}: {len(records)} records")
        
        return sorted_schools
    
    def separate_by_degree(self) -> Dict[str, List[Dict]]:
        """Separate data by degree program"""
        degree_data = defaultdict(list)
        
        for record in self.all_data:
            degree = record.get('degree')
            if degree:
                degree_data[degree].append(record)
        
        # Sort by degree name
        sorted_degrees = dict(sorted(degree_data.items()))
        
        print(f"\n🎓 DATA BY DEGREE:")
        print("=" * 50)
        for degree, records in sorted_degrees.items():
            print(f"{degree}: {len(records)} records")
        
        return sorted_degrees
    
    def separate_by_employment_overall(self, ranges: List[tuple] = None) -> Dict[str, List[Dict]]:
        """Separate data by overall employment rate ranges"""
        if ranges is None:
            ranges = [
                (0, 50, "Very Low (0-50%)"),
                (50, 70, "Low (50-70%)"),
                (70, 85, "Moderate (70-85%)"),
                (85, 95, "High (85-95%)"),
                (95, 100, "Very High (95-100%)")
            ]
        
        employment_data = defaultdict(list)
        
        for record in self.all_data:
            emp_rate_str = record.get('employment_rate_overall')
            if emp_rate_str and emp_rate_str != 'na':
                try:
                    emp_rate = float(emp_rate_str)
                    for min_rate, max_rate, label in ranges:
                        if min_rate <= emp_rate < max_rate:
                            employment_data[label].append(record)
                            break
                except ValueError:
                    employment_data["Invalid Data"].append(record)
        
        print(f"\n📊 DATA BY OVERALL EMPLOYMENT RATE:")
        print("=" * 50)
        for category, records in employment_data.items():
            print(f"{category}: {len(records)} records")
        
        return dict(employment_data)
    
    def separate_by_employment_ft_perm(self, ranges: List[tuple] = None) -> Dict[str, List[Dict]]:
        """Separate data by full-time permanent employment rate ranges"""
        if ranges is None:
            ranges = [
                (0, 50, "Very Low (0-50%)"),
                (50, 70, "Low (50-70%)"),
                (70, 85, "Moderate (70-85%)"),
                (85, 95, "High (85-95%)"),
                (95, 100, "Very High (95-100%)")
            ]
        
        employment_data = defaultdict(list)
        
        for record in self.all_data:
            emp_rate_str = record.get('employment_rate_ft_perm')
            if emp_rate_str and emp_rate_str != 'na':
                try:
                    emp_rate = float(emp_rate_str)
                    for min_rate, max_rate, label in ranges:
                        if min_rate <= emp_rate < max_rate:
                            employment_data[label].append(record)
                            break
                except ValueError:
                    employment_data["Invalid Data"].append(record)
        
        print(f"\n💼 DATA BY FULL-TIME PERMANENT EMPLOYMENT RATE:")
        print("=" * 50)
        for category, records in employment_data.items():
            print(f"{category}: {len(records)} records")
        
        return dict(employment_data)
    
    def separate_by_salary_range(self, salary_field: str, ranges: List[tuple] = None) -> Dict[str, List[Dict]]:
        """Separate data by salary ranges for any salary field"""
        if ranges is None:
            ranges = [
                (0, 2500, "Low ($0-$2,500)"),
                (2500, 3500, "Moderate ($2,500-$3,500)"),
                (3500, 4500, "High ($3,500-$4,500)"),
                (4500, 6000, "Very High ($4,500-$6,000)"),
                (6000, float('inf'), "Exceptional ($6,000+)")
            ]
        
        salary_data = defaultdict(list)
        
        for record in self.all_data:
            salary_str = record.get(salary_field)
            if salary_str and salary_str != 'na':
                try:
                    salary = float(salary_str)
                    for min_sal, max_sal, label in ranges:
                        if min_sal <= salary < max_sal:
                            salary_data[label].append(record)
                            break
                except ValueError:
                    salary_data["Invalid Data"].append(record)
        
        field_name = salary_field.replace('_', ' ').title()
        print(f"\n💰 DATA BY {field_name.upper()}:")
        print("=" * 50)
        for category, records in salary_data.items():
            print(f"{category}: {len(records)} records")
        
        return dict(salary_data)
    
    def create_summary_statistics(self) -> Dict[str, Any]:
        """Create summary statistics for all numeric fields"""
        numeric_fields = [
            'employment_rate_overall', 'employment_rate_ft_perm',
            'basic_monthly_mean', 'basic_monthly_median',
            'gross_monthly_mean', 'gross_monthly_median',
            'gross_mthly_25_percentile', 'gross_mthly_75_percentile'
        ]
        
        summary = {}
        
        for field in numeric_fields:
            values = []
            for record in self.all_data:
                value_str = record.get(field)
                if value_str and value_str != 'na':
                    try:
                        values.append(float(value_str))
                    except ValueError:
                        continue
            
            if values:
                summary[field] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'mean': sum(values) / len(values),
                    'median': sorted(values)[len(values)//2]
                }
        
        print(f"\n📈 SUMMARY STATISTICS:")
        print("=" * 50)
        for field, stats in summary.items():
            field_name = field.replace('_', ' ').title()
            print(f"\n{field_name}:")
            print(f"  Count: {stats['count']}")
            print(f"  Min: {stats['min']:.2f}")
            print(f"  Max: {stats['max']:.2f}")
            print(f"  Mean: {stats['mean']:.2f}")
            print(f"  Median: {stats['median']:.2f}")
        
        return summary
    
    def export_to_csv(self, filename: str = None) -> str:
        """Export all data to a single CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"singapore_graduate_employment_data_{timestamp}.csv"
        
        # Define the field order for CSV
        fieldnames = [
            'year', 'university', 'school', 'degree',
            'employment_rate_overall', 'employment_rate_ft_perm',
            'basic_monthly_mean', 'basic_monthly_median',
            'gross_monthly_mean', 'gross_monthly_median',
            'gross_mthly_25_percentile', 'gross_mthly_75_percentile'
        ]
        
        print(f"\n📄 Exporting data to CSV: {filename}")
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write data rows
                records_written = 0
                for record in self.all_data:
                    # Create a clean row with only the fields we want
                    clean_record = {}
                    for field in fieldnames:
                        clean_record[field] = record.get(field, '')
                    
                    writer.writerow(clean_record)
                    records_written += 1
                
                print(f"✅ Successfully exported {records_written} records to {filename}")
                print(f"📊 File size: {os.path.getsize(filename) / 1024:.1f} KB")
                
        except Exception as e:
            print(f"❌ Error exporting to CSV: {e}")
            return None
        
        return filename
    
    def create_summary_csv(self, filename: str = None) -> str:
        """Create a summary CSV with statistics for each field"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"graduate_data_summary_{timestamp}.csv"
        
        numeric_fields = [
            'employment_rate_overall', 'employment_rate_ft_perm',
            'basic_monthly_mean', 'basic_monthly_median',
            'gross_monthly_mean', 'gross_monthly_median',
            'gross_mthly_25_percentile', 'gross_mthly_75_percentile'
        ]
        
        summary_data = []
        
        for field in numeric_fields:
            values = []
            for record in self.all_data:
                value_str = record.get(field)
                if value_str and value_str != 'na':
                    try:
                        values.append(float(value_str))
                    except ValueError:
                        continue
            
            if values:
                values.sort()
                count = len(values)
                summary_data.append({
                    'field': field,
                    'field_name': field.replace('_', ' ').title(),
                    'count': count,
                    'min': min(values),
                    'max': max(values),
                    'mean': sum(values) / count,
                    'median': values[count//2],
                    'q1': values[count//4],
                    'q3': values[(3*count)//4]
                })
        
        print(f"\n📊 Creating summary CSV: {filename}")
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['field', 'field_name', 'count', 'min', 'max', 'mean', 'median', 'q1', 'q3']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in summary_data:
                    writer.writerow(row)
                
                print(f"✅ Successfully created summary CSV with {len(summary_data)} field statistics")
                
        except Exception as e:
            print(f"❌ Error creating summary CSV: {e}")
            return None
        
        return filename
    
    def create_year_breakdown_csv(self, filename: str = None) -> str:
        """Create a CSV showing data breakdown by year"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"graduate_data_by_year_{timestamp}.csv"
        
        year_stats = defaultdict(lambda: {
            'total_records': 0,
            'universities': set(),
            'degrees': set(),
            'avg_employment_overall': [],
            'avg_gross_median': []
        })
        
        # Collect year statistics
        for record in self.all_data:
            year = record.get('year')
            if year:
                year_stats[year]['total_records'] += 1
                year_stats[year]['universities'].add(record.get('university', ''))
                year_stats[year]['degrees'].add(record.get('degree', ''))
                
                # Collect numeric data
                emp_rate = record.get('employment_rate_overall')
                if emp_rate and emp_rate != 'na':
                    try:
                        year_stats[year]['avg_employment_overall'].append(float(emp_rate))
                    except ValueError:
                        pass
                
                gross_median = record.get('gross_monthly_median')
                if gross_median and gross_median != 'na':
                    try:
                        year_stats[year]['avg_gross_median'].append(float(gross_median))
                    except ValueError:
                        pass
        
        # Prepare data for CSV
        year_breakdown = []
        for year in sorted(year_stats.keys()):
            stats = year_stats[year]
            
            avg_employment = sum(stats['avg_employment_overall']) / len(stats['avg_employment_overall']) if stats['avg_employment_overall'] else 0
            avg_salary = sum(stats['avg_gross_median']) / len(stats['avg_gross_median']) if stats['avg_gross_median'] else 0
            
            year_breakdown.append({
                'year': year,
                'total_records': stats['total_records'],
                'unique_universities': len(stats['universities']),
                'unique_degrees': len(stats['degrees']),
                'avg_employment_rate': round(avg_employment, 2),
                'avg_gross_median_salary': round(avg_salary, 2)
            })
        
        print(f"\n📅 Creating year breakdown CSV: {filename}")
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['year', 'total_records', 'unique_universities', 'unique_degrees', 'avg_employment_rate', 'avg_gross_median_salary']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in year_breakdown:
                    writer.writerow(row)
                
                print(f"✅ Successfully created year breakdown CSV with {len(year_breakdown)} years")
                
        except Exception as e:
            print(f"❌ Error creating year breakdown CSV: {e}")
            return None
        
        return filename

def main():
    """Main function to fetch data and create CSV files automatically"""
    separator = GraduateDataSeparator()
    
    print("🚀 Starting Singapore Graduate Employment Data Analysis")
    print("="*70)
    
    # Fetch all data
    separator.fetch_all_data()
    
    if not separator.all_data:
        print("❌ No data fetched. Please check your internet connection and try again.")
        return
    
    # Create CSV files automatically
    print("\n📁 Creating CSV files...")
    
    # 1. Main data CSV with all records
    main_csv = separator.export_to_csv()
    
    # 2. Summary statistics CSV
    summary_csv = separator.create_summary_csv()
    
    # 3. Year breakdown CSV
    year_csv = separator.create_year_breakdown_csv()
    
    # Show basic analysis
    print("\n" + "="*70)
    print("📊 BASIC DATA ANALYSIS")
    print("="*70)
    
    # Quick analysis
    year_data = separator.separate_by_year()
    uni_data = separator.separate_by_university()
    
    print(f"\n✅ ANALYSIS COMPLETE!")
    print(f"📄 Files created:")
    if main_csv:
        print(f"   • {main_csv} - Complete dataset")
    if summary_csv:
        print(f"   • {summary_csv} - Summary statistics")
    if year_csv:
        print(f"   • {year_csv} - Year-by-year breakdown")
    
    print(f"\n📈 Dataset Overview:")
    print(f"   • Total records: {len(separator.all_data):,}")
    print(f"   • Years covered: {min(year_data.keys())} - {max(year_data.keys())}")
    print(f"   • Universities: {len(uni_data)}")
    print(f"   • Total degree programs: {len(separator.separate_by_degree())}")
    
    return main_csv, summary_csv, year_csv

if __name__ == "__main__":
    main()

# Quick access functions for specific analysis
def create_csv_only():
    """Quick function to just create the main CSV file"""
    print("🚀 Quick CSV Creation Mode")
    print("="*50)
    
    separator = GraduateDataSeparator()
    separator.fetch_all_data()
    
    if separator.all_data:
        csv_file = separator.export_to_csv()
        print(f"\n✅ CSV created: {csv_file}")
        print(f"📊 Total records: {len(separator.all_data):,}")
        return csv_file
    else:
        print("❌ No data available to export")
        return None

def quick_year_analysis():
    """Quick function to analyze data by year only"""
    separator = GraduateDataSeparator()
    separator.fetch_all_data()
    return separator.separate_by_year()

def quick_university_analysis():
    """Quick function to analyze data by university only"""
    separator = GraduateDataSeparator()
    separator.fetch_all_data()
    return separator.separate_by_university()

def quick_salary_analysis(field='gross_monthly_median'):
    """Quick function to analyze data by salary field"""
    separator = GraduateDataSeparator()
    separator.fetch_all_data()
    return separator.separate_by_salary_range(field)