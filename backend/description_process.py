# audit_tool/backend/description_process.py
import os
import pandas as pd
from datetime import datetime
import re
from dateutil.relativedelta import relativedelta

# Define the base directory where accounting data is stored
ACCOUNTING_BASE_DIR = r"C:\xampp\htdocs\audit_tool\ACCOUTNING\GENERAL LEDGER"
GL_NAME_FILE_DIR = os.path.join(ACCOUNTING_BASE_DIR, "GL NAME") # Directory for GL Name lookup files

# Helper function for currency formatting (duplicated for self-containment)
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

def _format_gl_code(gl_acc):
    """
    Formats a GLACC string into x-xx-xx or x-xx-xx-xxxx format.
    Removes non-digit characters before formatting.
    (Duplicated for self-containment)
    """
    if pd.isna(gl_acc) or gl_acc is None:
        return ''
    
    # Ensure gl_acc is a string and remove any non-digit characters
    gl_acc_str = str(gl_acc).strip().replace('-', '')

    if not gl_acc_str.isdigit():
        return gl_acc_str # Return as-is if not purely numeric

    length = len(gl_acc_str)
    if length == 5:
        return f"{gl_acc_str[0]}-{gl_acc_str[1:3]}-{gl_acc_str[3:5]}"
    elif length == 9:
        return f"{gl_acc_str[0]}-{gl_acc_str[1:3]}-{gl_acc_str[3:5]}-{gl_acc_str[5:9]}"
    else:
        return gl_acc_str # Return original if not 5 or 9 digits

