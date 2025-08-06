import pandas as pd
import os
from datetime import datetime
from sqlalchemy import create_engine, text
import traceback
import re

# --- Database Configuration ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # Your MySQL password
    'database': 'dc_req_db',
    'charset': 'utf8mb4'
}

# Define the base directory where your TRNM CSV files are located
# Each subfolder within this directory should be a branch name
TRNM_SOURCE_BASE_DIR = r"C:\ACC CLEANING\OPERATIONS\TRNM"

# Define the expected headers from your CSV and their corresponding MySQL column names
CSV_HEADERS_TO_DB_COLUMNS = {
    'TRN': 'TRN',
    'ACC': 'ACC',
    'TRNTYPE': 'TRNTYPE',
    'TLR': 'TLR',
    'LEVEL': 'LEVEL',
    'TRNDATE': 'TRNDATE',
    'TRNAMT': 'TRNAMT',
    'TRNNONC': 'TRNNONC',
    'TRNINT': 'TRNINT',
    'TRNTAXPEN': 'TRNTAXPEN',
    'BAL': 'BAL',
    'SEQ': 'SEQ',
    'TRNDESC': 'TRNDESC',
    'APPTYPE': 'APPTYPE'
}

# Define a chunk size for reading large CSVs
CHUNK_SIZE = 100000 # Process 100,000 rows at a time

def get_db_engine():
    """Establishes and returns a SQLAlchemy engine."""
    try:
        engine_url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
        )
        engine = create_engine(engine_url)
        # Test connection
        with engine.connect() as connection:
            print("Database: SQLAlchemy engine connected successfully.")
        return engine
    except Exception as e:
        print(f"Database: Error creating SQLAlchemy engine: {e}")
        traceback.print_exc()
        return None

def create_trnm_table(engine, table_name):
    """
    Drops the specified TRNM table if it exists, then creates it.
    """
    try:
        with engine.connect() as connection:
            print(f"Attempting to DROP TABLE IF EXISTS `{table_name}`...")
            connection.execute(text(f"DROP TABLE IF EXISTS `{table_name}`;"))
            connection.commit()
            print(f"Table '{table_name}' dropped (if it existed).")

            print(f"Attempting to CREATE TABLE `{table_name}`...")
            # MODIFIED: Changed DECIMAL precision to (18,2) for 2 decimal points
            connection.execute(text(f"""
                CREATE TABLE `{table_name}` (
                    `TRN` VARCHAR(255),
                    `ACC` VARCHAR(255),
                    `TRNTYPE` VARCHAR(255),
                    `TLR` VARCHAR(255),
                    `LEVEL` VARCHAR(255),
                    `TRNDATE` DATE,
                    `TRNAMT` DECIMAL(18,2),
                    `TRNNONC` DECIMAL(18,2),
                    `TRNINT` DECIMAL(18,2),
                    `TRNTAXPEN` DECIMAL(18,2),
                    `BAL` DECIMAL(18,2),
                    `SEQ` VARCHAR(255),
                    `TRNDESC` TEXT, -- Use TEXT for potentially long descriptions
                    `APPTYPE` VARCHAR(255)
                    -- No primary key as requested
                );
            """))
            connection.commit()
            print(f"Table '{table_name}' created successfully.")
            return True
    except Exception as e:
        print(f"Error creating table '{table_name}': {e}")
        traceback.print_exc()
        return False

# Custom date parsing function (reused from previous scripts)
def parse_date_robust(date_string):
    """
    Attempts to parse a date string using multiple common formats.
    Returns datetime.date object or pd.NaT if parsing fails.
    """
    if pd.isna(date_string) or not str(date_string).strip():
        return pd.NaT
    
    s = str(date_string).strip()
    s = s.replace('-', '/') # Standardize delimiters

    formats_to_try = [
        '%m/%d/%Y',  # MM/DD/YYYY
        '%Y/%m/%d',  # YYYY/MM/DD
        '%m/%d/%y',  # MM/DD/YY
    ]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    
    # Final fallback: try pandas' general to_datetime with coerce
    try:
        return pd.to_datetime(s, errors='coerce').date()
    except Exception:
        return pd.NaT # Return NaT if all formats fail

