# audit_tool/backend/import_trnm_to_mysql.py
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import re
import traceback
from sqlalchemy import create_engine
# FIX: Import specific SQLAlchemy types
from sqlalchemy.types import VARCHAR, DATE, DECIMAL, TEXT
from dateutil.relativedelta import relativedelta

# FIX: Robustly add the project root to sys.path to enable absolute imports
# This ensures that 'backend' is recognized as a package when this script is run directly.
# It finds the directory containing 'audit_tool' and adds it.
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up to the 'audit_tool' directory (from 'audit_tool/backend/')
project_root = os.path.abspath(os.path.join(current_script_dir, '..'))
# If 'audit_tool' itself is not the project root, but rather a subdirectory of the project root,
# you might need to adjust '..' accordingly. Assuming 'audit_tool' is the root here.

# Add the directory containing the 'backend' package to sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# FIX: Changed import to get the function, not the engine object directly
from backend.db_common import get_db_connection_sqlalchemy

# --- Configuration ---
TRNM_BASE_DIR = r"C:\xampp\htdocs\audit_tool\OPERATIONS\TRNM" # Adjust if your base directory is different
# DB_TABLE_NAME is now dynamically generated per branch folder

# FIX: Define the columns with actual SQLAlchemy type objects
CSV_COLUMNS_MAPPING = {
    'TRN': VARCHAR(255),
    'ACC': VARCHAR(255),
    'TRNTYPE': VARCHAR(255),
    'TLR': VARCHAR(255),
    'LEVEL': VARCHAR(255),
    'TRNDATE': DATE,
    'TRNAMT': DECIMAL(18, 2),
    'TRNNONC': DECIMAL(18, 2),
    'TRNINT': DECIMAL(18, 2),
    'TRNTAXPEN': DECIMAL(18, 2),
    'BAL': DECIMAL(18, 2),
    'SEQ': VARCHAR(255),
    'TRNDESC': TEXT,
    'APPTYPE': VARCHAR(255),
    'Branch': VARCHAR(255)
}

# --- Helper Functions ---
def parse_filename_dates_trnm(filename):
    """
    Parses start and end dates from TRNM CSV filenames.
    Supports "MMM YYYY TO MMM YYYY.csv" and "MM-DD-YYYY TO MM-DD-YYYY.csv" formats.
    """
    # Pattern for "BRANCH_CODE TYPE_CODE CATEGORY_CODE - MMM YYYY TO MMM YYYY.csv"
    match_month_year = re.match(r'.* - (\w{3} \d{4}) TO (\w{3} \d{4})\.csv$', filename, re.IGNORECASE)
    if match_month_year:
        start_date_str = match_month_year.group(1)
        end_date_str = match_month_year.group(2)
        try:
            file_start_date = datetime.strptime(start_date_str, '%b %Y').replace(day=1)
            temp_end_date = datetime.strptime(end_date_str, '%b %Y').replace(day=1)
            file_end_date = temp_end_date + relativedelta(months=1, days=-1)
            return file_start_date, file_end_date
        except ValueError:
            return None, None
    # Pattern for "BRANCH_CODE TYPE_CODE CATEGORY_CODE - MM-DD-YYYY TO MM-DD-YYYY.csv"
    match_full_date = re.match(r'.* - (\d{2}-\d{2}-\d{4}) TO (\d{2}-\d{2}-\d{4})\.csv$', filename, re.IGNORECASE)
    if match_full_date:
        start_date_str = match_full_date.group(1)
        end_date_str = match_full_date.group(2)
        try:
            file_start_date = datetime.strptime(start_date_str, '%m-%d-%Y')
            file_end_date = datetime.strptime(end_date_str, '%m-%d-%Y')
            return file_start_date, file_end_date
        except ValueError:
            return None, None
    return None, None

