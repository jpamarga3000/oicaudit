import pandas as pd
import os
from datetime import datetime, timedelta
import traceback
import re # Import regex module

# --- Base Directories (Should match frontend and be easily configurable) ---
BASE_DIR = r"C:\\xampp\\htdocs\\audit_tool"
TRNM_BASE_DIR = os.path.join(BASE_DIR, "OPERATIONS", "TRNM")
SVACC_BASE_DIR = os.path.join(BASE_DIR, "OPERATIONS", "SVACC")
LNACC_BASE_DIR = os.path.join(BASE_DIR, "OPERATIONS", "LNACC")
GL_BASE_DIR = os.path.join(BASE_DIR, "ACCOUTNING", "GENERAL LEDGER") # Corrected path
AGING_BASE_DIR = os.path.join(BASE_DIR, "OPERATIONS", "AGING")
LIST_BRANCHES_PATH = os.path.join(BASE_DIR, "db", "list_branches.csv")
TRIAL_BALANCE_BASE_DIR = r"C:\\xampp\\htdocs\\audit_tool\\ACCOUTNING\\TRIAL BALANCE" # Ensure this path is defined here

# --- Caching Variables ---
_cached_summary_data = None
_last_cached_time = None
CACHE_DURATION_SECONDS = 600 # Cache data for 10 minutes (600 seconds)

# --- Helper function for reading CSVs safely with targeted column loading ---
def read_csv_safe(file_path, target_date_column=None):
    """
    Reads a CSV file into a pandas DataFrame, optionally loading only a specific date column
    and parsing it during the read operation for efficiency.
    Handles FileNotFoundError and other potential pandas errors.
    
    Args:
        file_path (str): The full path to the CSV file.
        target_date_column (str, optional): The name of the column that contains dates
                                            to be parsed. If provided, only this column
                                            will be loaded. Defaults to None (load all columns).
                                            
    Returns:
        pd.DataFrame: The loaded DataFrame, with the target_date_column parsed to datetime,
                      or None if the file is not found or an error occurs.
    """
    try:
        # Determine columns to load: just the target date column if specified
        usecols = [target_date_column] if target_date_column else None
        
        # Try reading with utf-8 first, then fall back to latin1
        try:
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False, usecols=usecols)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='latin1', low_memory=False, usecols=usecols)
        
        # Strip whitespace from column names to ensure exact matches
        df.columns = df.columns.str.strip()

        # Parse the date column if it exists in the loaded DataFrame
        if target_date_column and target_date_column in df.columns:
            # Use format='mixed' to handle various date formats (MM/DD/YYYY, MM/DD/YYYY HH:MM:SS am/pm)
            df[target_date_column] = pd.to_datetime(df[target_date_column], errors='coerce', format='mixed')
        
        return df
    except FileNotFoundError:
        # print(f"File not found: {file_path}") # Uncomment for debugging file not found
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        # traceback.print_exc() # Uncomment for detailed error traceback
        return None

# --- Date Formatting Helper ---
def format_date_range(start_date, end_date):
    """
    Formats a start and end date into a 'MM/DD/YYYY to MM/DD/YYYY' string.
    Returns '-' if dates are invalid.
    """
    if pd.isna(start_date) or pd.isna(end_date):
        return "-"
    try:
        # Format to MM/DD/YYYY
        start_str = start_date.strftime("%m/%d/%Y")
        end_str = end_date.strftime("%m/%d/%Y")
        return f"{start_str} to {end_str}"
    except AttributeError: # If not a datetime object
        return "-"
    except Exception as e:
        print(f"Error formatting date range: {e}")
        return "-"

def format_single_date(date_obj):
    """
    Formats a single date into 'MM/DD/YYYY' string.
    Returns '-' if date is invalid.
    """
    if pd.isna(date_obj):
        return "-"
    try:
        return date_obj.strftime("%m/%d/%Y")
    except AttributeError: # If not a datetime object
        return "-"
    except Exception as e:
        print(f"Error formatting single date: {e}")
        return "-"

