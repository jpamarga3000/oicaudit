# audit_tool/backend/trial_balance_process.py
import os
import pandas as pd
import re
from datetime import datetime # Import datetime for date parsing

# Define the base directory where Trial Balance data is stored
TB_BASE_DIR = r"C:\xampp\htdocs\audit_tool\ACCOUTNING\TRIAL BALANCE"

# List of branches that should NOT have GL Code formatting
BRANCHES_NO_GL_FORMATTING = ['BAYUGAN', 'BALINGASAG', 'TORIL', 'ILUSTRE', 'TUBIGON']

# Helper function for GL Code formatting (reused from accounting_process)
def format_gl_code(code, branch_name=None): # Added branch_name parameter
    """
    Formats a GL Code string based on its digit length.
    - 1 digit: 1
    - 3 digits: x-xx
    - 5 digits: x-xx-xx
    - 9 digits: x-xx-xx-xxxx
    For specified branches, it returns the raw code as-is.
    """
    if pd.isna(code) or code is None:
        print(f"DEBUG (format_gl_code): Input code is NaN or None. Returning empty string.")
        return ''
    
    # Check if the current branch is one that should not have formatting
    if branch_name and branch_name.upper() in BRANCHES_NO_GL_FORMATTING:
        return str(code).strip() # Return as-is for these branches

    # Ensure input is string, remove existing hyphens and any other non-digit characters
    # This is a more aggressive cleaning to get only digits
    digits = ''.join(filter(str.isdigit, str(code).strip()))
    
    # Robustly remove .0 suffix if it's an integer-like float
    if digits.endswith('0') and len(digits) > 1 and digits[:-1].isdigit():
        pass

    length = len(digits)

    print(f"DEBUG (format_gl_code): Raw code input: '{code}', Cleaned digits: '{digits}', Length: {length}")

    if length == 1:
        return digits
    elif length == 3:
        return f"{digits[0]}-{digits[1:3]}"
    elif length == 5:
        return f"{digits[0]}-{digits[1:3]}-{digits[3:5]}"
    elif length == 9:
        return f"{digits[0]}-{digits[1:3]}-{digits[3:5]}-{digits[5:9]}"
    elif length == 6:
        if digits.endswith('0'):
            return f"{digits[0]}-{digits[1:3]}-{digits[3:5]}"
        else:
            return f"{digits[0]}-{digits[1:3]}-{digits[3:5]}-{digits[5]}"
    elif length == 10:
        return f"{digits[0]}-{digits[1:3]}-{digits[3:5]}-{digits[5:10]}"
    
    print(f"DEBUG (format_gl_code): No specific format matched for length {length}. Returning raw digits: '{digits}'")
    return digits # For any other length, just return the raw digits.

# Helper function for currency formatting (reused from accounting_process)
def format_currency(value):
    """
    Formats a numeric value to a currency string with comma separators,
    two decimal places, and parentheses for negative numbers.
    Returns blank string if value is NaN or None.
    """
    if pd.isna(value) or value is None:
        return ''
    
    num_val = float(value)

    if num_val < 0:
        return "({:,.2f})".format(abs(num_val))
    else:
        return "{:,.2f}".format(num_val)