def process_and_insert_trnm_data():
    """
    Scans for TRNM CSV files in branch subfolders, processes them in chunks,
    and inserts into MySQL tables per branch.
    """
    engine = get_db_engine()
    if engine is None:
        print("Error: Could not connect to the database. Exiting.")
        return

    print(f"Scanning for branch subfolders in: {TRNM_SOURCE_BASE_DIR}...")

    # Iterate through each branch folder
    for branch_folder_name in os.listdir(TRNM_SOURCE_BASE_DIR):
        branch_folder_path = os.path.join(TRNM_SOURCE_BASE_DIR, branch_folder_name)

        if os.path.isdir(branch_folder_path):
            normalized_branch_name_for_table = branch_folder_name.strip().replace(' ', '_').lower()
            target_table_name = f"trnm_{normalized_branch_name_for_table}"
            
            print(f"\nProcessing branch folder: {branch_folder_name} for table: {target_table_name}")

            # Ensure the table exists before processing any files for this branch
            if not create_trnm_table(engine, target_table_name):
                print(f"Error: Failed to create or verify table '{target_table_name}'. Skipping this branch.")
                continue

            csv_files_in_branch = [
                f for f in os.listdir(branch_folder_path) 
                if f.lower().endswith('.csv')
            ]

            if not csv_files_in_branch:
                print(f"No CSV files found in branch folder: {branch_folder_name}. Skipping.")
                continue

            # Sort files by date in their name to help maintain chronological order during chunk processing
            # This is a heuristic; true chronological order requires sorting the combined data.
            def get_date_from_filename(fname):
                match = re.search(r'\s-\s(\d{2}-\d{2}-\d{4})\sTO\s(\d{2}-\d{2}-\d{4})\.csv$', fname, re.IGNORECASE)
                if match:
                    try:
                        # Use the 'TO' date for sorting
                        return datetime.strptime(match.group(2), '%m-%d-%Y')
                    except ValueError:
                        pass
                # Fallback for files without 'TO' date in name, or if parsing fails
                try:
                    # Try to parse any date-like string in the filename
                    date_part_match = re.search(r'(\d{2}[-/]\d{2}[-/]\d{4})', fname)
                    if date_part_match:
                        return datetime.strptime(date_part_match.group(1), '%m/%d/%Y') # Assuming this format
                except ValueError:
                    pass
                return datetime.min # Return a very old date if no date can be parsed

            csv_files_in_branch.sort(key=get_date_from_filename)

            total_rows_inserted_for_branch = 0

            # MODIFIED: Use a single connection for all insertions within a branch
            with engine.connect() as connection:
                for filename in csv_files_in_branch:
                    file_path = os.path.join(branch_folder_path, filename)
                    print(f"  Processing file in chunks: {filename}")

                    try:
                        # Read CSV in chunks
                        for chunk_df in pd.read_csv(file_path, dtype=str, encoding='utf-8-sig', keep_default_na=False, chunksize=CHUNK_SIZE):
                            # Normalize column names for the chunk
                            chunk_df.columns = chunk_df.columns.str.strip().str.upper()

                            # Rename columns to match the target database schema
                            chunk_df.rename(columns={k.upper(): v for k, v in CSV_HEADERS_TO_DB_COLUMNS.items()}, inplace=True)

                            # Select only the columns that are in our target schema
                            selected_cols = [col for col in CSV_HEADERS_TO_DB_COLUMNS.values() if col in chunk_df.columns]
                            if not selected_cols:
                                print(f"    Skipping chunk from {filename}: No matching columns found after renaming. Expected: {list(CSV_HEADERS_TO_DB_COLUMNS.values())}. Actual after normalization: {chunk_df.columns.tolist()}")
                                continue
                            chunk_df = chunk_df[selected_cols]

                            # --- Data Cleaning and Type Conversion for the chunk ---
                            date_cols = ['TRNDATE']
                            for col in date_cols:
                                if col in chunk_df.columns:
                                    chunk_df[col] = chunk_df[col].apply(parse_date_robust)
                                else:
                                    chunk_df[col] = pd.NaT

                            numeric_cols = ['TRNAMT', 'TRNNONC', 'TRNINT', 'TRNTAXPEN', 'BAL']
                            for col in numeric_cols:
                                if col in chunk_df.columns:
                                    chunk_df[col] = chunk_df[col].astype(str).str.replace(r'[^\d\.\-()]+', '', regex=True)
                                    chunk_df[col] = chunk_df[col].str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
                                    chunk_df[col] = pd.to_numeric(chunk_df[col], errors='coerce').fillna(0)
                                else:
                                    chunk_df[col] = 0.0
                            
                            # MODIFIED: Convert TRN, TRNTYPE, TLR, SEQ, APPTYPE to integer then string to remove decimals
                            int_string_cols = ['TRN', 'TRNTYPE', 'TLR', 'SEQ', 'APPTYPE']
                            for col in int_string_cols:
                                if col in chunk_df.columns:
                                    # Convert to numeric, then to Int64 (to handle NaNs in integer column), then to string
                                    chunk_df[col] = pd.to_numeric(chunk_df[col], errors='coerce').astype(pd.Int64Dtype()).astype(str)
                                    # Replace '<NA>' (from Int64Dtype for NaN) with empty string if needed
                                    chunk_df[col] = chunk_df[col].replace('<NA>', '')
                                else:
                                    chunk_df[col] = '' # Ensure column exists as empty string

                            string_cols_to_strip = ['ACC', 'TRNDESC'] # Remaining string columns
                            for col in string_cols_to_strip:
                                if col in chunk_df.columns:
                                    chunk_df[col] = chunk_df[col].astype(str).str.strip()
                                else:
                                    chunk_df[col] = ''

                            # Sort the chunk by TRNDATE before inserting to maintain chronological order
                            chunk_df['TRNDATE_TEMP_SORT'] = pd.to_datetime(chunk_df['TRNDATE'], errors='coerce')
                            chunk_df.sort_values(by='TRNDATE_TEMP_SORT', inplace=True)
                            chunk_df.drop(columns=['TRNDATE_TEMP_SORT'], inplace=True, errors='ignore')
                            chunk_df['TRNDATE'] = chunk_df['TRNDATE'] # Keep as date object or NaT

                            # Insert the chunk into the database using the shared connection
                            try:
                                chunk_df.to_sql(name=target_table_name, con=connection, if_exists='append', index=False, chunksize=1000)
                                total_rows_inserted_for_branch += len(chunk_df)
                                print(f"    Inserted {len(chunk_df)} rows from {filename} into {target_table_name}.")
                            except Exception as e:
                                print(f"    Error inserting chunk from {filename} into '{target_table_name}': {e}")
                                traceback.print_exc()

                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}. Skipping this file.")
                        traceback.print_exc()
                        continue
                
                # MODIFIED: Explicitly commit the connection after processing all files for a branch
                connection.commit()
                print(f"Finished processing branch {branch_folder_name}. Total rows inserted: {total_rows_inserted_for_branch}")

    print("\nStarting TRNM data processing and insertion finished.")

if __name__ == "__main__":
    print("Starting TRNM data processing and insertion...")
    process_and_insert_trnm_data()
    print("TRNM data processing and insertion finished.")