# --- New Helper for flexible branch name matching in regex ---
def create_flexible_branch_regex_pattern(branch_name_from_list):
    """
    Creates a regex-escaped string for a branch name that can match
    either spaces or underscores in the filename/folder name.
    e.g., "EL SALVADOR" -> "EL[ _]SALVADOR"
    """
    # Escape special characters, then replace escaped spaces with [ _]
    escaped_name = re.escape(branch_name_from_list)
    flexible_name = escaped_name.replace(r'\ ', r'[ _]') # Replace escaped space with [ _]
    return flexible_name.upper() # Ensure uppercase for consistent matching


# --- Main processing functions for each data type ---

def get_trnm_date_range(branch_name):
    """
    Gets the oldest 'date from' and latest 'date to' from TRNM CSV filenames for a given branch.
    Filename format: BRANCH (3CHAR) TYPE (LN/DEP) CATEGORY - MM-DD-YYYY TO MM-DD-YYYY_part_X.csv
    Example: ELS LN CATEGORY - 01-01-2023 TO 01-31-2023_part_1.csv
    """
    # Normalize branch name for folder lookup (replace spaces with underscores)
    normalized_branch_name_for_folder = branch_name.replace(' ', '_').upper()
    branch_path = os.path.join(TRNM_BASE_DIR, normalized_branch_name_for_folder)
    
    if not os.path.isdir(branch_path):
        return "-"

    all_start_dates = []
    all_end_dates = []
    
    # Determine the 3-character abbreviation for the filename pattern
    branch_abbr_for_filename_prefix = ""
    if branch_name.upper() == "EL SALVADOR":
        branch_abbr_for_filename_prefix = "ELS"
    elif branch_name.upper() == "DON CARLOS":
        branch_abbr_for_filename_prefix = "DON"
    else:
        # Default to the first three characters of the original branch name (cleaned for alphanumeric)
        # Assuming branch_name from list_branches is already reasonably clean
        branch_abbr_for_filename_prefix = "".join([c for c in branch_name if c.isalnum()]).upper()[:3]


    # Create a flexible regex part for the abbreviation itself, just in case (e.g. for AGORA/AGO)
    # However, the requirement is specific: ELS/DON or first 3. So simple re.escape is fine here.
    escaped_abbr_prefix = re.escape(branch_abbr_for_filename_prefix)

    # Regex to capture MM-DD-YYYY dates, matching the specific abbreviation at the start
    # Adjusted regex to account for optional "_part_X" and to use the specific abbreviation
    date_pattern = re.compile(rf'^{escaped_abbr_prefix} (?:LN|DEP) .* - (\d{{2}}-\d{{2}}-\d{{4}}) TO (\d{{2}}-\d{{2}}-\d{{4}})(?:_part_\d+)?\.csv$', re.IGNORECASE)


    for root, _, files in os.walk(branch_path): # Keep os.walk for TRNM as it might have subfolders
        for file in files:
            match = date_pattern.match(file) # Use match() to ensure pattern is at the beginning
            if match:
                try:
                    start_date_str = match.group(1)
                    end_date_str = match.group(2)
                    
                    # Convert MM-DD-YYYY to datetime objects
                    all_start_dates.append(datetime.strptime(start_date_str, "%m-%d-%Y"))
                    all_end_dates.append(datetime.strptime(end_date_str, "%m-%d-%Y"))
                except ValueError:
                    # Handle cases where date parsing fails for a specific filename
                    print(f"Warning: Could not parse date from TRNM filename: {file}")
                    continue
    
    if all_start_dates and all_end_dates:
        min_overall_date = min(all_start_dates)
        max_overall_date = max(all_end_dates)
        return format_date_range(min_overall_date, max_overall_date)
    return "-"