def import_trnm_csv_to_mysql():
    """
    Reads all TRNM CSV files from specified directories and imports them into a MySQL table.
    Each branch folder will correspond to a new table named 'trnm_branchname'.
    Existing data in these tables will be replaced.
    """
    print(f"Starting TRNM CSV import to MySQL.")
    print(f"Source directory: {TRNM_BASE_DIR}")

    if not os.path.isdir(TRNM_BASE_DIR):
        print(f"Error: TRNM_BASE_DIR '{TRNM_BASE_DIR}' does not exist. Please check the path.")
        return

    # FIX: Call the function to get the engine object
    engine = get_db_connection_sqlalchemy()

    if engine is None: # Check if the function returned None (meaning connection failed)
        print("Error: SQLAlchemy engine is not initialized. Aborting import.")
        return

    total_files_processed = 0
    total_rows_imported = 0
    encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-8-sig']

    for branch_folder_name in os.listdir(TRNM_BASE_DIR):
        branch_path = os.path.join(TRNM_BASE_DIR, branch_folder_name)
        if not os.path.isdir(branch_path):
            continue

        # Dynamically set the table name for the current branch
        current_db_table_name = f'trnm_{branch_folder_name.lower()}'
        print(f"\nProcessing branch folder: {branch_folder_name}. Target table: {current_db_table_name}")

        # Collect all dataframes for the current branch before importing to ensure 'replace' works for the whole branch
        branch_dfs = []
        branch_rows_count = 0

        for filename in os.listdir(branch_path):
            if not filename.lower().endswith('.csv'):
                continue

            file_path = os.path.join(branch_path, filename)
            print(f"  - Reading file: {filename}")

            df = None
            read_success = False
            for encoding in encodings_to_try:
                try:
                    # Read all columns as string to prevent data type issues during initial load
                    df = pd.read_csv(file_path, encoding=encoding, dtype=str, low_memory=False)
                    read_success = True
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"    Error reading CSV file {filename} with {encoding}: {e}")
                    traceback.print_exc()
                    break # Stop trying encodings for this file if other error

            if not read_success or df is None:
                print(f"    Skipping file {filename}: Failed to read with all tried encodings or encountered an error.")
                continue
            
            # Standardize column names to uppercase
            df.columns = [col.strip().upper() for col in df.columns]

            # Ensure all columns from CSV_COLUMNS_MAPPING exist in the DataFrame.
            # If a column is missing, add it with a default empty string.
            # TRNDATE and Branch are handled specifically.
            for col_name in CSV_COLUMNS_MAPPING.keys(): # Iterate through keys of the mapping
                if col_name not in df.columns and col_name not in ['TRNDATE', 'Branch']:
                    df[col_name] = '' # Use col_name directly
                    print(f"    Warning: Column '{col_name}' not found in {filename}. Added as empty string.")
            
            # Add 'Branch' column, derived from folder name
            df['Branch'] = branch_folder_name.upper()

            # Process 'TRNDATE' column
            # Try multiple date formats for parsing
            date_formats = ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y', '%b %Y'] # Added '%b %Y' for "Jan 2008" format
            df['TRNDATE_PARSED'] = pd.NaT # Initialize with Not a Time
            
            for fmt in date_formats:
                # Only attempt to parse rows where TRNDATE_PARSED is still NaT
                mask = df['TRNDATE_PARSED'].isna()
                df.loc[mask, 'TRNDATE_PARSED'] = pd.to_datetime(df.loc[mask, 'TRNDATE'], format=fmt, errors='coerce')
            
            if df['TRNDATE_PARSED'].isna().any():
                print(f"    Warning: Some TRNDATE values in {filename} could not be parsed. These rows will be dropped.")
            
            # Drop rows where TRNDATE could not be parsed
            df.dropna(subset=['TRNDATE_PARSED'], inplace=True)
            df['TRNDATE'] = df['TRNDATE_PARSED'].dt.date # Store as date object for MySQL DATE type

            # Convert numeric columns to appropriate types
            numeric_cols = ['TRNAMT', 'TRNNONC', 'TRNINT', 'TRNTAXPEN', 'BAL']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                else:
                    df[col] = 0.0 # Add missing numeric columns as 0.0 with default value

            # Select and reorder columns to match the target MySQL table structure
            # Ensure all columns in CSV_COLUMNS_MAPPING are present in df before selecting
            # Use .reindex to ensure all target columns are present and in the correct order, filling missing with NaN
            df_to_import_single_file = df.reindex(columns=list(CSV_COLUMNS_MAPPING.keys()))
            
            # Final type conversion for SQLAlchemy, handling potential NaNs after reindexing
            for col, sql_type in CSV_COLUMNS_MAPPING.items():
                if col in df_to_import_single_file.columns:
                    if isinstance(sql_type, DECIMAL):
                        df_to_import_single_file[col] = pd.to_numeric(df_to_import_single_file[col], errors='coerce').fillna(0)
                    elif isinstance(sql_type, DATE):
                        df_to_import_single_file[col] = pd.to_datetime(df_to_import_single_file[col], errors='coerce')
                    else: # For VARCHAR, TEXT
                        df_to_import_single_file[col] = df_to_import_single_file[col].astype(str).fillna('')
            
            branch_dfs.append(df_to_import_single_file)
            branch_rows_count += len(df_to_import_single_file)
            total_files_processed += 1

        if branch_dfs:
            # Concatenate all dataframes for the current branch
            combined_branch_df = pd.concat(branch_dfs, ignore_index=True)
            try:
                # Use 'replace' to overwrite the table if it exists, otherwise create it.
                combined_branch_df.to_sql(
                    name=current_db_table_name,
                    con=engine,
                    if_exists='replace', # 'replace' to overwrite, 'append' to add
                    index=False,
                    dtype=CSV_COLUMNS_MAPPING # Specify SQL types for creation/validation
                )
                print(f"  Successfully imported {branch_rows_count} rows to table '{current_db_table_name}'.")
                total_rows_imported += branch_rows_count
            except Exception as e:
                print(f"  Error importing data for branch {branch_folder_name} to MySQL table '{current_db_table_name}': {e}")
                traceback.print_exc()
        else:
            print(f"  No valid CSV files found or processed in branch folder: {branch_folder_name}. Skipping table creation.")


    print(f"\nTRNM CSV import complete.")
    print(f"Total files processed: {total_files_processed}")
    print(f"Total rows imported: {total_rows_imported}")
    print(f"Please ensure the 'trnm_branchname' tables in MySQL have appropriate indexes for performance (e.g., on Branch, TRNDATE, ACC).")

if __name__ == '__main__':
    # This block will only run when the script is executed directly
    # You would run this script from your terminal: python audit_tool/backend/import_trnm_to_mysql.py
    import_trnm_csv_to_mysql()
