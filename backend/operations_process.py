# audit_tool/backend/operations_process.py (MODIFIED for MySQL data source and selected_date parameter)
import os
import pandas as pd
from datetime import datetime, timedelta
import re
from dateutil.relativedelta import relativedelta # For month arithmetic

# Import database connection helper
from backend.db_common import get_data_from_mysql, get_db_connection, AREA_BRANCH_MAP
import traceback # Import traceback for detailed error logging


# AGING_BASE_DIR is no longer directly used for data loading in operations_process.py
# but kept here for reference if other parts of the system still rely on it.
# AGING_BASE_DIR = r"C:\\xampp\\htdocs\\audit_tool\\\\OPERATIONS\\\\AGING"

# Helper function for currency formatting (copied for self-containment)
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


# format_decimal_amount and format_gl_code are moved to operations_soa.py


def get_aging_names_and_cids(selected_branches, selected_date=None): # Added selected_date
    """
    Fetches unique "Name_of_Member" and their corresponding "CID" values from MySQL,
    optionally filtered by a specific date.

    Args:
        selected_branches (list): A list of branch names (strings) to process.
                                  Can also contain 'CONSOLIDATED_ALL_AREAS' or 'ALL' for an area.
        selected_date (str, optional): The selected date in 'MM/DD/YYYY' format to filter by.

    Returns:
        list: A list of dictionaries, where each dictionary contains 'NAME' (Name of Member)
              and 'CID' (CID number). Returns an empty list if no data is found.
    """
    print(f"Server Log (Operations Aging Process): Fetching names and CIDs for branches: {selected_branches}, date: {selected_date}")

    actual_branches_to_process = []
    if 'CONSOLIDATED_ALL_AREAS' in selected_branches:
        for area_key, branches_list in AREA_BRANCH_MAP.items():
            if area_key not in ['Consolidated', 'ALL_BRANCHES_LIST']:
                actual_branches_to_process.extend(branches_list)
        actual_branches_to_process = sorted(list(set(actual_branches_to_process)))
    else:
        actual_branches_to_process = selected_branches

    if not actual_branches_to_process:
        print("Server Log (Operations Aging Process): No specific branches resolved for names and CIDs lookup.")
        return []

    # Construct the WHERE clause for branches
    branch_conditions = ", ".join([f"'{branch}'" for branch in actual_branches_to_process])
    
    date_condition = ""
    if selected_date:
        try:
            # Convert MM/DD/YYYY to YYYY-MM-DD for SQL
            parsed_date = datetime.strptime(selected_date, '%m/%d/%Y').strftime('%Y-%m-%d')
            date_condition = f" AND Date = '{parsed_date}'"
        except ValueError:
            print(f"Server Log (Operations Aging Process): Invalid date format received: {selected_date}. Ignoring date filter.")

    query = f"""
        SELECT DISTINCT Name_of_Member, CID
        FROM aging_report_data
        WHERE Branch IN ({branch_conditions})
        AND Name_of_Member IS NOT NULL AND Name_of_Member != ''
        {date_condition}
    """
    
    df = get_data_from_mysql(query)

    if df.empty:
        print("Server Log (Operations Aging Process): No relevant Aging data found in MySQL for names and CIDs.")
        return []

    # Ensure CID is also not blank for valid entries, fill with empty string if NaN
    df['CID'] = df['CID'].astype(str).fillna('')

    # Get unique names and their corresponding CIDs
    unique_name_cid_map = {}
    for index, row in df.iterrows():
        name = str(row['Name_of_Member']).strip()
        cid = str(row['CID']).strip()
        if name: # Only add if name is not empty
            unique_name_cid_map[name] = cid

    # Convert map back to list of dicts for frontend, ensuring alphabetical order by name
    result_list = [{'NAME': name, 'CID': cid} for name, cid in sorted(unique_name_cid_map.items())]

    print(f"Server Log (Operations Aging Process): Extracted {len(result_list)} unique Name/CID entries from MySQL.")
    return result_list


