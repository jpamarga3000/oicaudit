# audit_tool/backend/operations_soa.py
import os
import pandas as pd
from datetime import datetime, timedelta
import re
from dateutil.relativedelta import relativedelta

# Import database connection helper
from backend.db_common import get_data_from_mysql, get_db_connection

# TRNM_BASE_DIR is no longer used for direct file reading in this script,
# as data will now come from MySQL. Kept for reference if needed.
# TRNM_BASE_DIR = r"C:\\xampp\\htdocs\\audit_tool\\OPERATIONS\\TRNM"

# Helper function to format numeric values with commas and 2 decimal points
def format_decimal_amount(value):
    """
    Formats a numeric value to a string with comma separators and two decimal places.
    Returns blank string if value is NaN or None.
    """
    if pd.isna(value) or value is None:
        return ''
    try:
        # Convert to float first, then format
        return "{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return ''

# NEW Helper function to format signed amounts (positive as is, negative in parentheses)
def format_signed_amount(value):
    """
    Formats a numeric value: positive as is, negative in parentheses, with 2 decimal places and commas.
    Returns "0.00" if value is NaN or None.
    """
    if pd.isna(value) or value is None:
        return "0.00"
    num_val = float(value)
    if num_val < 0:
        return "({:,.2f})".format(abs(num_val))
    else:
        return "{:,.2f}".format(num_val)

# Helper function for GL Code formatting (reused from accounting_process)
def format_gl_code(code):
    """
    Formats a GL Code string based on its digit length.
    - 5 digits: x-xx-xx
    - 9 digits: x-xx-xx-xxxx
    For other lengths, it returns just the raw digits.
    """
    # Ensure input is string, remove existing hyphens
    digits = str(code).strip().replace('-', '') 
    
    # Robustly remove .0 suffix if it's an integer-like float
    if digits.endswith('.0') and digits[:-2].isdigit(): # Check if it ends with .0 and the part before is purely digits
        digits = digits[:-2] # Remove .0

    if len(digits) == 5:
        return f"{digits[0]}-{digits[1:3]}-{digits[3:5]}"
    elif len(digits) == 9:
        return f"{digits[0]}-{digits[1:3]}-{digits[3:5]}-{digits[5:9]}"
    # Handle 6-digit codes that might be intended as 5+1 or 9-3
    elif len(digits) == 6:
        # If it ends in '0', treat as 5 digits padded with a zero (common in some systems)
        if digits.endswith('0'):
            return f"{digits[0]}-{digits[1:3]}-{digits[3:5]}"
        else:
            # Otherwise, treat as 6-digit format if a specific format is known, or return as-is
            # Based on previous discussions, 6-digit might be x-xx-xx-x
            return f"{digits[0]}-{digits[1:3]}-{digits[3:5]}-{digits[5]}"
    elif len(digits) == 10: # Added for completeness if 10-digit codes appear
        return f"{digits[0]}-{digits[1:3]}-{digits[3:5]}-{digits[5:10]}"
    return digits # For any other length, just return the raw digits.


