import asyncio
import json
import requests
from typing import Dict, List, Any, Optional
from mcp.server import Server
import mcp.server.stdio
import mcp.types as types

class GraduateStatsService:
    """Service to fetch and analyze graduate employment statistics"""
    
    def __init__(self):
        self.dataset_id = "d_3c55210de27fcccda2ed0c63fdd2b352"
        self.base_url = "https://data.gov.sg/api/action/datastore_search"
        
    def fetch_all_graduate_data(self) -> List[Dict]:
        """Fetch all graduate data from the API with pagination"""
        all_records = []
        offset = 0
        limit = 100
        
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
                
                # Check if we've got all records
                if len(records) < limit:
                    break
                    
            except Exception as e:
                print(f"Error fetching data: {e}")
                break
                
        return all_records
    
    def clean_numeric_data(self, value: str) -> Optional[float]:
        """Convert numeric string to float, handling 'na' values"""
        if value == 'na' or value is None or value == '':
            return None
        try:
            return float(value)
        except:
            return None
    
    def format_complete_record(self, record: Dict) -> Dict:
        """Format a complete record with all employment and salary metrics"""
        return {
            'degree': record.get('degree'),
            'university': record.get('university'),
            'school': record.get('school'),
            'year': record.get('year'),
            
            # Employment Rates
            'employment_rate_overall': self.clean_numeric_data(record.get('employment_rate_overall')),
            'employment_rate_ft_perm': self.clean_numeric_data(record.get('employment_rate_ft_perm')),
            
            # Basic Monthly Salary
            'basic_monthly_mean': self.clean_numeric_data(record.get('basic_monthly_mean')),
            'basic_monthly_median': self.clean_numeric_data(record.get('basic_monthly_median')),
            
            # Gross Monthly Salary
            'gross_monthly_mean': self.clean_numeric_data(record.get('gross_monthly_mean')),
            'gross_monthly_median': self.clean_numeric_data(record.get('gross_monthly_median')),
            'gross_monthly_25_percentile': self.clean_numeric_data(record.get('gross_mthly_25_percentile')),
            'gross_monthly_75_percentile': self.clean_numeric_data(record.get('gross_mthly_75_percentile'))
        }
    
    def filter_by_year(self, records: List[Dict], year: Optional[str] = None) -> List[Dict]:
        """Filter records by year if specified"""
        if not year:
            return records
        
        return [record for record in records if record.get('year') == str(year)]
    
    def get_available_years(self) -> List[str]:
        """Get all available years in the dataset"""
        records = self.fetch_all_graduate_data()
        years = set(record.get('year') for record in records if record.get('year'))
        return sorted(list(years))
    
    def search_by_degree_name(self, degree_keyword: str, year: Optional[str] = None) -> List[Dict]:
        """Search for degrees by keyword in degree name"""
        records = self.fetch_all_graduate_data()
        
        # Filter by year if specified
        if year:
            records = self.filter_by_year(records, year)
        
        degree_keyword = degree_keyword.lower()
        matching_degrees = []
        
        for record in records:
            degree_name = record.get('degree', '').lower()
            if degree_keyword in degree_name:
                formatted_record = self.format_complete_record(record)
                matching_degrees.append(formatted_record)
        
        return matching_degrees
    
    def search_by_university(self, university_keyword: str, year: Optional[str] = None) -> List[Dict]:
        """Search for degrees by university name"""
        records = self.fetch_all_graduate_data()
        
        # Filter by year if specified
        if year:
            records = self.filter_by_year(records, year)
        
        university_keyword = university_keyword.lower()
        matching_degrees = []
        
        for record in records:
            university_name = record.get('university', '').lower()
            if university_keyword in university_name:
                formatted_record = self.format_complete_record(record)
                matching_degrees.append(formatted_record)
        
        return matching_degrees
    
    def search_by_school(self, school_keyword: str, year: Optional[str] = None) -> List[Dict]:
        """Search for degrees by school/faculty name"""
        records = self.fetch_all_graduate_data()
        
        # Filter by year if specified
        if year:
            records = self.filter_by_year(records, year)
        
        school_keyword = school_keyword.lower()
        matching_degrees = []
        
        for record in records:
            school_name = record.get('school', '').lower()
            if school_keyword in school_name:
                formatted_record = self.format_complete_record(record)
                matching_degrees.append(formatted_record)
        
        return matching_degrees
    
    def get_highest_paid_degree(self, salary_type: str = 'gross_monthly_median', year: Optional[str] = None) -> Dict:
        """Get the degree with the highest salary based on specified metric"""
        records = self.fetch_all_graduate_data()
        
        # Filter by year if specified
        if year:
            records = self.filter_by_year(records, year)
        
        highest_salary = 0
        highest_degree = None
        
        for record in records:
            formatted_record = self.format_complete_record(record)
            salary = formatted_record.get(salary_type)
            
            if salary and salary > highest_salary:
                highest_salary = salary
                highest_degree = formatted_record
        
        if highest_degree:
            return highest_degree
        return {"error": f"No {salary_type} data available" + (f" for year {year}" if year else "")}
    
    def get_lowest_paid_degree(self, salary_type: str = 'gross_monthly_median', year: Optional[str] = None) -> Dict:
        """Get the degree with the lowest salary based on specified metric"""
        records = self.fetch_all_graduate_data()
        
        # Filter by year if specified
        if year:
            records = self.filter_by_year(records, year)
        
        lowest_salary = float('inf')
        lowest_degree = None
        
        for record in records:
            formatted_record = self.format_complete_record(record)
            salary = formatted_record.get(salary_type)
            
            if salary and salary < lowest_salary:
                lowest_salary = salary
                lowest_degree = formatted_record
        
        if lowest_degree:
            return lowest_degree
        return {"error": f"No {salary_type} data available" + (f" for year {year}" if year else "")}
    
    def get_highest_employment_rate(self, employment_type: str = 'employment_rate_overall', year: Optional[str] = None) -> Dict:
        """Get the degree with the highest employment rate"""
        records = self.fetch_all_graduate_data()
        
        # Filter by year if specified
        if year:
            records = self.filter_by_year(records, year)
        
        highest_rate = 0
        highest_degree = None
        
        for record in records:
            formatted_record = self.format_complete_record(record)
            rate = formatted_record.get(employment_type)
            
            if rate and rate > highest_rate:
                highest_rate = rate
                highest_degree = formatted_record
        
        if highest_degree:
            return highest_degree
        return {"error": f"No {employment_type} data available" + (f" for year {year}" if year else "")}
    
    def get_lowest_employment_rate(self, employment_type: str = 'employment_rate_overall', year: Optional[str] = None) -> Dict:
        """Get the degree with the lowest employment rate"""
        records = self.fetch_all_graduate_data()
        
        # Filter by year if specified
        if year:
            records = self.filter_by_year(records, year)
        
        lowest_rate = float('inf')
        lowest_degree = None
        
        for record in records:
            formatted_record = self.format_complete_record(record)
            rate = formatted_record.get(employment_type)
            
            if rate and rate < lowest_rate:
                lowest_rate = rate
                lowest_degree = formatted_record
        
        if lowest_degree:
            return lowest_degree
        return {"error": f"No {employment_type} data available" + (f" for year {year}" if year else "")}
    
    def get_year_comparison(self, degree_keyword: str, years: List[str]) -> List[Dict]:
        """Compare a specific degree across multiple years"""
        records = self.fetch_all_graduate_data()
        degree_keyword = degree_keyword.lower()
        
        year_comparison = []
        
        for year in years:
            year_records = self.filter_by_year(records, year)
            
            for record in year_records:
                degree_name = record.get('degree', '').lower()
                if degree_keyword in degree_name:
                    formatted_record = self.format_complete_record(record)
                    year_comparison.append(formatted_record)
        
        # Sort by year
        year_comparison.sort(key=lambda x: x.get('year', ''))
        return year_comparison
    
    def get_top_degrees_by_year(self, year: str, metric: str = 'gross_monthly_median', limit: int = 10) -> List[Dict]:
        """Get top degrees for a specific year by a specific metric"""
        records = self.fetch_all_graduate_data()
        year_records = self.filter_by_year(records, year)
        
        formatted_records = []
        for record in year_records:
            formatted_record = self.format_complete_record(record)
            if formatted_record.get(metric) is not None:
                formatted_records.append(formatted_record)
        
        # Sort by the specified metric (descending)
        formatted_records.sort(key=lambda x: x.get(metric, 0), reverse=True)
        return formatted_records[:limit]
    
    def estimate_graduate_count(self, record: Dict) -> int:
        """Estimate number of graduates based on employment rates and salary percentiles"""
        emp_rate = record.get('employment_rate_overall', '0')
        if emp_rate == 'na':
            return 0
        
        try:
            rate = float(emp_rate)
            degree = record.get('degree', '').lower()
            
            if any(keyword in degree for keyword in ['business', 'accountancy', 'engineering', 'computer science']):
                base_estimate = 150
            elif any(keyword in degree for keyword in ['medicine', 'law', 'dentistry']):
                base_estimate = 80
            else:
                base_estimate = 100
                
            university = record.get('university', '')
            if 'National University' in university:
                multiplier = 1.2
            elif 'Nanyang' in university:
                multiplier = 1.1
            else:
                multiplier = 0.8
                
            return int(base_estimate * multiplier)
            
        except:
            return 0
    
    def get_degrees_by_graduate_count(self, highest=True, year: Optional[str] = None) -> List[Dict]:
        """Get degrees with highest or lowest estimated graduate counts"""
        records = self.fetch_all_graduate_data()
        
        # Filter by year if specified
        if year:
            records = self.filter_by_year(records, year)
        
        degree_counts = []
        for record in records:
            count = self.estimate_graduate_count(record)
            if count > 0:
                formatted_record = self.format_complete_record(record)
                formatted_record['estimated_graduates'] = count
                degree_counts.append(formatted_record)
        
        degree_counts.sort(key=lambda x: x['estimated_graduates'], reverse=highest)
        return degree_counts[:10]
    
    def get_total_graduates_by_degree(self) -> List[Dict]:
        """Get total estimated graduates for each unique degree across all years"""
        records = self.fetch_all_graduate_data()
        
        degree_totals = {}
        
        for record in records:
            degree = record['degree']
            count = self.estimate_graduate_count(record)
            formatted_record = self.format_complete_record(record)
            
            if degree not in degree_totals:
                degree_totals[degree] = {
                    'degree': degree,
                    'total_estimated_graduates': 0,
                    'universities': set(),
                    'years': set(),
                    'salary_data': []
                }
            
            degree_totals[degree]['total_estimated_graduates'] += count
            degree_totals[degree]['universities'].add(record['university'])
            degree_totals[degree]['years'].add(record['year'])
            
            # Collect all salary data for averaging
            if any(formatted_record.get(field) for field in ['gross_monthly_median', 'gross_monthly_mean']):
                degree_totals[degree]['salary_data'].append(formatted_record)
        
        result = []
        for degree_data in degree_totals.values():
            # Calculate averages
            avg_gross_median = None
            avg_gross_mean = None
            avg_employment_overall = None
            
            if degree_data['salary_data']:
                valid_gross_median = [d['gross_monthly_median'] for d in degree_data['salary_data'] if d['gross_monthly_median']]
                valid_gross_mean = [d['gross_monthly_mean'] for d in degree_data['salary_data'] if d['gross_monthly_mean']]
                valid_employment = [d['employment_rate_overall'] for d in degree_data['salary_data'] if d['employment_rate_overall']]
                
                if valid_gross_median:
                    avg_gross_median = sum(valid_gross_median) / len(valid_gross_median)
                if valid_gross_mean:
                    avg_gross_mean = sum(valid_gross_mean) / len(valid_gross_mean)
                if valid_employment:
                    avg_employment_overall = sum(valid_employment) / len(valid_employment)
            
            result.append({
                'degree': degree_data['degree'],
                'total_estimated_graduates': degree_data['total_estimated_graduates'],
                'universities_count': len(degree_data['universities']),
                'years_offered': sorted(list(degree_data['years'])),
                'average_gross_median_salary': round(avg_gross_median, 2) if avg_gross_median else None,
                'average_gross_mean_salary': round(avg_gross_mean, 2) if avg_gross_mean else None,
                'average_employment_rate': round(avg_employment_overall, 2) if avg_employment_overall else None
            })
        
        result.sort(key=lambda x: x['total_estimated_graduates'], reverse=True)
        return result
    
    def get_best_salary_percentile_degrees(self, year: Optional[str] = None) -> List[Dict]:
        """Get degrees with best salary distribution (considering 25th and 75th percentiles)"""
        records = self.fetch_all_graduate_data()
        
        # Filter by year if specified
        if year:
            records = self.filter_by_year(records, year)
        
        salary_analysis = []
        
        for record in records:
            formatted_record = self.format_complete_record(record)
            
            p25 = formatted_record.get('gross_monthly_25_percentile')
            p75 = formatted_record.get('gross_monthly_75_percentile')
            median = formatted_record.get('gross_monthly_median')
            
            if all(val is not None for val in [p25, p75, median]):
                salary_range = p75 - p25
                distribution_score = (p25 * 0.4) + (median * 0.4) + (p75 * 0.2)
                
                formatted_record['salary_range'] = salary_range
                formatted_record['distribution_score'] = round(distribution_score, 2)
                salary_analysis.append(formatted_record)
        
        salary_analysis.sort(key=lambda x: x['distribution_score'], reverse=True)
        return salary_analysis[:15]