def get_aging_summary_data(selected_branches, selected_date=None): # Added selected_date
    """
    Fetches Aging Report data from MySQL and calculates
    TOTAL CURRENT BALANCE, TOTAL PAST DUE, and TOTAL Both Current and Past Due.
    Calculations are based ONLY on data corresponding to the selected DATE.

    Args:
        selected_branches (list): A list of branch names (strings) to process.
                                  Can also contain 'CONSOLIDATED_ALL_AREAS' or 'ALL' for an area.
        selected_date (str, optional): The selected date in 'MM/DD/YYYY' format to filter by.
                                       If None, the latest date for the selected branches will be used.

    Returns:
        dict: A dictionary containing the calculated balances and the date used for the report.
              Returns default zero values and empty date if no data is found or an error occurs.
    """
    print(f"Server Log (Operations Aging Summary): Fetching summary data for branches: {selected_branches}, date: {selected_date}")

    actual_branches_to_process = []
    if 'CONSOLIDATED_ALL_AREAS' in selected_branches:
        for area_key, branches_list in AREA_BRANCH_MAP.items():
            if area_key not in ['Consolidated', 'ALL_BRANCHES_LIST']:
                actual_branches_to_process.extend(branches_list)
        actual_branches_to_process = sorted(list(set(actual_branches_to_process)))
    else:
        actual_branches_to_process = selected_branches

    if not actual_branches_to_process:
        print("Server Log (Operations Aging Summary): No specific branches resolved for summary data.")
        return {"TOTAL CURRENT BALANCE": 0.0, "TOTAL PAST DUE": 0.0, "TOTAL Both Current and Past Due": 0.0, "AS OF DATE": "",
                "CURRENT_ACCOUNTS_COUNT": 0, "PAST_DUE_ACCOUNTS_COUNT": 0, "TOTAL_ACCOUNTS_COUNT": 0,
                "DELINQUENCY_RATE": 0.0, "PROVISION_1_365_DAYS_BALANCE": 0.0, "PROVISION_1_365_DAYS_ACCOUNTS_COUNT": 0,
                "PROVISION_OVER_365_DAYS_BALANCE": 0.0, "PROVISION_OVER_365_DAYS_ACCOUNTS_COUNT": 0,
                "TOTAL_PROVISIONS": 0.0}

    branch_conditions = ", ".join([f"'{branch}'" for branch in actual_branches_to_process])
    
    report_date = None

    if selected_date:
        try:
            report_date = datetime.strptime(selected_date, '%m/%d/%Y').date()
            print(f"Server Log (Operations Aging Summary): Using provided date: {report_date.strftime('%Y-%m-%d')}")
        except ValueError:
            print(f"Server Log (Operations Aging Summary): Invalid selected_date format: {selected_date}. Attempting to find latest date.")
            selected_date = None # Fallback to finding latest if format is bad

    if not selected_date: # If no date was provided or it was invalid, find the latest
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            latest_date_query = f"""
                SELECT MAX(Date) AS latest_date
                FROM aging_report_data
                WHERE Branch IN ({branch_conditions})
            """
            cursor.execute(latest_date_query)
            result = cursor.fetchone() # Fetch a single row (dictionary due to DictCursor)

            if result and result['latest_date'] is not None:
                raw_latest_date = result['latest_date']
                # Ensure it's a datetime.date object (PyMySQL usually returns this directly for DATE columns)
                if isinstance(raw_latest_date, datetime.date):
                    report_date = raw_latest_date
                elif isinstance(raw_latest_date, str):
                    # If for some reason it's a string, try to parse it
                    report_date = pd.to_datetime(raw_latest_date, errors='coerce').date() # Convert to date object
                
                if report_date is None or pd.isna(report_date): # Check for None or NaT after parsing
                    print(f"Server Log (Operations Aging Summary): Failed to parse latest_date from raw: '{raw_latest_date}'. Returning default summary.")
                    return {"TOTAL CURRENT BALANCE": 0.0, "TOTAL PAST DUE": 0.0, "TOTAL Both Current and Past Due": 0.0, "AS OF DATE": "",
                            "CURRENT_ACCOUNTS_COUNT": 0, "PAST_DUE_ACCOUNTS_COUNT": 0, "TOTAL_ACCOUNTS_COUNT": 0,
                            "DELINQUENCY_RATE": 0.0, "PROVISION_1_365_DAYS_BALANCE": 0.0, "PROVISION_1_365_DAYS_ACCOUNTS_COUNT": 0,
                            "PROVISION_OVER_365_DAYS_BALANCE": 0.0, "PROVISION_OVER_365_DAYS_ACCOUNTS_COUNT": 0,
                            "TOTAL_PROVISIONS": 0.0}

                print(f"Server Log (Operations Aging Summary): Identified latest DATE from MySQL: {report_date.strftime('%Y-%m-%d')}")
            else:
                print("Server Log (Operations Aging Summary): No valid latest DATE found in MySQL for selected branches or query returned no data.")
                return {"TOTAL CURRENT BALANCE": 0.0, "TOTAL PAST DUE": 0.0, "TOTAL Both Current and Past Due": 0.0, "AS OF DATE": "",
                        "CURRENT_ACCOUNTS_COUNT": 0, "PAST_DUE_ACCOUNTS_COUNT": 0, "TOTAL_ACCOUNTS_COUNT": 0,
                        "DELINQUENCY_RATE": 0.0, "PROVISION_1_365_DAYS_BALANCE": 0.0, "PROVISION_1_365_DAYS_ACCOUNTS_COUNT": 0,
                        "PROVISION_OVER_365_DAYS_BALANCE": 0.0, "PROVISION_OVER_365_DAYS_ACCOUNTS_COUNT": 0,
                        "TOTAL_PROVISIONS": 0.0}
        except Exception as e:
            print(f"Error fetching latest date directly from MySQL: {e}")
            traceback.print_exc()
            return {"TOTAL CURRENT BALANCE": 0.0, "TOTAL PAST DUE": 0.0, "TOTAL Both Current and Past Due": 0.0, "AS OF DATE": "",
                    "CURRENT_ACCOUNTS_COUNT": 0, "PAST_DUE_ACCOUNTS_COUNT": 0, "TOTAL_ACCOUNTS_COUNT": 0,
                    "DELINQUENCY_RATE": 0.0, "PROVISION_1_365_DAYS_BALANCE": 0.0, "PROVISION_1_365_DAYS_ACCOUNTS_COUNT": 0,
                    "PROVISION_OVER_365_DAYS_BALANCE": 0.0, "PROVISION_OVER_365_DAYS_ACCOUNTS_COUNT": 0,
                    "TOTAL_PROVISIONS": 0.0}
        finally:
            if conn and conn.open:
                cursor.close()
                conn.close()

    if report_date is None: # Final check if no date could be determined
        print("Server Log (Operations Aging Summary): No valid report date determined. Returning default summary.")
        return {"TOTAL CURRENT BALANCE": 0.0, "TOTAL PAST DUE": 0.0, "TOTAL Both Current and Past Due": 0.0, "AS OF DATE": "",
                "CURRENT_ACCOUNTS_COUNT": 0, "PAST_DUE_ACCOUNTS_COUNT": 0, "TOTAL_ACCOUNTS_COUNT": 0,
                "DELINQUENCY_RATE": 0.0, "PROVISION_1_365_DAYS_BALANCE": 0.0, "PROVISION_1_365_DAYS_ACCOUNTS_COUNT": 0,
                "PROVISION_OVER_365_DAYS_BALANCE": 0.0, "PROVISION_OVER_365_DAYS_ACCOUNTS_COUNT": 0,
                "TOTAL_PROVISIONS": 0.0}


    # Now fetch all data for the determined report_date for the selected branches
    query = f"""
        SELECT Balance, Aging, `Loan_Account`
        FROM aging_report_data
        WHERE Branch IN ({branch_conditions})
        AND Date = '{report_date.strftime('%Y-%m-%d')}'
    """
    df_filtered_by_date = get_data_from_mysql(query)

    # Initialize all summary variables to 0 or 0.0 at the start of this block
    current_balance = 0.0
    past_due_balance = 0.0
    total_balance = 0.0
    current_accounts_count = 0
    past_due_accounts_count = 0
    total_accounts_count = 0
    delinquency_rate = 0.0
    provision_1_365_balance = 0.0
    provision_1_365_accounts_count = 0
    provision_over_365_balance = 0.0
    provision_over_365_accounts_count = 0
    total_provisions = 0.0


    if not df_filtered_by_date.empty:
        # Clean 'Aging' column to ensure consistent comparison
        df_filtered_by_date['Aging_CLEAN'] = df_filtered_by_date['Aging'].astype(str).str.strip().str.upper()

        # Calculate TOTAL CURRENT BALANCE
        current_balance = df_filtered_by_date[
            df_filtered_by_date['Aging_CLEAN'] == 'NOT YET DUE'
        ]['Balance'].sum()

        # Calculate TOTAL PAST DUE
        past_due_balance = df_filtered_by_date[
            df_filtered_by_date['Aging_CLEAN'] != 'NOT YET DUE'
        ]['Balance'].sum()
        
        # Calculate TOTAL Both Current and Past Due
        total_balance = df_filtered_by_date['Balance'].sum()

        # Calculate account counts
        current_accounts_count = df_filtered_by_date[
            df_filtered_by_date['Aging_CLEAN'] == 'NOT YET DUE'
        ]['Loan_Account'].nunique() # Count unique loan accounts

        past_due_accounts_count = df_filtered_by_date[
            df_filtered_by_date['Aging_CLEAN'] != 'NOT YET DUE'
        ]['Loan_Account'].nunique() # Count unique loan accounts

        total_accounts_count = df_filtered_by_date['Loan_Account'].nunique() # Total unique loan accounts

        # Calculate DELINQUENCY RATE (%)
        if total_balance != 0:
            delinquency_rate = (past_due_balance / total_balance) * 100

        # Calculate PROVISION (1-365 DAYS)
        provision_1_365_aging_categories = ['1-30 DAYS', '31-60', '61-90', '91-120', '121-180', '181-365']
        df_1_365_days = df_filtered_by_date[
            df_filtered_by_date['Aging_CLEAN'].isin(provision_1_365_aging_categories)
        ]
        if not df_1_365_days.empty: # Check if DataFrame is not empty before summing
            provision_1_365_balance = df_1_365_days['Balance'].sum() * 0.35 # Multiply by 35%
            provision_1_365_accounts_count = df_1_365_days['Loan_Account'].nunique()

        # Calculate PROVISION (OVER 365 DAYS)
        df_over_365_days = df_filtered_by_date[
            df_filtered_by_date['Aging_CLEAN'] == 'OVER 365'
        ]
        if not df_over_365_days.empty: # Check if DataFrame is not empty before summing
            provision_over_365_balance = df_over_365_days['Balance'].sum()
            provision_over_365_accounts_count = df_over_365_days['Loan_Account'].nunique()

        # Calculate TOTAL PROVISIONS
        total_provisions = provision_1_365_balance + provision_over_365_balance


    # Format output to two decimal places
    def format_balance(value):
        return float(f"{value:.2f}")

    summary_results = {
        "TOTAL CURRENT BALANCE": format_balance(current_balance),
        "TOTAL PAST DUE": format_balance(past_due_balance),
        "TOTAL Both Current and Past Due": format_balance(total_balance),
        "AS OF DATE": report_date.strftime("%m/%d/%Y") if report_date else "",
        "CURRENT_ACCOUNTS_COUNT": current_accounts_count,
        "PAST_DUE_ACCOUNTS_COUNT": past_due_accounts_count,
        "TOTAL_ACCOUNTS_COUNT": total_accounts_count,
        "DELINQUENCY_RATE": round(delinquency_rate, 2), # Round to 2 decimal places for percentage
        "PROVISION_1_365_DAYS_BALANCE": format_balance(provision_1_365_balance),
        "PROVISION_1_365_DAYS_ACCOUNTS_COUNT": provision_1_365_accounts_count,
        "PROVISION_OVER_365_DAYS_BALANCE": format_balance(provision_over_365_balance),
        "PROVISION_OVER_365_DAYS_ACCOUNTS_COUNT": provision_over_365_accounts_count,
        "TOTAL_PROVISIONS": format_balance(total_provisions)
    }

    print(f"Server Log (Operations Aging Summary): Calculated summary (for selected date): {summary_results}")
    return summary_results


