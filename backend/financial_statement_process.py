# audit_tool/backend/financial_statement_process.py
import os
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta # Import for date calculations
from backend.db_common import AREA_BRANCH_MAP # Import the centralized map
import numpy as np # Import numpy to check for NaN

# Define the base directory where financial statement data is stored
FS_BASE_DIR = r"C:\xampp\htdocs\audit_tool\db"
FS_FILENAME = "FS.xlsx"
FS_FILE_PATH = os.path.join(FS_BASE_DIR, FS_FILENAME)

# --- Global Cache for Financial Statement Data ---
# These variables will hold the loaded DataFrames and the last modification time
_cached_df_bs = None
_cached_df_is = None
_last_fs_file_modified_time = None

# Helper function to safely convert value to float, handling NaN and empty strings
def safe_float_conversion(value):
    if pd.isna(value): # Check for pandas NaN
        return 0.0
    s_value = str(value).strip()
    if not s_value: # Handle empty strings
        return 0.0
    try:
        # Handle parentheses for negative numbers and remove commas
        return float(s_value.replace(',', '').replace('(', '-').replace(')', ''))
    except ValueError:
        print(f"Server Log (FS Process Warning): Could not convert '{s_value}' to numeric. Setting to 0.0.")
        return 0.0

# --- Function to load and cache the Excel file ---
def _load_financial_statement_excel():
    """
    Loads the FS.xlsx file into global pandas DataFrames (BS and IS sheets)
    and caches them. It only reloads if the file has been modified on disk.
    """
    global _cached_df_bs, _cached_df_is, _last_fs_file_modified_time

    if not os.path.exists(FS_FILE_PATH):
        print(f"Server Log (FS Cache Error): FS.xlsx file not found at: {FS_FILE_PATH}")
        _cached_df_bs = None
        _cached_df_is = None
        _last_fs_file_modified_time = None
        return None, None

    current_modified_time = os.path.getmtime(FS_FILE_PATH)

    # Check if the file has been modified or if it's the first load
    if _cached_df_bs is None or _cached_df_is is None or current_modified_time != _last_fs_file_modified_time:
        print(f"Server Log (FS Cache): Reloading FS.xlsx due to modification or first load.")
        try:
            xl = pd.ExcelFile(FS_FILE_PATH)
            sheet_names_raw = xl.sheet_names
            
            actual_bs_sheet_name = next((s for s in sheet_names_raw if s.strip() == 'BS'), None)
            if actual_bs_sheet_name:
                _cached_df_bs = xl.parse(sheet_name=actual_bs_sheet_name, header=None, dtype=str)
                print(f"Server Log (FS Cache): Successfully loaded '{actual_bs_sheet_name}' sheet.")
            else:
                _cached_df_bs = None
                print(f"Server Log (FS Cache Error): Worksheet named 'BS' (stripped) not found in '{FS_FILENAME}'.")

            actual_is_sheet_name = next((s for s in sheet_names_raw if s.strip() == 'IS'), None)
            if actual_is_sheet_name:
                _cached_df_is = xl.parse(sheet_name=actual_is_sheet_name, header=None, dtype=str)
                print(f"Server Log (FS Cache): Successfully loaded '{actual_is_sheet_name}' sheet.")
            else:
                _cached_df_is = None
                print(f"Server Log (FS Cache Error): Worksheet named 'IS' (stripped) not found in '{FS_FILENAME}'.")

            _last_fs_file_modified_time = current_modified_time
            print(f"Server Log (FS Cache): FS.xlsx loaded and cache updated.")

        except Exception as e:
            print(f"Server Log (FS Cache Error): Error reading FS.xlsx during cache load: {e}")
            _cached_df_bs = None
            _cached_df_is = None
            _last_fs_file_modified_time = None # Reset on error to force reload next time
            return None, None
    else:
        print(f"Server Log (FS Cache): Using cached FS.xlsx data.")

    return _cached_df_bs, _cached_df_is


# --- Optimized Column Index Finder ---
def get_column_index_map(df, branch_lookup_row_idx, date_lookup_row_idx, target_area_name, current_branch_selection, lookup_date_str, last_december_lookup_str_fp, previous_period_lookup_str_is, bs_trend_dates_lookup_str, is_trend_dates_lookup_str):
    """
    Builds a map of (branch_name, date_str) to column index for efficient lookups.
    Handles 'ALL' and 'CONSOLIDATED' branches.
    """
    col_index_map = {}
    if df is None:
        return col_index_map

    branches_to_scan = []
    if current_branch_selection.upper() == 'CONSOLIDATED':
        branches_to_scan = ['CONSOLIDATED']
    elif current_branch_selection.upper() == 'ALL':
        # For 'ALL', get all branches in the selected area, excluding 'ALL' and 'CONSOLIDATED' itself
        branches_in_area = AREA_BRANCH_MAP.get(target_area_name, [])
        branches_to_scan = [b.upper() for b in branches_in_area if b.upper() not in ['ALL', 'CONSOLIDATED']]
        # If 'ALL' is selected for a specific area, and that area is 'CONSOLIDATED',
        # then only 'CONSOLIDATED' branch should be processed.
        if target_area_name.upper() == 'CONSOLIDATED':
            branches_to_scan = ['CONSOLIDATED']
    else:
        branches_to_scan = [current_branch_selection.upper()]
    
    # Collect all unique dates we need to look up
    all_target_dates = set([lookup_date_str, last_december_lookup_str_fp, previous_period_lookup_str_is])
    # Add all BS trend dates
    for d_str in bs_trend_dates_lookup_str:
        all_target_dates.add(d_str)

    # Add all IS trend dates
    for d_str in is_trend_dates_lookup_str:
        all_target_dates.add(d_str)


    print(f"Server Log (get_column_index_map): Branches to scan for: {branches_to_scan}")
    print(f"Server Log (get_column_index_map): All target dates: {all_target_dates}")

    # Ensure row indices are within DataFrame bounds
    if branch_lookup_row_idx >= len(df) or date_lookup_row_idx >= len(df):
        print(f"Server Log (get_column_index_map Error): Lookup row index out of bounds. Branch row: {branch_lookup_row_idx}, Date row: {date_lookup_row_idx}, DataFrame rows: {len(df)}")
        return col_index_map

    for col_idx in range(len(df.columns)):
        if col_idx >= len(df.columns): # Ensure column index is within bounds
            continue
        current_branch_cell_value = str(df.iloc[branch_lookup_row_idx, col_idx]).strip().upper()
        current_date_cell_value = str(df.iloc[date_lookup_row_idx, col_idx]).strip()

        if current_branch_cell_value in branches_to_scan and current_date_cell_value in all_target_dates:
            key = (current_branch_cell_value, current_date_cell_value)
            if key not in col_index_map: # Store the first matching column if duplicates exist
                col_index_map[key] = col_idx
    
    print(f"Server Log (get_column_index_map): Final column index map: {col_index_map}")
    return col_index_map

# --- Helper to get values for an account across multiple dates ---
def get_values_for_account_across_dates(df, account_row_idx, col_index_map, target_branches_list, target_dates):
    """
    Retrieves and sums values for a given account across multiple branches and dates.
    `target_branches_list` can be a single branch name in a list, or multiple branch names.
    """
    all_date_values = []
    for date_str in target_dates:
        total_value_for_date = 0.0
        for branch_to_sum in target_branches_list:
            key = (branch_to_sum.upper(), date_str)
            col_idx = col_index_map.get(key)
            if col_idx is not None:
                if account_row_idx < len(df) and col_idx < len(df.columns):
                    raw_value = df.iloc[account_row_idx, col_idx]
                    value = safe_float_conversion(raw_value)
                    total_value_for_date += value
        all_date_values.append(total_value_for_date)
    return all_date_values


# Helper to calculate percentages for Financial Position
def calculate_percentages_fp(current_val, last_dec_val, total_assets):
    changes_pct = 0.0
    if last_dec_val != 0:
        changes_pct = ((current_val - last_dec_val) / last_dec_val) * 100
    elif current_val != 0:
        changes_pct = 100.0 # Or float('inf')
    
    structure_pct = 0.0
    if total_assets != 0:
        structure_pct = (current_val / total_assets) * 100
    return changes_pct, structure_pct

