import os
import csv
from dbfread import DBF
from datetime import datetime, timedelta
import pandas as pd
import math
from io import StringIO
import re # Added for robust string cleaning
import numpy as np # Import numpy for vectorized operations

# Define the maximum file size in bytes (49.9 MB)
MAX_FILE_SIZE_BYTES = 49.9 * 1024 * 1024

# Excel's epoch start date (December 30, 1899) for converting numeric dates
EXCEL_EPOCH = datetime(1899, 12, 30)

# Define the fixed output directory for LNACC
FIXED_OUTPUT_DIR = r"C:\xampp\htdocs\audit_tool\OPERATIONS\LNACC" # Ensure this is defined globally

# --- Helper function for date parsing and addition ---
# This helper function is now primarily for fallback if vectorized parsing fails.
def parse_and_add_days(date_val, days_to_add=2):
    """
    Parses a date value (string or numeric), adds a specified number of days,
    and returns it formatted as 'MM/DD/YYYY'.
    Handles Excel numeric dates (days since 1899-12-30) and string dates.
    Returns an empty string if parsing fails.
    """
    parsed_date = pd.NaT # Initialize as Not a Time

    if pd.isna(date_val) or date_val == '': # Handle NaN or empty string upfront
        return ''

    if isinstance(date_val, (int, float)):
        try:
            parsed_date = EXCEL_EPOCH + timedelta(days=float(date_val))
        except (ValueError, OverflowError):
            pass
    elif isinstance(date_val, bytes):
        date_str = date_val.decode('latin-1').strip()
    elif isinstance(date_val, str):
        date_str = date_val.strip()
    else:
        return ''

    if pd.notna(parsed_date):
        return (parsed_date + timedelta(days=days_to_add)).strftime('%m/%d/%Y')
    return ''


# Helper function to clean and convert a Pandas Series (column) to numeric.
# It handles byte strings, currency symbols, commas, and missing values.
def clean_and_convert_numeric(series):
    # Convert to string type first for vectorized string operations
    s_str = series.astype(str)

    # Step 1: Remove ALL whitespace characters and common currency symbols
    # Use str.replace with regex=True for vectorized regex replacement
    s_cleaned_currency = s_str.str.replace(r'\s+|[₱$]', '', regex=True)

    # Step 2: Remove any characters that are not digits, '.', or '-'
    s_cleaned_non_numeric = s_cleaned_currency.str.replace(r'[^\d.-]', '', regex=True)

    # Convert to numeric, coercing any errors to NaN
    numeric_series = pd.to_numeric(s_cleaned_non_numeric, errors='coerce')

    # Fill NaN (Not a Number) values with 0.0
    return numeric_series.fillna(0.0)