def get_aging_history_per_member_loan(branch_name, cid_lookup, selected_date=None): # Added selected_date
    """
    Fetches Aging Report data from MySQL for a specific branch and CID,
    to generate a history of 'Aging' status per Loan_Account over time,
    optionally filtered up to a selected date.

    Args:
        branch_name (str): The name of the branch.
        cid_lookup (str): The CID of the member to filter by.
        selected_date (str, optional): The selected date in 'MM/DD/YYYY' format to filter up to.

    Returns:
        dict: A dictionary containing:
            - 'headers': A list of unique internal keys for data access (e.g., "JAN21", "FEB21").
            - 'display_headers_mmm': A list of three-letter month abbreviations for display (e.g., "Jan", "Feb").
            - 'full_month_years': A list of full month-year strings (e.g., "Jan 2021", "Feb 2021").
            - 'data': A list of dictionaries, where each dictionary represents a row for a Loan_Account.
                      Keys use the 'headers' (unique internal keys).
                      Values for month-year keys are numeric aging status (0-7), or None if blank.
            Returns an empty dictionary if no data is found or an error occurs.
    """
    print(f"Server Log (Aging History): Fetching data for branch: {branch_name}, CID: {cid_lookup}, date: {selected_date}")

    date_condition = ""
    query_params = {'branch_name': branch_name, 'cid_lookup': cid_lookup} # Use named parameters

    if selected_date:
        try:
            # Convert MM/DD/YYYY to YYYY-MM-DD for SQL
            parsed_date_str = datetime.strptime(selected_date, '%m/%d/%Y').strftime('%Y-%m-%d')
            date_condition = f" AND Date <= :parsed_date_str" # Use named parameter
            query_params['parsed_date_str'] = parsed_date_str
        except ValueError:
            print(f"Server Log (Aging History): Invalid date format received: {selected_date}. Ignoring date filter.")

    # Fetch all relevant data for the specific branch and CID from MySQL
    query = f"""
        SELECT Branch, Date, CID, Name_of_Member, Loan_Account, Principal, Balance, Aging, Disbursement_Date, Due_Date, Product
        FROM aging_report_data
        WHERE Branch = :branch_name AND CID = :cid_lookup
        {date_condition}
    """
    
    df_filtered_by_cid = get_data_from_mysql(query, params=query_params)

    if df_filtered_by_cid.empty:
        print(f"Server Log (Aging History): No data found for Branch: {branch_name}, CID: {cid_lookup} in MySQL.")
        return {'headers': [], 'display_headers_mmm': [], 'full_month_years': [], 'data': []}

    # Ensure date columns are datetime objects
    df_filtered_by_cid['Date'] = pd.to_datetime(df_filtered_by_cid['Date'], errors='coerce')
    df_filtered_by_cid['Disbursement_Date'] = pd.to_datetime(df_filtered_by_cid['Disbursement_Date'], errors='coerce')
    df_filtered_by_cid['Due_Date'] = pd.to_datetime(df_filtered_by_cid['Due_Date'], errors='coerce')
    df_filtered_by_cid.dropna(subset=['Date', 'Disbursement_Date'], inplace=True) # Drop rows where essential date conversion failed

    # Determine the overall latest date across ALL filtered data for this CID
    overall_latest_date_for_cid = df_filtered_by_cid['Date'].max()
    if pd.isna(overall_latest_date_for_cid):
        print("Server Log (Aging History): No valid dates found in filtered data for CID.")
        return {'headers': [], 'display_headers_mmm': [], 'full_month_years': [], 'data': []}

    # Define the mapping for AGING to numeric values
    AGING_TO_NUMERIC_MAP = {
        'NOT YET DUE': 0,
        '1-30 DAYS': 1,
        '31-60': 2,
        '61-90': 3,
        '91-120': 4,
        '121-180': 5,
        '181-365': 6,
        'OVER 365': 7
    }

    # Apply mapping to the 'Aging' column
    df_filtered_by_cid['Aging_NUM'] = df_filtered_by_cid['Aging'].astype(str).str.strip().str.upper().map(AGING_TO_NUMERIC_MAP)
    
    # Generate month-year objects from Jan 2021 (or earliest data) to the latest month of overall_latest_date_for_cid
    # Dynamically determine start_month_year from data
    earliest_date_in_data = df_filtered_by_cid['Date'].min()
    start_month_year = earliest_date_in_data.replace(day=1) if pd.notna(earliest_date_in_data) else datetime(2021, 1, 1)
    end_month_year = overall_latest_date_for_cid.replace(day=1) # Get first day of the latest month

    month_years = []
    current_month_year = start_month_year
    while current_month_year <= end_month_year:
        month_years.append(current_month_year)
        current_month_year += relativedelta(months=1)

    # Prepare unique internal keys for data access (e.g., "JAN21", "FEB21")
    unique_internal_headers = [dt.strftime('%b').upper() + dt.strftime('%y') for dt in month_years]
    # Prepare display headers for the frontend (e.g., "Jan", "Feb")
    display_headers_mmm = [dt.strftime('%b') for dt in month_years]
    # Also prepare full month-year strings for year grouping on frontend
    full_month_year_strings = [dt.strftime('%b %Y') for dt in month_years]

    print(f"Server Log (Aging History): Generated unique internal headers: {unique_internal_headers}")
    print(f"Server Log (Aging History): Generated display headers (MMM): {display_headers_mmm}")
    print(f"Server Log (Aging History): Generated full month-year strings: {full_month_year_strings}")

    # Build the history data
    history_data = []
    for loan_acct in sorted(df_filtered_by_cid['Loan_Account'].unique()):
        loan_df = df_filtered_by_cid[df_filtered_by_cid['Loan_Account'] == loan_acct].copy()
        
        # Sort by Disbursement_Date to ensure we get the earliest principal
        loan_df.sort_values(by='Disbursement_Date', ascending=True, inplace=True) 

        # DISBURSED (from earliest Disbursement_Date)
        formatted_disbursed_date = ''
        if not loan_df['Disbursement_Date'].empty and pd.notna(loan_df['Disbursement_Date'].iloc[0]):
            formatted_disbursed_date = loan_df['Disbursement_Date'].iloc[0].strftime('%m/%d/%Y')

        # PRINCIPAL (from earliest Disbursement_Date)
        principal_val = 0.0
        if not loan_df.empty and 'Principal' in loan_df.columns:
            # Find the row with the earliest Disbursement_Date for this loan_acct
            earliest_disb_row_for_principal = loan_df.loc[loan_df['Disbursement_Date'].idxmin()]
            principal_val = earliest_disb_row_for_principal['Principal']
        formatted_principal = format_currency(principal_val)

        # BALANCE (from overall_latest_date_for_cid, or 0 if not found)
        # Sort by Date to ensure we get the latest balance
        loan_df.sort_values(by='Date', ascending=True, inplace=True) 
        latest_balance_val = 0.0
        if 'Balance' in loan_df.columns and not loan_df['Balance'].empty:
            # Filter for the overall latest date for this specific loan account
            balance_on_latest_overall_date = loan_df[loan_df['Date'] == overall_latest_date_for_cid]['Balance']
            if not balance_on_latest_overall_date.empty:
                latest_balance_val = balance_on_latest_overall_date.iloc[0]
            else:
                latest_balance_val = 0.0 # Explicitly set to zero if not found on the exact overall latest date

        formatted_balance = format_currency(latest_balance_val)

        # PRODUCT
        product_name = ''
        if 'Product' in loan_df.columns and not loan_df['Product'].empty:
            product_name = loan_df['Product'].astype(str).str.strip().iloc[0]

        loan_row = {
            'ACCOUNT': loan_acct,
            'DISBURSED': formatted_disbursed_date,
            'PRINCIPAL': formatted_principal,
            'BALANCE': formatted_balance,
            'PRODUCT': product_name
        }

        # Prepare monthly aging series
        monthly_aging_series = pd.Series(index=[dt.replace(day=1) for dt in month_years], dtype=float)

        loan_df['month_start_raw'] = loan_df['Date'].apply(lambda x: x.replace(day=1))
        latest_raw_entries_per_month = loan_df.sort_values(by='Date').drop_duplicates(subset=['month_start_raw'], keep='last')

        for _, row in latest_raw_entries_per_month.iterrows():
            if row['month_start_raw'] in monthly_aging_series.index:
                monthly_aging_series.loc[row['month_start_raw']] = row['Aging_NUM']
        
        monthly_aging_series = monthly_aging_series.fillna(pd.NA)

        for month_dt in month_years:
            # Use the unique internal key for the dictionary
            month_key_internal = month_dt.strftime('%b').upper() + month_dt.strftime('%y')
            
            value_at_month_start = monthly_aging_series.loc[month_dt.replace(day=1)]
            
            if pd.isna(value_at_month_start):
                aging_value = None
            else:
                aging_value = value_at_month_start.item()
            
            loan_row[month_key_internal] = aging_value
            
        history_data.append(loan_row)

    print(f"Server Log (Aging History): Generated {len(history_data)} rows of history data (blank if no explicit data).")
    return {
        'headers': ['ACCOUNT', 'DISBURSED', 'PRINCIPAL', 'BALANCE', 'PRODUCT'] + unique_internal_headers,
        'display_headers_mmm': ['DISBURSED', 'PRINCIPAL', 'BALANCE', 'PRODUCT'] + display_headers_mmm,
        'full_month_years': full_month_year_strings,
        'data': history_data,
        'overall_latest_date': overall_latest_date_for_cid.strftime('%m/%d/%Y') if pd.notna(overall_latest_date_for_cid) else ''
    }