# Helper to calculate percentages for Financial Performance
def calculate_percentages_fp_is(current_val, previous_val, structure_base):
    changes_pct = 0.0
    if previous_val != 0:
        # Special handling for Net Surplus/Loss:
        # If previous_val is negative and current_val is less negative or positive, it's an improvement (positive change)
        # If previous_val is positive and current_val is less positive or negative, it's a decline (negative change)
        if (previous_val < 0 and current_val >= previous_val):
            # When previous is negative and current is less negative or positive, it's an improvement
            # Calculate the magnitude of change and express as a positive percentage
            changes_pct = ((current_val - previous_val) / abs(previous_val)) * 100
        elif (previous_val > 0 and current_val <= previous_val):
            # When previous is positive and current is less positive or negative, it's a decline
            changes_pct = ((current_val - previous_val) / previous_val) * 100
        elif (previous_val < 0 and current_val < previous_val):
            # When both are negative and current is more negative (worsening)
            changes_pct = ((current_val - previous_val) / abs(previous_val)) * 100
        else: # Standard percentage change for other scenarios (both positive, or positive and increasing)
            changes_pct = ((current_val - previous_val) / previous_val) * 100
    elif current_val != 0:
        changes_pct = 100.0 # If previous is zero and current is not, it's a 100% change (or infinite)

    structure_pct = 0.0
    if structure_base != 0:
        structure_pct = (current_val / structure_base) * 100
    return changes_pct, structure_pct