def get_svacc_date_range(branch_name):
    """
    Gets the latest date from SVACC CSV filenames for a given branch.
    Filename format: BRANCH - MM-DD-YYYY.csv
    Looks directly inside the SVACC_BASE_DIR, filtering by branch name in the filename.
    Example: ABC - 01-15-2023.csv (or ABC_BRANCH - 01-15-2023.csv)
    """
    base_dir = SVACC_BASE_DIR
    if not os.path.isdir(base_dir):
        return "-"

    all_dates = []
    # Create a flexible regex pattern for the branch name (e.g., EL[ _]SALVADOR)
    flexible_branch_pattern_part = create_flexible_branch_regex_pattern(branch_name)

    # Regex to capture MM-DD-YYYY date, ensuring it matches the flexible branch name at the start
    file_pattern = re.compile(rf'^{flexible_branch_pattern_part} - (\d{{2}}-\d{{2}}-\d{{4}})\.csv$', re.IGNORECASE)

    # Iterate directly through files in the base_dir, no os.walk
    found_files = os.listdir(base_dir)

    for file in found_files:
        if not file.lower().endswith('.csv'):
            continue
            
        match = file_pattern.match(file) # Use match() to ensure pattern is at the beginning of the string
        if match:
            try:
                date_str = match.group(1)
                # Convert MM-DD-YYYY to datetime object
                all_dates.append(datetime.strptime(date_str, "%m-%d-%Y"))
            except ValueError as ve:
                print(f"Warning: Could not parse date '{date_str}' from SVACC filename '{file}': {ve}")
                continue
    
    if all_dates:
        max_date = max(all_dates)
        formatted_date = format_single_date(max_date)
        return formatted_date # Return only the latest date
    else:
        return "-"

def get_lnacc_date_range(branch_name):
    """
    Gets the latest date from LNACC CSV filenames for a given branch.
    Filename format: BRANCH - MM-DD-YYYY.csv
    Looks directly inside the LNACC_BASE_DIR, filtering by branch name in the filename.
    Example: ABC - 01-15-2023.csv (or ABC_BRANCH - 01-15-2023.csv)
    """
    base_dir = LNACC_BASE_DIR
    if not os.path.isdir(base_dir):
        return "-"

    all_dates = []
    # Create a flexible regex pattern for the branch name (e.g., EL[ _]SALVADOR)
    flexible_branch_pattern_part = create_flexible_branch_regex_pattern(branch_name)

    # Regex to capture MM-DD-YYYY date, ensuring it matches the flexible branch name at the start
    file_pattern = re.compile(rf'^{flexible_branch_pattern_part} - (\d{{2}}-\d{{2}}-\d{{4}})\.csv$', re.IGNORECASE)

    # Iterate directly through files in the base_dir, no os.walk
    found_files = os.listdir(base_dir)

    for file in found_files:
        if not file.lower().endswith('.csv'):
            continue
            
        match = file_pattern.match(file) # Use match() to ensure pattern is at the beginning of the string
        if match:
            try:
                date_str = match.group(1)
                # Convert MM-DD-YYYY to datetime object
                all_dates.append(datetime.strptime(date_str, "%m-%d-%Y"))
            except ValueError as ve:
                print(f"Warning: Could not parse date '{date_str}' from LNACC filename '{file}': {ve}")
                continue
        else:
            pass # No need to print if no match
    
    if all_dates:
        max_date = max(all_dates)
        formatted_date = format_single_date(max_date)
        return formatted_date # Return only the latest date
    else:
        return "-"

def get_gl_date_range(branch_name):
    """
    Gets the oldest 'date from' and latest 'date to' from GL CSV files for a given branch.
    Filename format: BRANCH - MM-DD-YYYY (from) to MM-DD-YYYY (to).csv
    Example: ABC - 01-01-2023 to 01-31-2023.csv (or ABC_BRANCH - ...)
    """
    # Normalize branch name for folder lookup (replace spaces with underscores)
    normalized_branch_name_for_folder = branch_name.replace(' ', '_').upper()
    branch_path = os.path.join(GL_BASE_DIR, normalized_branch_name_for_folder)
    
    if not os.path.isdir(branch_path):
        return "-"

    all_start_dates = []
    all_end_dates = []
    
    # Create a flexible regex pattern for the branch name (e.g., EL[ _]SALVADOR)
    flexible_branch_pattern_part = create_flexible_branch_regex_pattern(branch_name)

    # Regex to capture MM-DD-YYYY dates for GL filename format
    # The regex pattern should match the flexible branch name at the start
    date_pattern = re.compile(rf'^{flexible_branch_pattern_part} - (\d{{2}}-\d{{2}}-\d{{4}}) to (\d{{2}}-\d{{2}}-\d{{4}})\.csv$', re.IGNORECASE)

    for root, _, files in os.walk(branch_path): # Keep os.walk for GL as it might have subfolders
        for file in files:
            match = date_pattern.match(file) # Use match() to ensure pattern is at the beginning
            if match:
                try:
                    start_date_str = match.group(1)
                    end_date_str = match.group(2)
                    
                    # Convert MM-DD-YYYY to datetime objects
                    all_start_dates.append(datetime.strptime(start_date_str, "%m-%d-%Y"))
                    all_end_dates.append(datetime.strptime(end_date_str, "%m-%d-%Y"))
                except ValueError:
                    # Handle cases where date parsing fails for a specific filename
                    print(f"Warning: Could not parse date from GL filename: {file}")
                    continue
    
    if all_start_dates and all_end_dates:
        min_overall_date = min(all_start_dates)
        max_overall_date = max(all_end_dates) # This should be max_overall_date = max(all_end_dates)
        return format_date_range(min_overall_date, max_overall_date)
    return "-"