def get_accounts_contribute_to_provisions_report(selected_branches, selected_month, selected_year, selected_aging_category, selected_date=None): # Added selected_date
    """
    Generates a report of accounts that contribute to provisions, based on selected criteria, from MySQL.

    Args:
        selected_branches (list): A list of branch names (strings) to process.
                                  Can also contain 'CONSOLIDATED_ALL_AREAS' or 'ALL' for an area.
        selected_month (int): The selected month (1-12).
        selected_year (int): The selected year (e.g., 2024).
        selected_aging_category (str): The selected aging category (e.g., '1-30 DAYS', 'OVER 365').
        selected_date (str, optional): The selected date in 'MM/DD/YYYY' format to filter up to.

    Returns:
        dict: A dictionary containing 'per_accounts_data' and 'per_member_data'.
    """
    print(f"Server Log (Provisions Report): Starting for branches: {selected_branches}, month: {selected_month}, year: {selected_year}, aging: {selected_aging_category}, date: {selected_date}")

    actual_branches_to_process = []
    if 'CONSOLIDATED_ALL_AREAS' in selected_branches:
        for area_key, branches_list in AREA_BRANCH_MAP.items():
            if area_key not in ['Consolidated', 'ALL_BRANCHES_LIST']:
                actual_branches_to_process.extend(branches_list)
        actual_branches_to_process = sorted(list(set(actual_branches_to_process)))
    else:
        actual_branches_to_process = selected_branches

    if not actual_branches_to_process:
        print("Server Log (Provisions Report): No branches provided for provisions report.")
        return {'per_accounts_data': [], 'per_member_data': []}

    branch_conditions = ", ".join([f"'{branch}'" for branch in actual_branches_to_process])

    # Define the dates for filtering
    dec_prev_year_date = datetime(selected_year - 1, 12, 31).date() 
    selected_month_year_date = (datetime(selected_year, selected_month, 1) + relativedelta(months=1, days=-1)).date()

    # Optimize SQL query to fetch only data for the two relevant dates
    date_list_for_query = [dec_prev_year_date.strftime('%Y-%m-%d'), selected_month_year_date.strftime('%Y-%m-%d')]
    date_conditions_sql = ", ".join([f"'{d}'" for d in date_list_for_query])

    query = f"""
        SELECT Branch, Date, CID, Name_of_Member, Loan_Account, Principal, Balance, Aging, Disbursement_Date, Due_Date, Product
        FROM aging_report_data
        WHERE Branch IN ({branch_conditions}) AND Date IN ({date_conditions_sql})
    """
    combined_df = get_data_from_mysql(query)
            
    if combined_df.empty:
        print("Server Log (Provisions Report): No relevant Aging data found in MySQL across all selected branches for the specified dates.")
        return {'per_accounts_data': [], 'per_member_data': []}

    # Ensure date columns are datetime objects
    combined_df['Date'] = pd.to_datetime(combined_df['Date'], format='%Y-%m-%d', errors='coerce')
    combined_df['Disbursement_Date'] = pd.to_datetime(combined_df['Disbursement_Date'], format='%Y-%m-%d', errors='coerce')
    combined_df['Due_Date'] = pd.to_datetime(combined_df['Due_Date'], format='%Y-%m-%d', errors='coerce')
    combined_df.dropna(subset=['Date'], inplace=True) # Drop rows where date conversion failed

    # Strip whitespace from Loan_Account and Branch columns
    combined_df['Loan_Account'] = combined_df['Loan_Account'].astype(str).str.strip()
    combined_df['Branch'] = combined_df['Branch'].astype(str).str.strip()
    combined_df['Aging_CLEAN'] = combined_df['Aging'].astype(str).str.strip().str.upper()


    print(f"Server Log (Provisions Report Debug): combined_df['Date'] dtype after pd.to_datetime: {combined_df['Date'].dtype}")
    print(f"Server Log (Provisions Report Debug): Sample of combined_df['Date'] values (first 10): {combined_df['Date'].head(10).tolist()}")
    print(f"Server Log (Provisions Report Debug): Number of NaT values in combined_df['Date']: {combined_df['Date'].isna().sum()}")
    print(f"Server Log (Provisions Report): Filtering for Dec {selected_year - 1} (date: {dec_prev_year_date}) and {selected_month_year_date}")
    print(f"Server Log (Provisions Report): Target Aging Category: {selected_aging_category.upper()}")

    # Filter for current month's data
    current_month_data_df = combined_df[combined_df['Date'].dt.date == selected_month_year_date].copy()

    # Filter for previous year's December data
    dec_prev_year_data_df = combined_df[combined_df['Date'].dt.date == dec_prev_year_date].copy()

    # Define aging categories for 35% provision
    aging_35_percent_categories = ['31-60', '61-90', '91-120', '121-180', '181-365']

    # Filter current month data by selected aging category
    filtered_current_loans = pd.DataFrame()
    if selected_aging_category.upper() == '30-365 DAYS':
        filtered_current_loans = current_month_data_df[
            current_month_data_df['Aging_CLEAN'].isin(aging_35_percent_categories)
        ].copy()
    elif selected_aging_category.upper() == 'OVER 365':
        filtered_current_loans = current_month_data_df[
            current_month_data_df['Aging_CLEAN'] == 'OVER 365'
        ].copy()
    elif selected_aging_category.upper() == '30_TO_OVER_365_DAYS':
        filtered_current_loans = current_month_data_df[
            current_month_data_df['Aging_CLEAN'].isin(aging_35_percent_categories + ['OVER 365'])
        ].copy()
    else:
        print(f"Server Log (Provisions Report): Unexpected selected_aging_category: {selected_aging_category}. No current month aging filter applied.")
        return {'per_accounts_data': [], 'per_member_data': []}

    if filtered_current_loans.empty:
        print("Server Log (Provisions Report): No accounts found matching current month and aging criteria.")
        return {'per_accounts_data': [], 'per_member_data': []}

    # Merge current month data with previous year's data
    # Use a left merge to keep all current month loans, and add previous year's data if available
    merged_df = filtered_current_loans.merge(
        dec_prev_year_data_df[['Loan_Account', 'Branch', 'Balance', 'Aging']],
        on=['Loan_Account', 'Branch'],
        how='left',
        suffixes=('_CURRENT', '_DEC_PREV_YEAR')
    )

    # Fill NaN values for previous year's data with defaults
    merged_df['Balance_DEC_PREV_YEAR'] = merged_df['Balance_DEC_PREV_YEAR'].fillna(0.0)
    merged_df['Aging_DEC_PREV_YEAR'] = merged_df['Aging_DEC_PREV_YEAR'].fillna('')

    # Vectorized Provision Calculation
    merged_df['previous_provision'] = 0.0
    merged_df.loc[merged_df['Aging_DEC_PREV_YEAR'].str.strip().str.upper() == 'OVER 365', 'previous_provision'] = merged_df['Balance_DEC_PREV_YEAR'] * 1.00
    merged_df.loc[merged_df['Aging_DEC_PREV_YEAR'].str.strip().str.upper().isin(aging_35_percent_categories), 'previous_provision'] = merged_df['Balance_DEC_PREV_YEAR'] * 0.35

    merged_df['current_provision'] = 0.0
    merged_df.loc[merged_df['Aging_CURRENT'].str.strip().str.upper() == 'OVER 365', 'current_provision'] = merged_df['Balance_CURRENT'] * 1.00
    merged_df.loc[merged_df['Aging_CURRENT'].str.strip().str.upper().isin(aging_35_percent_categories), 'current_provision'] = merged_df['Balance_CURRENT'] * 0.35

    merged_df['final_provision_value'] = merged_df['current_provision'] - merged_df['previous_provision']

    # Prepare per_accounts_data
    per_accounts_data = []
    for _, row in merged_df.iterrows():
        per_accounts_data.append({
            'ACCOUNT': row['Loan_Account'],
            'NAME': row['Name_of_Member'],
            'CID': row['CID'],
            'BRANCH': row['Branch'],
            'DISBURSED': row['Disbursement_Date'].strftime('%m/%d/%Y') if pd.notna(row['Disbursement_Date']) else '',
            'MATURITY': row['Due_Date'].strftime('%m/%d/%Y') if pd.notna(row['Due_Date']) else '',
            'PRINCIPAL': format_currency(row['Principal']),
            'BALANCE_DEC_PREV_YEAR': format_currency(row['Balance_DEC_PREV_YEAR']),
            'AGING_DEC_PREV_YEAR': row['Aging_DEC_PREV_YEAR'],
            'BALANCE_INPUTTED_MMYYYY': format_currency(row['Balance_CURRENT']),
            'AGING_INPUTTED_MMYYYY': row['Aging_CURRENT'],
            'PROVISION': format_currency(row['final_provision_value'])
        })
    
    print(f"Server Log (Provisions Report): Generated {len(per_accounts_data)} rows for Per Accounts table.")

    if per_accounts_data:
        df_per_accounts = pd.DataFrame(per_accounts_data)
        
        def parse_currency_to_float(currency_str):
            if isinstance(currency_str, str) and currency_str:
                cleaned_str = currency_str.replace('₱', '').replace('$', '').replace(',', '').strip()
                if cleaned_str.startswith('(') and cleaned_str.endswith(')'):
                    return -float(cleaned_str[1:-1])
                return float(cleaned_str)
            return 0.0

        if 'PROVISION' in df_per_accounts.columns:
            df_per_accounts['PROVISION_NUM_SORT'] = df_per_accounts['PROVISION'].apply(parse_currency_to_float)
            df_per_accounts.sort_values(by='PROVISION_NUM_SORT', ascending=False, inplace=True)
            per_accounts_data = df_per_accounts.drop(columns=['PROVISION_NUM_SORT']).to_dict(orient='records')
        else:
            print("Server Log (Provisions Report): 'PROVISION' column not found in df_per_accounts for sorting.")


    # Calculate PER MEMBER data
    per_member_data = []
    if per_accounts_data:
        df_per_accounts_for_member_sum = pd.DataFrame(per_accounts_data)
        
        def parse_currency_to_float(currency_str):
            if isinstance(currency_str, str) and currency_str:
                cleaned_str = currency_str.replace('₱', '').replace('$', '').replace(',', '').strip()
                if cleaned_str.startswith('(') and cleaned_str.endswith(')'):
                    return -float(cleaned_str[1:-1])
                return float(cleaned_str)
            return 0.0

        columns_to_process = ['PRINCIPAL', 'BALANCE_DEC_PREV_YEAR', 'BALANCE_INPUTTED_MMYYYY', 'PROVISION']
        for col_name in columns_to_process:
            if col_name in df_per_accounts_for_member_sum.columns:
                df_per_accounts_for_member_sum[f'{col_name}_NUM_SUM'] = df_per_accounts_for_member_sum[col_name].apply(parse_currency_to_float)
            else:
                df_per_accounts_for_member_sum[f'{col_name}_NUM_SUM'] = 0.0

        grouped_by_member = df_per_accounts_for_member_sum.groupby('NAME').agg(
            CID=('CID', 'first'),
            BRANCHES_INVOLVED=('BRANCH', lambda x: ', '. join(sorted(x.unique()))),
            TOTAL_PRINCIPAL=('PRINCIPAL_NUM_SUM', 'sum'),
            TOTAL_BALANCE_DEC_PREV_YEAR=('BALANCE_DEC_PREV_YEAR_NUM_SUM', 'sum'),
            TOTAL_BALANCE_INPUTTED_MMYYYY=('BALANCE_INPUTTED_MMYYYY_NUM_SUM', 'sum'),
            TOTAL_PROVISION=('PROVISION_NUM_SUM', 'sum'),
            ACCOUNT_COUNT=('ACCOUNT', 'count')
        ).reset_index()

        grouped_by_member.sort_values(by='TOTAL_PROVISION', ascending=False, inplace=True)


        for _, row in grouped_by_member.iterrows():
            per_member_data.append({
                'NAME': row['NAME'],
                'CID': row['CID'],
                'BRANCHES_INVOLVED': row['BRANCHES_INVOLVED'],
                'TOTAL_PRINCIPAL': format_currency(row['TOTAL_PRINCIPAL']),
                'TOTAL_BALANCE_DEC_PREV_YEAR': format_currency(row['TOTAL_BALANCE_DEC_PREV_YEAR']),
                'TOTAL_BALANCE_INPUTTED_MMYYYY': format_currency(row['TOTAL_BALANCE_INPUTTED_MMYYYY']),
                'TOTAL_PROVISION': format_currency(row['TOTAL_PROVISION']),
                'ACCOUNT_COUNT': int(row['ACCOUNT_COUNT'])
            })
    
    print(f"Server Log (Provisions Report): Generated {len(per_member_data)} rows for Per Member table.")
    return {'per_accounts_data': per_accounts_data, 'per_member_data': per_member_data}

