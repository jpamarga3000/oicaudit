import pandas as pd
import os
from datetime import datetime
from sqlalchemy import create_engine, text
import traceback
import re

# --- Database Configuration (ensure this matches your db_common.py) ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # Your MySQL password
    'database': 'dc_req_db',
    'charset': 'utf8mb4'
}

# Define the base directory where your SVACC CSV files are located (no subfolders)
SVACC_SOURCE_BASE_DIR = r"C:\ACC CLEANING\OPERATIONS\SVACC"

# Define the expected headers from your CSV and their corresponding MySQL column names
CSV_HEADERS_TO_DB_COLUMNS = {
    'ACC': 'ACC',
    'TYPE': 'TYPE',
    'GLCODE': 'GLCODE',
    'CID': 'CID',
    'ACCNAME': 'ACCNAME',
    'DOPEN': 'DOPEN',
    'DOLASTTRN': 'DOLASTTRN',
    'BAL': 'BAL',
    'INTRATE': 'INTRATE',
    'MATDATE': 'MATDATE',
    'CUMINTPD': 'CUMINTPD',
    'CUMTAXW': 'CUMTAXW'
}

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

def create_svacc_table(engine, table_name):
    """
    Drops the specified SVACC table if it exists, then creates it.
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
                    `ACC` VARCHAR(255),
                    `TYPE` VARCHAR(255),
                    `GLCODE` VARCHAR(255),
                    `CID` VARCHAR(255),
                    `ACCNAME` VARCHAR(255),
                    `DOPEN` DATE,
                    `DOLASTTRN` DATE,
                    `BAL` DECIMAL(18,2),
                    `INTRATE` DECIMAL(18,4), -- Allows for values like 0.1200 (12%)
                    `MATDATE` DATE,
                    `CUMINTPD` DECIMAL(18,2),
                    `CUMTAXW` DECIMAL(18,2)
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

# Custom date parsing function (reused from LNACC script)
def parse_date_robust(date_string):
    """
    Attempts to parse a date string using multiple common formats.
    Returns datetime.date object or pd.NaT if parsing fails.
    """
    if pd.isna(date_string) or not str(date_string).strip():
        return pd.NaT
    
    s = str(date_string).strip()
    # MODIFIED: Aggressively clean date string before parsing
    # Remove any characters that are not digits, slashes, or hyphens
    s = re.sub(r'[^\d/\-]', '', s) 

    formats_to_try = [
        '%m/%d/%Y',  # 01/08/1992
        '%m-%d-%Y',  # 01-08-1992
        '%Y-%m-%d',  # 1992-01-08
        '%m/%d/%y',  # 01/08/92
        '%m-%d-%y'   # 01-08-92
    ]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return pd.NaT # Return NaT if all formats fail

def process_and_insert_svacc_data():
    """
    Scans for SVACC CSV files, processes them per branch, and inserts into MySQL tables.
    """
    engine = get_db_engine()
    if engine is None:
        print("Error: Could not connect to the database. Exiting.")
        return

    all_svacc_files = [f for f in os.listdir(SVACC_SOURCE_BASE_DIR) if f.lower().endswith('.csv')]
    if not all_svacc_files:
        print(f"No CSV files found in {SVACC_SOURCE_BASE_DIR}.")
        return

    # Dictionary to hold DataFrames, keyed by branch name
    branch_dataframes = {}

    print(f"Scanning for CSV files in: {SVACC_SOURCE_BASE_DIR}...")

    for filename in all_svacc_files:
        file_path = os.path.join(SVACC_SOURCE_BASE_DIR, filename)
        
        # Extract branch name from filename (e.g., "AGLAYAN" from "AGLAYAN - 06-30-2025.csv")
        match = re.match(r'([A-Za-z\s]+)\s-\s\d{2}-\d{2}-\d{4}\.csv$', filename, re.IGNORECASE)
        branch_name = None
        if match:
            branch_name = match.group(1).strip().replace(' ', '_').lower() # Normalize for table name
        
        if not branch_name:
            print(f"Skipping {filename}: Could not extract branch name from filename.")
            continue

        target_table_name = f"svacc_{branch_name}"

        print(f"Processing file: {file_path} for table: {target_table_name}")

        try:
            # Use 'utf-8-sig' encoding to handle BOM, and read all as string initially
            df = pd.read_csv(file_path, dtype=str, encoding='utf-8-sig', keep_default_na=False)

            # Normalize column names by stripping whitespace and making uppercase for matching
            df.columns = df.columns.str.strip().str.upper()

            # DEBUG: Print actual columns after normalization
            print(f"DEBUG: Columns in {filename} after normalization: {df.columns.tolist()}")

            # Rename columns to match the target database schema
            df.rename(columns={k.upper(): v for k, v in CSV_HEADERS_TO_DB_COLUMNS.items()}, inplace=True)

            # Select only the columns that are in our target schema
            selected_cols = [col for col in CSV_HEADERS_TO_DB_COLUMNS.values() if col in df.columns]
            if not selected_cols:
                print(f"Skipping {filename}: No matching columns found after renaming. Expected: {list(CSV_HEADERS_TO_DB_COLUMNS.values())}. Actual after normalization: {df.columns.tolist()}")
                continue
            df = df[selected_cols]

            # --- Data Cleaning and Type Conversion ---
            # Date columns: Apply robust date parsing function
            date_cols = ['DOPEN', 'DOLASTTRN', 'MATDATE']
            for col in date_cols:
                if col in df.columns:
                    df[col] = df[col].apply(parse_date_robust)
                else:
                    df[col] = pd.NaT # Assign NaT if column is missing

            # Numeric columns: Convert to numeric, handle errors, NO DIVISION BY 100
            numeric_cols = ['BAL', 'CUMINTPD', 'CUMTAXW']
            for col in numeric_cols:
                if col in df.columns:
                    # Remove non-numeric characters like commas, currency symbols, and parentheses for negatives
                    df[col] = df[col].astype(str).str.replace(r'[^\d\.\-()]+', '', regex=True)
                    df[col] = df[col].str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                else:
                    df[col] = 0.0 # Assign 0.0 if column is missing
            
            # INTRATE handling: NO DIVISION BY 100, just convert to numeric
            if 'INTRATE' in df.columns:
                df['INTRATE'] = df['INTRATE'].astype(str).str.replace('%', '', regex=False).str.strip()
                df['INTRATE'] = pd.to_numeric(df['INTRATE'], errors='coerce').fillna(0)
            else:
                df['INTRATE'] = 0.0

            # String columns: Ensure all are stripped. ACC is included here.
            if 'ACC' in df.columns:
                df['ACC'] = df['ACC'].astype(str).str.strip()
            else:
                df['ACC'] = '' # Ensure ACC column exists even if missing in source and is empty string

            string_cols_to_strip = ['TYPE', 'GLCODE', 'CID', 'ACCNAME'] 
            for col in string_cols_to_strip:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                else:
                    df[col] = '' # Assign empty string if column is missing

            # DEBUG: Print sample DOPEN values and their dtypes before appending
            print(f"DEBUG: Sample DOPEN values for {filename}:")
            print(df['DOPEN'].head())
            print(f"DEBUG: DOPEN dtype for {filename}: {df['DOPEN'].dtype}")
            # DEBUG: Print sample MATDATE values and their dtypes before appending
            print(f"DEBUG: Sample MATDATE values for {filename}:")
            print(df['MATDATE'].head())
            print(f"DEBUG: MATDATE dtype for {filename}: {df['MATDATE'].dtype}")
            # DEBUG: Print sample ACC values and their dtypes before appending
            print(f"DEBUG: Sample ACC values for {filename}:")
            print(df['ACC'].head())
            print(f"DEBUG: ACC dtype for {filename}: {df['ACC'].dtype}")


            # Append DataFrame to the list for this branch
            if target_table_name not in branch_dataframes:
                branch_dataframes[target_table_name] = []
            branch_dataframes[target_table_name].append(df)

        except Exception as e:
            print(f"Error processing file {file_path}: {e}. Skipping this file.")
            traceback.print_exc()
            continue

    if not branch_dataframes:
        print("No valid data extracted from any CSV files for any branch. Nothing to insert.")
        return

    # Now, concatenate data for each branch and insert
    for table_name, list_of_dfs in branch_dataframes.items():
        final_combined_df = pd.concat(list_of_dfs, ignore_index=True)
        
        # Ensure the table exists before insertion
        if not create_svacc_table(engine, table_name):
            print(f"Error: Failed to create or verify table '{table_name}'. Skipping insertion for this branch.")
            continue

        print(f"Total {len(final_combined_df)} rows prepared for insertion into {table_name}.")

        try:
            final_combined_df.to_sql(name=table_name, con=engine, if_exists='append', index=False, chunksize=1000)
            print(f"Successfully inserted data into '{table_name}' table.")
        except Exception as e:
            print(f"Error inserting data into '{table_name}' table: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    print("Starting SVACC data processing and insertion...")
    process_and_insert_svacc_data()
    print("SVACC data processing and insertion finished.")