def process_financial_statement(branch_name, report_date_str, area_name): # Added area_name parameter
    print(f"Server Log (FS Process): Attempting to process FS for Area: '{area_name}', Branch: '{branch_name}', Date: '{report_date_str}'")
    
    # Load or reload the Excel data from cache
    df_bs, df_is = _load_financial_statement_excel()

    if df_bs is None and df_is is None:
        print(f"Server Log (FS Process Error): Neither 'BS' nor 'IS' sheets were found or loaded from cache. Returning empty data.")
        return {}

    # Convert report_date_str to datetime object for comparison
    try:
        report_date_dt = datetime.strptime(report_date_str, '%Y-%m-%d')
        lookup_date_str = report_date_dt.strftime('%#m/%d/%Y') # Format for Excel lookup (e.g., 5/31/2025)
        print(f"Server Log (FS Process): Converted report date '{report_date_str}' to lookup format '{lookup_date_str}'")

        # Calculate Last December date for Financial Position (previous year's December 31)
        last_december_dt_fp = datetime(report_date_dt.year - 1, 12, 31)
        last_december_lookup_str_fp = last_december_dt_fp.strftime('%#m/%d/%Y')
        print(f"Server Log (FS Process): Calculated Last December date for Financial Position lookup: '{last_december_lookup_str_fp}'")

        # Calculate Previous Period date for Financial Performance (same month/day, previous year)
        previous_period_dt_is = report_date_dt - relativedelta(years=1)
        previous_period_lookup_str_is = previous_period_dt_is.strftime('%#m/%d/%Y')
        print(f"Server Log (FS Process): Calculated Previous Period date for Financial Performance lookup: '{previous_period_lookup_str_is}'")

    except ValueError as e:
        print(f"Server Log (FS Process Error): Invalid date format for report_date_str: {e}")
        return {}

    # --- Column Row Indices ---
    bs_branch_row_index = 3 # Excel row 4
    bs_date_row_index = 5 # Excel row 6
    is_branch_row_index = 4 # Excel row 5 (for branch name)
    is_date_row_index = 5 # Excel row 6 (for date)

    # Generate the 5-year trend dates for BS
    bs_trend_dates_lookup_str = []
    for i in range(4, 0, -1):
        trend_year_dt = datetime(report_date_dt.year - i, 12, 31)
        bs_trend_dates_lookup_str.append(trend_year_dt.strftime('%#m/%d/%Y'))
    bs_trend_dates_lookup_str.append(lookup_date_str) # Add current date as the 5th point
    print(f"Server Log (FS Process): BS Trend Dates for lookup: {bs_trend_dates_lookup_str}")

    # Generate the 5-year trend dates for IS
    is_trend_dates_lookup_str = []
    for i in range(4, 0, -1):
        trend_year_dt = report_date_dt - relativedelta(years=i)
        is_trend_dates_lookup_str.append(trend_year_dt.strftime('%#m/%d/%Y'))
    is_trend_dates_lookup_str.append(lookup_date_str) # Add current date as the 5th point
    print(f"Server Log (FS Process): IS Trend Dates for lookup: {is_trend_dates_lookup_str}")


    # Determine the actual list of branches to process for BS
    bs_branches_to_process = []
    if branch_name.upper() == 'CONSOLIDATED':
        bs_branches_to_process = ['CONSOLIDATED']
    elif branch_name.upper() == 'ALL':
        bs_branches_to_process = [b.upper() for b in AREA_BRANCH_MAP.get(area_name, []) if b.upper() not in ['ALL', 'CONSOLIDATED']]
        if area_name.upper() == 'CONSOLIDATED': # If 'ALL' is chosen under 'CONSOLIDATED' area, it means only CONSOLIDATED branch
            bs_branches_to_process = ['CONSOLIDATED']
    else:
        bs_branches_to_process = [branch_name.upper()]

    # Pre-build column index map for BS (Called only once now)
    bs_col_index_map = get_column_index_map(df_bs, bs_branch_row_index, bs_date_row_index, area_name, branch_name, lookup_date_str, last_december_lookup_str_fp, previous_period_lookup_str_is, bs_trend_dates_lookup_str, is_trend_dates_lookup_str)
    if not bs_col_index_map and df_bs is not None: # If df_bs exists but no columns found for any date/branch
        print(f"Server Log (FS Process Error): No relevant columns found in BS sheet for branch '{branch_name}' and any target date. Returning empty data.")
        return {}


    # Define the main accounts and their row numbers (0-indexed for pandas) for BS
    bs_accounts_map = {
        # ASSETS - CURRENT ASSETS
        'cashAndCashEquivalents': {'label': 'Cash and Cash Equivalents:', 'row': 19 - 1, 'type': 'asset', 'category': 'current'},
        'loansAndReceivables': {'label': 'Loans and Receivables:', 'row': 42 - 1, 'type': 'asset', 'category': 'current'},
        'financialAssetsCurrent': {'label': 'Financial Assets:', 'row': 48 - 1, 'type': 'asset', 'category': 'current'},
        'otherCurrentAssets': {'label': 'Other Current Assets:', 'row': 57 - 1, 'type': 'asset', 'category': 'current'},
        
        # ASSETS - NON-CURRENT ASSETS
        'financialAssetsNonCurrent': {'label': 'Financial Assets - Non-Current:', 'row': 67 - 1, 'type': 'asset', 'category': 'non-current'},
        'investmentInSubsidiaries': {'label': 'Investment in Subsidiaries:', 'row': 68 - 1, 'type': 'asset', 'category': 'non-current'},
        'investmentInAssociates': {'label': 'Investment in Associates:', 'row': 69 - 1, 'type': 'asset', 'category': 'non-current'},
        'investmentInJointVentures': {'label': 'Investment in Joint Ventures:', 'row': 70 - 1, 'type': 'asset', 'category': 'non-current'},
        'investmentProperty': {'label': 'Investment Property:', 'row': 83 - 1, 'type': 'asset', 'category': 'non-current'},
        'propertyPlantAndEquipment': {'label': 'Property, Plant, and Equipment:', 'row': 102 - 1, 'type': 'asset', 'category': 'non-current'},
        'otherNonCurrentAssets': {'label': 'Other Non-Current Assets:', 'row': 108 - 1, 'type': 'asset', 'category': 'non-current'},

        # LIABILITIES - CURRENT LIABILITIES
        'depositLiabilities': {'label': 'Deposit Liabilities:', 'row': 119 - 1, 'type': 'liability', 'category': 'current'},
        'accountsAndOtherPayables': {'label': 'Accounts and Other Payables:', 'row': 127 - 1, 'type': 'liability', 'category': 'current'},
        'accruedExpenses': {'label': 'Accrued Expenses:', 'row': 135 - 1, 'type': 'liability', 'category': 'current'},
        'otherCurrentLiabilities': {'label': 'Other Current Liabilities:', 'row': 141 - 1, 'type': 'liability', 'category': 'current'},

        # LIABILITIES - NON-CURRENT LIABILITIES
        'loansPayableNet': {'label': 'Loans Payable, Net:', 'row': 147 - 1, 'type': 'liability', 'category': 'non-current'},
        'revolvingCapitalPayable': {'label': 'Revolving Capital Payable:', 'row': 148 - 1, 'type': 'liability', 'category': 'non-current'},
        'retirementFundPayable': {'label': 'Retirement Fund Payable:', 'row': 149 - 1, 'type': 'liability', 'category': 'non-current'},
        'projectSubsidyFundPayable': {'label': 'Project Subsidy Fund Payable:', 'row': 156 - 1, 'type': 'liability', 'category': 'non-current'},
        'membersBenefitsAndOtherFundsPayable': {'label': 'Members\' Benefits and Other Funds Payable:', 'row': 154 - 1, 'type': 'liability', 'category': 'non-current'},
        'dueToHeadOfficeBranchSubsidiary': {'label': 'Due to Head Office/Branch/Subsidiary:', 'row': 155 - 1, 'type': 'liability', 'category': 'non-current'},
        'otherNonCurrentLiabilities': {'label': 'Other Non-Current Liabilities:', 'row': 156 - 1, 'type': 'liability', 'category': 'non-current'},
        'commonShares': {'label': 'Common Shares:', 'row': 171 - 1, 'type': 'equity', 'category': 'equity'},
        'preferredShares': {'label': 'Preferred Shares:', 'row': 178 - 1, 'type': 'equity', 'category': 'equity'},
        'depositsForShareCapitalSubscription': {'label': 'Deposits for Share Capital Subscription:', 'row': 179 - 1, 'type': 'equity', 'category': 'equity'},
        'undividedNetSurplusNetLoss': {'label': 'Undivided Net Surplus (Net Loss):', 'row': 182 - 1, 'type': 'equity', 'category': 'equity'},
        'statutoryFunds': {'label': 'STATUTORY FUNDS:', 'row': 191 - 1, 'type': 'equity', 'category': 'equity'},
    }

    # Define sub-accounts and their row numbers (0-indexed) for BS
    bs_sub_accounts_map = {
        'Cash and Cash Equivalents:': [
            {'label': 'Cash on Hand', 'row': 11 - 1},
            {'label': 'Checks and Other Cash Items (COCI)', 'row': 12 - 1},
            {'label': 'Cash in Bank', 'row': 13 - 1},
            {'label': 'Cash in Cooperative Federation', 'row': 14 - 1},
            {'label': 'Petty Cash Fund', 'row': 15 - 1},
            {'label': 'Revolving Fund', 'row': 16 - 1},
            {'label': 'Change Fund', 'row': 17 - 1},
            {'label': 'ATM Fund', 'row': 18 - 1},
        ],
        'Loans and Receivables:': [
            {'label': 'Loans Receivable (based on PAR)', 'row': 21 - 1},
            {'label': 'Loans Receivable - Current', 'row': 22 - 1},
            {'label': 'Loans Receivable - Past Due', 'row': 23 - 1},
            {'label': 'Loans Receivable - Restructured (Past Due)', 'row': 24 - 1},
            {'label': 'Loans Receivable - Loans in Litigation (Past Due)', 'row': 25 - 1},
            {'label': 'Total Loans Receivables (Gross)', 'row': 26 - 1},
            {'label': 'Less: Unearned Interests and Discounts', 'row': 27 - 1},
            {'label': 'Allowance for Probable Losses on Loans', 'row': 28 - 1},
            {'label': 'Net, Loans Receivable', 'row': 29 - 1},
            {'label': 'Sales Contract Receivable', 'row': 30 - 1},
            {'label': 'Less: Allowance for Probable Losses - SCR', 'row': 31 - 1},
            {'label': 'Net, Sales Contract Receivable', 'row': 32 - 1},
            {'label': 'Accounts Receivables - Non Trade', 'row': 33 - 1},
            {'label': 'Less: Allowance for Probable Losses - AR-NT', 'row': 34 - 1},
            {'label': 'Net, Accounts Receivables - Non Trade', 'row': 35 - 1},
            {'label': 'Advances to Officers, Employees and Members', 'row': 36 - 1},
            {'label': 'Due from Accountable Officers and Employees', 'row': 37 - 1},
            {'label': 'Finance Lease Receivable', 'row': 38 - 1},
            {'label': 'Allowance for Impairment-Finance Lease Receivable', 'row': 39 - 1},
            {'label': 'Net, Finance Lease Receivable', 'row': 40 - 1},
            {'label': 'Other Current Receivables', 'row': 41 - 1},
        ],
        'Financial Assets:': [ # This is Financial Assets (Current)
            {'label': 'Financial Assets', 'row': 43 - 1},
            {'label': 'Financial Assets at Fair Value through Profit and Loss', 'row': 44 - 1},
            {'label': 'Financial Assets at Cost', 'row': 45 - 1},
            {'label': 'Less: Allowance for Impairment', 'row': 62 - 1}, # Corrected row number for consistency
            {'label': 'Net', 'row': 63 - 1}, # Corrected row number for consistency
            {'label': 'Financial Assets at Amortized Cost', 'row': 64 - 1}, # Corrected row number for consistency
            {'label': 'Less: Allowance for Impairment', 'row': 65 - 1}, # Corrected row number for consistency
            {'label': 'Net', 'row': 66 - 1}, # Corrected row number for consistency
        ],
        'Other Current Assets:': [
            {'label': 'Deposit to Suppliers', 'row': 50 - 1},
            {'label': 'Unused Supplies', 'row': 51 - 1},
            {'label': 'Prepaid Expenses', 'row': 52 - 1},
            {'label': 'Assets Acquired in Settlement of Loans/Accounts', 'row': 53 - 1},
            {'label': 'Less: Accumulated Depreciation - A/ASL/A', 'row': 54 - 1},
            {'label': 'Net, Assets Acquired in Settlement of Loans/Accounts', 'row': 55 - 1},
            {'label': 'Other Current Assets', 'row': 56 - 1},
        ],
        'Financial Assets - Non-Current:': [
            {'label': 'Financial Assets - Non-Current', 'row': 60 - 1},
            {'label': 'Financial Assets at Cost', 'row': 61 - 1},
            {'label': 'Less: Allowance for Impairment', 'row': 62 - 1},
            {'label': 'Net', 'row': 63 - 1},
            {'label': 'Financial Assets at Amortized Cost', 'row': 64 - 1},
            {'label': 'Less: Allowance for Impairment', 'row': 65 - 1},
            {'label': 'Net', 'row': 66 - 1},
        ],
        'Investment Property:': [
            {'label': 'Investment Property - Land', 'row': 72 - 1},
            {'label': 'Investment Property - Land Improvements', 'row': 73 - 1},
            {'label': 'Less: Accumulated Depreciation - Land Improvements', 'row': 74 - 1},
            {'label': 'Investment Property - Furniture, Fixtures and Equipment', 'row': 75 - 1},
            {'label': 'Less: Accumulated Depreciation - Furniture, Fixtures and Equipment', 'row': 76 - 1},
            {'label': 'Investment Property - Machineries, Tools and Equipment', 'row': 77 - 1},
            {'label': 'Less: Accumulated Depreciation - Machineries, Tools and Equipment', 'row': 78 - 1},
            {'label': 'Investment Property - Building', 'row': 79 - 1},
            {'label': 'Less: Accumulated Depreciation - IP - Building', 'row': 80 - 1},
            {'label': 'Real Properties Acquired (RPA)', 'row': 81 - 1},
            {'label': 'Less: Accumulated Depreciation - RPA', 'row': 82 - 1},
        ],
        'Property, Plant, and Equipment:': [
            {'label': 'Land', 'row': 85 - 1},
            {'label': 'Land Improvements', 'row': 86 - 1},
            {'label': 'Less: Accumulated Depreciation - Land Improvements', 'row': 87 - 1},
            {'label': 'Building and Improvements', 'row': 88 - 1},
            {'label': 'Less: Accumulated Depreciation - Bldg and Improv', 'row': 89 - 1},
            {'label': 'Building on Leased/Usufruct Land', 'row': 90 - 1},
            {'label': 'Less: Accumulated Depreciation - Bldg on Leased/Usufruct Land', 'row': 91 - 1},
            {'label': 'Property, Plant and Equipment - Under Finance Lease', 'row': 92 - 1},
            {'label': 'Less: Accumulated Depreciation - PPE Under Finance Lease', 'row': 93 - 1},
            {'label': 'Construction in Progress', 'row': 94 - 1},
            {'label': 'Furniture, Fixtures and Equipment', 'row': 95 - 1},
            {'label': 'Less: Accumulated Depreciation - FF and E', 'row': 96 - 1},
            {'label': 'Machineries, Tools and Equipment', 'row': 97 - 1},
            {'label': 'Less: Accumulated Depreciation - Machineries and Equiptment', 'row': 98 - 1},
            {'label': 'Transportation Equipment', 'row': 99 - 1},
            {'label': 'Less: Accumulated Depreciation - Transpo Equiptment', 'row': 100 - 1},
            {'label': 'Leasehold Rights and Improvements (net of Amortization)', 'row': 101 - 1},
        ],
        'Other Non-Current Assets:': [
            {'label': 'Computerization Cost, net', 'row': 104 - 1},
            {'label': 'Other Funds and Deposits', 'row': 105 - 1},
            {'label': 'Due from Head Office/Branch/Subsidy', 'row': 106 - 1},
            {'label': 'Miscellaneous Assets', 'row': 107 - 1},
        ],
        'Deposit Liabilities:': [
            {'label': 'Savings Deposits', 'row': 117 - 1},
            {'label': 'Time Deposits', 'row': 118 - 1},
        ],
        'Accounts and Other Payables:': [
            {'label': 'Accounts Payable - Non-Trade', 'row': 121 - 1},
            {'label': 'Loans Payable - Current', 'row': 122 - 1},
            {'label': 'Less: Discounts on Loans Payable', 'row': 123 - 1},
            {'label': 'Loans Payable, Net', 'row': 124 - 1},
            {'label': 'Cash Bond Payable', 'row': 125 - 1},
            {'label': 'Other Payables', 'row': 126 - 1},
        ],
        'Accrued Expenses:': [
            {'label': 'Due to Regulatory Agencies', 'row': 129 - 1},
            {'label': 'SSS/ECC/PhilHealth and Pag-ibig Premium Contributions Payable', 'row': 130 - 1},
            {'label': 'SSS / Pag-ibig Loans Payable', 'row': 131 - 1},
            {'label': 'Withholding Tax Payable', 'row': 132 - 1},
            {'label': 'Income Tax Payable', 'row': 133 - 1},
            {'label': 'Other Accrued Expenses', 'row': 134 - 1},
        ],
        'Other Current Liabilities:': [
            {'label': 'Other Current Liabilities', 'row': 136 - 1},
            {'label': 'Deposit from Customers', 'row': 137 - 1},
            {'label': 'Interest on Share Capital Payable', 'row': 138 - 1},
            {'label': 'Patronage Refund Payable', 'row': 139 - 1},
            {'label': 'Due to Union/Federation (CETF)', 'row': 140 - 1},
        ],
        'STATUTORY FUNDS:': [
            {'label': 'Reserve Fund', 'row': 187 - 1},
            {'label': 'Coop Education and Training Fund', 'row': 188 - 1},
            {'label': 'Community Development Fund', 'row': 189 - 1},
            {'label': 'Optional Fund', 'row': 190 - 1},
        ],
    }

    # Initialize structured data for BS
    bs_structured_data = {
        'assets': {
            'current': [],
            'non-current': [],
            'totalCurrent': {'label': 'TOTAL CURRENT ASSETS:', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5},
            'totalNonCurrent': {'label': 'TOTAL NON-CURRENT ASSETS:', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5},
            'grandTotal': {'label': 'TOTAL ASSETS:', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5}
        },
        'liabilities': {
            'current': [],
            'non-current': [],
            'totalCurrent': {'label': 'TOTAL CURRENT LIABILITIES:', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5},
            'totalNonCurrent': {'label': 'TOTAL NON-CURRENT LIABILITIES:', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5},
            'grandTotal': {'label': 'TOTAL LIABILITIES:', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5}
        },
        'equity': {
            'equity': [],
            'grandTotal': {'label': 'TOTAL MEMBERS\' EQUITY:', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5}
        },
        'totalLiabilitiesAndMembersEquity': {'label': 'TOTAL LIABILITIES AND MEMBERS\' EQUITY:', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5}
    }

    # Process BS data only if df_bs was loaded successfully
    if df_bs is not None:
        # The bs_col_index_map is already built above, no need to rebuild it here.

        # Populate bs_structured_data with main account details and their sub-accounts
        for key, item_info in bs_accounts_map.items():
            main_account_label = item_info['label']
            
            # Get all required values for main account in one go
            main_account_all_values = get_values_for_account_across_dates(
                df_bs, item_info['row'], bs_col_index_map, bs_branches_to_process, # Pass the list of branches
                [lookup_date_str, last_december_lookup_str_fp] + bs_trend_dates_lookup_str
            )
            current_main_account_value = main_account_all_values[0]
            last_dec_main_account_value = main_account_all_values[1]
            main_account_trend_data = main_account_all_values[2:] # Remaining are trend data

            components = []
            if main_account_label in bs_sub_accounts_map:
                for sub_item_info in bs_sub_accounts_map[main_account_label]:
                    sub_row_idx = sub_item_info['row']
                    
                    # Get all required values for sub-account in one go
                    sub_account_all_values = get_values_for_account_across_dates(
                        df_bs, sub_row_idx, bs_col_index_map, bs_branches_to_process, # Pass the list of branches
                        [lookup_date_str, last_december_lookup_str_fp] + bs_trend_dates_lookup_str
                    )
                    current_sub_value = sub_account_all_values[0]
                    last_dec_sub_value = sub_account_all_values[1]
                    sub_account_trend_data = sub_account_all_values[2:] # Remaining are trend data

                    # Calculate percentages for sub-account
                    sub_changes_pct, sub_structure_pct = calculate_percentages_fp(current_sub_value, last_dec_sub_value, 0) # total_assets will be calculated later

                    components.append({
                        'label': sub_item_info['label'],
                        'current_balance': current_sub_value,
                        'last_december_balance': last_dec_sub_value,
                        'changes_percentage': sub_changes_pct,
                        'structure_percentage': sub_structure_pct,
                        'trend_data': sub_account_trend_data # Add trend data to sub-account
                    })

            # Calculate percentages for main account
            main_changes_pct, main_structure_pct = calculate_percentages_fp(current_main_account_value, last_dec_main_account_value, 0) # total_assets will be calculated later

            account_entry = {
                'label': main_account_label,
                'current_balance': current_main_account_value,
                'last_december_balance': last_dec_main_account_value,
                'changes_percentage': main_changes_pct,
                'structure_percentage': main_structure_pct,
                'trend_data': main_account_trend_data, # Add trend data to main account
                'components': components # Add the list of sub-accounts
            }

            if item_info['type'] == 'asset':
                bs_structured_data['assets'][item_info['category']].append(account_entry)
            elif item_info['type'] == 'liability':
                bs_structured_data['liabilities'][item_info['category']].append(account_entry)
            elif item_info['type'] == 'equity':
                bs_structured_data['equity'][item_info['category']].append(account_entry)

        # Recalculate totals for current and last december balances
        bs_structured_data['assets']['totalCurrent']['current_balance'] = sum(item['current_balance'] for item in bs_structured_data['assets']['current'])
        bs_structured_data['assets']['totalCurrent']['last_december_balance'] = sum(item['last_december_balance'] for item in bs_structured_data['assets']['current'])
        bs_structured_data['assets']['totalCurrent']['trend_data'] = [sum(x) for x in zip(*[item['trend_data'] for item in bs_structured_data['assets']['current']])]
        
        bs_structured_data['assets']['totalNonCurrent']['current_balance'] = sum(item['current_balance'] for item in bs_structured_data['assets']['non-current'])
        bs_structured_data['assets']['totalNonCurrent']['last_december_balance'] = sum(item['last_december_balance'] for item in bs_structured_data['assets']['non-current'])
        bs_structured_data['assets']['totalNonCurrent']['trend_data'] = [sum(x) for x in zip(*[item['trend_data'] for item in bs_structured_data['assets']['non-current']])]
        
        bs_structured_data['assets']['grandTotal']['current_balance'] = sum(item['current_balance'] for item in bs_structured_data['assets']['current']) + sum(item['current_balance'] for item in bs_structured_data['assets']['non-current']) # Corrected sum
        bs_structured_data['assets']['grandTotal']['last_december_balance'] = sum(item['last_december_balance'] for item in bs_structured_data['assets']['current']) + sum(item['last_december_balance'] for item in bs_structured_data['assets']['non-current']) # Corrected sum
        bs_structured_data['assets']['grandTotal']['trend_data'] = [sum(x) for x in zip(bs_structured_data['assets']['totalCurrent']['trend_data'], bs_structured_data['assets']['totalNonCurrent']['trend_data'])]

        bs_structured_data['liabilities']['totalCurrent']['current_balance'] = sum(item['current_balance'] for item in bs_structured_data['liabilities']['current'])
        bs_structured_data['liabilities']['totalCurrent']['last_december_balance'] = sum(item['last_december_balance'] for item in bs_structured_data['liabilities']['current'])
        bs_structured_data['liabilities']['totalCurrent']['trend_data'] = [sum(x) for x in zip(*[item['trend_data'] for item in bs_structured_data['liabilities']['current']])]
        
        bs_structured_data['liabilities']['totalNonCurrent']['current_balance'] = sum(item['current_balance'] for item in bs_structured_data['liabilities']['non-current'])
        bs_structured_data['liabilities']['totalNonCurrent']['last_december_balance'] = sum(item['last_december_balance'] for item in bs_structured_data['liabilities']['non-current'])
        bs_structured_data['liabilities']['totalNonCurrent']['trend_data'] = [sum(x) for x in zip(*[item['trend_data'] for item in bs_structured_data['liabilities']['non-current']])]
        
        bs_structured_data['liabilities']['grandTotal']['current_balance'] = sum(item['current_balance'] for item in bs_structured_data['liabilities']['current']) + sum(item['current_balance'] for item in bs_structured_data['liabilities']['non-current']) # Corrected sum
        bs_structured_data['liabilities']['grandTotal']['last_december_balance'] = sum(item['last_december_balance'] for item in bs_structured_data['liabilities']['current']) + sum(item['last_december_balance'] for item in bs_structured_data['liabilities']['non-current']) # Corrected sum
        bs_structured_data['liabilities']['grandTotal']['trend_data'] = [sum(x) for x in zip(bs_structured_data['liabilities']['totalCurrent']['trend_data'], bs_structured_data['liabilities']['totalNonCurrent']['trend_data'])]

        bs_structured_data['equity']['grandTotal']['current_balance'] = sum(item['current_balance'] for item in bs_structured_data['equity']['equity'])
        bs_structured_data['equity']['grandTotal']['last_december_balance'] = sum(item['last_december_balance'] for item in bs_structured_data['equity']['equity'])
        bs_structured_data['equity']['grandTotal']['trend_data'] = [sum(x) for x in zip(*[item['trend_data'] for item in bs_structured_data['equity']['equity']])]

        bs_structured_data['totalLiabilitiesAndMembersEquity']['current_balance'] = bs_structured_data['liabilities']['grandTotal']['current_balance'] + bs_structured_data['equity']['grandTotal']['current_balance']
        bs_structured_data['totalLiabilitiesAndMembersEquity']['last_december_balance'] = bs_structured_data['liabilities']['grandTotal']['last_december_balance'] + bs_structured_data['equity']['grandTotal']['last_december_balance']
        bs_structured_data['totalLiabilitiesAndMembersEquity']['trend_data'] = [sum(x) for x in zip(bs_structured_data['liabilities']['grandTotal']['trend_data'], bs_structured_data['equity']['grandTotal']['trend_data'])]


        # Now calculate percentages for totals and sub-accounts using the final total_assets_current_date
        total_assets_current_date = bs_structured_data['assets']['grandTotal']['current_balance']

        # Recalculate percentages for all accounts and sub-accounts in BS
        for category_key in ['assets', 'liabilities', 'equity']:
            for sub_category_key in bs_structured_data[category_key]:
                if isinstance(bs_structured_data[category_key][sub_category_key], list): # It's a list of accounts
                    for account in bs_structured_data[category_key][sub_category_key]:
                        account['changes_percentage'], account['structure_percentage'] = \
                            calculate_percentages_fp(account['current_balance'], account['last_december_balance'], total_assets_current_date)
                        for sub_component in account['components']:
                            sub_component['changes_percentage'], sub_component['structure_percentage'] = \
                                calculate_percentages_fp(sub_component['current_balance'], sub_component['last_december_balance'], total_assets_current_date)
                elif isinstance(bs_structured_data[category_key][sub_category_key], dict) and 'current_balance' in bs_structured_data[category_key][sub_category_key]: # It's a total
                    total_item = bs_structured_data[category_key][sub_category_key]
                    total_item['changes_percentage'], total_item['structure_percentage'] = \
                        calculate_percentages_fp(total_item['current_balance'], total_item['last_december_balance'], total_assets_current_date)
        
        # Handle the top-level totalLiabilitiesAndMembersEquity separately
        bs_structured_data['totalLiabilitiesAndMembersEquity']['changes_percentage'], bs_structured_data['totalLiabilitiesAndMembersEquity']['structure_percentage'] = \
            calculate_percentages_fp(bs_structured_data['totalLiabilitiesAndMembersEquity']['current_balance'], bs_structured_data['totalLiabilitiesAndMembersEquity']['last_december_balance'], total_assets_current_date)


        print(f"Server Log (FS Process): Successfully processed BS data for branch '{branch_name}' on '{report_date_str}'.")
    else:
        print(f"Server Log (FS Process): Skipping BS data processing as df_bs was not loaded.")

    # --- Income Statement (IS) Processing ---
    # Determine the actual list of branches to process for IS
    is_branches_to_process = []
    if branch_name.upper() == 'CONSOLIDATED':
        is_branches_to_process = ['CONSOLIDATED']
    elif branch_name.upper() == 'ALL':
        is_branches_to_process = [b.upper() for b in AREA_BRANCH_MAP.get(area_name, []) if b.upper() not in ['ALL', 'CONSOLIDATED']]
        if area_name.upper() == 'CONSOLIDATED': # If 'ALL' is chosen under 'CONSOLIDATED' area, it means only CONSOLIDATED branch
            is_branches_to_process = ['CONSOLIDATED']
    else:
        is_branches_to_process = [branch_name.upper()]

    # Pre-build column index map for IS (Called only once now)
    is_col_index_map = get_column_index_map(df_is, is_branch_row_index, is_date_row_index, area_name, branch_name, lookup_date_str, last_december_lookup_str_fp, previous_period_lookup_str_is, bs_trend_dates_lookup_str, is_trend_dates_lookup_str)
    if not is_col_index_map and df_is is not None:
        print(f"Server Log (FS Process Error): No relevant columns found in IS sheet for branch '{branch_name}' and any target date. Returning empty data.")
        return {}


    # Define the main accounts and their row numbers (0-indexed) for IS
    # Removed direct row numbers for Administrative Costs and Operating Costs as they will be summed from sub-accounts
    is_accounts_map = { 
        'incomeFromCreditOperations': {'label': 'Income from Credit Operations', 'row': 13 - 1, 'type': 'revenue'},
        'otherIncome': {'label': 'Other Income', 'row': 19 - 1, 'type': 'revenue'},
        'financingCost': {'label': 'FINANCING COST', 'row': 28 - 1, 'type': 'expense'},
        'administrativeCosts': {'label': 'Administrative Costs', 'type': 'expense'}, # No direct row, calculated from sub-accounts
        'operatingCosts': {'label': 'Operating Costs', 'type': 'expense'}, # No direct row, calculated from sub-accounts
        'otherItemsSubsidyGainLosses': {'label': 'Other Items - Subsidy/Gain (Losses)', 'row': 81 - 1, 'type': 'other_item'},
    }

    # Define sub-accounts and their row numbers (0-indexed) for IS
    is_sub_accounts_map = {
        'Income from Credit Operations': [
            {'label': 'Interest Income from Loans', 'row': 9 - 1},
            {'label': 'Service Fees', 'row': 10 - 1},
            {'label': 'Filing Fees', 'row': 11 - 1},
            {'label': 'Fines, Penalties, and Surcharges', 'row': 12 - 1},
        ],
        'Other Income': [
            {'label': 'Income/ Interest from Investments/ Deposits', 'row': 15 - 1},
            {'label': 'Membership Fees', 'row': 16 - 1},
            {'label': 'Commissions', 'row': 17 - 1},
            {'label': 'Miscellaneous Income', 'row': 18 - 1},
        ],
        'FINANCING COST': [
            {'label': 'Interest Expense on Deposits', 'row': 25 - 1},
            {'label': 'Interest Expense on Borrowings', 'row': 26 - 1},
            {'label': 'Other Charges on Borrowings', 'row': 27 - 1},
        ],
        'Administrative Costs': [
            {'label': 'Salaries and Wages', 'row': 30 - 1},
            {'label': 'Employees\' Benefits', 'row': 31 - 1},
            {'label': 'SSS,PhilHealth,ECC, Pag-ibig Premium', 'row': 32 - 1},
            {'label': 'Retirement Benefit Expense', 'row': 33 - 1},
            {'label': 'Officers\' Honorarium and Allowances', 'row': 34 - 1},
            {'label': 'Trainings/Seminars', 'row': 35 - 1},
        ],
        'Operating Costs': [
            {'label': 'Office Supplies', 'row': 36 - 1},
            {'label': 'Power, Light and Water', 'row': 37 - 1},
            {'label': 'Travel and Transportation', 'row': 38 - 1},
            {'label': 'Insurance', 'row': 39 - 1},
            {'label': 'Repairs and Maintenance', 'row': 40 - 1},
            {'label': 'Rentals', 'row': 41 - 1},
            {'label': 'Taxes, Fees and Charges', 'row': 42 - 1},
            {'label': 'Professional Fees', 'row': 43 - 1},
            {'label': 'Communication', 'row': 44 - 1},
            {'label': 'Representation', 'row': 45 - 1},
            {'label': 'Meetings and Conferences', 'row': 46 - 1},
            {'label': 'Periodicals, Magazines & Subscriptions', 'row': 47 - 1},
            {'label': 'General Support Services', 'row': 48 - 1},
            {'label': 'Litigation Expenses', 'row': 49 - 1},
            {'label': 'Gas, Oil & Lubricants', 'row': 50 - 1},
            {'label': 'Miscellaneous Expense', 'row': 51 - 1},
            {'label': 'Bank Charges', 'row': 52 - 1},
            {'label': 'Depreciation', 'row': 53 - 1},
            {'label': 'Amortization', 'row': 54 - 1},
            {'label': 'Amortization of Leasehold Rights and Improvement', 'row': 55 - 1},
            {'label': 'Provision for Probable Losses on Loans/Accounts/Installment Receivables', 'row': 56 - 1},
            {'label': 'Impairment Losses', 'row': 57 - 1},
            {'label': 'Collection Expense', 'row': 58 - 1},
            {'label': 'Commision Expense', 'row': 59 - 1},
            {'label': 'Advertising and Promotion', 'row': 60 - 1},
            {'label': 'General Assembly Expenses', 'row': 61 - 1},
            {'label': 'Members\' Benefit Expense', 'row': 62 - 1},
            {'label': 'Provision for Members\' Future Benefits', 'row': 63 - 1},
            {'label': 'Affiliation Fee', 'row': 64 - 1},
            {'label': 'Social & Community Service Expense', 'row': 65 - 1},
            {'label': 'Provision for CGF (KBGF)', 'row': 66 - 1},
        ],
        'Other Items - Subsidy/Gain (Losses)': [
            {'label': 'Project Subsidy', 'row': 71 - 1},
            {'label': 'Donation and Grant Subsidy', 'row': 72 - 1},
            {'label': 'Optional Fund Subsidy', 'row': 73 - 1},
            {'label': 'Gains (Losses) on Sale of Property & Eqpt', 'row': 74 - 1},
            {'label': 'Gains (Losses) in Investment', 'row': 75 - 1},
            {'label': 'Gains (Losses) on Sale of Repossessed Item', 'row': 76 - 1},
            {'label': 'Gains (Losses) from Foreign Exchange Valuation', 'row': 77 - 1},
            {'label': 'Subsidized Project Expenses', 'row': 78 - 1},
            {'label': 'Special Project Expenses', 'row': 79 - 1},
            {'label': 'Prior Years\' Adjustment', 'row': 80 - 1},
        ],
    }

    # Initialize structured data for IS
    is_structured_data = {
        'revenues': {
            'incomeFromCreditOperations': {'label': 'Income from Credit Operations', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5, 'components': []},
            'otherIncome': {'label': 'Other Income', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'components': []},
            'totalRevenues': {'label': 'TOTAL REVENUES', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5}
        },
        'expenses': {
            'financingCost': {'label': 'FINANCING COST', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'components': []},
            'administrativeCosts': {'label': 'Administrative Costs', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'components': []},
            'operatingCosts': {'label': 'Operating Costs', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'components': []},
            'totalExpenses': {'label': 'TOTAL EXPENSES', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5}
        },
        'netSurplusBeforeOtherItems': {'label': 'Net Surplus Before Other Items', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5},
        'otherItems': {
            'otherItemsSubsidyGainLosses': {'label': 'Other Items - Subsidy/Gain (Losses)', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'components': []},
            'totalOtherItems': {'label': 'TOTAL OTHER ITEMS', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5}
        },
        'netSurplusForAllocation': {'label': 'NET SURPLUS (FOR ALLOCATION)', 'current_balance': 0.0, 'last_december_balance': 0.0, 'changes_percentage': 0.0, 'structure_percentage': 0.0, 'trend_data': [0.0]*5}
    }

    # Process IS data only if df_is was loaded successfully
    if df_is is not None:
        # The is_col_index_map is already built above, no need to rebuild it here.

        # Populate IS structured data with main account details and their sub-accounts
        for main_account_key, main_account_info in is_accounts_map.items():
            main_account_label = main_account_info['label']
            
            components = []
            current_total_main_account_value = 0.0
            previous_total_main_account_value = 0.0
            main_account_trend_data = [0.0] * 5 # Initialize trend data for main account

            if main_account_label in is_sub_accounts_map:
                for sub_item_info in is_sub_accounts_map[main_account_label]:
                    sub_row_idx = sub_item_info['row']
                    
                    # Get all required values for sub-account in one go
                    sub_account_all_values = get_values_for_account_across_dates(
                        df_is, sub_row_idx, is_col_index_map, is_branches_to_process, # Pass the list of branches
                        [lookup_date_str, previous_period_lookup_str_is] + is_trend_dates_lookup_str
                    )
                    current_sub_value = sub_account_all_values[0]
                    previous_sub_value = sub_account_all_values[1]
                    sub_account_trend_data = sub_account_all_values[2:] # Remaining are trend data

                    components.append({
                        'label': sub_item_info['label'],
                        'current_balance': current_sub_value,
                        'last_december_balance': previous_sub_value, # Renamed for consistency with JS, but means previous period
                        'changes_percentage': 0.0, # Calculated later
                        'structure_percentage': 0.0, # Calculated later
                        'trend_data': sub_account_trend_data # Add trend data to sub-account
                    })
                    
                    # Sum up sub-account values for the main account total
                    current_total_main_account_value += current_sub_value
                    previous_total_main_account_value += previous_sub_value
                    main_account_trend_data = [sum(x) for x in zip(main_account_trend_data, sub_account_trend_data)]
            else: # For accounts that still rely on a single row (not summed from sub-accounts)
                if 'row' in main_account_info:
                    main_account_all_values = get_values_for_account_across_dates(
                        df_is, main_account_info['row'], is_col_index_map, is_branches_to_process,
                        [lookup_date_str, previous_period_lookup_str_is] + is_trend_dates_lookup_str
                    )
                    current_total_main_account_value = main_account_all_values[0]
                    previous_total_main_account_value = main_account_all_values[1]
                    main_account_trend_data = main_account_all_values[2:]


            # Assign the calculated total and components to the structured data
            account_data_entry = {
                'label': main_account_label,
                'current_balance': current_total_main_account_value,
                'last_december_balance': previous_total_main_account_value, # Renamed for consistency with JS, but means previous period
                'changes_percentage': 0.0, # Calculated later
                'structure_percentage': 0.0, # Calculated later
                'trend_data': main_account_trend_data, # Add trend data to main account
                'components': components
            }

            if main_account_info['type'] == 'revenue':
                if main_account_key == 'incomeFromCreditOperations':
                    is_structured_data['revenues']['incomeFromCreditOperations'] = account_data_entry
                elif main_account_key == 'otherIncome':
                    is_structured_data['revenues']['otherIncome'] = account_data_entry
            elif main_account_info['type'] == 'expense':
                if main_account_key == 'financingCost':
                    is_structured_data['expenses']['financingCost'] = account_data_entry
                elif main_account_key == 'administrativeCosts':
                    is_structured_data['expenses']['administrativeCosts'] = account_data_entry
                elif main_account_key == 'operatingCosts':
                    is_structured_data['expenses']['operatingCosts'] = account_data_entry
            elif main_account_info['type'] == 'other_item':
                if main_account_key == 'otherItemsSubsidyGainLosses':
                    is_structured_data['otherItems']['otherItemsSubsidyGainLosses'] = account_data_entry

    # Calculate IS totals (Current and Previous Period)
    is_structured_data['revenues']['totalRevenues']['current_balance'] = (
        is_structured_data['revenues']['incomeFromCreditOperations']['current_balance'] +
        is_structured_data['revenues']['otherIncome']['current_balance']
    )
    is_structured_data['revenues']['totalRevenues']['last_december_balance'] = ( # This is actually previous period
        is_structured_data['revenues']['incomeFromCreditOperations']['last_december_balance'] +
        is_structured_data['revenues']['otherIncome']['last_december_balance']
    )
    # Corrected typo: 'revenuses' to 'revenues'
    is_structured_data['revenues']['totalRevenues']['trend_data'] = [sum(x) for x in zip(*[is_structured_data['revenues']['incomeFromCreditOperations']['trend_data'], is_structured_data['revenues']['otherIncome']['trend_data']])]


    is_structured_data['expenses']['totalExpenses']['current_balance'] = (
        is_structured_data['expenses']['financingCost']['current_balance'] +
        is_structured_data['expenses']['administrativeCosts']['current_balance'] +
        is_structured_data['expenses']['operatingCosts']['current_balance']
    )
    is_structured_data['expenses']['totalExpenses']['last_december_balance'] = ( # This is actually previous period
        is_structured_data['expenses']['financingCost']['last_december_balance'] +
        is_structured_data['expenses']['administrativeCosts']['last_december_balance'] +
        is_structured_data['expenses']['operatingCosts']['last_december_balance']
    )
    is_structured_data['expenses']['totalExpenses']['trend_data'] = [sum(x) for x in zip(*[is_structured_data['expenses']['financingCost']['trend_data'], is_structured_data['expenses']['administrativeCosts']['trend_data'], is_structured_data['expenses']['operatingCosts']['trend_data']])]


    is_structured_data['netSurplusBeforeOtherItems']['current_balance'] = (
        is_structured_data['revenues']['totalRevenues']['current_balance'] -
        is_structured_data['expenses']['totalExpenses']['current_balance']
    )
    is_structured_data['netSurplusBeforeOtherItems']['last_december_balance'] = ( # This is actually previous period
        is_structured_data['revenues']['totalRevenues']['last_december_balance'] -
        is_structured_data['expenses']['totalExpenses']['last_december_balance']
    )
    is_structured_data['netSurplusBeforeOtherItems']['trend_data'] = [a - b for a, b in zip(is_structured_data['revenues']['totalRevenues']['trend_data'], is_structured_data['expenses']['totalExpenses']['trend_data'])]


    is_structured_data['otherItems']['totalOtherItems']['current_balance'] = (
        is_structured_data['otherItems']['otherItemsSubsidyGainLosses']['current_balance']
    )
    is_structured_data['otherItems']['totalOtherItems']['last_december_balance'] = ( # This is actually previous period
        is_structured_data['otherItems']['otherItemsSubsidyGainLosses']['last_december_balance']
    )
    is_structured_data['otherItems']['totalOtherItems']['trend_data'] = is_structured_data['otherItems']['otherItemsSubsidyGainLosses']['trend_data']


    is_structured_data['netSurplusForAllocation']['current_balance'] = (
        is_structured_data['netSurplusBeforeOtherItems']['current_balance'] +
        is_structured_data['otherItems']['totalOtherItems']['current_balance']
    )
    is_structured_data['netSurplusForAllocation']['last_december_balance'] = ( # This is actually previous period
        is_structured_data['netSurplusBeforeOtherItems']['last_december_balance'] +
        is_structured_data['otherItems']['totalOtherItems']['last_december_balance']
    )
    is_structured_data['netSurplusForAllocation']['trend_data'] = [a + b for a, b in zip(is_structured_data['netSurplusBeforeOtherItems']['trend_data'], is_structured_data['otherItems']['totalOtherItems']['trend_data'])]


    # Now calculate percentages for IS accounts and sub-accounts with correct structure base
    # For main accounts and their sub-accounts, the base is their respective category total
    # For overall totals, the base is total_assets_current_date (from BS)

    # Revenues
    for account_key in ['incomeFromCreditOperations', 'otherIncome']:
        account = is_structured_data['revenues'][account_key]
        account['changes_percentage'], account['structure_percentage'] = \
            calculate_percentages_fp_is(account['current_balance'], account['last_december_balance'], is_structured_data['revenues']['totalRevenues']['current_balance'])
        for sub_component in account['components']:
            sub_component['changes_percentage'], sub_component['structure_percentage'] = \
                calculate_percentages_fp_is(sub_component['current_balance'], sub_component['last_december_balance'], account['current_balance'])

    # Expenses
    for account_key in ['financingCost', 'administrativeCosts', 'operatingCosts']:
        account = is_structured_data['expenses'][account_key]
        account['changes_percentage'], account['structure_percentage'] = \
            calculate_percentages_fp_is(account['current_balance'], account['last_december_balance'], is_structured_data['expenses']['totalExpenses']['current_balance'])
        for sub_component in account['components']:
            sub_component['changes_percentage'], sub_component['structure_percentage'] = \
                calculate_percentages_fp_is(sub_component['current_balance'], sub_component['last_december_balance'], account['current_balance'])

    # Other Items - Subsidy/Gain (Losses)
    account = is_structured_data['otherItems']['otherItemsSubsidyGainLosses']
    account['changes_percentage'], account['structure_percentage'] = \
        calculate_percentages_fp_is(account['current_balance'], account['last_december_balance'], is_structured_data['otherItems']['totalOtherItems']['current_balance'])
    for sub_component in account['components']:
        sub_component['changes_percentage'], sub_component['structure_percentage'] = \
            calculate_percentages_fp_is(sub_component['current_balance'], sub_component['last_december_balance'], account['current_balance'])

    # Calculate percentages for IS totals (using total_assets_current_date as base for structure)
    # Total Revenues structure should be 100%
    is_structured_data['revenues']['totalRevenues']['changes_percentage'], _ = \
        calculate_percentages_fp_is(is_structured_data['revenues']['totalRevenues']['current_balance'], is_structured_data['revenues']['totalRevenues']['last_december_balance'], 0) # Base is 0 for 100%
    is_structured_data['revenues']['totalRevenues']['structure_percentage'] = 100.0 # Always 100% for total revenues
    
    is_structured_data['expenses']['totalExpenses']['changes_percentage'], is_structured_data['expenses']['totalExpenses']['structure_percentage'] = \
        calculate_percentages_fp_is(is_structured_data['expenses']['totalExpenses']['current_balance'], is_structured_data['expenses']['totalExpenses']['last_december_balance'], is_structured_data['revenues']['totalRevenues']['current_balance'])
    
    is_structured_data['netSurplusBeforeOtherItems']['changes_percentage'], is_structured_data['netSurplusBeforeOtherItems']['structure_percentage'] = \
        calculate_percentages_fp_is(is_structured_data['netSurplusBeforeOtherItems']['current_balance'], is_structured_data['netSurplusBeforeOtherItems']['last_december_balance'], is_structured_data['revenues']['totalRevenues']['current_balance'])
    
    is_structured_data['otherItems']['totalOtherItems']['changes_percentage'], is_structured_data['otherItems']['totalOtherItems']['structure_percentage'] = \
        calculate_percentages_fp_is(is_structured_data['otherItems']['totalOtherItems']['current_balance'], is_structured_data['otherItems']['totalOtherItems']['last_december_balance'], is_structured_data['revenues']['totalRevenues']['current_balance'])
    
    is_structured_data['netSurplusForAllocation']['changes_percentage'], is_structured_data['netSurplusForAllocation']['structure_percentage'] = \
        calculate_percentages_fp_is(is_structured_data['netSurplusForAllocation']['current_balance'], is_structured_data['netSurplusForAllocation']['last_december_balance'], is_structured_data['revenues']['totalRevenues']['current_balance'])


    print(f"Server Log (FS Process): Successfully processed IS data for branch '{branch_name}' on '{report_date_str}'.")

    # Combine BS and IS data into a single result
    final_structured_data = {
        'financialPosition': bs_structured_data,
        'financialPerformance': is_structured_data
    }
    
    return final_structured_data

