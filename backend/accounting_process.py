# audit_tool/backend/accounting_process.py
import os
import pandas as pd
from datetime import datetime
import re
from dateutil.relativedelta import relativedelta

# Import the new TRIAL_BALANCE_BASE_DIR from db_common
from backend.db_common import TRIAL_BALANCE_BASE_DIR 

# Define the base directory where accounting data is stored (for GL report processing)
ACCOUNTING_BASE_DIR = r"C:\xampp\htdocs\audit_tool\ACCOUTNING\GENERAL LEDGER"

# List of branches that should NOT have GL Code formatting for GL Names datalist
BRANCHES_NO_GL_FORMATTING_GL_NAMES = ['BAYUGAN', 'BALINGASAG', 'TORIL', 'ILUSTRE', 'TUBIGON']

# Helper function for currency formatting
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

def _format_gl_code(gl_acc_raw):
    """
    Formats a raw GLACC string into x-xx, x-xx-xx, x-xx-xx-xxxx format.
    Removes non-digit characters before formatting.
    This helper is used for standard formatting, not for the "as-is" branches.
    """
    if pd.isna(gl_acc_raw) or gl_acc_raw is None:
        return ''
    
    # Ensure gl_acc_raw is a string and remove any non-digit characters
    gl_acc_str = str(gl_acc_raw).strip()
    gl_acc_digits = ''.join(filter(str.isdigit, gl_acc_str))

    if not gl_acc_digits:
        return gl_acc_str # Return original if no digits found

    length = len(gl_acc_digits)

    if length == 1:
        return gl_acc_digits
    elif length == 3:
        return f"{gl_acc_digits[0]}-{gl_acc_digits[1:3]}"
    elif length == 5:
        return f"{gl_acc_digits[0]}-{gl_acc_digits[1:3]}-{gl_acc_digits[3:5]}"
    elif length == 9:
        return f"{gl_acc_digits[0]}-{gl_acc_digits[1:3]}-{gl_acc_digits[3:5]}-{gl_acc_digits[5:9]}"
    elif length == 6:
        if gl_acc_digits.endswith('0'):
            return f"{gl_acc_digits[0]}-{gl_acc_digits[1:3]}-{gl_acc_digits[3:5]}"
        else:
            return f"{gl_acc_digits[0]}-{gl_acc_digits[1:3]}-{gl_acc_digits[3:5]}-{gl_acc_digits[5]}"
    elif length == 10:
        return f"{gl_acc_digits[0]}-{gl_acc_digits[1:3]}-{gl_acc_digits[3:5]}-{gl_acc_digits[5:10]}"
    else:
        return gl_acc_digits # Return raw digits if not matching specific lengths

