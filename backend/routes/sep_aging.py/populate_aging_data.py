import pandas as pd
import os
from datetime import datetime
from sqlalchemy import create_engine, text
import traceback

# --- Database Configuration (ensure this matches your db_common.py) ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # Your MySQL password
    'database': 'dc_req_db',
    'charset': 'utf8mb4'
}

# Define the base directory where your aging CSV files are located, including subfolders
AGING_SOURCE_BASE_DIR = r"C:\ACC CLEANING\OPERATIONS\AGING"

# Define the target table name
TARGET_TABLE_NAME = 'aging_report_data'

# Define the expected headers from your CSV and their corresponding MySQL column names
# Note: MySQL column names are typically lowercase and use underscores
CSV_HEADERS_TO_DB_COLUMNS = {
    'BRANCH': 'Branch',
    'DATE': 'Date',
    'CID': 'CID',
    'NAME OF MEMBER': 'Name_of_Member',
    'LOAN ACCT.': 'Loan_Account',
    'PRINCIPAL': 'Principal',
    'BALANCE': 'Balance',
    'GL CODE': 'GL_Code', # Assuming GL CODE maps to GL_Code
    'PRODUCT': 'Product',
    'DISBDATE': 'Disbursement_Date',
    'DUE DATE': 'Due_Date',
    'AGING': 'Aging',
    'GROUP': 'Group'
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

# MODIFIED: Function to drop and then create the aging_report_data table with GL_Code
def create_aging_table(engine):
    """
    Drops the aging_report_data table if it exists, then creates it.
    """
    try:
        with engine.connect() as connection:
            print(f"Attempting to DROP TABLE IF EXISTS `{TARGET_TABLE_NAME}`...")
            connection.execute(text(f"DROP TABLE IF EXISTS `{TARGET_TABLE_NAME}`;"))
            connection.commit()
            print(f"Table '{TARGET_TABLE_NAME}' dropped (if it existed).")

            print(f"Attempting to CREATE TABLE `{TARGET_TABLE_NAME}`...")
            connection.execute(text(f"""
                CREATE TABLE `{TARGET_TABLE_NAME}` (
                    `Branch` VARCHAR(255),
                    `Date` DATE,
                    `CID` VARCHAR(255),
                    `Name_of_Member` VARCHAR(255),
                    `Loan_Account` VARCHAR(255),
                    `Principal` DECIMAL(18,2),
                    `Balance` DECIMAL(18,2),
                    `GL_Code` VARCHAR(255),
                    `Aging` VARCHAR(255),
                    `Disbursement_Date` DATE,
                    `Due_Date` DATE,
                    `Product` VARCHAR(255),
                    `Group` VARCHAR(255)
                );
            """))
            connection.commit()
            print(f"Table '{TARGET_TABLE_NAME}' created successfully.")
            return True
    except Exception as e:
        print(f"Error creating table '{TARGET_TABLE_NAME}': {e}")
        traceback.print_exc()
        return False

def process_and_insert_aging_data():
    """
    Scans for aging CSV files, combines them, cleans data, and inserts into MySQL.
    """
    engine = get_db_engine()
    if engine is None:
        print("Error: Could not connect to the database. Exiting.")
        return

    # NEW: Ensure the aging_report_data table exists before proceeding
    if not create_aging_table(engine):
        print("Error: Failed to create or verify aging_report_data table. Exiting.")
        return

    all_aging_data = []
    found_csv_files = False

    print(f"Scanning for CSV files in: {AGING_SOURCE_BASE_DIR} and its subfolders...")

    # Walk through the base directory and its subfolders
    for root, _, files in os.walk(AGING_SOURCE_BASE_DIR):
        for filename in files:
            if filename.lower().endswith('.csv'):
                file_path = os.path.join(root, filename)
                found_csv_files = True
                print(f"Processing file: {file_path}")

                try:
                    # Read CSV, assuming first row is header, and read all as strings initially
                    df = pd.read_csv(file_path, dtype=str, encoding='latin1', keep_default_na=False)

                    # Normalize column names by stripping whitespace and making uppercase for matching
                    df.columns = df.columns.str.strip().str.upper()

                    # Rename columns to match the target database schema
                    df.rename(columns={k.upper(): v for k, v in CSV_HEADERS_TO_DB_COLUMNS.items()}, inplace=True)

                    # Select only the columns that are in our target schema
                    # And ensure they are in the correct order
                    df = df[[col for col in CSV_HEADERS_TO_DB_COLUMNS.values() if col in df.columns]]

                    # --- Data Cleaning and Type Conversion ---
                    # Date columns: Convert to datetime objects, then format to 'YYYY-MM-DD' for MySQL DATE type
                    date_cols = ['Date', 'Disbursement_Date', 'Due_Date']
                    for col in date_cols:
                        if col in df.columns:
                            # Attempt multiple date formats for robustness
                            df[col] = pd.to_datetime(df[col], errors='coerce', format='%m/%d/%Y').fillna(pd.NaT)
                            df[col] = df[col].dt.date # Keep only date part
                        else:
                            df[col] = pd.NaT # Assign NaT if column is missing

                    # Numeric columns: Convert to numeric, handle errors, NO DIVISION BY 100
                    numeric_cols = ['Principal', 'Balance']
                    for col in numeric_cols:
                        if col in df.columns:
                            # Remove non-numeric characters like commas, currency symbols, and parentheses for negatives
                            df[col] = df[col].astype(str).str.replace(r'[^\d\.\-()]+', '', regex=True)
                            df[col] = df[col].str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
                            # MODIFIED: Removed division by 100
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                        else:
                            df[col] = 0.0 # Assign 0.0 if column is missing

                    # String columns: Strip whitespace
                    string_cols = ['Branch', 'CID', 'Name_of_Member', 'Loan_Account', 'GL_Code', 'Product', 'Aging', 'Group']
                    for col in string_cols:
                        if col in df.columns:
                            df[col] = df[col].astype(str).str.strip()
                        else:
                            df[col] = '' # Assign empty string if column is missing

                    all_aging_data.append(df)

                except Exception as e:
                    print(f"Error processing file {file_path}: {e}. Skipping this file.")
                    traceback.print_exc()
                    continue

    if not found_csv_files:
        print(f"No CSV files found in {AGING_SOURCE_BASE_DIR} or its subfolders.")
        return

    if not all_aging_data:
        print("No valid data extracted from any CSV files. Nothing to insert.")
        return

    final_combined_df = pd.concat(all_aging_data, ignore_index=True)
    
    # MODIFIED: Removed the drop_duplicates line as requested
    # initial_rows = len(final_combined_df)
    # final_combined_df.drop_duplicates(subset=['Loan_Account', 'Date', 'Branch'], keep='first', inplace=True)
    # rows_removed = initial_rows - len(final_combined_df)
    # if rows_removed > 0:
    #     print(f"Removed {rows_removed} duplicate rows based on (Loan_Account, Date, Branch).")

    print(f"Total {len(final_combined_df)} rows prepared for insertion into {TARGET_TABLE_NAME}.")

    try:
        # Insert data into MySQL table
        # Using if_exists='append' to add new data without recreating table each time
        # Using index=False to prevent pandas from writing the DataFrame index as a column
        final_combined_df.to_sql(name=TARGET_TABLE_NAME, con=engine, if_exists='append', index=False, chunksize=1000)
        print(f"Successfully inserted data into '{TARGET_TABLE_NAME}' table.")
    except Exception as e:
        print(f"Error inserting data into '{TARGET_TABLE_NAME}' table: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting aging report data processing and insertion...")
    process_and_insert_aging_data()
    print("Aging report data processing and insertion finished.")