def get_gl_names_and_codes_from_file(branch_name):
    """
    Reads GL Name and GL Code from an Excel/CSV file named after the branch,
    located within the 'ACCOUNTING/GENERAL LEDGER/GL NAME/' directory.
    Returns a dictionary mapping GLACC (cleaned, no hyphens) to TITLE.
    (Duplicated for self-containment)
    """
    sanitized_branch_name = "".join([c for c in branch_name if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch_name:
        print("Server Log (Description Process - GL Name): Invalid branch name provided for GL Name lookup.")
        return {}

    expected_filename_prefix = sanitized_branch_name.upper()
    
    gl_name_map = {}
    file_found_and_processed = False
    
    encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-8-sig']

    for ext in ['.xlsx', '.xls', '.csv']:
        filename = f"{expected_filename_prefix}{ext}"
        file_path = os.path.join(GL_NAME_FILE_DIR, filename)
        
        if os.path.exists(file_path):
            df = None
            read_success = False

            if ext in ['.xlsx', '.xls']:
                try:
                    df = pd.read_excel(file_path, dtype={'GLACC': str}) # Read GLACC as string
                    read_success = True
                except Exception as e:
                    print(f"Server Log (Description Process - GL Name): Error reading Excel GL Name file {filename}: {e}")
            elif ext == '.csv':
                for encoding in encodings_to_try:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, dtype={'GLACC': str}) # Read GLACC as string
                        read_success = True
                        break
                    except UnicodeDecodeError:
                        pass # Try next encoding
                    except Exception as e:
                        print(f"Server Log (Description Process - GL Name): Error reading CSV GL Name file {filename} with {encoding}: {e}")
            
            if read_success and df is not None:
                file_found_and_processed = True

                df.columns = [col.strip().upper() for col in df.columns]

                required_cols = ['TITLE', 'GLACC']
                if all(col in df.columns for col in required_cols):
                    for index, row in df.iterrows():
                        title = str(row['TITLE']).strip() if pd.notna(row['TITLE']) else ''
                        gl_acc = str(row['GLACC']).strip() if pd.notna(row['GLACC']) else ''
                        
                        # Further cleaning for gl_acc: remove .0 if it's a float representation of an integer
                        if gl_acc.endswith('.0') and gl_acc[:-2].isdigit():
                            gl_acc = gl_acc[:-2]
                        
                        # Remove hyphens for lookup key
                        gl_acc_lookup = gl_acc.replace('-', '')

                        if title and gl_acc_lookup:
                            gl_name_map[gl_acc_lookup] = title
                    if gl_name_map:
                        break # Stop after finding and processing the first valid file
                else:
                    print(f"Server Log (Description Process - GL Name): Found {filename}, but missing 'TITLE' or 'GLACC' columns. Available columns: {df.columns.tolist()}")
            else:
                print(f"Server Log (Description Process - GL Name): Could not read GL Name file: {filename} with any tried encoding or format.")
    
    if not file_found_and_processed:
        print(f"Server Log (Description Process - GL Name): No suitable GL Name file found for branch '{branch_name}' in {GL_NAME_FILE_DIR}.")
    elif not gl_name_map:
        print(f"Server Log (Description Process - GL Name): No GL name data extracted from the found file(s) for branch '{branch_name}'. This might mean the file was empty or rows had no valid TITLE/GLACC.")

    return gl_name_map

def _load_and_process_base_gl_data(branch, from_date_str, to_date_str):
    """
    Loads and processes base GL data for a specific branch and date range.
    Combines data from all Excel/CSV files in the branch's GL folder,
    filters by date range, and calculates DR/CR based on AMT and BAL.
    Returns the processed DataFrame including original 'GLACC' for further use.
    (Duplicated for self-containment)
    """
    sanitized_branch_name = "".join([c for c in branch if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch_name:
        print("Server Log (Description Process - Base GL Data): Invalid branch name provided.")
        return pd.DataFrame()

    branch_folder_path = os.path.join(ACCOUNTING_BASE_DIR, sanitized_branch_name.upper())
    print(f"Server Log (Description Process - Base GL Data): Loading GL data for branch: {branch_folder_path}")
    print(f"Server Log (Description Process - Base GL Data): Date Range: {from_date_str} to {to_date_str}")

    if not os.path.isdir(branch_folder_path):
        print(f"Server Log (Description Process - Base GL Data): Branch folder not found: {branch_folder_path}")
        return pd.DataFrame()

    all_gl_data = []
    encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-8-sig']

    try:
        from_date = datetime.strptime(from_date_str, '%m/%d/%Y')
        to_date = datetime.strptime(to_date_str, '%m/%d/%Y')
    except ValueError as e:
        print(f"Server Log (Description Process - Base GL Data): Invalid date format received from frontend: {e}")
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

        match_full_date = re.match(r'.* - (\d{2}-\d{2}-\d{4}) to (\d{2}-\d{2}-\d{4})\.csv$', filename, re.IGNORECASE)
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
            print(f"Server Log (Description Process - Base GL Data): Skipping file {filename}: Could not parse date range from filename.")
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
                print(f"Server Log (Description Process - Base GL Data): Error reading Excel file {filename}: {e}")
        elif lower_filename.endswith('.csv'):
            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, dtype={'GLACC': str}) # Read GLACC as string
                    read_success = True
                    break
                except UnicodeDecodeError:
                    pass
                except Exception as e:
                    print(f"Server Log (Description Process - Base GL Data): Error reading CSV file {filename} with {encoding}: {e}")
        
        if read_success and df is not None:
            df.columns = [col.strip().upper() for col in df.columns]

            required_cols = ['DOCDATE', 'TRN', 'DESC', 'REF', 'AMT', 'BAL', 'GLACC'] 
            if not all(col in df.columns for col in required_cols):
                print(f"Server Log (Description Process - Base GL Data): Skipping {filename}: Missing one or more required columns ({', '.join(required_cols)}).")
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
                print(f"Server Log (Description Process - Base GL Data): No data within date range for {filename}.")
        else:
            print(f"Server Log (Description Process - Base GL Data): Could not read file: {filename}")

    if not all_gl_data:
        print("Server Log (Description Process - Base GL Data): No relevant GL data found across all files for the specified criteria.")
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


def process_desc_report(branch, from_date_str, to_date_str, description_lookup, match_type):
    """
    Processes Accounting Description data: loads GL data, adds GL Code/Name,
    and filters by DESC field.
    """
    df = _load_and_process_base_gl_data(branch, from_date_str, to_date_str)
    if df.empty:
        print("Server Log (Description Report): No base GL data to process.")
        return []

    # Add GL Code and GL Name
    gl_name_map = get_gl_names_and_codes_from_file(branch)
    df['GLACC_CLEAN'] = df['GLACC'].astype(str).str.replace('-', '').str.strip()
    df['GL CODE'] = df['GLACC'].apply(_format_gl_code)
    df['GL NAME'] = df['GLACC_CLEAN'].map(gl_name_map).fillna('')

    # Filter by DESC
    if match_type == 'exact':
        df_filtered = df[df['DESC'].astype(str).str.strip().str.upper() == description_lookup.upper().strip()].copy()
    else: # approximate
        df_filtered = df[df['DESC'].astype(str).str.strip().str.upper().str.contains(description_lookup.upper().strip(), na=False)].copy()

    if df_filtered.empty:
        print(f"Server Log (Description Report): No data found for description '{description_lookup}'.")
        return []

    # Format output columns
    df_filtered['DATE'] = df_filtered['DOCDATE_DT'].dt.strftime('%m/%d/%Y')
    df_filtered['TRN'] = df_filtered['TRN'].astype(str)
    df_filtered['DESCRIPTION'] = df_filtered['DESC'].astype(str)
    df_filtered['REF'] = df_filtered['REF'].astype(str)
    
    df_filtered['DR'] = df_filtered['DR_VAL'].apply(lambda x: format_currency(x) if x != 0 else '')
    df_filtered['CR'] = df_filtered['CR_VAL'].apply(lambda x: format_currency(x) if x != 0 else '')
    df_filtered['BALANCE'] = df_filtered['BAL_NUM'].apply(format_currency)

    # Select and reorder final columns
    final_columns = ['DATE', 'GL CODE', 'GL NAME', 'TRN', 'DESCRIPTION', 'REF', 'DR', 'CR', 'BALANCE']
    report_df = df_filtered[final_columns]

    print(f"Server Log (Description Report): Processed {len(report_df)} rows.")
    return report_df.to_dict(orient='records')