def get_tb_as_of_dates(branch_name):
    """
    Lists CSV and Excel filenames (representing "As Of Dates") within a specific branch folder
    in the Trial Balance directory, accepting MM-DD-YYYY.csv/xlsx/xls format.

    Args:
        branch_name (str): The name of the branch folder.

    Returns:
        list: A list of valid "As Of Date" filenames (without extension) found in the branch folder,
              sorted chronologically. Returns an empty list if the folder doesn't exist or no valid files are found.
    """
    sanitized_branch = "".join([c for c in str(branch_name) if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch:
        print("Server Log (TB Process - get_tb_as_of_dates): Invalid branch name provided.")
        return []

    branch_folder_path = os.path.join(TB_BASE_DIR, sanitized_branch.upper())
    
    if not os.path.isdir(branch_folder_path):
        print(f"Server Log (TB Process - get_tb_as_of_dates): Branch folder not found: {branch_folder_path}")
        return []

    as_of_date_files = []
    print(f"Server Log (TB Process - get_tb_as_of_dates): Scanning directory: {branch_folder_path}")
    for filename in os.listdir(branch_folder_path):
        lower_filename = filename.lower()
        print(f"Server Log (TB Process - get_tb_as_of_dates): Found file: {filename}")
        
        # Include .xlsx and .xls now
        if lower_filename.endswith(('.csv', '.xlsx', '.xls')) and not filename.startswith('~'):
            base_name = os.path.splitext(filename)[0]
            print(f"Server Log (TB Process - get_tb_as_of_dates): Processing base_name: {base_name}")
            
            # Directly add the base_name to the list without strict date validation here.
            # Validation will happen during actual report processing.
            as_of_date_files.append(base_name)
            print(f"Server Log (TB Process - get_tb_as_of_dates): Added {base_name} to list.")
        else:
            print(f"Server Log (TB Process - get_tb_as_of_dates): Skipping file {filename}: Not a valid CSV/Excel extension or is a temp file.")
            continue
    
    # Sort the dates chronologically if they are in MM-DD-YYYY format, otherwise sort alphabetically
    def sort_key(filename_str):
        try:
            # Attempt to parse as MM-DD-YYYY for sorting
            return datetime.strptime(filename_str, '%m-%d-%Y')
        except ValueError:
            # If it's not a valid MM-DD-YYYY date, fall back to alphabetical sort
            # This handles date range filenames or other non-standard names gracefully in sort order
            return filename_str 

    as_of_date_files.sort(key=sort_key)
    
    print(f"Server Log (TB Process - get_tb_as_of_dates): Found {len(as_of_date_files)} valid TB files for branch '{branch_name}'. Final list: {as_of_date_files}")
    return as_of_date_files

def process_trial_balance_data(branch_name, as_of_date_filename):
    """
    Processes a specific Trial Balance CSV/Excel file for a given branch and "As Of Date".
    Formats GL Codes, determines DR/CR based on CBAL, and returns structured data.

    Args:
        branch_name (str): The name of the branch.
        as_of_date_filename (str): The filename (without extension) of the "As Of Date" CSV/Excel.

    Returns:
        list: A list of dictionaries representing the processed table data.
              Returns an empty list if the file is not found or an error occurs.
    """
    sanitized_branch = "".join([c for c in str(branch_name) if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch:
        print("Server Log (TB Process): Invalid branch name provided.")
        return []

    # Dynamically determine file extension for processing
    file_path_csv = os.path.join(TB_BASE_DIR, sanitized_branch.upper(), as_of_date_filename + '.csv')
    file_path_xlsx = os.path.join(TB_BASE_DIR, sanitized_branch.upper(), as_of_date_filename + '.xlsx')
    file_path_xls = os.path.join(TB_BASE_DIR, sanitized_branch.upper(), as_of_date_filename + '.xls')
    
    file_to_read = None
    if os.path.exists(file_path_csv):
        file_to_read = file_path_csv
    elif os.path.exists(file_path_xlsx):
        file_to_read = file_path_xlsx
    elif os.path.exists(file_path_xls):
        file_to_read = file_path_xls

    if not file_to_read:
        print(f"Server Log (TB Process): TB file not found (CSV, XLSX, or XLS) for: {as_of_date_filename} in branch {sanitized_branch}.")
        return []

    df = None
    read_success = False
    
    # Usecols for specified columns: Column A (0) for GLACC, Column C (2) for GL Name,
    # Column D (3) for DR, Column E (4) for CR.
    # Header=None because the first row is data, not headers.
    # ADDED: skiprows=1 to start reading from the second row (index 1)
    if file_to_read.endswith('.csv'):
        encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-8-sig']
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(file_to_read, encoding=encoding, header=None, usecols=[0, 2, 3, 4], dtype=str, skiprows=1)
                print(f"Server Log (TB Process): Read CSV file: {file_to_read} with encoding {encoding}, skipping first row.")
                read_success = True
                break
            except UnicodeDecodeError:
                pass
            except Exception as e:
                print(f"Server Log (TB Process): Error reading CSV file {file_to_read} with {encoding}: {e}")
    elif file_to_read.endswith(('.xlsx', '.xls')):
        try:
            df = pd.read_excel(file_to_read, header=None, usecols=[0, 2, 3, 4], dtype=str, skiprows=1)
            print(f"Server Log (TB Process): Read Excel file: {file_to_read}, skipping first row.")
            read_success = True
        except Exception as e:
            print(f"Server Log (TB Process): Error reading Excel file {file_to_read}: {e}")
    
    if not read_success or df is None:
        print(f"Server Log (TB Process): Failed to read TB file: {file_to_read}")
        return []

    # Rename columns for clarity: Column A (0) is GLACC, Column C (2) is TITLE,
    # Column D (3) is DR, Column E (4) is CR.
    df.rename(columns={0: 'GLACC', 2: 'TITLE', 3: 'DR_RAW', 4: 'CR_RAW'}, inplace=True)

    required_cols = ['GLACC', 'TITLE', 'DR_RAW', 'CR_RAW']
    if not all(col in df.columns for col in required_cols):
        print(f"Server Log (TB Process): Missing required columns in {file_to_read}. Expected: {', '.join(required_cols)}")
        return []
    
    # DEBUG: Print sample of raw GLACC data before formatting
    print("Server Log (TB Process - Debug): Sample raw GLACC (Column A) before formatting:")
    print(df['GLACC'].head().to_string())

    # Apply GL Code formatting using the existing format_gl_code helper function
    # Pass the branch_name to format_gl_code
    df['GL ACCOUNT'] = df['GLACC'].apply(lambda x: format_gl_code(x, branch_name))
    
    # DEBUG: Print sample of formatted GL ACCOUNT data
    print("Server Log (TB Process - Debug): Sample formatted 'GL ACCOUNT' after apply(format_gl_code):")
    print(df['GL ACCOUNT'].head().to_string())

    # Apply GL Name from TITLE
    df['GL NAME'] = df['TITLE'].astype(str).str.strip()

    # Convert DR_RAW and CR_RAW to numeric and apply currency formatting
    df['DR_VAL'] = df['DR_RAW'].astype(str).str.replace(',', '', regex=False).apply(pd.to_numeric, errors='coerce').fillna(0)
    df['CR_VAL'] = df['CR_RAW'].astype(str).str.replace(',', '', regex=False).apply(pd.to_numeric, errors='coerce').fillna(0)

    # NEW: Divide DR_VAL and CR_VAL by 100 as per previous instructions for TRNM, applying here for TB
    df['DR_VAL'] = df['DR_VAL'] 
    df['CR_VAL'] = df['CR_VAL'] 

    df['DR'] = df['DR_VAL'].apply(format_currency)
    df['CR'] = df['CR_VAL'].apply(format_currency)

    # Select and reorder final columns
    final_columns = ['GL ACCOUNT', 'GL NAME', 'DR', 'CR']
    report_df = df[final_columns]

    # Sort by GL ACCOUNT alphabetically
    report_df.sort_values(by='GL ACCOUNT', ascending=True, inplace=True)

    print(f"Server Log (TB Process): Processed {len(report_df)} rows for Trial Balance report.")
    return report_df.to_dict(orient='records')