def get_top_borrowers_report(selected_branches, status_filter, selected_date=None): # NEW: Added selected_date
    """
    Generates a report of top borrowers based on their current or past due status, from MySQL.

    Args:
        selected_branches (list): A list of branch names (strings) to process.
                                  Can also contain 'CONSOLIDATED_ALL_AREAS' or 'ALL' for an area.
        status_filter (str): 'CURRENT' or 'PAST DUE'.
        selected_date (str, optional): The selected date in 'MM/DD/YYYY' format to filter by.

    Returns:
        list: A list of dictionaries representing the processed table data for top borrowers.
              Returns an empty list if no data is found or an error occurs.
    """
    print(f"Server Log (Top Borrowers Report): Starting for branches: {selected_branches}, status: {status_filter}, date: {selected_date}")

    actual_branches_to_process = []
    if 'CONSOLIDATED_ALL_AREAS' in selected_branches:
        for area_key, branches_list in AREA_BRANCH_MAP.items():
            if area_key not in ['Consolidated', 'ALL_BRANCHES_LIST']:
                actual_branches_to_process.extend(branches_list)
        actual_branches_to_process = sorted(list(set(actual_branches_to_process)))
    else:
        actual_branches_to_process = selected_branches

    if not actual_branches_to_process:
        print("Server Log (Top Borrowers Report): No branches provided for top borrowers report.")
        return []

    branch_conditions = ", ".join([f"'{branch}'" for branch in actual_branches_to_process])

    report_date = None
    if selected_date:
        try:
            report_date = datetime.strptime(selected_date, '%m/%d/%Y').date()
            print(f"Server Log (Top Borrowers Report): Using provided date: {report_date.strftime('%Y-%m-%d')}")
        except ValueError:
            print(f"Server Log (Top Borrowers Report): Invalid selected_date format: {selected_date}. Will try to find latest date.")
            selected_date = None # Fallback to finding latest if format is bad

    if not selected_date: # If no date was provided or it was invalid, find the latest
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            latest_date_query = f"""
                SELECT MAX(Date) AS latest_date
                FROM aging_report_data
                WHERE Branch IN ({branch_conditions})
            """
            cursor.execute(latest_date_query)
            result = cursor.fetchone()

            if result and result['latest_date'] is not None:
                report_date = result['latest_date']
                print(f"Server Log (Top Borrowers Report): Identified latest DATE from MySQL: {report_date.strftime('%Y-%m-%d')}")
            else:
                print("Server Log (Top Borrowers Report): No valid DATEs found in MySQL for selected branches.")
                return []
        except Exception as e:
            print(f"Error fetching latest date directly from MySQL for Top Borrowers: {e}")
            traceback.print_exc()
            return []
        finally:
            if conn and conn.open:
                cursor.close()
                conn.close()
    
    if report_date is None:
        print("Server Log (Top Borrowers Report): No valid report date determined. Returning empty report.")
        return []

    # Fetch all data for that determined report_date for the selected branches
    query = f"""
        SELECT Branch, Date, CID, Name_of_Member, Loan_Account, Principal, Balance, Aging
        FROM aging_report_data
        WHERE Branch IN ({branch_conditions})
        AND Date = '{report_date.strftime('%Y-%m-%d')}'
    """
    df_filtered_by_date = get_data_from_mysql(query)
            
    if df_filtered_by_date.empty:
        print("Server Log (Top Borrowers Report): No data found for the selected date in MySQL.")
        return []

    df_filtered_by_date['Aging_CLEAN'] = df_filtered_by_date['Aging'].astype(str).str.strip().str.upper()

    # Create helper columns for conditional aggregation
    df_filtered_by_date['is_current'] = (df_filtered_by_date['Aging_CLEAN'] == 'NOT YET DUE')
    df_filtered_by_date['is_past_due'] = (df_filtered_by_date['Aging_CLEAN'] != 'NOT YET DUE')

    # Group by Name_of_Member and aggregate
    grouped_by_name = df_filtered_by_date.groupby('Name_of_Member').agg(
        CID=('CID', 'first'), # Assuming CID is consistent per Name_of_Member
        BRANCH=('Branch', lambda x: ', '.join(sorted(x.unique()))), # Aggregate unique branches
        CURRENT_ACCOUNT_COUNT=('Loan_Account', lambda x: x[df_filtered_by_date.loc[x.index, 'is_current']].nunique()),
        CURRENT_BALANCE=('Balance', lambda x: x[df_filtered_by_date.loc[x.index, 'is_current']].sum()),
        PAST_DUE_ACCOUNT_COUNT=('Loan_Account', lambda x: x[df_filtered_by_date.loc[x.index, 'is_past_due']].nunique()),
        PAST_DUE_BALANCE=('Balance', lambda x: x[df_filtered_by_date.loc[x.index, 'is_past_due']].sum()),
    ).reset_index()

    grouped_by_name['TOTAL_ACCOUNT_COUNT'] = grouped_by_name['CURRENT_ACCOUNT_COUNT'] + grouped_by_name['PAST_DUE_ACCOUNT_COUNT']
    grouped_by_name['TOTAL_BALANCE'] = grouped_by_name['CURRENT_BALANCE'] + grouped_by_name['PAST_DUE_BALANCE']

    # Apply status filter
    if status_filter == 'CURRENT':
        filtered_borrowers = grouped_by_name[grouped_by_name['PAST_DUE_ACCOUNT_COUNT'] == 0].copy()
    elif status_filter == 'PAST DUE':
        filtered_borrowers = grouped_by_name[grouped_by_name['PAST_DUE_ACCOUNT_COUNT'] > 0].copy()
    else:
        filtered_borrowers = grouped_by_name.copy()

    filtered_borrowers.sort_values(by='TOTAL_BALANCE', ascending=False, inplace=True)

    # Format currency columns
    filtered_borrowers['CURRENT_BALANCE'] = filtered_borrowers['CURRENT_BALANCE'].apply(format_currency)
    filtered_borrowers['PAST_DUE_BALANCE'] = filtered_borrowers['PAST_DUE_BALANCE'].apply(format_currency)
    filtered_borrowers['TOTAL_BALANCE'] = filtered_borrowers['TOTAL_BALANCE'].apply(format_currency)

    final_report_data = []
    for _, row in filtered_borrowers.iterrows():
        final_report_data.append({
            'NAME': row['Name_of_Member'],
            'CID': row['CID'],
            'BRANCH': row['BRANCH'],
            'CURRENT_ACCOUNT': int(row['CURRENT_ACCOUNT_COUNT']),
            'CURRENT_BALANCE': row['CURRENT_BALANCE'],
            'PAST_DUE_ACCOUNT': int(row['PAST_DUE_ACCOUNT_COUNT']),
            'PAST_DUE_BALANCE': row['PAST_DUE_BALANCE'],
            'TOTAL_ACCOUNT': int(row['TOTAL_ACCOUNT_COUNT']),
            'TOTAL_BALANCE': row['TOTAL_BALANCE']
        })
    
    print(f"Server Log (Top Borrowers Report): Generated {len(final_report_data)} rows.")
    return final_report_data