def process_lnacc_dos_data_web(input_dir, branch): # Removed output_dir parameter
    """
    Processes DBF, CSV, and XLSX files from input_dir, extracts/formats Loan Account (LNACC) data,
    and combines into a single CSV file in the FIXED_OUTPUT_DIR.
    Output filename uses the selected branch name and the latest DOPEN date.
    Existing files with the same branch name are overwritten.

    Args:
        input_dir (str): The directory containing the DBF, CSV, and XLSX files.
        branch (str): The selected branch name for output filename.
    """
    # Ensure the fixed output directory exists
    os.makedirs(FIXED_OUTPUT_DIR, exist_ok=True)

    # Define the required headers and their desired order for the final CSV.
    target_headers = [
        'ACC', 'CID', 'GLCODE', 'LOANID', 'DOPEN', 'DOFIRSTI', 'DOLASTTRN',
        'BAL', 'INTRATE', 'CUMINTPD', 'MATDATE', 'PRINCIPAL', 'CUMPENPD',
        'DISBDATE', 'INTBAL', 'PENBAL'
    ]

    all_dataframes = [] # List to hold DataFrames generated from each file
    files_found = False # Flag to track if any supported files were found

    print(f"Server Log (LNACC DOS): Starting file processing from {input_dir} for branch '{branch}'")

    # Iterate through each file in the specified input directory
    for filename in os.listdir(input_dir):
        filepath = os.path.join(input_dir, filename)
        df_current = pd.DataFrame() # Initialize empty DataFrame for current file

        try:
            if filename.lower().endswith('.dbf'):
                files_found = True
                print(f"Server Log (LNACC DOS): Processing DBF file: {filename}...")
                df_current = pd.DataFrame(list(DBF(filepath, encoding='latin-1', ignore_missing_memofile=True)))
            elif filename.lower().endswith('.csv'):
                files_found = True
                print(f"Server Log (LNACC DOS): Processing CSV file: {filename}...")
                df_current = pd.read_csv(filepath, encoding='utf-8', on_bad_lines='skip', low_memory=False, dtype={'ACC': str, 'CID': str, 'GLCODE':str, 'LOANID':str, 'CHD':str})
            elif filename.lower().endswith('.xlsx'):
                files_found = True
                print(f"Server Log (LNACC DOS): Processing XLSX file: {filename}...")
                df_current = pd.read_excel(filepath, dtype={'ACC': str, 'CID': str, 'GLCODE':str, 'LOANID':str, 'CHD':str})
            else:
                continue # Skip unsupported file types

            if df_current.empty:
                print(f"Server Log (LNACC DOS): Skipping empty file: {filename}")
                continue

            df_current.columns = [col.upper() for col in df_current.columns]

            # Define the minimum required fields for a file to be considered valid
            required_fields_check = set(target_headers)
            if 'CHD' in df_current.columns:
                required_fields_check.add('CHD')

            if not required_fields_check.issubset(set(df_current.columns)):
                missing = required_fields_check.difference(set(df_current.columns))
                print(f"Server Log (LNACC DOS): Skipping {filename} (missing required headers: {missing})")
                continue
            
            # --- Apply Transformations ---

            # 1. Combine ACC and CHD into new ACC format (Vectorized)
            if 'ACC' in df_current.columns and 'CHD' in df_current.columns:
                # Ensure ACC and CHD are strings for string operations, handle potential NaNs
                df_current['ACC'] = df_current['ACC'].astype(str).replace('nan', '').str.strip()
                df_current['CHD'] = df_current['CHD'].astype(str).replace('nan', '').str.strip()

                # Define the condition for applying the specific format
                # Check if ACC has at least 7 characters and CHD has at least 1 character
                condition = (df_current['ACC'].str.len() >= 7) & (df_current['CHD'].str.len() >= 1)

                # Apply vectorized string slicing and concatenation using numpy.where
                df_current['ACC'] = np.where(
                    condition,
                    df_current['ACC'].str[:2] + '-' + df_current['ACC'].str[2:7] + '-' + df_current['CHD'],
                    df_current['ACC'] # Fallback to original ACC if condition is not met (including empty ACC)
                )


            # 2. Date Formatting (Vectorized first, then fallback to .apply())
            date_cols_to_process = ['DOPEN', 'DOFIRSTI', 'DOLASTTRN', 'MATDATE', 'DISBDATE']
            for col in date_cols_to_process:
                if col in df_current.columns:
                    # Attempt vectorized conversion for common formats first
                    original_series = df_current[col].copy() # Keep a copy of original for fallback
                    
                    # Try Excel numeric date conversion first (vectorized)
                    if pd.api.types.is_numeric_dtype(original_series):
                        df_current[col] = pd.to_datetime(original_series, unit='D', origin=EXCEL_EPOCH, errors='coerce')
                    else: # Try string date formats
                        # Try 'MM/DD/YYYY HH:MM:SS %p'
                        df_current[col] = pd.to_datetime(original_series, format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
                        
                        # Fill NaT (failed conversions) with another format attempt
                        mask_nat = df_current[col].isna()
                        if mask_nat.any():
                            df_current.loc[mask_nat, col] = pd.to_datetime(original_series[mask_nat], format='%m/%d/%Y', errors='coerce')
                    
                    # Apply timedelta and format for successfully converted dates
                    # Ensure it's datetime before adding timedelta
                    valid_dates_mask = df_current[col].notna()
                    if valid_dates_mask.any():
                        df_current.loc[valid_dates_mask, col] = (
                            df_current.loc[valid_dates_mask, col] + timedelta(days=2)
                        ).dt.strftime('%m/%d/%Y')
                    
                    # Fallback for any remaining NaT or original unparsed values using the old .apply method
                    # This targets only the values that failed vectorized parsing
                    needs_fallback_mask = (df_current[col].isna()) | (df_current[col] == '') # Check for NaT or empty string after vectorized attempts
                    if needs_fallback_mask.any():
                        df_current.loc[needs_fallback_mask, col] = original_series[needs_fallback_mask].apply(parse_and_add_days)

            # 3. Numeric columns: Convert to numeric AND divide by 100 (using optimized clean_and_convert_numeric)
            numeric_cols_to_process = ['BAL', 'CUMINTPD', 'PRINCIPAL', 'CUMPENPD', 'INTBAL', 'PENBAL']
            for col in numeric_cols_to_process:
                if col in df_current.columns:
                    # Apply cleaning, then divide by 100
                    df_current[col] = clean_and_convert_numeric(df_current[col]) / 100
                    
            # 4. INTRATE: Convert to numeric, then normalize to standard percentage (e.g., 5 for 5%, not 0.05)
            if 'INTRATE' in df_current.columns:
                df_current['INTRATE'] = clean_and_convert_numeric(df_current['INTRATE'])
                max_rate_val = df_current['INTRATE'].max()
                if pd.notna(max_rate_val) and max_rate_val > 0 and max_rate_val <= 1.0:
                     df_current['INTRATE'] = df_current['INTRATE'] * 100


            # Ensure CID, GLCODE, LOANID are strings and stripped, and apply Excel formula protection (Vectorized)
            for col in ['ACC', 'CID', 'GLCODE', 'LOANID']:
                if col in df_current.columns:
                    df_current[col] = df_current[col].astype(str).str.strip() # Ensure string and strip whitespace
                    # Apply conditional formatting using numpy.where for vectorized operation
                    df_current[col] = np.where(
                        df_current[col].str.startswith('='),
                        '="' + df_current[col] + '"', # Add quotes if starts with '='
                        df_current[col] # Otherwise, keep original
                    )

            all_dataframes.append(df_current)

        except Exception as e:
            print(f"Server Log (LNACC DOS): ❌ Error processing {filename}: {e}")

    if not files_found:
        raise Exception("No supported DBF, CSV, or XLSX files found in the specified input directory for LNACC DOS processing.")

    if not all_dataframes:
        raise Exception("No valid data was processed or combined from any supported files for LNACC DOS. No CSV will be generated.")

    print("Server Log (LNACC DOS): Concatenating all data into a single DataFrame...")
    df_combined = pd.concat(all_dataframes, ignore_index=True)
    del all_dataframes

    # Convert 'DOPEN' to datetime objects for finding the latest date
    # Ensure 'DOPEN' column exists before attempting conversion
    if 'DOPEN' in df_combined.columns:
        df_combined['DOPEN_DT'] = pd.to_datetime(df_combined['DOPEN'], format='%m/%d/%Y', errors='coerce')
    else:
        # If DOPEN column is missing, create DOPEN_DT as all NaT
        df_combined['DOPEN_DT'] = pd.Series([pd.NaT] * len(df_combined), index=df_combined.index) # Use df_combined.index to align length and index
        print("Server Log (LNACC DOS): Warning: 'DOPEN' column not found in combined data. Latest date will be 'UNKNOWN_DATE'.")

    latest_dopen_date_str = "UNKNOWN_DATE"
    if not df_combined['DOPEN_DT'].dropna().empty:
        latest_dopen = df_combined['DOPEN_DT'].max()
        latest_dopen_date_str = latest_dopen.strftime('%m-%d-%Y')
    else:
        # If DOPEN_DT is still all NaT, set latest_dopen_date_str to '-'
        latest_dopen_date_str = "-"


    # Sanitize branch name for filename: allow alphanumeric and spaces, then strip and uppercase
    sanitized_branch = "".join([c for c in str(branch) if c.isalnum() or c == ' ']).strip().upper()
    if not sanitized_branch:
        sanitized_branch = "UNSPECIFIED_BRANCH"

    # Define the output filename based on the selected branch and latest DOPEN date
    # Format: BRANCH - MM-DD-YYYY.csv
    new_output_filename = f"{sanitized_branch} - {latest_dopen_date_str}.csv"
    new_output_filepath = os.path.join(FIXED_OUTPUT_DIR, new_output_filename)

    # Find and delete existing files for the same branch, regardless of date in their name
    # Regex to match files starting with the sanitized branch name and ending with .csv
    branch_file_pattern = re.compile(rf'^{re.escape(sanitized_branch)} - \d{{2}}-\d{{2}}-\d{{4}}\.csv$', re.IGNORECASE)
    
    for existing_file in os.listdir(FIXED_OUTPUT_DIR):
        if branch_file_pattern.match(existing_file):
            existing_filepath = os.path.join(FIXED_OUTPUT_DIR, existing_file)
            try:
                os.remove(existing_filepath)
                print(f"Server Log (LNACC DOS): Deleted old file: {existing_filepath}")
            except OSError as e:
                print(f"Server Log (LNACC DOS): Error deleting old file {existing_filepath}: {e}")

    # Sort the entire combined DataFrame by 'DISBDATE' (assuming it's a primary date for ordering)
    print("Server Log (LNACC DOS): Sorting combined data by DISBDATE...")
    if 'DISBDATE' in df_combined.columns:
        # Convert to datetime temporarily for sorting if not already, then sort
        df_combined['DISBDATE_TEMP'] = pd.to_datetime(df_combined['DISBDATE'], format='%m/%d/%Y', errors='coerce')
        df_combined.sort_values(by='DISBDATE_TEMP', inplace=True)
        df_combined.drop(columns=['DISBDATE_TEMP'], inplace=True) # Drop temp column
    else:
        print("Server Log (LNACC DOS): Warning: 'DISBDATE' column not found for sorting.")
    
    df_combined.reset_index(drop=True, inplace=True)

    # Select and reorder columns to match the 'target_headers' sequence for the final CSV output
    # Ensure all target headers exist; if not, add them as empty columns before selecting
    for col in target_headers:
        if col not in df_combined.columns:
            df_combined[col] = ''
    df_combined = df_combined[target_headers]

    # Save the combined DataFrame to CSV (this will be the new file)
    # Drop the temporary datetime column before saving
    # Ensure 'DOPEN_DT' exists before attempting to drop it
    if 'DOPEN_DT' in df_combined.columns: # Added check here
        df_combined.drop(columns=['DOPEN_DT'], inplace=True) 
    df_combined.to_csv(new_output_filepath, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8-sig')
    print(f"Server Log (LNACC DOS): ✅ Successfully combined and saved {len(df_combined)} rows to: {new_output_filepath}")

    print(f"\nServer Log (LNACC DOS): Processing complete! Output saved to {new_output_filepath}")
    return {"message": f"LNACC DOS processing completed. Output saved to {new_output_filepath}", "output_path": new_output_filepath}