def get_aging_date_range(branch_name):
    """
    Gets the oldest and latest DATE from AGING CSV files for a given branch.
    """
    # Normalize branch name for folder lookup (replace spaces with underscores)
    normalized_branch_name_for_folder = branch_name.replace(' ', '_').upper()
    branch_path = os.path.join(AGING_BASE_DIR, normalized_branch_name_for_folder)

    if not os.path.isdir(branch_path):
        return "-"

    all_dates = []
    for root, _, files in os.walk(branch_path):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                # Use optimized read_csv_safe to load only 'DATE'
                df = read_csv_safe(file_path, target_date_column='DATE')
                if df is not None and 'DATE' in df.columns:
                    valid_dates = df['DATE'].dropna()
                    if not valid_dates.empty:
                        all_dates.extend(valid_dates.tolist())
    
    if all_dates:
        min_date = min(all_dates)
        max_date = max(all_dates)
        return format_date_range(min_date, max_date)
    return "-"

# Import the new function from db_common.py
from backend.db_common import get_tb_latest_date

def get_database_summary_data(force_refresh=False):
    """
    Generates a summary of date ranges for various data types across all branches.
    Uses an in-memory cache to speed up repeated requests.
    
    Args:
        force_refresh (bool): If True, bypasses the cache and re-computes the data.
    """
    global _cached_summary_data, _last_cached_time

    # Check if cached data is valid and no force refresh is requested
    if not force_refresh and _cached_summary_data is not None and \
       (datetime.now() - _last_cached_time).total_seconds() < CACHE_DURATION_SECONDS:
        print("Server Log: Returning cached database summary data.")
        return _cached_summary_data

    print("Server Log: Re-computing database summary data (cache invalid or forced refresh).")
    summary_data = []
    
    # Read list of branches
    branches_df = read_csv_safe(LIST_BRANCHES_PATH)
    if branches_df is None or 'BRANCH' not in branches_df.columns:
        print(f"Error: Could not read branches from {LIST_BRANCHES_PATH}")
        return []

    branches = branches_df['BRANCH'].unique().tolist()
    
    # Add "HEAD OFFICE" if not already present, ensuring it's processed
    if "HEAD OFFICE" not in branches:
        branches.append("HEAD OFFICE")

    # Sort branches alphabetically for consistent display
    branches.sort()

    for branch in branches:
        row = {
            "BRANCH": branch, # Display original branch name from list_branches.csv
            "TRNM": get_trnm_date_range(branch),
            "SVACC": get_svacc_date_range(branch),
            "LNACC": get_lnacc_date_range(branch),
            "GL": get_gl_date_range(branch),
            "ACCLIST": "-",
            "AGING": get_aging_date_range(branch),
            "TB": get_tb_latest_date(branch), # NEW: Add Trial Balance (TB) date
        }
        summary_data.append(row)
    
    # Update cache
    _cached_summary_data = summary_data
    _last_cached_time = datetime.now()
    
    return summary_data

# For testing (can be run directly to see output in console)
if __name__ == "__main__":
    print("Running database summary process...")
    data = get_database_summary_data()
    for row in data:
        print(row)
