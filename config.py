# API Configuration
API_BASE_URL = "https://api.usaspending.gov/api/v2"
API_TIMEOUT = 90  #  to 90 seconds for better reliability
DATA_LIMIT = 1000

# Sequential Pagination Settings (NEW)
BATCH_SIZE = 100  # Records per batch (API maximum is 100)
MAX_BATCHES = 2000  # Safety limit to prevent infinite loops (100 records × 2000 batches = 200,000 max records)
API_DELAY = 1  # Seconds to wait between requests (be respectful to API)

# File paths
DATA_DIR = "data"
CSV_FILENAME = "spending_data_unlimited.csv"  # Updated filename to reflect unlimited capability

# Dashboard settings
PAGE_TITLE = "Federal Spending Dashboard"  # Updated title
PAGE_ICON ="💰"

# Data Collection Settings (NEW)
DEFAULT_AWARD_GROUP = "contracts"  # Default award type to collect
FISCAL_YEAR_START = "2023-10-01"  # FY 2024 start date
FISCAL_YEAR_END = "2024-09-30"    # FY 2024 end date

# Progress Reporting (NEW)
PROGRESS_REPORT_INTERVAL = 10  # Report progress every N batches
SHOW_DETAILED_PROGRESS = True  # Show detailed progress information