def get_new_loans_with_past_due_history_report(selected_branches, selected_year, selected_date=None): # Added selected_date
    """
    Generates a report of new loans (disbursed in selected_year) from borrowers
    who have a past due credit history prior to the selected year, from MySQL.
    The report data is filtered up to the selected_date.

    Args:
        selected_branches (list): A list of branch names (strings) to process.
                                  Can also contain 'CONSOLIDATED_ALL_AREAS' or 'ALL' for an area.
        selected_year (int): The year of the new loans to consider.
        selected_date (str, optional): The selected date in 'MM/DD/YYYY' format to filter up to.

    Returns:
        list: A list of dictionaries representing the report data.
              Returns an empty list if no data is found or an error occurs.
    """
    print(f"Server Log (New Loans with Past Due History Report): Starting for branches: {selected_branches}, year: {selected_year}, date: {selected_date}")

    actual_branches_to_process = []
    if 'CONSOLIDATED_ALL_AREAS' in selected_branches:
        for area_key, branches_list in AREA_BRANCH_MAP.items():
            if area_key not in ['Consolidated', 'ALL_BRANCHES_LIST']:
                actual_branches_to_process.extend(branches_list)
        actual_branches_to_process = sorted(list(set(actual_branches_to_process)))
    else:
        actual_branches_to_process = selected_branches

    if not actual_branches_to_process:
        print("Server Log (New Loans with Past Due History Report): No branches provided.")
        return []

    branch_conditions = ", ".join([f"'{branch}'" for branch in actual_branches_to_process])

    # Determine the date range for the initial SQL query
    # Fetch data from the start of the previous year up to the selected_date
    start_date_for_query = datetime(selected_year - 1, 1, 1).strftime('%Y-%m-%d')
    end_date_for_query = datetime.strptime(selected_date, '%m/%d/%Y').strftime('%Y-%m-%d') if selected_date else None

    date_range_condition = f" AND Date >= '{start_date_for_query}'"
    if end_date_for_query:
        date_range_condition += f" AND Date <= '{end_date_for_query}'"

    # Fetch all relevant data for the selected branches within the optimized date range
    query = f"""
        SELECT Branch, Date, CID, Name_of_Member, Loan_Account, Principal, Balance, Aging, Disbursement_Date, Due_Date, Product
        FROM aging_report_data
        WHERE Branch IN ({branch_conditions}) {date_range_condition}
    """
    combined_df = get_data_from_mysql(query)
            
    if combined_df.empty:
        print("Server Log (New Loans with Past Due History Report): No data found after initial optimized query from MySQL.")
        return []

    # Ensure date columns are datetime objects
    combined_df['Date'] = pd.to_datetime(combined_df['Date'], errors='coerce')
    combined_df['Disbursement_Date'] = pd.to_datetime(combined_df['Disbursement_Date'], errors='coerce')
    combined_df['Due_Date'] = pd.to_datetime(combined_df['Due_Date'], errors='coerce')
    combined_df.dropna(subset=['Date', 'Disbursement_Date'], inplace=True) # Drop rows where date conversion failed

    combined_df['Aging_CLEAN'] = combined_df['Aging'].astype(str).str.strip().str.upper()

    # Define aging categories for past due history check
    past_due_history_categories = ['31-60', '61-90', '91-120', '121-180', '181-365', 'OVER 365']
    
    # Define aging categories for 30-365 DAYS count (excluding 'OVER 365')
    aging_30_to_365_days_count_categories = ['31-60', '61-90', '91-120', '121-180', '181-365']

    # 1. Identify members with past due credit history BEFORE the selected year
    history_end_date = datetime(selected_year - 1, 12, 31).date()
    
    # Filter for historical past due records
    historical_past_due_df = combined_df[
        (combined_df['Date'].dt.date <= history_end_date) &
        (combined_df['Aging_CLEAN'].isin(past_due_history_categories))
    ].copy()

    # Get unique names of members who had past due history
    members_with_past_due_history = historical_past_due_df['Name_of_Member'].dropna().unique()
    
    # 2. Identify members with new loans IN the selected year
    new_loans_in_year_df = combined_df[
        (combined_df['Disbursement_Date'].dt.year == selected_year)
    ].copy()

    # Get unique names of members who received new loans in the selected year
    members_with_new_loans = new_loans_in_year_df['Name_of_Member'].dropna().unique()

    # 3. Find the intersection: members who had past due history AND new loans in the selected year
    qualified_members = pd.Series(list(set(members_with_past_due_history) & set(members_with_new_loans))).dropna().unique()

    if len(qualified_members) == 0:
        print("Server Log (New Loans with Past Due History Report): No qualified members found after intersection.")
        return []

    print(f"Server Log (New Loans with Past Due History Report): Found {len(qualified_members)} qualified members.")

    # Filter the combined_df to only include data for qualified members
    final_report_df = combined_df[combined_df['Name_of_Member'].isin(qualified_members)].copy()

    # Create helper columns for aggregation
    final_report_df['is_new_loan_in_year'] = (final_report_df['Disbursement_Date'].dt.year == selected_year)
    final_report_df['is_historical_30_365'] = (final_report_df['Date'].dt.date <= history_end_date) & \
                                              (final_report_df['Aging_CLEAN'].isin(aging_30_to_365_days_count_categories))
    final_report_df['is_historical_over_365'] = (final_report_df['Date'].dt.date <= history_end_date) & \
                                                (final_report_df['Aging_CLEAN'] == 'OVER 365')

    # Calculate Principal and Balance for new loans in the selected year for each member
    # Get unique new loan accounts and their earliest principal per member
    new_loans_principals = final_report_df[final_report_df['is_new_loan_in_year']].sort_values(by=['Name_of_Member', 'Loan_Account', 'Disbursement_Date']) \
                                                     .drop_duplicates(subset=['Name_of_Member', 'Loan_Account'], keep='first') \
                                                     .groupby('Name_of_Member')['Principal'].sum().reset_index()
    new_loans_principals.rename(columns={'Principal': 'PRINCIPAL_SUM_AGG'}, inplace=True)

    # Get unique new loan accounts and their latest balance per member (as of max date in the year for that loan)
    new_loans_balances = final_report_df[final_report_df['is_new_loan_in_year']].sort_values(by=['Name_of_Member', 'Loan_Account', 'Date']) \
                                                   .drop_duplicates(subset=['Name_of_Member', 'Loan_Account'], keep='last') \
                                                   .groupby('Name_of_Member')['Balance'].sum().reset_index()
    new_loans_balances.rename(columns={'Balance': 'BALANCE_SUM_AGG'}, inplace=True)

    # Count historical aging categories per member
    historical_aging_counts = final_report_df.groupby('Name_of_Member').agg(
        COUNT_30_365=('is_historical_30_365', 'sum'),
        COUNT_OVER_365=('is_historical_over_365', 'sum')
    ).reset_index()
    
    # Get unique branches for new loans for each member
    new_loan_branches_agg = final_report_df[final_report_df['is_new_loan_in_year']].groupby('Name_of_Member')['Branch'].apply(lambda x: ', '.join(sorted(x.unique()))).reset_index()
    new_loan_branches_agg.rename(columns={'Branch': 'BRANCH_AGG'}, inplace=True)

    # Get unique account counts for new loans in the year per member
    new_loan_account_counts = final_report_df[final_report_df['is_new_loan_in_year']].groupby('Name_of_Member')['Loan_Account'].nunique().reset_index()
    new_loan_account_counts.rename(columns={'Loan_Account': 'ACCOUNTS_COUNT_AGG'}, inplace=True)


    # Merge all aggregated data into a single DataFrame for the final report
    report_data_merged = pd.DataFrame({'Name_of_Member': qualified_members}) # Start with all qualified members to ensure all are included
    report_data_merged = report_data_merged.merge(new_loan_branches_agg, on='Name_of_Member', how='left')
    report_data_merged = report_data_merged.merge(new_loan_account_counts, on='Name_of_Member', how='left')
    report_data_merged = report_data_merged.merge(new_loans_principals, on='Name_of_Member', how='left')
    report_data_merged = report_data_merged.merge(new_loans_balances, on='Name_of_Member', how='left')
    report_data_merged = report_data_merged.merge(historical_aging_counts, on='Name_of_Member', how='left')

    # Fill NaN values from left merges with 0 or empty string as appropriate
    report_data_merged['PRINCIPAL_SUM_AGG'] = report_data_merged['PRINCIPAL_SUM_AGG'].fillna(0)
    report_data_merged['BALANCE_SUM_AGG'] = report_data_merged['BALANCE_SUM_AGG'].fillna(0)
    report_data_merged['COUNT_30_365'] = report_data_merged['COUNT_30_365'].fillna(0).astype(int)
    report_data_merged['COUNT_OVER_365'] = report_data_merged['COUNT_OVER_365'].fillna(0).astype(int)
    report_data_merged['ACCOUNTS_COUNT_AGG'] = report_data_merged['ACCOUNTS_COUNT_AGG'].fillna(0).astype(int)
    report_data_merged['BRANCH_AGG'] = report_data_merged['BRANCH_AGG'].fillna('')

    report_data = []
    for _, row in report_data_merged.iterrows():
        report_data.append({
            'NAME': row['Name_of_Member'],
            'BRANCH': row['BRANCH_AGG'],
            'ACCOUNTS': row['ACCOUNTS_COUNT_AGG'],
            'PRINCIPAL': format_currency(row['PRINCIPAL_SUM_AGG']),
            'BALANCE': format_currency(row['BALANCE_SUM_AGG']),
            '30-365 DAYS': row['COUNT_30_365'],
            'OVER 365 DAYS': row['COUNT_OVER_365']
        })
    
    if report_data:
        df_report = pd.DataFrame(report_data)
        df_report.sort_values(by='PRINCIPAL', ascending=False, inplace=True)
        report_data = df_report.to_dict(orient='records')

    print(f"Server Log (New Loans with Past Due History Report): Generated {len(report_data)} rows.")
    return report_data

