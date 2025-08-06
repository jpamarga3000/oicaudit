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

# Define the base directory where your GL CSV files are located
# Each subfolder within this directory should be a branch name
GL_SOURCE_BASE_DIR = r"C:\ACC CLEANING\ACCOUTNING\GENERAL LEDGER"

# Define the expected headers from your CSV and their corresponding MySQL column names
CSV_HEADERS_TO_DB_COLUMNS = {
    'TRN': 'TRN',
    'GLACC': 'GLACC',
    'ACCOUNT': 'ACCOUNT',
    'DOCDATE': 'DOCDATE',
    'REF': 'REF',
    'AMT': 'AMT',
    'DESC': 'DESC',
    'BAL': 'BAL'
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
        # MODIFIED: Add pool_size and max_overflow for better connection management
        # Also, set isolation_level to READ COMMITTED or AUTOCOMMIT if explicit commits are desired
        engine = create_engine(engine_url, pool_size=10, max_overflow=20, isolation_level="READ COMMITTED")
        # Test connection
        with engine.connect() as connection:
            print("Database: SQLAlchemy engine connected successfully.")
        return engine
    except Exception as e:
        print(f"Database: Error creating SQLAlchemy engine: {e}")
        traceback.print_exc()
        return None

def create_gl_table(engine, table_name):
    """
    Drops the specified GL table if it exists, then creates it.
    """
    try:
        with engine.connect() as connection:
            print(f"Attempting to DROP TABLE IF EXISTS `{table_name}`...")
            connection.execute(text(f"DROP TABLE IF EXISTS `{table_name}`;"))
            connection.commit()
            print(f"Table '{table_name}' dropped (if it existed).")

            print(f"Attempting to CREATE TABLE `{table_name}`...")
            connection.execute(text(f"""
                CREATE TABLE `{table_name}` (
                    `TRN` VARCHAR(255),
                    `GLACC` VARCHAR(255),
                    `ACCOUNT` VARCHAR(255),
                    `DOCDATE` DATE,
                    `REF` VARCHAR(255),
                    `AMT` DECIMAL(18,2),
                    `DESC` TEXT,
                    `BAL` DECIMAL(18,2)
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

def process_and_insert_gl_data():
    """
    Scans for GL CSV files in branch subfolders, processes them in chunks,
    and inserts into MySQL tables per branch.
    """
    engine = get_db_engine()
    if engine is None:
        print("Error: Could not connect to the database. Exiting.")
        return

    print(f"Scanning for branch subfolders in: {GL_SOURCE_BASE_DIR}...")

    # Iterate through each branch folder
    for branch_folder_name in os.listdir(GL_SOURCE_BASE_DIR):
        branch_folder_path = os.path.join(GL_SOURCE_BASE_DIR, branch_folder_name)

        if os.path.isdir(branch_folder_path):
            normalized_branch_name_for_table = branch_folder_name.strip().replace(' ', '_').lower()
            target_table_name = f"gl_{normalized_branch_name_for_table}"
            
            print(f"\nProcessing branch folder: {branch_folder_name} for table: {target_table_name}")

            # Ensure the table exists before processing any files for this branch
            if not create_gl_table(engine, target_table_name):
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
            def get_date_from_filename(fname):
                match = re.search(r'(\d{2}[-/]\d{2}[-/]\d{4})', fname) # Look for MM-DD-YYYY or MM/DD/YYYY
                if match:
                    try:
                        return datetime.strptime(match.group(1), '%m-%d-%Y').date() # Try with hyphen first
                    except ValueError:
                        try:
                            return datetime.strptime(match.group(1), '%m/%d/%Y').date() # Then try with slash
                        except ValueError:
                            pass
                return datetime.min.date() # Return a very old date if no date can be parsed

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
                            date_cols = ['DOCDATE']
                            for col in date_cols:
                                if col in chunk_df.columns:
                                    chunk_df[col] = chunk_df[col].apply(parse_date_robust)
                                else:
                                    chunk_df[col] = pd.NaT

                            numeric_cols = ['AMT', 'BAL']
                            for col in numeric_cols:
                                if col in chunk_df.columns:
                                    # Remove non-numeric characters like commas, currency symbols, and parentheses for negatives
                                    chunk_df[col] = chunk_df[col].astype(str).str.replace(r'[^\d\.\-()]+', '', regex=True)
                                    chunk_df[col] = chunk_df[col].str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
                                    chunk_df[col] = pd.to_numeric(chunk_df[col], errors='coerce').fillna(0)
                                else:
                                    chunk_df[col] = 0.0
                            
                            # MODIFIED: Clean ACCOUNT column
                            if 'ACCOUNT' in chunk_df.columns:
                                # Remove leading/trailing quotes and equals sign, then strip whitespace
                                chunk_df['ACCOUNT'] = chunk_df['ACCOUNT'].astype(str).str.replace('=', '', regex=False).str.replace('"', '', regex=False).str.strip()
                            else:
                                chunk_df['ACCOUNT'] = '' # Ensure column exists

                            string_cols_to_strip = ['TRN', 'GLACC', 'REF', 'DESC'] # Removed 'ACCOUNT' from here
                            for col in string_cols_to_strip:
                                if col in chunk_df.columns:
                                    chunk_df[col] = chunk_df[col].astype(str).str.strip()
                                else:
                                    chunk_df[col] = ''

                            # Insert the chunk into the database using the shared connection
                            try:
                                # MODIFIED: Use method='multi' for faster insertion
                                chunk_df.to_sql(name=target_table_name, con=connection, if_exists='append', index=False, chunksize=1000, method='multi')
                                total_rows_inserted_for_branch += len(chunk_df)
                                print(f"    Inserted {len(chunk_df)} rows from {filename} into {target_table_name}.")
                            except Exception as e:
                                print(f"    Error inserting chunk from {filename} into '{target_table_name}': {e}")
                                traceback.print_exc()

                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}. Skipping this file.")
                        traceback.print_exc()
                        continue
                
                connection.commit()
                print(f"Finished processing branch {branch_folder_name}. Total rows inserted: {total_rows_inserted_for_branch}")

    print("\nStarting GL data processing and insertion finished.")

if __name__ == "__main__":
    print("Starting GL data processing and insertion...")
    process_and_insert_gl_data()
    print("GL data processing and insertion finished.")