# Modified function signature: removed type_input and category_input_code
def process_statement_of_account_report(branch_name, from_date_str, to_date_str, account_lookup, code_lookup, description_lookup, trn_type_lookup, match_type):
    """
    Processes Statement of Account data from the MySQL 'trnm_{branch_name}' table.
    Filters by branch, date range, account number, code, description, and TRN type.
    Applies match_type ('exact' or 'approximate') to account and description lookups.

    Args:
        branch_name (str): The selected branch name.
        from_date_str (str): Start date in MM/DD/YYYY format.
        to_date_str (str): End date in MM/DD/YYYY format.
        account_lookup (str): The account number to filter by (ACC column).
        code_lookup (str): 2-digit code to filter ACC by starting digits.
        description_lookup (str): Text to search for in TRNDESC (case-insensitive, contains).
        trn_type_lookup (str): Text to search for in TRNTYPE (case-insensitive, contains).
        match_type (str): 'exact' or 'approximate' for account and description lookups.

    Returns:
        list: A list of dictionaries representing the processed table data.
            Returns an empty list if no data is found or an error occurs.
    """
    print(f"Server Log (Statement of Account): Processing report for branch: {branch_name}")
    print(f"Server Log (Statement of Account): Date Range: {from_date_str} to {to_date_str}")
    print(f"Server Log (Statement of Account): Lookups - Account: '{account_lookup}', Code: '{code_lookup}', Description: '{description_lookup}', TRN Type: '{trn_type_lookup}', Match Type: '{match_type}'")

    try:
        from_date_sql = datetime.strptime(from_date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
        to_date_sql = datetime.strptime(to_date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
    except ValueError as e:
        print(f"Server Log (Statement of Account): Invalid date format received from frontend: {e}")
        return []

    # FIX: Dynamically determine the table name based on branch_name
    # This assumes tables are named trnm_aglayan, trnm_bulua, etc.
    table_name = f"trnm_{branch_name.lower()}"

    # Base query now uses the branch-specific table directly.
    # MODIFIED: Removed 'Branch' column from SELECT statement as it doesn't exist in trnm_ tables
    query = f"""
        SELECT
            TRN,
            ACC,
            TRNTYPE,
            TLR,
            LEVEL,
            TRNDATE,
            TRNAMT,
            TRNNONC,
            TRNINT,
            TRNTAXPEN,
            BAL,
            SEQ,
            TRNDESC,
            APPTYPE
        FROM `{table_name}`
        WHERE TRNDATE BETWEEN '{from_date_sql}' AND '{to_date_sql}'
    """
    
    # Add filters for lookup fields
    if account_lookup:
        account_lookup_clean = account_lookup.strip()
        if match_type == 'exact':
            query += f" AND ACC = '{account_lookup_clean}'"
        elif match_type == 'approximate':
            query += f" AND ACC LIKE '%{account_lookup_clean}%'"

    if code_lookup: # Removed len(code_lookup) == 2 and code_lookup.isdigit() for more flexibility
        query += f" AND GLCODE LIKE '{code_lookup}%'" # Assuming code_lookup is for GLCODE prefix

    if description_lookup:
        description_lookup_clean = description_lookup.strip()
        if match_type == 'exact':
            query += f" AND TRNDESC = '{description_lookup_clean}'"
        elif match_type == 'approximate':
            query += f" AND TRNDESC LIKE '%{description_lookup_clean}%'"
    
    if trn_type_lookup:
        query += f" AND TRNTYPE LIKE '%{trn_type_lookup}%'"

    # Order the results for proper post-processing in Pandas
    query += " ORDER BY ACC, TRNDATE, SEQ"

    combined_df = get_data_from_mysql(query)
            
    if combined_df.empty:
        print("Server Log (Statement of Account): No data found in MySQL for the specified criteria.")
        return []

    # --- Post-processing in Pandas (now includes previous balance calculation) ---

    # Ensure date columns are datetime objects for Pandas operations
    combined_df['TRNDATE_DT'] = pd.to_datetime(combined_df['TRNDATE'], errors='coerce')
    combined_df.dropna(subset=['TRNDATE_DT'], inplace=True)

    # Convert BAL and TRNNONC (original) to numeric, handling potential non-numeric strings
    combined_df['BAL'] = pd.to_numeric(combined_df['BAL'], errors='coerce').fillna(0)
    combined_df['TRNNONC'] = pd.to_numeric(combined_df['TRNNONC'], errors='coerce').fillna(0)

    # Calculate previous balance using Pandas shift (reverted to this for compatibility)
    # Ensure ACC is string for grouping
    combined_df['ACC_STR'] = combined_df['ACC'].astype(str)
    combined_df['BAL_RAW_PREVIOUS'] = combined_df.groupby('ACC_STR')['BAL'].shift(1)

    # Calculate TRNNONC_CALCULATED in Pandas based on Pandas-provided previous balance
    combined_df['TRNNONC_CALCULATED'] = combined_df['TRNNONC'] # Start with original TRNNONC

    # Apply conditional sign change based on balance movement, for non-first rows
    combined_df.loc[
        (combined_df['BAL'] < combined_df['BAL_RAW_PREVIOUS']) & (combined_df['BAL_RAW_PREVIOUS'].notna()),
        'TRNNONC_CALCULATED'
    ] = -combined_df['TRNNONC'].abs()

    combined_df.loc[
        (combined_df['BAL'] > combined_df['BAL_RAW_PREVIOUS']) & (combined_df['BAL_RAW_PREVIOUS'].notna()),
        'TRNNONC_CALCULATED'
    ] = combined_df['TRNNONC'].abs()

    # Handle the very first row of each group (BAL_RAW_PREVIOUS is NaN or 0)
    combined_df.loc[
        (combined_df['BAL_RAW_PREVIOUS'].isna()) & (combined_df['BAL'] < 0),
        'TRNNONC_CALCULATED'
    ] = -combined_df['TRNNONC'].abs()
    
    combined_df.loc[
        (combined_df['BAL_RAW_PREVIOUS'].isna()) & (combined_df['BAL'] >= 0),
        'TRNNONC_CALCULATED'
    ] = combined_df['TRNNONC'].abs()

    # Final edge case: If the original TRNNONC from CSV was 0, it should always remain 0.
    combined_df.loc[combined_df['TRNNONC'] == 0, 'TRNNONC_CALCULATED'] = 0


    # Re-sort the DataFrame back to the original desired output order (TRNDATE_DT, SEQ/TRN)
    # Use TRN_NUM_SORT if available, otherwise SEQ should be sufficient for tie-breaking
    if 'TRN' in combined_df.columns:
        combined_df['TRN_NUM_SORT'] = pd.to_numeric(combined_df['TRN'], errors='coerce').fillna(0)
        combined_df.sort_values(by=['TRNDATE_DT', 'TRN_NUM_SORT'], ascending=[True, True], inplace=True)
    else:
        combined_df.sort_values(by=['TRNDATE_DT', 'SEQ'], ascending=[True, True], inplace=True)


    # Format TRNDATE to mm/dd/yyyy
    combined_df['TRNDATE'] = combined_df['TRNDATE_DT'].dt.strftime('%m/%d/%Y')

    # Apply formatting for TRNAMT, TRNINT, TRNTAXPEN, BAL
    for col in ['TRNAMT', 'TRNINT', 'TRNTAXPEN', 'BAL']:
        if col in combined_df.columns:
            combined_df[col] = combined_df[col].apply(format_decimal_amount)
        else:
            combined_df[col] = '' # Ensure column exists and is empty string if not found

    # Apply formatting for the newly calculated TRNNONC
    combined_df['TRNNONC'] = combined_df['TRNNONC_CALCULATED'].apply(format_signed_amount)
    
    # Handle TLR, SEQ, TRN, TRNTYPE, LEVEL, TRNDESC columns explicitly to ensure they are strings and NaNs are handled
    for col in ['TLR', 'SEQ', 'TRN', 'TRNTYPE', 'LEVEL', 'TRNDESC']:
        if col in combined_df.columns:
            combined_df[col] = combined_df[col].astype(str).fillna('')
            if col == 'TLR': # Specific formatting for TLR if needed
                combined_df[col] = combined_df[col].apply(
                    lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.', '', 1).isdigit() else x
                )
        else:
            combined_df[col] = '' # Ensure column exists even if empty

    # MODIFIED: Add the 'Branch' column to the DataFrame
    combined_df['Branch'] = branch_name # Add the branch_name from the function argument

    # Ensure all required output columns are present and in order
    final_columns = ['TRN', 'ACC', 'TRNTYPE', 'TLR', 'LEVEL', 'TRNDATE',
                     'TRNAMT', 'TRNNONC', 'TRNINT', 'TRNTAXPEN', 'BAL', 'SEQ', 'TRNDESC', 'Branch'] # Added 'Branch'
    
    # Reindex to ensure all columns are present and in the correct order
    report_df = combined_df.reindex(columns=final_columns, fill_value='')

    print(f"Server Log (Statement of Account): Processed {len(report_df)} rows for Statement of Account report.")
    return report_df.to_dict(orient='records')

