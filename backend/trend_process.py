# audit_tool/backend/trend_process.py
import os
import pandas as pd
from datetime import datetime, timedelta
import re
from dateutil.relativedelta import relativedelta

# Define the base directory where accounting data is stored
ACCOUNTING_BASE_DIR = r"C:\xampp\htdocs\audit_tool\ACCOUTNING\GENERAL LEDGER"

# Helper function for currency formatting (copied from accounting_process for self-containment)
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

def process_trend_report(branch, from_date_str, to_date_str, gl_code_lookup, frequency):
    """
    Processes GL data for a specific branch, date range, GL Code, and frequency.
    Generates a trend report showing the last transaction's balance for each period.
    Includes logic for previous period balance, GL code multipliers, and nominal account rules.

    Args:
        branch (str): The selected branch name.
        from_date_str (str): Start date in MM/DD/YYYY format.
        to_date_str (str): End date in MM/DD/YYYY format.
        gl_code_lookup (str): The GL Code to filter by (without hyphens).
        frequency (str): 'daily', 'monthly', 'semi-annually', 'annually'.

    Returns:
        list: A list of dictionaries representing the processed table data (Date, Balance, Change).
              Returns an empty list if no data is found or an error occurs.
    """
    sanitized_branch_name = "".join([c for c in branch if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch_name:
        print("Server Log (TREND Report): Invalid branch name provided.")
        return []

    branch_folder_path = os.path.join(ACCOUNTING_BASE_DIR, sanitized_branch_name.upper())
    print(f"Server Log (TREND Report): Processing TREND report for branch: {branch_folder_path}")
    print(f"Server Log (TREND Report): Date Range: {from_date_str} to {to_date_str}, GL Code: {gl_code_lookup}, Frequency: {frequency}")

    if not os.path.isdir(branch_folder_path):
        print(f"Server Log (TREND Report): Branch folder not found: {branch_folder_path}")
        return []

    all_gl_data_raw = [] # To store all relevant GL data before filtering by GLACC and date range
    encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-8-sig']

    try:
        from_date = datetime.strptime(from_date_str, '%m/%d/%Y')
        to_date = datetime.strptime(to_date_str, '%m/%d/%Y')
    except ValueError as e:
        print(f"Server Log (TREND Report): Invalid date format received from frontend: {e}")
        return []

    # Calculate the extended_from_date to include the previous period for initial balance calculation
    extended_from_date = from_date
    if frequency == 'daily':
        extended_from_date = from_date - timedelta(days=1)
    elif frequency == 'monthly':
        # Get the first day of the 'from_date's month, then subtract one month
        extended_from_date = (from_date.replace(day=1) - relativedelta(months=1))
    elif frequency == 'semi-annually':
        # Determine the start of the current semi-annual period
        current_semi_annual_start = datetime(from_date.year, 1 if from_date.month <= 6 else 7, 1)
        # Subtract 6 months to get to the start of the previous semi-annual period
        extended_from_date = current_semi_annual_start - relativedelta(months=6)
    elif frequency == 'annually':
        extended_from_date = datetime(from_date.year - 1, 1, 1) # Start of previous year

    print(f"Server Log (TREND Report): Extended date range for file selection: {extended_from_date.strftime('%m/%d/%Y')} to {to_date.strftime('%m/%d/%Y')}")


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
        if not lower_filename.endswith('.csv'):
            continue

        file_path = os.path.join(branch_folder_path, filename)
        file_start_date, file_end_date = parse_filename_dates(filename)

        if file_start_date is None or file_end_date is None:
            print(f"Server Log (TREND Report): Skipping file {filename}: Could not parse date range from filename.")
            continue

        # Check for overlap with the *extended* date range for efficient file loading
        if not (file_start_date <= to_date and file_end_date >= extended_from_date):
            print(f"Server Log (TREND Report): Skipping file {filename}: Date range from filename ({file_start_date.strftime('%Y-%m-%d')} to {file_end_date.strftime('%Y-%m-%d')}) does not overlap with extended requested range.")
            continue

        df = None
        read_success = False
        if lower_filename.endswith(('.xlsx', '.xls')): # Although only CSV is expected, keep for robustness
            try:
                df = pd.read_excel(file_path)
                read_success = True
            except Exception as e:
                print(f"Server Log (TREND Report): Error reading Excel file {filename}: {e}")
        elif lower_filename.endswith('.csv'):
            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    read_success = True
                    break
                except UnicodeDecodeError:
                    pass
                except Exception as e:
                    print(f"Server Log (TREND Report): Error reading CSV file {filename} with {encoding}: {e}")
        
        if read_success and df is not None:
            df.columns = [col.strip().upper() for col in df.columns]
            required_cols = ['DOCDATE', 'TRN', 'DESC', 'REF', 'AMT', 'BAL', 'GLACC'] 
            if not all(col in df.columns for col in required_cols):
                print(f"Server Log (TREND Report): Skipping {filename}: Missing required columns.")
                continue

            df['DOCDATE_DT'] = pd.to_datetime(df['DOCDATE'], errors='coerce')
            df.dropna(subset=['DOCDATE_DT'], inplace=True)
            
            # Convert AMT and BAL to numeric, handling missing values
            df['AMT_NUM'] = df['AMT'].astype(str).str.replace(',', '', regex=False).apply(pd.to_numeric, errors='coerce').fillna(0)
            df['BAL_NUM'] = df['BAL'].astype(str).str.replace(',', '', regex=False).apply(pd.to_numeric, errors='coerce').fillna(0)
            
            all_gl_data_raw.append(df)
            print(f"Server Log (TREND Report): Added raw data from {filename} ({len(df)} rows).")
        else:
            print(f"Server Log (TREND Report): Could not read file: {filename}")

    if not all_gl_data_raw:
        print("Server Log (TREND Report): No raw GL data found in any files.")
        return []

    combined_df_raw = pd.concat(all_gl_data_raw, ignore_index=True)
    
    # Filter by GLACC (raw, no hyphens) across all loaded data
    gl_code_lookup_clean = gl_code_lookup.replace('-', '').strip()
    combined_df_gl_filtered = combined_df_raw[
        combined_df_raw['GLACC'].astype(str).str.replace('-', '').str.strip() == gl_code_lookup_clean
    ].copy()
    
    if combined_df_gl_filtered.empty:
        print(f"Server Log (TREND Report): No data found for GLACC '{gl_code_lookup_clean}' after initial filtering.")
        return []

    # Sort by DOCDATE_DT and then by TRN for consistent "last transaction" logic
    if 'TRN' in combined_df_gl_filtered.columns:
        combined_df_gl_filtered['TRN_NUM_SORT'] = pd.to_numeric(combined_df_gl_filtered['TRN'], errors='coerce').fillna(0)
        combined_df_gl_filtered.sort_values(by=['DOCDATE_DT', 'TRN_NUM_SORT'], ascending=[True, True], inplace=True)
    else:
        combined_df_gl_filtered.sort_values(by=['DOCDATE_DT'], ascending=[True], inplace=True)

    # --- Calculate initial_previous_balance for the very first period's 'Change' calculation ---
    initial_previous_balance = 0.0
    
    # Determine the start and end date of the period *before* the 'from_date'
    prev_period_start_date = None
    prev_period_end_date = None

    if frequency == 'daily':
        prev_period_end_date = from_date - timedelta(days=1)
        prev_period_start_date = prev_period_end_date # For daily, start and end are the same
    elif frequency == 'monthly':
        prev_period_end_date = from_date.replace(day=1) - timedelta(days=1)
        prev_period_start_date = prev_period_end_date.replace(day=1)
    elif frequency == 'semi-annually':
        # Find the start of the 'from_date's semi-annual period
        current_semi_annual_start = datetime(from_date.year, 1 if from_date.month <= 6 else 7, 1)
        prev_period_end_date = current_semi_annual_start - timedelta(days=1)
        prev_period_start_date = datetime(prev_period_end_date.year, 1 if prev_period_end_date.month <= 6 else 7, 1)
    elif frequency == 'annually':
        prev_period_end_date = datetime(from_date.year - 1, 12, 31)
        prev_period_start_date = datetime(from_date.year - 1, 1, 1)

    if prev_period_start_date and prev_period_end_date:
        # Filter for the previous period's data
        df_prev_period = combined_df_gl_filtered[ # This is correct, it uses the already filtered-by-GLACC data
            (combined_df_gl_filtered['DOCDATE_DT'] >= prev_period_start_date) &
            (combined_df_gl_filtered['DOCDATE_DT'] <= prev_period_end_date)
        ]
        if not df_prev_period.empty:
            # Get the last balance of the previous period
            initial_previous_balance = df_prev_period['BAL_NUM'].iloc[-1]
            print(f"Server Log (TREND Report): Found initial previous balance of {initial_previous_balance} for GLACC '{gl_code_lookup_clean}' from {prev_period_start_date.strftime('%m/%d/%Y')} to {prev_period_end_date.strftime('%m/%d/%Y')}.")
        else:
            print(f"Server Log (TREND Report): No data found for GLACC '{gl_code_lookup_clean}' in previous period ({prev_period_start_date.strftime('%m/%d/%Y')} to {prev_period_end_date.strftime('%m/%d/%Y')}). Initial previous balance remains 0.")
    else:
        print("Server Log (TREND Report): Could not determine previous period dates for initial balance calculation.")

    # --- Apply -1 multiplier based on GL Code prefix (2, 3, or 4) ---
    gl_code_prefix = gl_code_lookup_clean[0]
    if gl_code_prefix in ['2', '3', '4']:
        print(f"Server Log (TREND Report): Applying -1 multiplier for GL Code prefix '{gl_code_prefix}'.")
        combined_df_gl_filtered['BAL_NUM'] *= -1
        combined_df_gl_filtered['AMT_NUM'] *= -1 # Also flip AMT for consistency if needed later
        initial_previous_balance *= -1 # Apply multiplier to initial previous balance as well

    # Filter for the main report date range
    combined_df = combined_df_gl_filtered[
        (combined_df_gl_filtered['DOCDATE_DT'] >= from_date) & 
        (combined_df_gl_filtered['DOCDATE_DT'] <= to_date)
    ].copy()

    if combined_df.empty:
        print(f"Server Log (TREND Report): No data within main date range for GLACC '{gl_code_lookup_clean}'.")
        return []

    # Determine period start/end dates based on frequency
    # Group by period and get the last balance for each period
    trend_data = []
    
    previous_balance = initial_previous_balance # Start with the balance from the period before from_date

    # Track if it's the very first entry in the report to handle special January rule
    is_first_report_entry = True

    if frequency == 'daily':
        # Group by actual date
        grouped = combined_df.groupby(combined_df['DOCDATE_DT'].dt.date)
    elif frequency == 'monthly':
        # Group by year and month
        grouped = combined_df.groupby([combined_df['DOCDATE_DT'].dt.year, combined_df['DOCDATE_DT'].dt.month])
    elif frequency == 'semi-annually':
        # Group by year and semi-annual period (1-6, 7-12)
        combined_df['SEMI_ANNUAL_PERIOD'] = combined_df['DOCDATE_DT'].dt.month.apply(lambda x: 1 if x <= 6 else 2)
        grouped = combined_df.groupby([combined_df['DOCDATE_DT'].dt.year, combined_df['SEMI_ANNUAL_PERIOD']])
    elif frequency == 'annually':
        # Group by year
        grouped = combined_df.groupby(combined_df['DOCDATE_DT'].dt.year)
    else:
        print("Server Log (TREND Report): Invalid frequency specified.")
        return []

    for name, group in grouped:
        # Get the last transaction in the group
        last_transaction = group.iloc[-1]
        current_balance = last_transaction['BAL_NUM']
        
        # Determine the display date for the period
        period_date = None
        if frequency == 'daily':
            period_date = datetime(name.year, name.month, name.day)
        elif frequency == 'monthly':
            period_date = datetime(name[0], name[1], 1) + relativedelta(months=1, days=-1) # End of month
        elif frequency == 'semi-annually':
            year, period_num = name
            start_month = 1 if period_num == 1 else 7
            period_date = datetime(year, start_month, 1) + relativedelta(months=6, days=-1) # End of semi-annual period
        elif frequency == 'annually':
            year = name
            period_date = datetime(year, 12, 31) # End of year

        change = 0.0
        # --- Nominal Accounts (GL Code starts with 4 or 5) and First January Transaction Rule ---
        if gl_code_prefix in ['4', '5'] and period_date.month == 1 and is_first_report_entry:
            change = current_balance
            print(f"Server Log (TREND Report): Nominal account rule applied for {period_date.strftime('%m/%d/%Y')}: Change = Balance ({change}).")
        elif previous_balance is not None:
            change = current_balance - previous_balance
            print(f"Server Log (TREND Report): Standard change calculation for {period_date.strftime('%m/%d/%Y')}: {current_balance} - {previous_balance} = {change}.")
        
        is_first_report_entry = False # After the first entry, this flag is set to False

        trend_data.append({
            'DATE': period_date.strftime('%m/%d/%Y'),
            'BALANCE': format_currency(current_balance),
            'BALANCE_RAW': current_balance, # Keep raw balance for charting
            'CHANGE': format_currency(change),
            'CHANGE_RAW': change # Keep raw change for charting
        })
        previous_balance = current_balance

    print(f"Server Log (TREND Report): Processed {len(trend_data)} trend entries.")
    return trend_data