def get_new_loans_details(selected_branches, borrower_name, selected_year, category_type, selected_date=None): # Added selected_date
    """
    Retrieves detailed loan information for a specific borrower based on category type, from MySQL.
    The data is filtered up to the selected_date.

    Args:
        selected_branches (list): List of branches to search within.
        borrower_name (str): The name of the borrower.
        selected_year (int): The year selected in the main report.
        category_type (str): 'new_loans', '30-365_history', or 'over_365_history'.
        selected_date (str, optional): The selected date in 'MM/DD/YYYY' format to filter up to.

    Returns:
        list: A list of dictionaries with detailed loan information.
    """
    print(f"Server Log (New Loans Details): Fetching details for {borrower_name}, year {selected_year}, type {category_type}, date: {selected_date}")

    if not selected_branches:
        print("Server Log (New Loans Details): No branches provided.")
        return []

    branch_conditions = ", ".join([f"'{branch}'" for branch in selected_branches])

    date_filter_condition = ""
    query_params = {'borrower_name': borrower_name} # Initialize params dictionary
    if selected_date:
        try:
            parsed_date_str = datetime.strptime(selected_date, '%m/%d/%Y').strftime('%Y-%m-%d')
            date_filter_condition = f" AND Date <= :parsed_date_filter" # Use named parameter
            query_params['parsed_date_filter'] = parsed_date_str
        except ValueError:
            print(f"Server Log (New Loans Details): Invalid selected_date format: {selected_date}. Ignoring date filter.")


    # Fetch all relevant data for the specific borrower and selected branches from MySQL
    query = f"""
        SELECT Branch, Date, CID, Name_of_Member, Loan_Account, Principal, Balance, Aging, Disbursement_Date, Due_Date, Product
        FROM aging_report_data
        WHERE Branch IN ({branch_conditions}) AND Name_of_Member = :borrower_name {date_filter_condition}
    """
    # FIX: Pass the params dictionary to get_data_from_mysql
    combined_df = get_data_from_mysql(query, params=query_params)
            
    if combined_df.empty:
        print(f"Server Log (New Loans Details): No relevant Aging data found for details for borrower {borrower_name} in MySQL.")
        return []

    # Ensure date columns are datetime objects
    combined_df['Date'] = pd.to_datetime(combined_df['Date'], errors='coerce')
    combined_df['Disbursement_Date'] = pd.to_datetime(combined_df['Disbursement_Date'], errors='coerce')
    combined_df['Due_Date'] = pd.to_datetime(combined_df['Due_Date'], errors='coerce')
    combined_df.dropna(subset=['Date', 'Disbursement_Date'], inplace=True) # Drop rows where date conversion failed

    combined_df['Aging_CLEAN'] = combined_df['Aging'].astype(str).str.strip().str.upper()

    # Filter by borrower name (already done in query, but defensive check)
    borrower_loans_df = combined_df[combined_df['Name_of_Member'].astype(str).str.strip().str.upper() == borrower_name.upper()].copy()

    if borrower_loans_df.empty:
        print(f"Server Log (New Loans Details): No loans found for borrower {borrower_name}.")
        return []

    details_data = []
    
    past_due_history_categories = ['31-60', '61-90', '91-120', '121-180', '181-365', 'OVER 365']
    aging_30_to_365_days_count_categories = ['31-60', '61-90', '91-120', '121-180', '181-365']

    history_end_date = datetime(selected_year - 1, 12, 31).date()

    if category_type == 'new_loans':
        filtered_loans_for_display = borrower_loans_df[
            borrower_loans_df['Disbursement_Date'].dt.year == selected_year
        ].copy()
        
        for _, row in filtered_loans_for_display.iterrows():
            this_loan_df = borrower_loans_df[borrower_loans_df['Loan_Account'] == row['Loan_Account']].copy()
            this_loan_df_in_year = this_loan_df[this_loan_df['Date'].dt.year == selected_year].copy()
            latest_entry_for_this_loan = this_loan_df_in_year.loc[this_loan_df_in_year['Date'].idxmax()] if not this_loan_df_in_year.empty else None

            current_balance = latest_entry_for_this_loan['Balance'] if latest_entry_for_this_loan is not None else 0.0
            current_aging = latest_entry_for_this_loan['Aging'] if latest_entry_for_this_loan is not None else ''
            current_date = latest_entry_for_this_loan['Date'].strftime('%m/%d/%Y') if latest_entry_for_this_loan is not None and pd.notna(latest_entry_for_this_loan['Date']) else ''


            details_data.append({
                'DATE': current_date,
                'NAME': row['Name_of_Member'],
                'ACCOUNT': row['Loan_Account'],
                'PRINCIPAL': format_currency(row['Principal']),
                'BALANCE': format_currency(current_balance),
                'PRODUCT': row['Product'],
                'DISBURSED': row['Disbursement_Date'].strftime('%m/%d/%Y') if pd.notna(row['Disbursement_Date']) else '',
                'MATURITY': row['Due_Date'].strftime('%m/%d/%Y') if pd.notna(row['Due_Date']) else '',
                'AGING': current_aging
            })
    
    elif category_type == '30-365_history':
        filtered_loans_for_display = borrower_loans_df[
            (borrower_loans_df['Date'].dt.date <= history_end_date) &
            (borrower_loans_df['Aging_CLEAN'].isin(aging_30_to_365_days_count_categories))
        ].copy()

        filtered_loans_for_display.sort_values(by='Date', ascending=False, inplace=True)
        unique_historical_loans = filtered_loans_for_display.drop_duplicates(subset='Loan_Account', keep='first')

        for _, row in unique_historical_loans.iterrows():
            details_data.append({
                'DATE': row['Date'].strftime('%m/%d/%Y') if pd.notna(row['Date']) else '',
                'NAME': row['Name_of_Member'],
                'ACCOUNT': row['Loan_Account'],
                'PRINCIPAL': format_currency(row['Principal']),
                'BALANCE': format_currency(row['Balance']),
                'PRODUCT': row['Product'],
                'DISBURSED': row['Disbursement_Date'].strftime('%m/%d/%Y') if pd.notna(row['Disbursement_Date']) else '',
                'MATURITY': row['Due_Date'].strftime('%m/%d/%Y') if pd.notna(row['Due_Date']) else '',
                'AGING': row['Aging']
            })

    elif category_type == 'over_365_history':
        filtered_loans_for_display = borrower_loans_df[
            (borrower_loans_df['Date'].dt.date <= history_end_date) &
            (borrower_loans_df['Aging_CLEAN'] == 'OVER 365')
        ].copy()

        filtered_loans_for_display.sort_values(by='Date', ascending=False, inplace=True)
        unique_historical_loans = filtered_loans_for_display.drop_duplicates(subset='Loan_Account', keep='first')

        for _, row in unique_historical_loans.iterrows():
            details_data.append({
                'DATE': row['Date'].strftime('%m/%d/%Y') if pd.notna(row['Date']) else '',
                'NAME': row['Name_of_Member'],
                'ACCOUNT': row['Loan_Account'],
                'PRINCIPAL': format_currency(row['Principal']),
                'BALANCE': format_currency(row['Balance']),
                'PRODUCT': row['Product'],
                'DISBURSED': row['Disbursement_Date'].strftime('%m/%d/%Y') if pd.notna(row['Disbursement_Date']) else '',
                'MATURITY': row['Due_Date'].strftime('%m/%d/%Y') if pd.notna(row['Due_Date']) else '',
                'AGING': row['Aging']
            })
    
    print(f"Server Log (New Loans Details): Generated {len(details_data)} detail rows for category: {category_type}.")
    return details_data
