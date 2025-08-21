# Import all the tools we need
import requests  # For downloading data from websites
import pandas as pd  # For organizing data in tables
import json  # For handling data format
import traceback  # For detailed error reporting
from datetime import datetime, timedelta  # For working with dates
import os  # For creating folders and files
import shutil  # For file operations like disk usage and copying

# This line assumes a config.py file exists with your settings.
# If it doesn't, you can define the variables directly here.
try:
    from config import *
except ImportError:
    # Define default values if config.py is not found
    API_BASE_URL = "https://api.usaspending.gov/api/v2"
    DATA_DIR = "data"
    API_TIMEOUT = 60
    DATA_LIMIT = 1000


class SimpleCollector:
    """This class handles downloading and saving government spending data"""

    def __init__(self):
        """Set up the collector when we create it"""
        # Use settings from our config file or the defaults
        self.api_base = API_BASE_URL
        self.data_dir = DATA_DIR
        self.timeout = API_TIMEOUT
        self.limit = DATA_LIMIT

        # Create the data folder if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        print(f"Data collector initialized. Data will be saved to: {self.data_dir}")

    def fetch_spending_data(self, limit=None, award_group='contracts'):
        """Download spending data from the government API with only useful fields"""
        if limit is None:
            limit = self.limit

        # Define award type groups based on the API error message
        award_type_groups = {
            'contracts': ['A', 'B', 'C', 'D'],  # BPA Call, Purchase Order, Delivery Order, Definitive Contract
            'grants': ['02', '03', '04', '05'],  # Block Grant, Formula Grant, Project Grant, Cooperative Agreement
            'direct_payments': ['06', '10'],  # Direct Payment, Direct Payment with Unrestricted Use
            'loans': ['07', '08'],  # Direct Loan, Guaranteed/Insured Loan
            'other': ['09', '11', '-1']  # Other, Other Financial Assistance, No Award Type
        }

        # Validate award group
        if award_group not in award_type_groups:
            print(f"Invalid award group: {award_group}")
            print(f"    Valid groups: {list(award_type_groups.keys())}")
            return None

        # The specific web address for spending data
        url = f"{self.api_base}/search/spending_by_award/"

        # Define ONLY useful field sets (removed all "Unknown" value fields)
        useful_fields = {
            'contracts': [
                # Financial Information (5 fields)
                'Award Amount', 'COVID-19 Obligations', 'COVID-19 Outlays',
                'Infrastructure Obligations', 'Infrastructure Outlays',
                
                # Recipient Information (4 fields)
                'Award ID', 'Recipient Name', 'recipient_id', 'Recipient UEI',
                
                # Agency Information (8 fields)
                'Awarding Agency', 'Awarding Agency Code', 'Awarding Sub Agency', 'Awarding Sub Agency Code',
                'Funding Agency', 'Funding Agency Code', 'Funding Sub Agency', 'Funding Sub Agency Code',
                
                # Geographic Data (3 fields)
                'Place of Performance State Code', 'Place of Performance Country Code', 'Place of Performance Zip5',
                
                # Contract Details (6 fields)
                'Description', 'Contract Award Type', 'naics_code', 'naics_description',
                'psc_code', 'psc_description',
                
                # Date Information (4 fields)
                'Last Modified Date', 'Base Obligation Date', 'Start Date', 'End Date'
            ],
            'grants': [
                # Financial Information (5 fields)
                'Award Amount', 'COVID-19 Obligations', 'COVID-19 Outlays',
                'Infrastructure Obligations', 'Infrastructure Outlays',
                
                # Recipient Information (4 fields)
                'Award ID', 'Recipient Name', 'recipient_id', 'Recipient UEI',
                
                # Agency Information (8 fields)
                'Awarding Agency', 'Awarding Agency Code', 'Awarding Sub Agency', 'Awarding Sub Agency Code',
                'Funding Agency', 'Funding Agency Code', 'Funding Sub Agency', 'Funding Sub Agency Code',
                
                # Geographic Data (3 fields)
                'Place of Performance State Code', 'Place of Performance Country Code', 'Place of Performance Zip5',
                
                # Grant Details (2 fields - removed cfda fields as they contained only "Unknown")
                'Description', 'Contract Award Type',
                
                # Date Information (4 fields)
                'Last Modified Date', 'Base Obligation Date', 'Start Date', 'End Date'
            ]
        }
        
        # Use grants field set for other award types
        useful_fields['direct_payments'] = useful_fields['grants']
        useful_fields['loans'] = useful_fields['grants']
        useful_fields['other'] = useful_fields['grants']

        # Get the appropriate useful field set
        fields = useful_fields.get(award_group, useful_fields['contracts'])

        # Updated payload with only useful field names
        payload = {
            "filters": {
                "time_period": [
                    {
                        "start_date": "2023-10-01",  # FY 2024 start
                        "end_date": "2024-09-30"  # FY 2024 end
                    }
                ],
                # Use only one award type group
                "award_type_codes": award_type_groups[award_group]
            },
            "fields": fields,
            "sort": "Award Amount",  # This field exists in both contracts and grants
            "order": "desc",
            "limit": limit
        }

        print(f"Requesting {limit} {award_group} records from USAspending.gov...")
        print(f"Date range: 2023-10-01 to 2024-09-30 (FY 2024)")
        print(f"Award types: {award_type_groups[award_group]}")
        print(f"Requesting {len(fields)} useful fields only (removed {46-len(fields)} unused fields)")

        try:
            # Make the actual request to the government website
            print(f"Debug: Making POST request to {url}")
            print(f"Debug: Award group: {award_group}")

            response = requests.post(url, json=payload, timeout=self.timeout)

            print(f"Debug: Response status code: {response.status_code}")

            # Check if the request was successful
            if response.status_code == 200:
                print("Successfully downloaded data from government API")
                response_data = response.json()
                print(f"Debug: Response keys: {list(response_data.keys())}")

                # Show first record structure for debugging
                if 'results' in response_data and response_data['results']:
                    first_record = response_data['results'][0]
                    print(f"Debug: First record has {len(first_record)} fields")
                    print("Debug: Sample field values:")
                    for key, value in list(first_record.items())[:8]:
                        print(f"        {key}: {value}")

                # Validate the response before returning it
                if self.validate_api_response(response_data):
                    return response_data
                else:
                    print("Response validation failed - returning None")
                    return None
            else:
                print(f"HTTP Error: {response.status_code}")
                print(f"Debug: Response text: {response.text[:800]}...")
                return None

        except requests.exceptions.Timeout:
            print(f"Request timed out after {self.timeout} seconds")
            return None
        except requests.exceptions.ConnectionError:
            print("Connection error - check your internet connection")
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            print(f"Debug: Full traceback: {traceback.format_exc()}")
            return None

    def fetch_all_award_types(self, limit_per_group=10):
        """Fetch data from all award type groups and combine them"""
        award_groups = ['contracts', 'grants', 'direct_payments', 'loans', 'other']
        all_data = []

        print(f"Fetching data from {len(award_groups)} award type groups...")

        for group in award_groups:
            print(f"\nFetching {group} data...")
            data = self.fetch_spending_data(limit=limit_per_group, award_group=group)

            if data and 'results' in data and data['results']:
                all_data.extend(data['results'])
                print(f"Added {len(data['results'])} {group} records")
            else:
                print(f"No {group} data available")

        if all_data:
            # Create combined response structure
            combined_response = {
                'results': all_data,
                'page_metadata': {
                    'page': 1,
                    'hasNext': False,
                    'hasPrevious': False,
                    'total': len(all_data)
                }
            }
            print(f"\nCombined total: {len(all_data)} records from all award types")
            return combined_response
        else:
            print("\nNo data retrieved from any award type group")
            return None
    # Add this new method to your SimpleCollector class in data_collector.py

    def fetch_spending_data_with_pagination(self, total_limit=None, award_group='contracts'):
        """Download spending data using pagination to get more than 100 records"""
        if total_limit is None:
            total_limit = self.limit

        # API maximum per request is 100
        api_max_limit = 100
        all_results = []
        
        # Calculate how many requests we need
        total_requests = (total_limit + api_max_limit - 1) // api_max_limit  # Ceiling division
        
        print(f"Need to make {total_requests} requests to get {total_limit} records")
        print(f"API limit per request: {api_max_limit}")
        
        for request_num in range(total_requests):
            # Calculate how many records to request in this batch
            remaining_records = total_limit - len(all_results)
            current_limit = min(api_max_limit, remaining_records)
            
            if current_limit <= 0:
                break
            
            # THIS IS THE KEY FIX: Add page parameter for pagination
            current_page = request_num + 1  # Pages start from 1, not 0
            
            print(f"\nRequest {request_num + 1}/{total_requests}: Fetching {current_limit} records (Page {current_page})...")
            print(f"Progress: {len(all_results)}/{total_limit} records collected so far")
            
            # Make the API request for this batch WITH PAGE PARAMETER
            batch_data = self.fetch_spending_data_with_page(
                limit=current_limit, 
                award_group=award_group,
                page=current_page  # Add page parameter
            )
            
            if batch_data and 'results' in batch_data and batch_data['results']:
                batch_results = batch_data['results']
                all_results.extend(batch_results)
                print(f"Batch {request_num + 1}: Retrieved {len(batch_results)} records from page {current_page}")
                
                # If we got fewer records than requested, we've hit the end
                if len(batch_results) < current_limit:
                    print(f"Received fewer records than requested - likely reached end of available data")
                    break
                    
            else:
                print(f"Batch {request_num + 1}: No data received from page {current_page}")
                # Continue with next batch instead of stopping
                continue
                
            # Add a small delay between requests to be respectful to the API
            import time
            time.sleep(1)  # 1 second delay between requests
        
        # Create final response structure
        if all_results:
            print(f"\nPagination complete!")
            print(f"Total records collected: {len(all_results)}")
            print(f"Unique records check: {len(set(r.get('Award ID', '') for r in all_results))} unique IDs")
            
            final_response = {
                'results': all_results,
                'page_metadata': {
                    'page': 1,
                    'hasNext': False,
                    'hasPrevious': False,
                    'total': len(all_results),
                    'requests_made': request_num + 1,
                    'pagination_used': True
                }
            }
            return final_response
        else:
            print(f"\nNo data collected from any request")
            return None

    def fetch_spending_data_with_page(self, limit=None, award_group='contracts', page=1):
        """Modified version of fetch_spending_data that accepts a page parameter"""
        if limit is None:
            limit = self.limit

        # Define award type groups based on the API error message
        award_type_groups = {
            'contracts': ['A', 'B', 'C', 'D'],  # BPA Call, Purchase Order, Delivery Order, Definitive Contract
            'grants': ['02', '03', '04', '05'],  # Block Grant, Formula Grant, Project Grant, Cooperative Agreement
            'direct_payments': ['06', '10'],  # Direct Payment, Direct Payment with Unrestricted Use
            'loans': ['07', '08'],  # Direct Loan, Guaranteed/Insured Loan
            'other': ['09', '11', '-1']  # Other, Other Financial Assistance, No Award Type
        }

        # Validate award group
        if award_group not in award_type_groups:
            print(f"Invalid award group: {award_group}")
            print(f"    Valid groups: {list(award_type_groups.keys())}")
            return None

        # The specific web address for spending data
        url = f"{self.api_base}/search/spending_by_award/"

        # Define ONLY useful field sets (removed all "Unknown" value fields)
        useful_fields = {
            'contracts': [
                # Financial Information (5 fields)
                'Award Amount', 'COVID-19 Obligations', 'COVID-19 Outlays',
                'Infrastructure Obligations', 'Infrastructure Outlays',
                
                # Recipient Information (4 fields)
                'Award ID', 'Recipient Name', 'recipient_id', 'Recipient UEI',
                
                # Agency Information (8 fields)
                'Awarding Agency', 'Awarding Agency Code', 'Awarding Sub Agency', 'Awarding Sub Agency Code',
                'Funding Agency', 'Funding Agency Code', 'Funding Sub Agency', 'Funding Sub Agency Code',
                
                # Geographic Data (3 fields)
                'Place of Performance State Code', 'Place of Performance Country Code', 'Place of Performance Zip5',
                
                # Contract Details (6 fields)
                'Description', 'Contract Award Type', 'naics_code', 'naics_description',
                'psc_code', 'psc_description',
                
                # Date Information (4 fields)
                'Last Modified Date', 'Base Obligation Date', 'Start Date', 'End Date'
            ],
            'grants': [
                # Financial Information (5 fields)
                'Award Amount', 'COVID-19 Obligations', 'COVID-19 Outlays',
                'Infrastructure Obligations', 'Infrastructure Outlays',
                
                # Recipient Information (4 fields)
                'Award ID', 'Recipient Name', 'recipient_id', 'Recipient UEI',
                
                # Agency Information (8 fields)
                'Awarding Agency', 'Awarding Agency Code', 'Awarding Sub Agency', 'Awarding Sub Agency Code',
                'Funding Agency', 'Funding Agency Code', 'Funding Sub Agency', 'Funding Sub Agency Code',
                
                # Geographic Data (3 fields)
                'Place of Performance State Code', 'Place of Performance Country Code', 'Place of Performance Zip5',
                
                # Grant Details (2 fields - removed cfda fields as they contained only "Unknown")
                'Description', 'Contract Award Type',
                
                # Date Information (4 fields)
                'Last Modified Date', 'Base Obligation Date', 'Start Date', 'End Date'
            ]
        }
        
        # Use grants field set for other award types
        useful_fields['direct_payments'] = useful_fields['grants']
        useful_fields['loans'] = useful_fields['grants']
        useful_fields['other'] = useful_fields['grants']

        # Get the appropriate useful field set
        fields = useful_fields.get(award_group, useful_fields['contracts'])

        # Updated payload with page parameter - THIS IS THE KEY ADDITION
        payload = {
            "filters": {
                "time_period": [
                    {
                        "start_date": "2023-10-01",  # FY 2024 start
                        "end_date": "2024-09-30"  # FY 2024 end
                    }
                ],
                # Use only one award type group
                "award_type_codes": award_type_groups[award_group]
            },
            "fields": fields,
            "sort": "Award Amount",  # This field exists in both contracts and grants
            "order": "desc",
            "limit": limit,
            "page": page  # THIS IS THE CRUCIAL ADDITION FOR PAGINATION
        }

        print(f"Requesting {limit} {award_group} records from page {page} of USAspending.gov...")
        print(f"Date range: 2023-10-01 to 2024-09-30 (FY 2024)")
        print(f"Award types: {award_type_groups[award_group]}")
        print(f"Requesting {len(fields)} useful fields only (removed {46-len(fields)} unused fields)")

        try:
            # Make the actual request to the government website
            print(f"Debug: Making POST request to {url} (Page {page})")
            print(f"Debug: Award group: {award_group}")

            response = requests.post(url, json=payload, timeout=self.timeout)

            print(f"Debug: Response status code: {response.status_code}")

            # Check if the request was successful
            if response.status_code == 200:
                print("Successfully downloaded data from government API")
                response_data = response.json()
                print(f"Debug: Response keys: {list(response_data.keys())}")

                # Show first record structure for debugging
                if 'results' in response_data and response_data['results']:
                    first_record = response_data['results'][0]
                    print(f"Debug: First record has {len(first_record)} fields")
                    
                    # Show the Award ID to verify we're getting different records
                    award_id = first_record.get('Award ID', 'No ID')
                    print(f"Debug: First record Award ID from page {page}: {award_id}")

                # Validate the response before returning it
                if self.validate_api_response(response_data):
                    return response_data
                else:
                    print("Response validation failed - returning None")
                    return None
            else:
                print(f"HTTP Error: {response.status_code}")
                print(f"Debug: Response text: {response.text[:800]}...")
                return None

        except requests.exceptions.Timeout:
            print(f"Request timed out after {self.timeout} seconds")
            return None
        except requests.exceptions.ConnectionError:
            print("Connection error - check your internet connection")
            return None
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            print(f"Debug: Full traceback: {traceback.format_exc()}")
            return None
    

    def process_to_dataframe(self, data):
        """Convert downloaded data into an organized table with only useful columns"""
        # First, check if we have any data at all
        try:
            if not data or 'results' not in data:
                print("No data to process")
                return pd.DataFrame()

            results = data.get('results', [])
            if not results:
                print("Results list is empty")
                return pd.DataFrame()

            print(f"Processing {len(results)} spending records with useful fields only...")

        except Exception as e:
            print(f"Error accessing data structure: {str(e)}")
            return pd.DataFrame()

        # Initialize counters for tracking
        records = []
        processed_count = 0
        error_count = 0
        field_errors = {}  # Track which fields cause the most errors

        # Process each record with comprehensive error handling
        for i, item in enumerate(results):
            try:
                # Validate that item is a dictionary
                if not isinstance(item, dict):
                    error_count += 1
                    print(f"Record {i+1}: Not a valid dictionary, skipping")
                    continue

                # Extract and clean each field with individual error handling
                record = {}

                # Helper function to safely extract field
                def safe_extract(field_name, fallback="", convert_type=str):
                    try:
                        value = item.get(field_name, fallback)
                        if value is None or value == "":
                            return fallback
                        if convert_type == str:
                            return str(value).strip() if value != "" else fallback
                        elif convert_type == float:
                            return float(value) if value not in [None, "", "null"] else 0.0
                        elif convert_type == int:
                            return int(value) if value not in [None, "", "null"] else 0
                        else:
                            return value
                    except Exception as e:
                        field_errors[field_name] = field_errors.get(field_name, 0) + 1
                        if field_name in ['Award Amount', 'Award ID', 'Recipient Name']:  # Only log errors for critical fields
                            print(f"Record {i+1}: Error processing {field_name}: {str(e)}")
                        return fallback

                # === USEFUL COLUMNS ONLY ===
                
                # Financial Information (5 fields)
                record['award_amount'] = safe_extract('Award Amount', 0.0, float)
                record['covid_19_obligations'] = safe_extract('COVID-19 Obligations', 0.0, float)
                record['covid_19_outlays'] = safe_extract('COVID-19 Outlays', 0.0, float)
                record['infrastructure_obligations'] = safe_extract('Infrastructure Obligations', 0.0, float)
                record['infrastructure_outlays'] = safe_extract('Infrastructure Outlays', 0.0, float)

                # Recipient Information (4 fields)
                record['award_id'] = safe_extract('Award ID', f'UNKNOWN_ID_{i+1}')
                record['recipient_name'] = safe_extract('Recipient Name', 'Unknown Recipient')
                record['recipient_id'] = safe_extract('recipient_id', 'No ID')
                record['recipient_uei'] = safe_extract('Recipient UEI', 'No UEI')

                # Agency Information (8 fields)
                record['awarding_agency'] = safe_extract('Awarding Agency', 'Unknown Agency')
                record['awarding_agency_code'] = safe_extract('Awarding Agency Code', 'Unknown Code')
                record['awarding_sub_agency'] = safe_extract('Awarding Sub Agency', 'Unknown Sub Agency')
                record['awarding_sub_agency_code'] = safe_extract('Awarding Sub Agency Code', 'Unknown Code')
                record['funding_agency'] = safe_extract('Funding Agency', 'Unknown Funding Agency')
                record['funding_agency_code'] = safe_extract('Funding Agency Code', 'Unknown Code')
                record['funding_sub_agency'] = safe_extract('Funding Sub Agency', 'Unknown Sub Agency')
                record['funding_sub_agency_code'] = safe_extract('Funding Sub Agency Code', 'Unknown Code')

                # Geographic Data (3 fields)
                record['place_of_performance_state_code'] = safe_extract('Place of Performance State Code', 'Unknown')
                record['place_of_performance_country_code'] = safe_extract('Place of Performance Country Code', 'USA')
                record['place_of_performance_zip5'] = safe_extract('Place of Performance Zip5', 'Unknown')

                # Contract/Award Details (varies by type, but we keep common ones)
                record['description'] = safe_extract('Description', 'No Description')
                record['contract_award_type'] = safe_extract('Contract Award Type', 'N/A')

                # Industry Classification (4 fields)
                record['naics_code'] = safe_extract('naics_code', 'Unknown')
                record['naics_description'] = safe_extract('naics_description', 'Unknown')
                record['psc_code'] = safe_extract('psc_code', 'Unknown')
                record['psc_description'] = safe_extract('psc_description', 'Unknown')

                # Date Fields (4 fields)
                record['last_modified_date'] = safe_extract('Last Modified Date', 'Unknown Date')
                record['base_obligation_date'] = safe_extract('Base Obligation Date', 'Unknown Date')
                record['start_date'] = safe_extract('Start Date', 'Unknown Date')
                record['end_date'] = safe_extract('End Date', 'Unknown Date')

                # Add timestamp
                try:
                    record['fetched_at'] = datetime.now().isoformat()
                except Exception as e:
                    record['fetched_at'] = "Error - Timestamp"
                    print(f"Record {i+1}: Error adding timestamp: {str(e)}")

                # Only add record if we have essential fields
                essential_fields = ['award_id', 'recipient_name']
                has_essential = all(
                    record.get(field) and
                    record.get(field) not in [f'UNKNOWN_ID_{i+1}', 'Unknown Recipient', '', None]
                    for field in essential_fields
                )

                if has_essential:
                    records.append(record)
                    processed_count += 1
                else:
                    error_count += 1
                    print(f"Record {i+1}: Missing essential fields, skipping")

            except Exception as e:
                error_count += 1
                print(f"Critical error processing record {i+1}: {str(e)}")
                print(f"    Raw record data: {str(item)[:200]}...")
                continue

        # Create DataFrame with comprehensive error handling
        try:
            if records:
                df = pd.DataFrame(records)
                
                print("Analyzing data quality before cleaning...")
                self.debug_data_quality(df)

                # Additional data cleaning
                df = self.clean_dataframe(df)

                print(f"Successfully processed {processed_count} records")
                print(f"Final dataset contains {len(df.columns)} useful columns (reduced from 46 original columns)")
                if error_count > 0:
                    print(f"Skipped {error_count} records due to errors")

                # Report field-specific errors only if significant
                significant_errors = {k: v for k, v in field_errors.items() if v > len(results) * 0.1}
                if significant_errors:
                    print("Significant Field Error Summary:")
                    for field, count in significant_errors.items():
                        print(f"    • {field}: {count} errors")

                # Validate the processed data
                if self.validate_processed_data(df):
                    self.print_data_summary(df)
                    return df
                else:
                    print("Data validation failed - returning empty DataFrame")
                    return pd.DataFrame()
            else:
                print("No valid records could be processed")
                return pd.DataFrame()

        except Exception as e:
            print(f"Critical error creating DataFrame: {str(e)}")
            return pd.DataFrame()
     
    

    def clean_dataframe(self, df):
        """Clean and validate the DataFrame with less aggressive filtering"""
        if df.empty:
            return df

        print("Cleaning data with improved logic...")

        initial_count = len(df)
        print(f"Starting with {initial_count} records")

        # Step 1: Remove records with completely empty recipient names
        empty_recipients_before = len(df)
        df = df[df['recipient_name'].str.strip() != '']
        empty_recipients_removed = empty_recipients_before - len(df)
        if empty_recipients_removed > 0:
            print(f"Removed {empty_recipients_removed} records with empty recipient names")

        # Step 2: Handle negative amounts more carefully
        negative_amounts_before = len(df)
        # Instead of removing all negative amounts, just flag them
        negative_count = (df['award_amount'] < 0).sum()
        if negative_count > 0:
            print(f"Found {negative_count} records with negative amounts (keeping them)")
            # Only remove if amount is exactly 0 and looks like missing data
            df = df[~((df['award_amount'] == 0) & (df['recipient_name'].str.contains('Unknown', case=False, na=False)))]
        
        negative_amounts_removed = negative_amounts_before - len(df)
        if negative_amounts_removed > 0:
            print(f"Removed {negative_amounts_removed} records with zero amounts and unknown recipients")

        # Step 3: Handle duplicates more intelligently
        duplicates_before = len(df)
        
        # First check how many duplicates we have
        duplicate_count = df.duplicated(subset=['award_id']).sum()
        print(f"Found {duplicate_count} duplicate award IDs")
        
        if duplicate_count > 0:
            # Keep the record with the highest award amount for each duplicate ID
            df = df.sort_values('award_amount', ascending=False)
            df = df.drop_duplicates(subset=['award_id'], keep='first')
            
        duplicates_removed = duplicates_before - len(df)
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate records (kept highest amount for each ID)")

        # Step 4: Sort by award amount (largest first)
        df = df.sort_values('award_amount', ascending=False)

        # Step 5: Reset index
        df = df.reset_index(drop=True)

        final_count = len(df)
        total_removed = initial_count - final_count
        
        if total_removed > 0:
            print(f"Data cleaning summary:")
            print(f"    • Started with: {initial_count} records")
            print(f"    • Removed: {total_removed} records ({(total_removed/initial_count)*100:.1f}%)")
            print(f"    • Final dataset: {final_count} records")
            
            # Warn if we lost too much data
            if total_removed > initial_count * 0.5:  # More than 50% lost
                print(f"WARNING: Lost {(total_removed/initial_count)*100:.1f}% of data during cleaning")
                print(f"    This might indicate data quality issues or overly aggressive cleaning")
        else:
            print(f"No cleaning needed: {final_count} records maintained")

        return df
    def debug_data_quality(self, df):
        """Debug why so much data is being removed"""
        if df.empty:
            print("DataFrame is empty - nothing to debug")
            return
            
        print("DEBUGGING DATA QUALITY ISSUES")
        print("=" * 50)
        
        total_records = len(df)
        print(f"Total records to analyze: {total_records}")
        
        # Check award_id issues
        print("\nAward ID Analysis:")
        empty_ids = df['award_id'].isna().sum()
        duplicate_ids = df['award_id'].duplicated().sum()
        unique_ids = df['award_id'].nunique()
        
        print(f"    • Empty/missing IDs: {empty_ids}")
        print(f"    • Duplicate IDs: {duplicate_ids}")
        print(f"    • Unique IDs: {unique_ids}")
        print(f"    • Expected unique ratio: {unique_ids/total_records:.2%}")
        
        # Check recipient name issues
        print("\nRecipient Name Analysis:")
        empty_recipients = (df['recipient_name'].str.strip() == '').sum()
        unknown_recipients = df['recipient_name'].str.contains('Unknown', case=False, na=False).sum()
        
        print(f"    • Empty recipient names: {empty_recipients}")
        print(f"    • 'Unknown' recipients: {unknown_recipients}")
        
        # Check award amount issues
        print("\nAward Amount Analysis:")
        zero_amounts = (df['award_amount'] == 0).sum()
        negative_amounts = (df['award_amount'] < 0).sum()
        very_large = (df['award_amount'] > 1e12).sum()
        
        print(f"    • Zero amounts: {zero_amounts}")
        print(f"    • Negative amounts: {negative_amounts}")
        print(f"    • Very large amounts (>$1T): {very_large}")
        
        # Show sample of duplicate IDs
        if duplicate_ids > 0:
            print("\nSample Duplicate Award IDs:")
            dup_ids = df[df['award_id'].duplicated(keep=False)]['award_id'].value_counts().head(5)
            for award_id, count in dup_ids.items():
                print(f"    • {award_id}: appears {count} times")
                
            # Show details of first duplicate
            first_dup_id = dup_ids.index[0]
            dup_records = df[df['award_id'] == first_dup_id][['award_id', 'recipient_name', 'award_amount']].head(3)
            print(f"\nDetails for duplicate ID '{first_dup_id}':")
            for idx, row in dup_records.iterrows():
                print(f"    • Recipient: {row['recipient_name']}, Amount: ${row['award_amount']:,.2f}")
        
        print("=" * 50)


    def validate_processed_data(self, df):
        """Validate the quality of processed data with correct field names"""
        if df.empty:
            print("Validation failed: DataFrame is empty")
            return False

        print("Validating processed data quality...")

        # Check required columns exist (core fields that must be present)
        required_columns = [
            'award_id', 'recipient_name', 'award_amount',
            'awarding_agency', 'fetched_at'
        ]

        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            print(f"Validation failed: Missing critical columns: {missing_columns}")
            return False

        # Check for data quality issues
        total_records = len(df)
        issues = []

        # Check for empty recipient names
        empty_recipients = df[df['recipient_name'].str.strip() == ''].shape[0]
        if empty_recipients > 0:
            issues.append(f"{empty_recipients} records with empty recipient names")

        # Check for zero or negative amounts
        invalid_amounts = df[df['award_amount'] <= 0].shape[0]
        if invalid_amounts > 0:
            issues.append(f"{invalid_amounts} records with zero or negative award amounts")

        # Check for extremely large amounts (potential data errors)
        very_large_amounts = df[df['award_amount'] > 1e12].shape[0]  # > 1 trillion
        if very_large_amounts > 0:
            issues.append(f"{very_large_amounts} records with suspiciously large amounts (>$1T)")

        # Check for empty agency names
        empty_agencies = df[df['awarding_agency'].str.strip() == ''].shape[0]
        if empty_agencies > 0:
            issues.append(f"{empty_agencies} records with empty agency names")

        # Check for duplicate award IDs
        duplicate_ids = df.duplicated(subset=['award_id']).sum()
        if duplicate_ids > 0:
            issues.append(f"{duplicate_ids} duplicate award IDs found")

        # Report validation results
        if issues:
            print("Data quality issues found:")
            for issue in issues:
                print(f"    • {issue}")

            # Decide if issues are acceptable
            critical_issues = empty_recipients + duplicate_ids
            if critical_issues > total_records * 0.1:  # More than 10% critical issues
                print("Validation failed: Too many critical data quality issues")
                return False
            else:
                print("Validation passed: Issues found but within acceptable limits")
                return True
        else:
            print("Validation passed: No data quality issues found")
            return True
    
    def print_data_summary(self, df):
        """Print a comprehensive summary of the processed data with useful columns only"""
        if df.empty:
            print("Data Summary: No data to summarize")
            return

        print("Data Summary (Useful Columns Only):")
        print(f"    Total Records: {len(df):,}")
        print(f"    Total Columns: {len(df.columns)} (optimized from 46 original)")
        print(f"    Total Award Amount: ${df['award_amount'].sum():,.2f}")
        print(f"    Average Award: ${df['award_amount'].mean():,.2f}")
        print(f"    Largest Award: ${df['award_amount'].max():,.2f}")
        print(f"    Smallest Award: ${df['award_amount'].min():,.2f}")
        print(f"    Unique Recipients: {df['recipient_name'].nunique():,}")
        print(f"    Unique Agencies: {df['awarding_agency'].nunique():,}")

        # Show COVID-19 and Infrastructure spending totals
        covid_obligations = df['covid_19_obligations'].sum()
        covid_outlays = df['covid_19_outlays'].sum()
        infra_obligations = df['infrastructure_obligations'].sum()
        infra_outlays = df['infrastructure_outlays'].sum()
        
        if covid_obligations > 0 or covid_outlays > 0:
            print(f"\nCOVID-19 Spending:")
            print(f"    Obligations: ${covid_obligations:,.2f}")
            print(f"    Outlays: ${covid_outlays:,.2f}")
            
        if infra_obligations > 0 or infra_outlays > 0:
            print(f"\nInfrastructure Spending:")
            print(f"    Obligations: ${infra_obligations:,.2f}")
            print(f"    Outlays: ${infra_outlays:,.2f}")

        # Show top 5 recipients by total award amount
        if len(df) > 0:
            print("\nTop 5 Recipients by Total Award Amount:")
            top_recipients = df.groupby('recipient_name')['award_amount'].sum().sort_values(ascending=False).head(5)
            for i, (recipient, amount) in enumerate(top_recipients.items(), 1):
                print(f"    {i}. {recipient}: ${amount:,.2f}")

        # Show distribution by agency
        if 'awarding_agency' in df.columns:
            print("\nTop 5 Awarding Agencies:")
            agency_counts = df['awarding_agency'].value_counts()
            for agency, count in agency_counts.head(5).items():
                if agency not in ['Unknown Agency', '']:
                    print(f"    • {agency}: {count:,} awards")

        # Show geographic distribution (if available)
        if 'place_of_performance_state_code' in df.columns:
            print("\nTop 5 States by Number of Awards:")
            state_counts = df['place_of_performance_state_code'].value_counts()
            for state, count in state_counts.head(5).items():
                if state not in ['Unknown', '', 'Unknown State']:
                    print(f"    • {state}: {count:,} awards")

        # Show industry distribution if available
        if 'naics_description' in df.columns:
            print("\nTop 5 Industries (NAICS):")
            industry_counts = df['naics_description'].value_counts()
            for industry, count in industry_counts.head(5).items():
                if industry not in ['Unknown', '']:
                    print(f"    • {industry}: {count:,} awards")

    def validate_api_response(self, response_data):
        """Check if the API response is valid and usable"""
        print("Debug: Starting response validation...")

        if response_data is None:
            print("Validation failed: No response data")
            return False

        # Check if response has the expected structure
        if not isinstance(response_data, dict):
            print("Validation failed: Response is not a dictionary")
            print(f"Debug: Response type: {type(response_data)}")
            return False

        print(f"Debug: Response is a dict with keys: {list(response_data.keys())}")

        # Check if results key exists
        if 'results' not in response_data:
            print("Validation failed: No 'results' key in response")
            print(f"Debug: Available keys: {list(response_data.keys())}")
            return False

        # Check if results is a list
        if not isinstance(response_data['results'], list):
            print("Validation failed: 'results' is not a list")
            print(f"Debug: Results type: {type(response_data['results'])}")
            return False

        # Check if we got any data
        results = response_data['results']
        if len(results) == 0:
            print("Warning: Response contains no spending records")
            # This is not necessarily a failure, so we return True but with a warning.
            # The calling function can decide how to handle an empty but valid response.
            return True

        print(f"Debug: Found {len(results)} results")

        # Check for at least some basic fields (using actual API field names)
        basic_fields = ['Award ID', 'Recipient Name', 'Award Amount']
        first_record = results[0]
        print(f"Debug: First record has {len(first_record)} fields")

        found_fields = []
        for field in basic_fields:
            if field in first_record:
                found_fields.append(field)

        if len(found_fields) == 0:
            print("Validation failed: No basic fields found")
            print(f"Debug: Expected any of: {basic_fields}")
            print(f"Debug: Found fields: {list(first_record.keys())}")
            return False
        else:
            print(f"Validation successful: {len(results)} records with {len(found_fields)} basic fields")
            print(f"Debug: Found basic fields: {found_fields}")
            return True

    def save_data(self, df, save_format='both'):
        """Save the data to files with comprehensive validation checks"""
        if df.empty:
            print("Cannot save empty DataFrame")
            return False

        # Step 1: Validate storage environment BEFORE attempting to save
        if not self.validate_storage_environment():
            print("Storage environment validation failed - cannot save")
            return False

        try:
            # Create timestamp for file names
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Define file paths
            csv_filename = f"spending_data_useful_{timestamp}.csv"
            json_filename = f"spending_data_useful_{timestamp}.json"

            csv_path = os.path.join(self.data_dir, csv_filename)
            json_path = os.path.join(self.data_dir, json_filename)

            # Also create "latest" versions without timestamp
            latest_csv_path = os.path.join(self.data_dir, "spending_data_useful_latest.csv")
            latest_json_path = os.path.join(self.data_dir, "spending_data_useful_latest.json")

            print(f"Saving {len(df)} records with {len(df.columns)} useful columns to local files...")

            saved_files = []

            # Save as CSV (always save CSV as it's most compatible)
            if save_format in ['csv', 'both']:
                try:
                    print("Saving CSV files...")

                    # Save timestamped version
                    df.to_csv(csv_path, index=False, encoding='utf-8')
                    print(f"CSV saved: {csv_filename}")
                    saved_files.append(csv_path)

                    # Validate CSV immediately after saving
                    is_valid, message = self.check_file_integrity(csv_path)
                    if not is_valid:
                        print(f"CSV validation failed: {message}")
                        return False
                    else:
                        print(f"CSV integrity verified: {message}")

                    # Save latest version (overwrite previous)
                    df.to_csv(latest_csv_path, index=False, encoding='utf-8')
                    print(f"Latest CSV updated: spending_data_useful_latest.csv")

                    # Validate latest CSV
                    is_valid, message = self.check_file_integrity(latest_csv_path)
                    if not is_valid:
                        print(f"Latest CSV validation failed: {message}")
                        return False

                except Exception as e:
                    print(f"Error saving CSV: {str(e)}")
                    return False

            # Save as JSON (for more complex data structures)
            if save_format in ['json', 'both']:
                try:
                    print("Saving JSON files...")

                    # Convert DataFrame to records format for JSON
                    records = df.to_dict('records')

                    # Add comprehensive metadata
                    json_data = {
                        "metadata": {
                            "total_records": len(df),
                            "total_columns": len(df.columns),
                            "saved_at": datetime.now().isoformat(),
                            "data_source": "USAspending.gov API",
                            "optimization": "Contains only useful columns (30 out of 46 original)",
                            "total_amount": float(df['award_amount'].sum()),
                            "average_amount": float(df['award_amount'].mean()),
                            "largest_amount": float(df['award_amount'].max()),
                            "smallest_amount": float(df['award_amount'].min()),
                            "unique_recipients": int(df['recipient_name'].nunique()),
                            "unique_agencies": int(df['awarding_agency'].nunique()),
                            "covid_19_total": float(df['covid_19_obligations'].sum() + df['covid_19_outlays'].sum()),
                            "infrastructure_total": float(df['infrastructure_obligations'].sum() + df['infrastructure_outlays'].sum()),
                            "file_format_version": "2.0",
                            "columns": list(df.columns)
                        },
                        "records": records
                    }

                    # Save timestamped version
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    print(f"JSON saved: {json_filename}")
                    saved_files.append(json_path)

                    # Validate JSON immediately after saving
                    is_valid, message = self.check_file_integrity(json_path)
                    if not is_valid:
                        print(f"JSON validation failed: {message}")
                        return False
                    else:
                        print(f"JSON integrity verified: {message}")

                    # Save latest version
                    with open(latest_json_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    print(f"Latest JSON updated: spending_data_useful_latest.json")

                    # Validate latest JSON
                    is_valid, message = self.check_file_integrity(latest_json_path)
                    if not is_valid:
                        print(f"Latest JSON validation failed: {message}")
                        return False

                except Exception as e:
                    print(f"Error saving JSON: {str(e)}")
                    return False

            # Create backup/versioning system
            self.create_backup_versions()

            # Final comprehensive validation of all saved files
            if self.validate_saved_files(saved_files):
                print(f"Successfully saved and validated {len(saved_files)} files")
                print(f"Files saved in: {self.data_dir}")
                print(f"Optimization: Reduced from 46 to {len(df.columns)} columns")

                # Log successful save operation
                self.log_successful_save(df, saved_files)

                return True
            else:
                print("Final file validation failed")
                return False

        except Exception as e:
            print(f"Unexpected error during save: {str(e)}")
            print(f"Debug: {traceback.format_exc()}")
            return False

    def log_successful_save(self, df, saved_files):
        """Log details about successful save operations"""
        try:
            log_file_path = os.path.join(self.data_dir, "save_operations.log")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n[{timestamp}] Successful Save Operation (Optimized)\n")
                log_file.write("=" * 50 + "\n")
                log_file.write(f"Records saved: {len(df)}\n")
                log_file.write(f"Columns saved: {len(df.columns)} (optimized from 46)\n")
                log_file.write(f"Total award amount: ${df['award_amount'].sum():,.2f}\n")
                log_file.write(f"COVID-19 spending: ${df['covid_19_obligations'].sum() + df['covid_19_outlays'].sum():,.2f}\n")
                log_file.write(f"Infrastructure spending: ${df['infrastructure_obligations'].sum() + df['infrastructure_outlays'].sum():,.2f}\n")
                log_file.write("Files created:\n")
                for file_path in saved_files:
                    file_size = os.path.getsize(file_path)
                    log_file.write(f"  - {os.path.basename(file_path)}: {file_size:,} bytes\n")
                log_file.write("-" * 50 + "\n")

            print("Save operation logged to: save_operations.log")

        except Exception as e:
            print(f"Could not write save log: {str(e)}")

    def validate_storage_environment(self):
        """Verify file write permissions and available disk space before saving"""
        try:
            print("Validating storage environment...")

            # Check if data directory exists and is writable
            if not os.path.exists(self.data_dir):
                print(f"Creating data directory: {self.data_dir}")
                os.makedirs(self.data_dir, exist_ok=True)

            # Test write permissions
            test_file_path = os.path.join(self.data_dir, "temp_write_test.txt")
            try:
                with open(test_file_path, 'w') as f:
                    f.write("test")
                os.remove(test_file_path)
                print("Write permissions confirmed")
            except Exception as e:
                print(f"Write permission error: {str(e)}")
                return False

            # Check available disk space
            try:
                total, used, free = shutil.disk_usage(self.data_dir)
                free_mb = free // (1024 * 1024)  # Convert to MB
                print(f"Available disk space: {free_mb:,} MB")

                # Warn if less than 100MB available
                if free_mb < 100:
                    print("Warning: Low disk space (less than 100MB available)")
                else:
                    print("Sufficient disk space available")

            except Exception as e:
                print(f"Could not check disk space: {str(e)}")

            return True

        except Exception as e:
            print(f"Storage environment validation failed: {str(e)}")
            return False

    def validate_saved_files(self, file_paths):
        """Enhanced validation that saved files exist and are properly formatted"""
        try:
            print("Validating saved files...")
            all_valid = True
            validation_results = {}

            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                validation_results[file_name] = {}

                # Check if file exists
                if not os.path.exists(file_path):
                    print(f"File not found: {file_name}")
                    validation_results[file_name]['exists'] = False
                    all_valid = False
                    continue
                else:
                    validation_results[file_name]['exists'] = True

                # Check file size
                file_size = os.path.getsize(file_path)
                validation_results[file_name]['size_bytes'] = file_size

                if file_size == 0:
                    print(f"File is empty: {file_name}")
                    validation_results[file_name]['valid_size'] = False
                    all_valid = False
                    continue
                else:
                    validation_results[file_name]['valid_size'] = True
                    print(f"{file_name}: {file_size:,} bytes")

                # Validate file content based on extension
                try:
                    if file_path.endswith('.csv'):
                        # Comprehensive CSV validation
                        validation_results[file_name]['format'] = 'CSV'

                        # Try to read entire CSV
                        test_df = pd.read_csv(file_path)
                        validation_results[file_name]['rows'] = len(test_df)
                        validation_results[file_name]['columns'] = len(test_df.columns)

                        if test_df.empty:
                            print(f"CSV file contains no data: {file_name}")
                            validation_results[file_name]['has_data'] = False
                            all_valid = False
                        else:
                            print(f"CSV validated: {file_name} ({len(test_df):,} rows, {len(test_df.columns)} columns)")
                            validation_results[file_name]['has_data'] = True

                            # Check for required columns in CSV
                            required_csv_columns = ['award_id', 'recipient_name', 'award_amount']
                            missing_cols = [col for col in required_csv_columns if col not in test_df.columns]
                            if missing_cols:
                                print(f"CSV missing required columns: {missing_cols}")
                                validation_results[file_name]['has_required_columns'] = False
                            else:
                                validation_results[file_name]['has_required_columns'] = True

                    elif file_path.endswith('.json'):
                        # Comprehensive JSON validation
                        validation_results[file_name]['format'] = 'JSON'

                        # Try to read and parse JSON
                        with open(file_path, 'r', encoding='utf-8') as f:
                            test_data = json.load(f)

                        if not test_data:
                            print(f"JSON file appears empty: {file_name}")
                            validation_results[file_name]['has_data'] = False
                            all_valid = False
                        else:
                            # Check JSON structure
                            if isinstance(test_data, dict) and 'records' in test_data:
                                records_count = len(test_data['records'])
                                validation_results[file_name]['records_count'] = records_count
                                validation_results[file_name]['has_metadata'] = 'metadata' in test_data

                                print(f"JSON validated: {file_name} ({records_count:,} records)")
                                validation_results[file_name]['has_data'] = True

                                # Validate metadata if present
                                if 'metadata' in test_data:
                                    metadata = test_data['metadata']
                                    print(f"Metadata: {metadata.get('total_records', 'Unknown')} records, {metadata.get('total_columns', 'Unknown')} columns")
                                    if 'optimization' in metadata:
                                        print(f"Optimization: {metadata['optimization']}")
                            else:
                                print(f"JSON structure unexpected: {file_name}")
                                validation_results[file_name]['has_data'] = True

                except Exception as e:
                    print(f"Cannot read/validate file {file_name}: {str(e)}")
                    validation_results[file_name]['read_error'] = str(e)
                    all_valid = False

            # Print validation summary
            if all_valid:
                print("All files validated successfully")
            else:
                print("Some file validation issues found")

            # Store validation results for logging
            self.log_validation_results(validation_results)

            return all_valid

        except Exception as e:
            print(f"Error during file validation: {str(e)}")
            return False

    def log_validation_results(self, validation_results):
        """Log detailed validation results to a log file"""
        try:
            log_file_path = os.path.join(self.data_dir, "file_validation.log")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n[{timestamp}] File Validation Results (Optimized):\n")
                log_file.write("=" * 50 + "\n")

                for file_name, results in validation_results.items():
                    log_file.write(f"File: {file_name}\n")
                    for key, value in results.items():
                        log_file.write(f"  {key}: {value}\n")
                    log_file.write("-" * 30 + "\n")

            print("Validation results logged to: file_validation.log")

        except Exception as e:
            print(f"Could not write validation log: {str(e)}")

    def check_file_integrity(self, file_path):
        """Check the integrity of a specific saved file"""
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"

            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "File is empty"

            # Try to read the file completely
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                if df.empty:
                    return False, "CSV contains no data"
                return True, f"Valid CSV with {len(df)} rows, {len(df.columns)} columns"

            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not data:
                    return False, "JSON contains no data"
                return True, f"Valid JSON with {len(data.get('records', []))} records"

            return True, "File exists and is readable"

        except Exception as e:
            return False, f"File integrity check failed: {str(e)}"

    def create_backup_versions(self):
        """Create backup/versioning for optimized data files"""
        try:
            # Create backups directory if it doesn't exist
            backup_dir = os.path.join(self.data_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)

            # Files to backup (updated for optimized versions)
            files_to_backup = [
                "spending_data_useful_latest.csv",
                "spending_data_useful_latest.json"
            ]

            for filename in files_to_backup:
                source_path = os.path.join(self.data_dir, filename)
                if os.path.exists(source_path):
                    # Create backup with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_filename = f"backup_{timestamp}_{filename}"
                    backup_path = os.path.join(backup_dir, backup_filename)

                    # Copy file to backup location
                    shutil.copy2(source_path, backup_path)
                    print(f"Backup created: {backup_filename}")

            # Clean up old backups (keep only last 10)
            self.cleanup_old_backups(backup_dir)

        except Exception as e:
            print(f"Warning: Could not create backups: {str(e)}")

    def cleanup_old_backups(self, backup_dir, keep_count=10):
        """Keep only the most recent backup files"""
        try:
            # Get all backup files
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.startswith("backup_"):
                    file_path = os.path.join(backup_dir, filename)
                    backup_files.append((filename, os.path.getmtime(file_path)))

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups
            if len(backup_files) > keep_count:
                files_to_remove = backup_files[keep_count:]
                print(f"Cleaning up {len(files_to_remove)} old backups...")
                for filename, _ in files_to_remove:
                    file_path = os.path.join(backup_dir, filename)
                    os.remove(file_path)

        except Exception as e:
            print(f"Warning: Could not cleanup old backups: {str(e)}")


def main():
    """Main execution function with user-friendly interface and progress indicators"""
    print("=" * 70)
    print("OPTIMIZED FEDERAL SPENDING DATA COLLECTOR")
    print("=" * 70)
    print("This tool collects federal spending data from USAspending.gov")
    print("OPTIMIZED: Fetches only 30 useful columns (instead of 46)")
    print("Data will be saved as both CSV and JSON files")
    print("")

    # Initialize collector
    try:
        print("Step 1/4: Initializing optimized data collector...")
        collector = SimpleCollector()
        print("Data collector initialized successfully")
    except Exception as e:
        print(f"Failed to initialize collector: {str(e)}")
        return False

    # Get user preferences
    print("\n" + "-" * 40)
    print("CONFIGURATION OPTIONS")
    print("-" * 40)

    # Award type selection
    award_groups = {
        '1': ('contracts', 'Federal Contracts (A, B, C, D)'),
        '2': ('grants', 'Grants & Assistance (02, 03, 04, 05)'),
        '3': ('direct_payments', 'Direct Payments (06, 10)'),
        '4': ('loans', 'Loans (07, 08)'),
        '5': ('other', 'Other Awards (09, 11, -1)'),
        '6': ('all', 'All Award Types (separate requests)')
    }

    print("Available award types:")
    for key, (group, description) in award_groups.items():
        print(f"    {key}. {description}")

    # Use DATA_LIMIT from config
    selected_group = 'contracts'  
    limit = DATA_LIMIT

    print(f"\nSelected: {award_groups['1'][1]}")
    print(f"Records to fetch: {limit}")
    print(f"Optimization: Will fetch only 30 useful columns")

    # Data collection with pagination
    print(f"\nStep 2/4: Collecting {selected_group} data with pagination...")
    print("-" * 40)

    try:
        print("Connecting to USAspending.gov API with pagination support...")
        
        # Use pagination to get more than 100 records
        data = collector.fetch_spending_data_with_pagination(
            total_limit=limit, 
            award_group=selected_group
        )

        if not data:
            print("No data received from API with pagination")

            # Try alternative award type with pagination
            print(f"\nTrying grants as alternative with pagination...")
            data = collector.fetch_spending_data_with_pagination(
                total_limit=limit, 
                award_group='grants'
            )

            if not data:
                print("No data available from any award type with pagination")
                return False
            else:
                selected_group = 'grants'
                print(f"Successfully retrieved {selected_group} data with pagination")
        else:
            print("Data retrieved successfully with pagination")

    except Exception as e:
        print(f"Data collection failed: {str(e)}")
        return False

    # Data processing with progress indicators
    print(f"\nStep 3/4: Processing data...")
    print("-" * 40)

    try:
        print("Converting raw data to structured format with useful columns...")
        df = collector.process_to_dataframe(data)

        if df.empty:
            print("No valid data could be processed")
            return False
        else:
            print(f"Successfully processed {len(df)} records with {len(df.columns)} useful columns")

    except Exception as e:
        print(f"Data processing failed: {str(e)}")
        return False

    # Data saving with progress indicators
    print(f"\nStep 4/4: Saving optimized data to files...")
    print("-" * 40)

    try:
        print("Saving to CSV and JSON formats...")
        save_success = collector.save_data(df, save_format='both')

        if save_success:
            print("Data saved successfully")
        else:
            print("Data saving failed")
            return False

    except Exception as e:
        print(f"Data saving failed: {str(e)}")
        return False

    # Success summary
    print("\n" + "=" * 70)
    print("OPTIMIZED DATA COLLECTION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print(f"Records collected: {len(df):,}")
    print(f"Columns optimized: {len(df.columns)} ")
    print(f"Total award value: ${df['award_amount'].sum():,.2f}")
    print(f"COVID-19 spending: ${df['covid_19_obligations'].sum() + df['covid_19_outlays'].sum():,.2f}")
    print(f"Infrastructure spending: ${df['infrastructure_obligations'].sum() + df['infrastructure_outlays'].sum():,.2f}")
    print(f"Data saved to: {collector.data_dir}/")
    print(f"Award type: {selected_group}")

    # Show available files
    print(f"\nFiles created:")
    data_files = []
    for filename in os.listdir(collector.data_dir):
        if filename.startswith('spending_data_useful') and filename.endswith(('.csv', '.json')):
            file_path = os.path.join(collector.data_dir, filename)
            file_size = os.path.getsize(file_path)
            data_files.append((filename, file_size))

    for filename, size in sorted(data_files, reverse=True)[:4]:  # Show newest 4 files
        print(f"    {filename} ({size:,} bytes)")

   

    print("\n" + "=" * 70)
    return True

def display_help():
    """Display help information about using the optimized data collector"""
    help_text = """
OPTIMIZED FEDERAL SPENDING DATA COLLECTOR - HELP
════════════════════════════════════════════════════

OVERVIEW:
This optimized tool collects federal spending data from the USAspending.gov API
and saves only the 30 most useful columns (out of 46 original) in CSV and JSON formats.

OPTIMIZATION BENEFITS:
• 35% fewer columns (30 vs 46)
• Removes all "Unknown" value fields
• Faster processing and smaller file sizes
• Focus on analytically useful data only

USEFUL COLUMNS INCLUDED:
Financial (5): award_amount, covid_19_obligations, covid_19_outlays, 
             infrastructure_obligations, infrastructure_outlays
Recipient (4): award_id, recipient_name, recipient_id, recipient_uei  
Agency (8): awarding_agency, awarding_agency_code, awarding_sub_agency,
           awarding_sub_agency_code, funding_agency, funding_agency_code,
           funding_sub_agency, funding_sub_agency_code
Geographic (3): place_of_performance_state_code, place_of_performance_country_code,
               place_of_performance_zip5
Contract Details (6): description, contract_award_type, naics_code, 
                     naics_description, psc_code, psc_description
Dates (4): last_modified_date, base_obligation_date, start_date, end_date

USAGE:
    python data_collector.py                # Run with default settings
    python data_collector.py --help         # Show this help message
    python data_collector.py --interactive  # Run in interactive mode
    python data_collector.py --test         # Run full test suite

OUTPUT FILES:
• spending_data_useful_latest.csv     - Always current optimized data (CSV)
• spending_data_useful_latest.json    - Always current optimized data (JSON)
• spending_data_useful_TIMESTAMP.csv  - Timestamped backup (CSV)
• spending_data_useful_TIMESTAMP.json - Timestamped backup (JSON)

For more information, visit: https://api.usaspending.gov/docs/
    """
    print(help_text)


def run_interactive_mode():
    """Run the collector in interactive mode with user choices"""
    print("INTERACTIVE MODE - OPTIMIZED VERSION")
    print("-" * 35)

    # Get award type preference
    award_groups = {
        '1': ('contracts', 'Federal Contracts'),
        '2': ('grants', 'Grants & Assistance'),
        '3': ('direct_payments', 'Direct Payments'),
        '4': ('loans', 'Loans'),
        '5': ('other', 'Other Awards'),
        '6': ('all', 'All Types (takes longer)')
    }

    print("Which type of awards would you like to collect?")
    for key, (group, description) in award_groups.items():
        print(f"    {key}. {description}")

    choice = input("\nEnter your choice (1-6) [default: 1]: ").strip()
    if not choice:
        choice = '1'

    if choice not in award_groups:
        print("Invalid choice, using contracts (default)")
        choice = '1'

    selected_group, description = award_groups[choice]
    print(f"Selected: {description}")

    # Get record limit
    try:
        limit_input = input(f"\nHow many records to fetch? [default: {DATA_LIMIT}]: ").strip()
        limit = int(limit_input) if limit_input else DATA_LIMIT
        if limit <= 0 or limit > 1000:
            print("Invalid limit, using 50 (default)")
            limit = 50
    except ValueError:
        print("Invalid number, using 50 (default)")
        limit = 50

    print(f"Will fetch {limit} records with 30 useful columns")

    # Confirm and proceed
    print(f"\nReady to collect {limit} optimized {description.lower()} records")
    proceed = input("Proceed? (y/n) [default: y]: ").strip().lower()

    if proceed in ['', 'y', 'yes']:
        return main_with_params(selected_group, limit)
    else:
        print("Operation cancelled by user")
        return False


def main_with_params(award_group='contracts', limit=DATA_LIMIT):
    """Main function with specific parameters"""
    
    collector = SimpleCollector()

    print(f"Collecting {limit} optimized {award_group} records...")

    # Collect data
    data = collector.fetch_spending_data(limit=limit, award_group=award_group)
    if not data:
        return False

    # Process data
    df = collector.process_to_dataframe(data)
    if df.empty:
        return False

    # Save data
    save_success = collector.save_data(df, save_format='both')
    return save_success


if __name__ == "__main__":
    import sys

    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h', 'help']:
            display_help()
            sys.exit(0)
        elif sys.argv[1] in ['--interactive', '-i', 'interactive']:
            success = run_interactive_mode()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        # Run main function with default settings
        print("Running optimized version with default settings...")
        print("Use --help for more options")
        print("")
        success = main()

    # Exit with appropriate code
    if success:
        print("\nOptimized program completed successfully!")
        sys.exit(0)
    else:
        print("\nProgram completed with errors!")
        print("Check the log files in the data/ directory for details")
        sys.exit(1)