def get_gl_names_and_codes_from_file(branch_name):
    """
    Reads GL Name and GL Code from the latest dated CSV file within the
    branch's subfolder in the TRIAL_BALANCE_BASE_DIR.
    Returns a list of dictionaries, each with 'TITLE' (GL Name),
    'GLACC_RAW' (unformatted GL Code), and 'GLACC_FORMATTED' (formatted GL Code).
    The formatting of 'GLACC_FORMATTED' depends on the branch_name.
    """
    sanitized_branch_name = "".join([c for c in branch_name if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_').upper()
    if not sanitized_branch_name:
        print("Server Log (Accounting Process - GL Name): Invalid branch name provided for GL Name lookup.")
        return []

    # Construct the path to the branch's subfolder within TRIAL_BALANCE_BASE_DIR
    branch_folder_path = os.path.join(TRIAL_BALANCE_BASE_DIR, sanitized_branch_name)
    
    print(f"Server Log (Accounting Process - GL Name): Looking for GL name file in: {branch_folder_path}")

    if not os.path.isdir(branch_folder_path):
        print(f"Server Log (Accounting Process - GL Name): Branch folder not found: {branch_folder_path}")
        return []

    latest_file = None
    latest_date = None

    # Regex to extract MM-DD-YYYY date from filename
    date_pattern = re.compile(r'(\d{2}-\d{2}-\d{4})')

    for filename in os.listdir(branch_folder_path):
        if filename.lower().endswith('.csv'):
            match = date_pattern.search(filename)
            if match:
                try:
                    file_date_str = match.group(1)
                    file_date = datetime.strptime(file_date_str, '%m-%d-%Y')
                    
                    if latest_date is None or file_date > latest_date:
                        latest_date = file_date
                        latest_file = os.path.join(branch_folder_path, filename)
                except ValueError:
                    print(f"Server Log (Accounting Process - GL Name): Could not parse date from filename: {filename}")
                    continue
    
    if not latest_file:
        print(f"Server Log (Accounting Process - GL Name): No CSV file with MM-DD-YYYY date format found in {branch_folder_path}.")
        return []

    print(f"Server Log (Accounting Process - GL Name): Found latest file: {latest_file}")
    
    gl_data_list = []
    encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-8-sig']

    df = None
    read_success = False

    for encoding in encodings_to_try:
        try:
            # Read CSV, specifying columns by index (0 for GLACC, 2 for TITLE)
            # Header=None because the first row is data, not headers.
            # skiprows=1 to start reading from the second row (index 1)
            df = pd.read_csv(latest_file, encoding=encoding, header=None, usecols=[0, 2], dtype=str, skiprows=1)
            read_success = True
            print(f"Server Log (Accounting Process - GL Name): Successfully read CSV file: {latest_file} with encoding: {encoding}, skipping first row.")
            break
        except UnicodeDecodeError:
            print(f"Server Log (Accounting Process - GL Name): UnicodeDecodeError with {encoding} for {latest_file}. Trying next encoding...")
            pass # Try next encoding
        except Exception as e:
            print(f"Server Log (Accounting Process - GL Name): Error reading CSV GL Name file {latest_file} with {encoding}: {e}")
    
    if read_success and df is not None:
        # Rename columns for clarity based on user's request: Column A is GLACC (raw), Column C is TITLE
        df.rename(columns={0: 'GLACC_RAW', 2: 'TITLE'}, inplace=True)

        required_cols = ['GLACC_RAW', 'TITLE']
        if not all(col in df.columns for col in required_cols):
            print(f"Server Log (Accounting Process - GL Name): Found {latest_file}, but missing 'GLACC_RAW' or 'TITLE' columns. Available columns: {df.columns.tolist()}")
            return []

        for index, row in df.iterrows():
            title = str(row['TITLE']).strip() if pd.notna(row['TITLE']) else ''
            gl_acc_raw = str(row['GLACC_RAW']).strip() if pd.notna(row['GLACC_RAW']) else ''
            
            if title and gl_acc_raw:
                # Determine if GL Code should be formatted or left as is
                if sanitized_branch_name in BRANCHES_NO_GL_FORMATTING_GL_NAMES:
                    gl_acc_final = gl_acc_raw # "as is"
                    print(f"DEBUG (GL Name): Branch '{sanitized_branch_name}' detected. GLACC '{gl_acc_raw}' returned as-is.")
                else:
                    gl_acc_final = _format_gl_code(gl_acc_raw) # Apply formatting
                    print(f"DEBUG (GL Name): Branch '{sanitized_branch_name}' detected. GLACC '{gl_acc_raw}' formatted to '{gl_acc_final}'.")
                
                gl_data_list.append({'TITLE': title, 'GLACC_RAW': gl_acc_raw, 'GLACC_FORMATTED': gl_acc_final})
        
        print(f"Server Log (Accounting Process - GL Name): Extracted {len(gl_data_list)} GL name entries from {latest_file}.")
        if gl_data_list:
            print("Server Log (Accounting Process - GL Name): Sample of populated GL name entries (first 5 items):")
            for i, item in enumerate(gl_data_list):
                if i >= 5: break
                print(f"  GL Name: '{item['TITLE']}', Raw GL Code: '{item['GLACC_RAW']}', Formatted GL Code: '{item['GLACC_FORMATTED']}'")
    else:
        print(f"Server Log (Accounting Process - GL Name): Could not read GL Name file: {latest_file} with any tried encoding or format.")
    
    return gl_data_list


def _load_and_process_base_gl_data(branch, from_date_str, to_date_str):
    """
    Loads and processes base GL data for a specific branch and date range.
    Combines data from all Excel/CSV files in the branch's GL folder,
    filters by date range, and calculates DR/CR based on AMT and BAL.
    Returns the processed DataFrame including original 'GLACC' for further use.
    """
    sanitized_branch_name = "".join([c for c in branch if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch_name:
        print("Server Log (Base GL Data): Invalid branch name provided.")
        return pd.DataFrame()

    branch_folder_path = os.path.join(ACCOUNTING_BASE_DIR, sanitized_branch_name.upper())
    print(f"Server Log (Base GL Data): Loading GL data for branch: {branch_folder_path}")
    print(f"Server Log (Base GL Data): Date Range: {from_date_str} to {to_date_str}")

    if not os.path.isdir(branch_folder_path):
        print(f"Server Log (Base GL Data): Branch folder not found: {branch_folder_path}")
        return pd.DataFrame()

    all_gl_data = []
    encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-8-sig']

    try:
        from_date = datetime.strptime(from_date_str, '%m/%d/%Y')
        to_date = datetime.strptime(to_date_str, '%m/%d/%Y')
    except ValueError as e:
        print(f"Server Log (Base GL Data): Invalid date format received from frontend: {e}")
        return pd.DataFrame()

    def parse_filename_dates(filename):
        match_month_year = re.match(r'.* - (\w{3} \d{4}) to (\w{3} \d{4})\.csv$', filename, re.IGNORECASE)
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

    for filename in os.listdir(branch_folder_path):
        lower_filename = filename.lower()
        
        if not (lower_filename.endswith('.csv') or lower_filename.endswith(('.xlsx', '.xls'))):
            continue

        file_path = os.path.join(branch_folder_path, filename)
        
        file_start_date, file_end_date = parse_filename_dates(filename)

        if file_start_date is None or file_end_date is None:
            print(f"Server Log (Base GL Data): Skipping file {filename}: Could not parse date range from filename.")
            continue

        if not (file_start_date <= to_date and file_end_date >= from_date):
            continue

        df = None
        read_success = False
        if lower_filename.endswith(('.xlsx', '.xls')):
            try:
                df = pd.read_excel(file_path, dtype={'GLACC': str}) # Read GLACC as string
                read_success = True
            except Exception as e:
                print(f"Server Log (Base GL Data): Error reading Excel file {filename}: {e}")
        elif lower_filename.endswith('.csv'):
            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, dtype={'GLACC': str}) # Read GLACC as string
                    read_success = True
                    break
                except UnicodeDecodeError:
                    pass
                except Exception as e:
                    print(f"Server Log (Base GL Data): Error reading CSV file {filename} with {encoding}: {e}")
        
        if read_success and df is not None:
            df.columns = [col.strip().upper() for col in df.columns]

            required_cols = ['DOCDATE', 'TRN', 'DESC', 'REF', 'AMT', 'BAL', 'GLACC'] 
            if not all(col in df.columns for col in required_cols):
                print(f"Server Log (Base GL Data): Skipping {filename}: Missing one or more required columns ({', '.join(required_cols)}).")
                continue

            df['DOCDATE_DT'] = pd.to_datetime(df['DOCDATE'], errors='coerce')
            df.dropna(subset=['DOCDATE_DT'], inplace=True)

            df_filtered_date = df[
                (df['DOCDATE_DT'] >= from_date) & 
                (df['DOCDATE_DT'] <= to_date)
            ].copy()

            if not df_filtered_date.empty:
                df_filtered_date['AMT_NUM'] = df_filtered_date['AMT'].astype(str).str.replace(',', '', regex=False).apply(pd.to_numeric, errors='coerce').fillna(0)
                df_filtered_date['BAL_NUM'] = df_filtered_date['BAL'].astype(str).str.replace(',', '', regex=False).apply(pd.to_numeric, errors='coerce').fillna(0)
                all_gl_data.append(df_filtered_date)
            else:
                print(f"Server Log (Base GL Data): No data within date range for {filename}.")
        else:
            print(f"Server Log (Base GL Data): Could not read file: {filename}")

    if not all_gl_data:
        print("Server Log (Base GL Data): No relevant GL data found across all files for the specified criteria.")
        return pd.DataFrame()

    combined_df = pd.concat(all_gl_data, ignore_index=True)

    if 'TRN' in combined_df.columns:
        combined_df['TRN_NUM_SORT'] = pd.to_numeric(combined_df['TRN'], errors='coerce').fillna(0)
        combined_df.sort_values(by=['DOCDATE_DT', 'TRN_NUM_SORT'], ascending=[True, True], inplace=True)
    else:
        combined_df.sort_values(by=['DOCDATE_DT'], ascending=[True], inplace=True)

    # Calculate DR and CR based on BALANCE change
    combined_df['BALANCE_CHANGE'] = combined_df['BAL_NUM'].diff()

    combined_df['DR_VAL'] = 0.0
    combined_df['CR_VAL'] = 0.0

    combined_df.loc[combined_df['BALANCE_CHANGE'] > 0, 'DR_VAL'] = combined_df['AMT_NUM'].abs()
    combined_df.loc[combined_df['BALANCE_CHANGE'] < 0, 'CR_VAL'] = combined_df['AMT_NUM'].abs()

    # Handle the very first row
    if not combined_df.empty:
        first_row_index = combined_df.index[0]
        if pd.isna(combined_df.loc[first_row_index, 'BALANCE_CHANGE']):
            initial_bal = combined_df.loc[first_row_index, 'BAL_NUM']
            initial_amt = combined_df.loc[first_row_index, 'AMT_NUM']
            if initial_bal > 0:
                combined_df.loc[first_row_index, 'DR_VAL'] = initial_amt
            elif initial_bal < 0:
                combined_df.loc[first_row_index, 'CR_VAL'] = initial_amt
    
    return combined_df.copy() # Return a copy to avoid SettingWithCopyWarning


def process_gl_report(branch, from_date_str, to_date_str, gl_code_lookup):
    """
    Processes GL data for a specific branch, date range, and GL Code.
    Leverages _load_and_process_base_gl_data and then filters by GLACC.
    """
    df = _load_and_process_base_gl_data(branch, from_date_str, to_date_str)
    if df.empty:
        print("Server Log (GL Report): No base GL data to process.")
        return []

    # Filter by GLACC (raw, no hyphens)
    # Ensure GLACC is treated as string for comparison
    df_filtered_glacc = df[df['GLACC'].astype(str).str.replace('-', '').str.strip() == gl_code_lookup].copy()
    
    if df_filtered_glacc.empty:
        print(f"Server Log (GL Report): No data for GLACC '{gl_code_lookup}' after filtering.")
        return []

    # Add GL Code and GL Name for GL report specifically
    # Now, get_gl_names_and_codes_from_file returns a list of dicts with 'TITLE', 'GLACC_RAW', and 'GLACC_FORMATTED'
    gl_names_and_codes_list = get_gl_names_and_codes_from_file(branch)
    
    # Create a map from formatted GLACC to TITLE for easy lookup
    gl_code_to_name_map = {item['GLACC_FORMATTED']: item['TITLE'] for item in gl_names_and_codes_list}
    
    # Apply the formatted GL Code and GL Name to the report DataFrame
    # Use the _format_gl_code to ensure consistency if the raw GLACC is directly used
    # Note: For the GL Report table itself, we always want the formatted version.
    df_filtered_glacc['GL CODE'] = df_filtered_glacc['GLACC'].apply(_format_gl_code)
    
    # Map GL Name using the formatted GL CODE
    df_filtered_glacc['GL NAME'] = df_filtered_glacc['GL CODE'].map(gl_code_to_name_map).fillna('')


    # Format output columns
    df_filtered_glacc['DATE'] = df_filtered_glacc['DOCDATE_DT'].dt.strftime('%m/%d/%Y')
    df_filtered_glacc['TRN'] = df_filtered_glacc['TRN'].astype(str)
    df_filtered_glacc['DESCRIPTION'] = df_filtered_glacc['DESC'].astype(str)
    df_filtered_glacc['REF'] = df_filtered_glacc['REF'].astype(str)
    
    df_filtered_glacc['DR'] = df_filtered_glacc['DR_VAL'].apply(lambda x: format_currency(x) if x != 0 else '')
    df_filtered_glacc['CR'] = df_filtered_glacc['CR_VAL'].apply(lambda x: format_currency(x) if x != 0 else '')
    df_filtered_glacc['BALANCE'] = df_filtered_glacc['BAL_NUM'].apply(format_currency)

    # Select and reorder final columns for GL report
    final_columns = ['DATE', 'GL CODE', 'GL NAME', 'TRN', 'DESCRIPTION', 'REF', 'DR', 'CR', 'BALANCE']
    report_df = df_filtered_glacc[final_columns]

    print(f"Server Log (GL Report): Processed {len(report_df)} rows for GL report.")
    return report_df.to_dict(orient='records')