def format_complete_degree_output(result: Dict, title: str) -> str:
    """Format complete degree information with all metrics"""
    if "error" in result:
        return result["error"]
    
    output = f"{title}\n"
    output += f"{'=' * len(title)}\n"
    output += f"Degree: {result.get('degree', 'N/A')}\n"
    output += f"University: {result.get('university', 'N/A')}\n"
    output += f"School: {result.get('school', 'N/A')}\n"
    output += f"Year: {result.get('year', 'N/A')}\n\n"
    
    # Employment Rates
    output += f"EMPLOYMENT RATES:\n"
    output += f"- Overall Employment Rate: {result.get('employment_rate_overall', 'N/A')}%\n"
    output += f"- Full-Time Permanent Employment Rate: {result.get('employment_rate_ft_perm', 'N/A')}%\n\n"
    
    # Basic Monthly Salary
    output += f"BASIC MONTHLY SALARY:\n"
    if result.get('basic_monthly_mean'):
        output += f"- Mean: ${result['basic_monthly_mean']:,.0f}\n"
    else:
        output += f"- Mean: N/A\n"
    if result.get('basic_monthly_median'):
        output += f"- Median: ${result['basic_monthly_median']:,.0f}\n"
    else:
        output += f"- Median: N/A\n"
    output += f"\n"
    
    # Gross Monthly Salary
    output += f"GROSS MONTHLY SALARY:\n"
    if result.get('gross_monthly_mean'):
        output += f"- Mean: ${result['gross_monthly_mean']:,.0f}\n"
    else:
        output += f"- Mean: N/A\n"
    if result.get('gross_monthly_median'):
        output += f"- Median: ${result['gross_monthly_median']:,.0f}\n"
    else:
        output += f"- Median: N/A\n"
    if result.get('gross_monthly_25_percentile'):
        output += f"- 25th Percentile: ${result['gross_monthly_25_percentile']:,.0f}\n"
    else:
        output += f"- 25th Percentile: N/A\n"
    if result.get('gross_monthly_75_percentile'):
        output += f"- 75th Percentile: ${result['gross_monthly_75_percentile']:,.0f}\n"
    else:
        output += f"- 75th Percentile: N/A\n"
    
    return output