def get_financial_statement_trend_data(branch_name, report_date_str, area_name, account_label, report_type):
    """
    Retrieves historical trend data for a specific account from the Financial Statement.
    This function is designed to be called by a new API endpoint.
    """
    print(f"Server Log (FS Trend Data): Fetching trend data for Account: '{account_label}', Report Type: '{report_type}', Area: '{area_name}', Branch: '{branch_name}', Date: '{report_date_str}'")

    # First, process the full financial statement to get the structured data
    # This ensures all necessary data is loaded and calculated, including trend data arrays
    fs_data = process_financial_statement(branch_name, report_date_str, area_name)

    if not fs_data:
        print(f"Server Log (FS Trend Data Error): No financial statement data available for the given criteria.")
        return None

    trend_data_points = []
    trend_dates = []

    # Convert report_date_str to datetime object for comparison
    try:
        report_date_dt = datetime.strptime(report_date_str, '%Y-%m-%d')
        # Generate the 5-year trend dates (same logic as in process_financial_statement)
        if report_type == 'financial_position':
            for i in range(4, 0, -1):
                trend_year_dt = datetime(report_date_dt.year - i, 12, 31)
                trend_dates.append(trend_year_dt.strftime('%#m/%d/%Y'))
            trend_dates.append(report_date_dt.strftime('%#m/%d/%Y')) # Add current date
        elif report_type == 'financial_performance':
            for i in range(4, 0, -1):
                trend_year_dt = report_date_dt - relativedelta(years=i)
                trend_dates.append(trend_year_dt.strftime('%#m/%d/%Y'))
            trend_dates.append(report_date_dt.strftime('%#m/%d/%Y')) # Add current date
        else:
            print(f"Server Log (FS Trend Data Error): Invalid report_type: {report_type}")
            return None

    except ValueError as e:
        print(f"Server Log (FS Trend Data Error): Invalid date format for report_date_str: {e}")
        return None

    if report_type == 'financial_position':
        # Search in Financial Position data
        # Check top-level totals first, as their labels are direct
        if fs_data['financialPosition']['assets']['grandTotal']['label'] == account_label:
            trend_data_points = fs_data['financialPosition']['assets']['grandTotal']['trend_data']
        elif fs_data['financialPosition']['liabilities']['grandTotal']['label'] == account_label:
            trend_data_points = fs_data['financialPosition']['liabilities']['grandTotal']['trend_data']
        elif fs_data['financialPosition']['equity']['grandTotal']['label'] == account_label:
            trend_data_points = fs_data['financialPosition']['equity']['grandTotal']['trend_data']
        elif fs_data['financialPosition']['totalLiabilitiesAndMembersEquity']['label'] == account_label:
            trend_data_points = fs_data['financialPosition']['totalLiabilitiesAndMembersEquity']['trend_data']
        elif fs_data['financialPosition']['assets']['totalCurrent']['label'] == account_label:
            trend_data_points = fs_data['financialPosition']['assets']['totalCurrent']['trend_data']
        elif fs_data['financialPosition']['assets']['totalNonCurrent']['label'] == account_label:
            trend_data_points = fs_data['financialPosition']['assets']['totalNonCurrent']['trend_data']
        elif fs_data['financialPosition']['liabilities']['totalCurrent']['label'] == account_label:
            trend_data_points = fs_data['financialPosition']['liabilities']['totalCurrent']['trend_data']
        elif fs_data['financialPosition']['liabilities']['totalNonCurrent']['label'] == account_label:
            trend_data_points = fs_data['financialPosition']['liabilities']['totalNonCurrent']['trend_data']
        
        if not trend_data_points: # If not found in top-level totals, search within categories
            for category_key in ['assets', 'liabilities', 'equity']:
                for sub_category_key in fs_data['financialPosition'][category_key]:
                    if isinstance(fs_data['financialPosition'][category_key][sub_category_key], list):
                        for account in fs_data['financialPosition'][category_key][sub_category_key]:
                            if account['label'] == account_label:
                                trend_data_points = account['trend_data']
                                break
                            for sub_component in account['components']:
                                if sub_component['label'] == account_label:
                                    trend_data_points = sub_component['trend_data']
                                    break
                        if trend_data_points:
                            break
                    elif isinstance(fs_data['financialPosition'][category_key][sub_category_key], dict) and fs_data['financialPosition'][category_key][sub_category_key].get('label') == account_label:
                        trend_data_points = fs_data['financialPosition'][category_key][sub_category_key]['trend_data']
                        break
                if trend_data_points:
                    break

    elif report_type == 'financial_performance':
        # Search in Financial Performance data
        # Check top-level totals first
        if fs_data['financialPerformance']['revenues']['totalRevenues']['label'] == account_label:
            trend_data_points = fs_data['financialPerformance']['revenues']['totalRevenues']['trend_data']
        elif fs_data['financialPerformance']['expenses']['totalExpenses']['label'] == account_label:
            trend_data_points = fs_data['financialPerformance']['expenses']['totalExpenses']['trend_data']
        elif fs_data['financialPerformance']['netSurplusBeforeOtherItems']['label'] == account_label:
            trend_data_points = fs_data['financialPerformance']['netSurplusBeforeOtherItems']['trend_data']
        elif fs_data['financialPerformance']['otherItems']['totalOtherItems']['label'] == account_label:
            trend_data_points = fs_data['financialPerformance']['otherItems']['totalOtherItems']['trend_data']
        elif fs_data['financialPerformance']['netSurplusForAllocation']['label'] == account_label:
            trend_data_points = fs_data['financialPerformance']['netSurplusForAllocation']['trend_data']

        if not trend_data_points: # If not found in top-level totals, search within categories
            for category_key in ['revenues', 'expenses', 'otherItems']:
                for account_key in fs_data['financialPerformance'][category_key]:
                    account = fs_data['financialPerformance'][category_key][account_key]
                    if isinstance(account, dict) and account.get('label') == account_label:
                        trend_data_points = account['trend_data']
                        break
                    if isinstance(account, dict) and 'components' in account:
                        for sub_component in account['components']:
                            if sub_component.get('label') == account_label:
                                trend_data_points = sub_component['trend_data']
                                break
                    if trend_data_points:
                        break
                if trend_data_points:
                    break


    if not trend_data_points:
        print(f"Server Log (FS Trend Data Error): Trend data not found for account '{account_label}' in '{report_type}'.")
        return None

    # Ensure trend_data_points and trend_dates have the same length
    if len(trend_data_points) != len(trend_dates):
        print(f"Server Log (FS Trend Data Warning): Mismatch in length of trend data points ({len(trend_data_points)}) and dates ({len(trend_dates)}).")
        # Adjust to the minimum length to prevent errors, or handle as an error
        min_len = min(len(trend_data_points), len(trend_dates))
        trend_data_points = trend_data_points[:min_len]
        trend_dates = trend_dates[:min_len]


    return {
        'account_label': account_label,
        'report_type': report_type,
        'dates': trend_dates,
        'values': trend_data_points
    }