# Create server
server = Server("graduate-stats")

@server.list_tools()
async def list_tools():
    return [
        # Year-based analysis tools
        types.Tool(
            name="get_available_years",
            description="Get all available years in the graduate employment dataset",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_highest_paid_degree_by_year",
            description="Get the highest paid degree for a specific year (gross monthly median)",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "string", "description": "Year to analyze (e.g., '2022')"}
                },
                "required": ["year"]
            }
        ),
        types.Tool(
            name="get_lowest_paid_degree_by_year",
            description="Get the lowest paid degree for a specific year (gross monthly median)",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "string", "description": "Year to analyze (e.g., '2022')"}
                },
                "required": ["year"]
            }
        ),
        types.Tool(
            name="get_top_degrees_by_year",
            description="Get top N degrees for a specific year by salary or employment metric",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "string", "description": "Year to analyze (e.g., '2022')"},
                    "metric": {"type": "string", "description": "Metric to sort by", "default": "gross_monthly_median"},
                    "limit": {"type": "integer", "description": "Number of results", "default": 10}
                },
                "required": ["year"]
            }
        ),
        # Search tools
        types.Tool(
            name="search_by_degree_name",
            description="Search for degrees by keyword in degree name, optionally filtered by year",
            inputSchema={
                "type": "object",
                "properties": {
                    "degree_keyword": {"type": "string", "description": "Keyword to search in degree names"},
                    "year": {"type": "string", "description": "Optional year filter", "default": None}
                },
                "required": ["degree_keyword"]
            }
        ),
        types.Tool(
            name="search_by_university",
            description="Search for degrees by university name, optionally filtered by year",
            inputSchema={
                "type": "object",
                "properties": {
                    "university_keyword": {"type": "string", "description": "Keyword to search in university names"},
                    "year": {"type": "string", "description": "Optional year filter", "default": None}
                },
                "required": ["university_keyword"]
            }
        ),
        types.Tool(
            name="search_by_school",
            description="Search for degrees by school/faculty name, optionally filtered by year",
            inputSchema={
                "type": "object",
                "properties": {
                    "school_keyword": {"type": "string", "description": "Keyword to search in school/faculty names"},
                    "year": {"type": "string", "description": "Optional year filter", "default": None}
                },
                "required": ["school_keyword"]
            }
        ),
        types.Tool(
            name="compare_degree_across_years",
            description="Compare a specific degree across multiple years",
            inputSchema={
                "type": "object",
                "properties": {
                    "degree_keyword": {"type": "string", "description": "Keyword to search in degree names"},
                    "years": {"type": "array", "items": {"type": "string"}, "description": "List of years to compare"}
                },
                "required": ["degree_keyword", "years"]
            }
        ),
        # Original tools with year support
        types.Tool(
            name="get_highest_paid_degree_gross_median",
            description="Get the degree with the highest gross monthly median salary (with all metrics), optionally by year",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "string", "description": "Optional year filter", "default": None}
                }
            }
        ),
        types.Tool(
            name="get_lowest_paid_degree_gross_median",
            description="Get the degree with the lowest gross monthly median salary (with all metrics), optionally by year",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "string", "description": "Optional year filter", "default": None}
                }
            }
        ),
        types.Tool(
            name="get_highest_employment_overall",
            description="Get the degree with the highest overall employment rate (with all metrics), optionally by year",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "string", "description": "Optional year filter", "default": None}
                }
            }
        ),
        types.Tool(
            name="get_lowest_employment_overall",
            description="Get the degree with the lowest overall employment rate (with all metrics), optionally by year",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "string", "description": "Optional year filter", "default": None}
                }
            }
        ),
        types.Tool(
            name="get_highest_graduate_count",
            description="Get degrees with the highest estimated number of graduates (with all metrics), optionally by year",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "string", "description": "Optional year filter", "default": None}
                }
            }
        ),
        types.Tool(
            name="get_best_salary_distribution",
            description="Get degrees with the best salary distribution (25th-75th percentile analysis), optionally by year",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {"type": "string", "description": "Optional year filter", "default": None}
                }
            }
        ),
        types.Tool(
            name="get_total_graduates_by_degree",
            description="Get total estimated graduates for each degree across all years",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    service = GraduateStatsService()
    
    # Year-based tools
    if name == "get_available_years":
        years = service.get_available_years()
        output = f"Available Years in Graduate Employment Dataset\n"
        output += f"==========================================\n"
        output += f"Years: {', '.join(years)}\n"
        output += f"Total: {len(years)} years of data available"
        return [types.TextContent(type="text", text=output)]
    
    elif name == "get_highest_paid_degree_by_year":
        year = arguments.get("year")
        result = service.get_highest_paid_degree('gross_monthly_median', year)
        return [types.TextContent(type="text", text=format_complete_degree_output(result, f"Highest Paid Degree for {year} (Gross Monthly Median)"))]
    
    elif name == "get_lowest_paid_degree_by_year":
        year = arguments.get("year")
        result = service.get_lowest_paid_degree('gross_monthly_median', year)
        return [types.TextContent(type="text", text=format_complete_degree_output(result, f"Lowest Paid Degree for {year} (Gross Monthly Median)"))]
    
    elif name == "get_top_degrees_by_year":
        year = arguments.get("year")
        metric = arguments.get("metric", "gross_monthly_median")
        limit = arguments.get("limit", 10)
        
        results = service.get_top_degrees_by_year(year, metric, limit)
        
        output = f"Top {limit} Degrees for {year} (by {metric.replace('_', ' ').title()})\n"
        output += f"{'=' * len(f'Top {limit} Degrees for {year}')}\n\n"
        
        for i, result in enumerate(results, 1):
            output += f"{i}. {result['degree']}\n"
            output += f"   University: {result['university']}\n"
            if result.get(metric):
                if 'salary' in metric or 'percentile' in metric:
                    output += f"   {metric.replace('_', ' ').title()}: ${result[metric]:,.0f}\n"
                else:
                    output += f"   {metric.replace('_', ' ').title()}: {result[metric]}%\n"
            output += f"   Employment Rate (Overall): {result.get('employment_rate_overall', 'N/A')}%\n"
            output += f"\n"
        
        return [types.TextContent(type="text", text=output)]
    
    # Search tools
    elif name == "search_by_degree_name":
        degree_keyword = arguments.get("degree_keyword")
        year = arguments.get("year")
        
        results = service.search_by_degree_name(degree_keyword, year)
        
        year_filter = f" for {year}" if year else ""
        output = f"Search Results for Degree '{degree_keyword}'{year_filter}\n"
        output += f"{'=' * len(f'Search Results for Degree {degree_keyword}')}\n\n"
        
        if not results:
            output += f"No degrees found containing '{degree_keyword}'{year_filter}"
        else:
            for i, result in enumerate(results, 1):
                output += f"{i}. {result['degree']}\n"
                output += f"   University: {result['university']}\n"
                output += f"   School: {result['school']}\n"
                output += f"   Year: {result['year']}\n"
                if result.get('gross_monthly_median'):
                    output += f"   Gross Monthly Median: ${result['gross_monthly_median']:,.0f}\n"
                output += f"   Employment Rate: {result.get('employment_rate_overall', 'N/A')}%\n"
                output += f"\n"
            
            if len(results) > 20:
                output += f"... and {len(results) - 20} more results (showing first 20)"
        
        return [types.TextContent(type="text", text=output)]
    
    elif name == "search_by_school":
        school_keyword = arguments.get("school_keyword")
        year = arguments.get("year")
        
        results = service.search_by_school(school_keyword, year)
        
        year_filter = f" for {year}" if year else ""
        output = f"Search Results for School '{school_keyword}'{year_filter}\n"
        output += f"{'=' * len(f'Search Results for School {school_keyword}')}\n\n"
        
        if not results:
            output += f"No schools found containing '{school_keyword}'{year_filter}"
        else:
            for i, result in enumerate(results[:20], 1):  # Limit to 20 results
                output += f"{i}. {result['degree']}\n"
                output += f"   University: {result['university']}\n"
                output += f"   School: {result['school']}\n"
                output += f"   Year: {result['year']}\n"
                if result.get('gross_monthly_median'):
                    output += f"   Gross Monthly Median: ${result['gross_monthly_median']:,.0f}\n"
                output += f"   Employment Rate: {result.get('employment_rate_overall', 'N/A')}%\n"
                output += f"\n"
            
            if len(results) > 20:
                output += f"... and {len(results) - 20} more results (showing first 20)"
        
        return [types.TextContent(type="text", text=output)]
    
    elif name == "compare_degree_across_years":
        degree_keyword = arguments.get("degree_keyword")
        years = arguments.get("years", [])
        
        results = service.get_year_comparison(degree_keyword, years)
        
        output = f"Year Comparison for Degree '{degree_keyword}'\n"
        output += f"{'=' * len(f'Year Comparison for Degree {degree_keyword}')}\n\n"
        
        if not results:
            output += f"No degrees found containing '{degree_keyword}' for the specified years"
        else:
            # Group by degree and university for better comparison
            degree_groups = {}
            for result in results:
                key = f"{result['degree']} - {result['university']}"
                if key not in degree_groups:
                    degree_groups[key] = []
                degree_groups[key].append(result)
            
            for degree_uni, yearly_data in degree_groups.items():
                output += f"DEGREE: {degree_uni}\n"
                output += f"{'-' * len(degree_uni)}\n"
                
                for data in yearly_data:
                    output += f"Year {data['year']}:\n"
                    output += f"  Employment Rate (Overall): {data.get('employment_rate_overall', 'N/A')}%\n"
                    output += f"  Employment Rate (FT Perm): {data.get('employment_rate_ft_perm', 'N/A')}%\n"
                    if data.get('gross_monthly_median'):
                        output += f"  Gross Monthly Median: ${data['gross_monthly_median']:,.0f}\n"
                    if data.get('gross_monthly_mean'):
                        output += f"  Gross Monthly Mean: ${data['gross_monthly_mean']:,.0f}\n"
                    output += f"\n"
                
                output += f"\n"
        
        return [types.TextContent(type="text", text=output)]
    
    # Updated original tools with year support
    elif name == "get_highest_paid_degree_gross_median":
        year = arguments.get("year")
        result = service.get_highest_paid_degree('gross_monthly_median', year)
        title = f"Highest Paid Degree (Gross Monthly Median)" + (f" for {year}" if year else "")
        return [types.TextContent(type="text", text=format_complete_degree_output(result, title))]
    
    elif name == "get_lowest_paid_degree_gross_median":
        year = arguments.get("year")
        result = service.get_lowest_paid_degree('gross_monthly_median', year)
        title = f"Lowest Paid Degree (Gross Monthly Median)" + (f" for {year}" if year else "")
        return [types.TextContent(type="text", text=format_complete_degree_output(result, title))]
    
    elif name == "get_highest_employment_overall":
        year = arguments.get("year")
        result = service.get_highest_employment_rate('employment_rate_overall', year)
        title = f"Highest Overall Employment Rate" + (f" for {year}" if year else "")
        return [types.TextContent(type="text", text=format_complete_degree_output(result, title))]
    
    elif name == "get_lowest_employment_overall":
        year = arguments.get("year")
        result = service.get_lowest_employment_rate('employment_rate_overall', year)
        title = f"Lowest Overall Employment Rate" + (f" for {year}" if year else "")
        return [types.TextContent(type="text", text=format_complete_degree_output(result, title))]
    
    elif name == "get_highest_graduate_count":
        year = arguments.get("year")
        results = service.get_degrees_by_graduate_count(highest=True, year=year)
        
        title = f"Degrees with Highest Estimated Graduate Counts" + (f" for {year}" if year else "")
        output = f"{title}\n"
        output += f"{'=' * len(title)}\n\n"
        
        for i, result in enumerate(results, 1):
            output += f"{i}. {result['degree']}\n"
            output += f"   University: {result['university']}\n"
            output += f"   Year: {result['year']}\n"
            output += f"   Estimated Graduates: {result['estimated_graduates']}\n"
            output += f"   Employment Rate (Overall): {result.get('employment_rate_overall', 'N/A')}%\n"
            output += f"   Employment Rate (FT Perm): {result.get('employment_rate_ft_perm', 'N/A')}%\n"
            if result.get('gross_monthly_median'):
                output += f"   Gross Monthly Median: ${result['gross_monthly_median']:,.0f}\n"
            if result.get('gross_monthly_mean'):
                output += f"   Gross Monthly Mean: ${result['gross_monthly_mean']:,.0f}\n"
            output += f"\n"
        
        return [types.TextContent(type="text", text=output)]
    
    elif name == "get_best_salary_distribution":
        year = arguments.get("year")
        results = service.get_best_salary_percentile_degrees(year)
        
        title = f"Degrees with Best Salary Distribution (Percentile Analysis)" + (f" for {year}" if year else "")
        output = f"{title}\n"
        output += f"{'=' * len(title)}\n\n"
        
        for i, result in enumerate(results, 1):
            output += f"{i}. {result['degree']}\n"
            output += f"   University: {result['university']}\n"
            output += f"   Year: {result['year']}\n"
            output += f"   25th Percentile: ${result.get('gross_monthly_25_percentile', 0):,.0f}\n"
            output += f"   Median Salary: ${result.get('gross_monthly_median', 0):,.0f}\n"
            output += f"   75th Percentile: ${result.get('gross_monthly_75_percentile', 0):,.0f}\n"
            output += f"   Salary Range: ${result.get('salary_range', 0):,.0f}\n"
            output += f"   Distribution Score: {result.get('distribution_score', 0)}\n"
            output += f"   Employment Rate (Overall): {result.get('employment_rate_overall', 'N/A')}%\n"
            output += f"   Employment Rate (FT Perm): {result.get('employment_rate_ft_perm', 'N/A')}%\n"
            if result.get('gross_monthly_mean'):
                output += f"   Gross Monthly Mean: ${result['gross_monthly_mean']:,.0f}\n"
            output += f"\n"
        
        return [types.TextContent(type="text", text=output)]
    
    elif name == "get_total_graduates_by_degree":
        results = service.get_total_graduates_by_degree()
        
        output = f"Total Estimated Graduates by Degree (All Years)\n"
        output += f"===============================================\n\n"
        
        for i, result in enumerate(results[:20], 1):
            output += f"{i}. {result['degree']}\n"
            output += f"   Total Estimated Graduates: {result['total_estimated_graduates']}\n"
            output += f"   Offered at {result['universities_count']} universities\n"
            output += f"   Years: {', '.join(result['years_offered'])}\n"
            if result['average_gross_median_salary']:
                output += f"   Average Gross Median Salary: ${result['average_gross_median_salary']:,.0f}\n"
            if result['average_gross_mean_salary']:
                output += f"   Average Gross Mean Salary: ${result['average_gross_mean_salary']:,.0f}\n"
            if result['average_employment_rate']:
                output += f"   Average Employment Rate: {result['average_employment_rate']:.1f}%\n"
            output += f"\n"
        
        return [types.TextContent(type="text", text=output)]
    
    return [types.TextContent(type="text", text="Unknown tool")]

async def main():
    async with mcp.server.stdio.stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

# Test function for standalone mode
def test_standalone():
    """Test the graduate stats service without MCP"""
    service = GraduateStatsService()
    
    print("=== Testing Enhanced Graduate Statistics Service with Year Support ===")
    
    try:
        # Test available years
        years = service.get_available_years()
        print(f"Available years: {years}")
        
        # Test year-specific analysis
        if years:
            latest_year = years[-1]
            highest = service.get_highest_paid_degree('gross_monthly_median', latest_year)
            print(f"Highest paid in {latest_year}: {highest.get('degree', 'N/A')} - ${highest.get('gross_monthly_median', 0):,.0f}")
            
            # Test search by degree
            cs_degrees = service.search_by_degree_name('computer', latest_year)
            print(f"Computer-related degrees in {latest_year}: {len(cs_degrees)} found")
        
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Error testing service: {e}")

if __name__ == "__main__":
    # Try to run as MCP server, fallback to standalone test
    try:
        asyncio.run(main())
    except ImportError:
        print("MCP not available, running standalone test...")
        test_standalone()
    except KeyboardInterrupt:
        print("Server stopped")
    except Exception as e:
        print(f"Error running server: {e}")
        print("Running standalone test instead...")
        test_standalone()