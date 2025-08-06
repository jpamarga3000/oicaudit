import os
import pandas as pd
from flask import request, jsonify, send_file
from datetime import datetime
import io
import re # Import regex module

# --- Configuration for file paths ---
# IMPORTANT: Ensure these paths are correct and accessible on your server.
# It is highly recommended to use environment variables or a separate config file for paths
# in a production environment, rather than hardcoding them.
BASE_OPERATIONS_PATH = "C:/xampp/htdocs/audit_tool/OPERATIONS/"
AGING_PATH = os.path.join(BASE_OPERATIONS_PATH, "AGING") # Used for DOSRI Loans and Former Emp Loans
SVACC_PATH = os.path.join(BASE_OPERATIONS_PATH, "SVACC") # Used for DOSRI Deposits and Former Emp Deposits


# NEW: Define path for DOSRI CSV file
DOSRI_CSV_PATH = "C:/xampp/htdocs/audit_tool/db/list_dosri.csv"

# Placeholder for get_form_emp_data (if operations_form_emp.py is not imported)
# This allows operations_dosri.py to run even if operations_form_emp.py is missing or has issues,
# though Former Employee reports will not function.
try:
    from operations_form_emp import get_form_emp_data as get_form_emp_db_data
except ImportError:
    print("Warning: operations_form_emp.py not found or cannot be imported. Former Employee reports will not function correctly.")
    def get_form_emp_db_data():
        return pd.DataFrame(columns=['ID', 'CID', 'BRANCH', 'NAME', 'TYPE', 'POSITION', 'RELATED_TO', 'RELATIONSHIP']) # Return empty DataFrame


# --- CSV Helper Functions ---

def _read_dosri_csv():
    """
    Reads the DOSRI CSV file into a pandas DataFrame.
    Handles file not found by returning an empty DataFrame.
    Standardizes column names and converts 'id' to int if possible.
    Ensures that critical columns are present and cleaned.
    """
    try:
        # Attempt to read with utf-8, then fall back to latin-1 or cp1252 if decoding error occurs
        try:
            df = pd.read_csv(DOSRI_CSV_PATH, encoding='utf-8', dtype={'CID': str})
        except UnicodeDecodeError:
            print(f"Warning: UTF-8 decoding failed for DOSRI CSV at '{DOSRI_CSV_PATH}', trying latin-1...")
            df = pd.read_csv(DOSRI_CSV_PATH, encoding='latin-1', dtype={'CID': str})

        # Standardize column names: uppercase, replace spaces with underscores
        df.columns = df.columns.str.upper().str.replace(' ', '_')

        # Define expected columns and their default values/types for consistency
        expected_cols = {
            'ID': 0, 'CID': '', 'BRANCH': '', 'NAME': '', 'TYPE': '',
            'POSITION': '', 'RELATED_TO': '', 'RELATIONSHIP': ''
        }

        # Add missing columns with default empty values
        for col, default_val in expected_cols.items():
            if col not in df.columns:
                df[col] = default_val

        # Ensure 'ID' column is properly numeric and unique
        if 'ID' in df.columns:
            df['ID'] = pd.to_numeric(df['ID'], errors='coerce').fillna(0).astype(int)
            # Ensure unique IDs, reassign if duplicates or zeros exist after conversion
            if df['ID'].duplicated().any() or (df['ID'] == 0).any():
                print("Warning: Duplicate or zero IDs found in DOSRI CSV. Reassigning IDs.")
                df['ID'] = range(1, len(df) + 1)
        else:
            df['ID'] = range(1, len(df) + 1) # Assign IDs if completely missing

        # Ensure all relevant string columns are stripped and filled with empty strings
        for col in ['CID', 'BRANCH', 'NAME', 'TYPE', 'POSITION', 'RELATED_TO', 'RELATIONSHIP']:
            if col in df.columns: # Check if column actually exists after initial read and standardization
                df[col] = df[col].astype(str).fillna('').str.strip()

        # DEBUGGING: Print the head of the DataFrame after reading and initial cleaning
        print(f"\n--- Debugging _read_dosri_csv: {DOSRI_CSV_PATH} ---")
        print(df[['ID', 'NAME', 'TYPE', 'BRANCH', 'CID']].head()) # Show relevant columns
        print(f"DataFrame shape: {df.shape}")
        print("--------------------------------------------------")

        return df
    except FileNotFoundError:
        print(f"DOSRI CSV file '{DOSRI_CSV_PATH}' not found. Returning empty DataFrame.")
        expected_cols = ['ID', 'CID', 'BRANCH', 'NAME', 'TYPE', 'POSITION', 'RELATED_TO', 'RELATIONSHIP']
        return pd.DataFrame(columns=expected_cols)
    except pd.errors.EmptyDataError:
        print(f"Warning: DOSRI CSV file '{DOSRI_CSV_PATH}' is empty. Returning empty DataFrame.")
        expected_cols = ['ID', 'CID', 'BRANCH', 'NAME', 'TYPE', 'POSITION', 'RELATED_TO', 'RELATIONSHIP']
        return pd.DataFrame(columns=expected_cols)
    except Exception as e:
        print(f"FATAL Error reading DOSRI CSV at '{DOSRI_CSV_PATH}': {type(e).__name__}: {e}")
        # Return an empty DataFrame with expected columns on critical error to prevent downstream crashes
        expected_cols = ['ID', 'CID', 'BRANCH', 'NAME', 'TYPE', 'POSITION', 'RELATED_TO', 'RELATIONSHIP']
        return pd.DataFrame(columns=expected_cols)

def _write_dosri_csv(df):
    """
    Writes the pandas DataFrame to the DOSRI CSV file.
    Ensures the directory exists.
    """
    os.makedirs(os.path.dirname(DOSRI_CSV_PATH), exist_ok=True)
    df.to_csv(DOSRI_CSV_PATH, index=False, encoding='utf-8')


# --- CSV Operations for DOSRI List Management (replacing database calls) ---

def get_dosri_data(entry_id=None, search_term='', type_filter=None): # Changed type_filter to None default
    """
    Fetches data from the 'list_dosri.csv' file.
    Can fetch a single record by ID, or filter all records by search term and type.
    Ensures that 'branch' and 'cid' keys are returned in lowercase for consistency
    with frontend expectations.
    """
    df = _read_dosri_csv()
    
    if df.empty:
        return [] if entry_id is None else None

    # Apply filters if fetching all records
    if entry_id is None:
        filtered_df = df.copy() # Operate on a copy to avoid SettingWithCopyWarning

        if search_term:
            # Case-insensitive search across relevant columns
            search_lower = search_term.lower()
            filtered_df = filtered_df[
                filtered_df['NAME'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['BRANCH'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['CID'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['RELATED_TO'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['POSITION'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['RELATIONSHIP'].str.lower().str.contains(search_lower, na=False)
            ]
            
        # NEW: Handle multi-select type filter
        if isinstance(type_filter, list) and type_filter:
            # Filter where 'TYPE' column (case-insensitive) is in the list of selected types
            filtered_df = filtered_df[filtered_df['TYPE'].str.lower().isin([t.lower() for t in type_filter])]
        elif isinstance(type_filter, str) and type_filter: # For single select dropdown
            filtered_df = filtered_df[filtered_df['TYPE'].str.lower() == type_filter.lower()]
            
        # Convert DataFrame to a list of dictionaries, ensuring consistent keys
        records = filtered_df.to_dict(orient='records')
        formatted_records = []
        for record in records:
            # Map internal uppercase/underscore keys to frontend expected keys (can be mixed case)
            # This section remains unchanged to provide lowercase keys to the frontend
            formatted_record = {
                'id': record.get('ID'),
                'cid': record.get('CID'),
                'branch': record.get('BRANCH'),
                'name': record.get('NAME'),
                'type': record.get('TYPE'),
                'position': record.get('POSITION'),
                'related_to': record.get('RELATED_TO'),
                'relationship': record.get('RELATIONSHIP')
            }
            # Ensure values are never None, but empty string
            for key, value in formatted_record.items():
                if value is None:
                    formatted_record[key] = ''
            formatted_records.append(formatted_record)

        return formatted_records
    else:
        # Fetch a single record by ID
        record_df = df[df['ID'] == entry_id]
        if not record_df.empty:
            record = record_df.iloc[0].to_dict()
            formatted_record = {
                'id': record.get('ID'),
                'cid': record.get('CID'),
                'branch': record.get('BRANCH'),
                'name': record.get('NAME'),
                'type': record.get('TYPE'),
                'position': record.get('POSITION'),
                'related_to': record.get('RELATED_TO'),
                'relationship': record.get('RELATIONSHIP')
            }
            # Ensure values are never None, but empty string
            for key, value in formatted_record.items():
                if value is None:
                    formatted_record[key] = ''
            return formatted_record
        return None

def add_dosri_entry(data):
    """
    Adds a new entry to the 'list_dosri.csv' file.
    Generates a new ID and appends the record.
    """
    df = _read_dosri_csv()
    new_id = 1 if df.empty else df['ID'].max() + 1
    
    new_record = {
        'ID': new_id,
        'CID': str(data.get('cid', '')).strip(), # Ensure CID is stored as string
        'BRANCH': str(data.get('branch', '')).strip(),
        'NAME': str(data.get('name', '')).strip(),
        'TYPE': str(data.get('type', '')).strip(),
        'POSITION': str(data.get('position', '')).strip(),
        'RELATED_TO': str(data.get('related_to', '')).strip(),
        'RELATIONSHIP': str(data.get('relationship', '')).strip()
    }
    
    # Use pandas.concat for appending
    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    _write_dosri_csv(df)
    print(f"Successfully added entry for Name: {data.get('name')} with ID: {new_id}")
    return True

def update_dosri_entry(entry_id, data):
    """
    Updates an existing entry in the 'list_dosri.csv' file.
    """
    df = _read_dosri_csv()
    if df.empty:
        print(f"No entry found with ID: {entry_id} to update (CSV is empty).")
        return False

    idx = df[df['ID'] == entry_id].index
    if not idx.empty:
        # Prepare data for update, ensuring keys match DataFrame columns (uppercase, underscore)
        # This section remains unchanged as it correctly maps from frontend's lowercase to backend's uppercase
        update_data = {}
        if 'cid' in data: update_data['CID'] = str(data['cid']).strip()
        if 'branch' in data: update_data['BRANCH'] = str(data['branch']).strip()
        if 'name' in data: update_data['NAME'] = str(data['name']).strip()
        if 'type' in data: update_data['TYPE'] = str(data['type']).strip()
        if 'position' in data: update_data['POSITION'] = str(data['position']).strip()
        if 'related_to' in data: update_data['RELATED_TO'] = str(data['related_to']).strip()
        if 'relationship' in data: update_data['RELATIONSHIP'] = str(data['relationship']).strip()

        for col, value in update_data.items():
            df.loc[idx, col] = value

        _write_dosri_csv(df)
        print(f"Successfully updated entry for ID: {entry_id}")
        return True
    else:
        print(f"No entry found with ID: {entry_id} to update.")
        return False

def delete_dosri_entry(entry_id):
    """
    Deletes an entry from the 'list_dosri.csv' file.
    """
    df = _read_dosri_csv()
    if df.empty:
        print(f"No entry found with ID: {entry_id} to delete (CSV is empty).")
        return False

    initial_len = len(df)
    df = df[df['ID'] != entry_id]
    if len(df) < initial_len:
        _write_dosri_csv(df)
        print(f"Successfully deleted entry for ID: {entry_id}")
        return True
    else:
        print(f"No entry found with ID: {entry_id} to delete.")
        return False

def seed_dosri_data_to_db(): # Renamed to reflect CSV seeding
    """
    Seeds initial default data into the 'list_dosri.csv' file if it's empty or doesn't exist.
    """
    # Read existing data to check if seeding is needed
    current_df = _read_dosri_csv() # This will handle FileNotFoundError or EmptyDataError internally
    if current_df.empty:
        print("Seeding default DOSRI data to CSV...")
        default_data = [
            {'ID': 1, 'CID': 'CID001', 'BRANCH': 'MAIN', 'NAME': 'DOE, JANE', 'TYPE': 'Director', 'POSITION': 'Chairperson', 'RELATED_TO': 'N/A', 'RELATIONSHIP': 'N/A'},
            {'ID': 2, 'CID': 'CID002', 'BRANCH': 'BRANCH A', 'NAME': 'SMITH, JOHN', 'TYPE': 'Officer', 'POSITION': 'Manager', 'RELATED_TO': 'DOE, JANE', 'RELATIONSHIP': 'Sibling'},
            {'ID': 3, 'CID': 'CID003', 'BRANCH': 'BRANCH B', 'NAME': 'BROWN, ALICE', 'TYPE': 'Stockholder', 'POSITION': 'N/A', 'RELATED_TO': 'N/A', 'RELATIONSHIP': 'N/A'}
        ]
        df_default = pd.DataFrame(default_data)
        _write_dosri_csv(df_default)
        print("Default DOSRI data seeded successfully to CSV.")
    else:
        print(f"DOSRI CSV '{DOSRI_CSV_PATH}' already contains data. Skipping seeding.")

def upload_dosri_csv_to_db(filepath, upload_option='override'):
    """
    Uploads DOSRI data from a CSV file to the 'list_dosri.csv' file.
    """
    try:
        try:
            df_new = pd.read_csv(filepath, encoding='utf-8', dtype={'CID': str})
        except UnicodeDecodeError:
            print(f"Warning: UTF-8 decoding failed for uploaded DOSRI CSV at '{filepath}', trying latin-1...")
            df_new = pd.read_csv(filepath, encoding='latin-1', dtype={'CID': str})

        df_new.columns = df_new.columns.str.upper().str.replace(' ', '_')

        # Define expected columns for mapping and validation
        expected_cols_map = {
            'CID': 'CID', 'BRANCH': 'BRANCH', 'NAME': 'NAME', 'TYPE': 'TYPE',
            'POSITION': 'POSITION', 'RELATED_TO': 'RELATED_TO', 'RELATIONSHIP': 'RELATIONSHIP'
        }
        
        # Check for missing required columns
        missing_cols = [col_csv for col_csv in expected_cols_map.keys() if col_csv not in df_new.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in uploaded CSV: {', '.join(missing_cols)}")

        # Select only expected columns and ensure string type and stripping
        df_new = df_new[[col_csv for col_csv in expected_cols_map.keys()]]
        df_new = df_new.fillna('').astype(str).apply(lambda x: x.str.strip()) # Ensure all relevant columns are stripped and filled

        current_df = _read_dosri_csv()

        if upload_option == 'override':
            df_to_write = df_new.copy()
            # Assign new IDs starting from 1
            df_to_write['ID'] = range(1, len(df_to_write) + 1)
        elif upload_option == 'append':
            df_to_write = pd.concat([current_df.drop(columns=['ID'], errors='ignore'), df_new], ignore_index=True) # Drop old IDs for re-assignment
            # Assign new IDs based on max existing ID + 1
            max_id = 0 if current_df.empty else current_df['ID'].max()
            df_to_write['ID'] = range(max_id + 1, max_id + 1 + len(df_to_write))
        else:
            raise ValueError("Invalid upload_option. Must be 'override' or 'append'.")

        _write_dosri_csv(df_to_write)
        print(f"Successfully uploaded {len(df_new)} DOSRI records to CSV using '{upload_option}' option.")

    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty.")
    except FileNotFoundError:
        raise ValueError(f"CSV file not found at: {filepath}")
    except Exception as e:
        print(f"Error uploading DOSRI CSV data: {type(e).__name__}: {e}")
        raise # Re-raise to indicate a serious problem


# --- Helper function to parse dates ---
# Handles both 'MM/DD/YYYY' and 'MM/DD/YYYY HH:MM:SS am/pm' formats.
def parse_date_robust(date_str):
    if not isinstance(date_str, str):
        return pd.NaT # Not a Time (Pandas equivalent of None for datetime)
    date_str = date_str.strip()
    try:
        # Try parsing 'MM/DD/YYYY HH:MM:SS am/pm'
        return datetime.strptime(date_str, '%m/%d/%Y %I:%M:%S %p')
    except ValueError:
        try:
            # Try parsing 'MM/DD/YYYY'
            return datetime.strptime(date_str, '%m/%d/%Y')
        except ValueError:
            return pd.NaT # Return Not a Time if neither format matches

# --- Placeholder for fetching DOSRI members from CSV for summary reports ---
def get_dosri_members_for_summary(type_filter=None): # NEW: Added type_filter parameter
    """
    Fetches the list of DOSRI members from the CSV for summary report generation,
    optionally filtered by type(s).
    Normalizes branch and CID for consistent lookup, including removing spaces.
    """
    # Pass type_filter to get_dosri_data for filtering at the source
    dosri_members_raw = get_dosri_data(type_filter=type_filter) 
    
    normalized_dosri_members = []
    for member in dosri_members_raw:
        # The 'member' dictionary here should contain lowercase keys ('branch', 'cid')
        branch = str(member.get('branch', '')).strip().replace(' ', '').upper()
        cid = str(member.get('cid', '')).strip()
        name = str(member.get('name', '')).strip()
        member_type = str(member.get('type', '')).strip() # Get the 'type'

        if branch and cid and name: # Only include if essential fields are present
            normalized_dosri_members.append({
                "branch": branch,
                "cid": cid,
                "name": name,
                "type": member_type # Add the type here
            })
    # DEBUGGING: Print the members fetched for summary before normalization
    print("\n--- Debugging get_dosri_members_for_summary (raw members) ---")
    for m in dosri_members_raw[:5]: # Print first 5 for brevity
        print(f"  ID: {m.get('id')}, Name: {m.get('name')}, Type: {m.get('type')}")
    print("--------------------------------------------------")

    return normalized_dosri_members

# --- Placeholder for fetching Former Employee members from CSV for summary reports ---
def get_form_emp_members_for_summary():
    """
    Fetches the list of Former Employee members from the CSV for summary report generation.
    Normalizes branch and CID for consistent lookup, including removing spaces.
    """
    form_emp_members_raw = get_form_emp_db_data() # This now reads from CSV via operations_form_emp
    
    normalized_form_emp_members = []
    for member in form_emp_members_raw:
        # Robustly convert to string, strip whitespace, and remove all spaces, then uppercase for branch
        # Note: get_form_emp_db_data is assumed to return uppercase keys (BRANCH, CID) or handle internally
        branch = str(member.get('BRANCH', '')).strip().replace(' ', '').upper() # Assume 'BRANCH' from form_emp_db_data
        cid = str(member.get('CID', '')).strip() # Assume 'CID' from form_emp_db_data
        name = str(member.get('NAME', '')).strip() # Assume 'NAME' from form_emp_db_data
        # No 'TYPE' for former employees in the current schema for summary, but adding for future proofing if needed.
        # type_val = str(member.get('TYPE', '')).strip() 
        
        if branch and cid and name: # Only include if essential fields are present
            normalized_form_emp_members.append({
                "branch": branch,
                "cid": cid,
                "name": name,
                # "type": type_val 
            })
    return normalized_form_emp_members


# --- New functions for detailed data and counts ---

def get_deposit_accounts_count_details(df_deposit_liabilities):
    """
    Counts the number of accounts for each ACCNAME (product type) in deposit liabilities
    ONLY IF THE BALANCE IS NON-ZERO.
    """
    if df_deposit_liabilities.empty or 'ACCNAME' not in df_deposit_liabilities.columns or 'BAL' not in df_deposit_liabilities.columns:
        return {}
    
    # Filter for non-zero balances first
    df_non_zero_balances = df_deposit_liabilities[df_deposit_liabilities['BAL'] != 0].copy()

    if df_non_zero_balances.empty:
        return {}

    # Ensure ACCNAME is treated as a string for grouping and standardized
    df_non_zero_balances['ACCNAME'] = df_non_zero_balances['ACCNAME'].astype(str).str.strip().str.upper()
    
    account_counts = df_non_zero_balances.groupby('ACCNAME').size().to_dict()
    return account_counts

def get_loan_balance_details_from_df(df_loans_filtered, member_list):
    """
    Prepares detailed loan balance data for members (DOSRI or Former Employees) from a filtered DataFrame.
    Filters to get only the latest entry per loan account based on DATE (for DUE DATE).
    """
    loan_details = []
    
    if df_loans_filtered.empty:
        return []

    # Create a dictionary for quick (BRANCH, CID) to Name and Type lookup from the provided member_list
    # Ensure keys in map are standardized to match how data from CSVs will be processed
    member_branch_cid_name_type = {
        (str(member.get('branch', '')).strip().replace(' ', '').upper(), str(member.get('cid', '')).strip()): 
            {'name': str(member.get('name', '')), 'type': str(member.get('type', ''))} # Include 'type' here
        for member in member_list if isinstance(member, dict) and member.get('branch') is not None and member.get('cid') is not None
    }

    # Ensure required columns for loan data exist
    required_data_cols = ['LOAN ACCT.', 'DISBDATE', 'BALANCE', 'DATE', 'AGING', 'PRODUCT', 'BRANCH', 'CID']
    for col in required_data_cols:
        if col not in df_loans_filtered.columns:
            df_loans_filtered[col] = '' # Add missing columns as empty to prevent KeyError later

    # Convert 'DISBDATE' and 'DATE' (for DUE DATE) to datetime using the robust parser
    df_loans_filtered['DISBDATE_PARSED'] = df_loans_filtered['DISBDATE'].apply(parse_date_robust)
    df_loans_filtered['DATE_PARSED'] = df_loans_filtered['DATE'].apply(parse_date_robust)
    
    # Drop rows where critical dates (DISBDATE or DUE DATE) couldn't be parsed for primary logic
    df_loans_filtered.dropna(subset=['DISBDATE_PARSED', 'DATE_PARSED'], inplace=True)
    
    if df_loans_filtered.empty:
        return []

    # Convert BALANCE to numeric, handling potential non-numeric values
    df_loans_filtered['BALANCE'] = df_loans_filtered['BALANCE'].astype(str).str.replace(',', '', regex=False)
    df_loans_filtered['BALANCE'] = pd.to_numeric(df_loans_filtered['BALANCE'], errors='coerce').fillna(0) # Fill NaN with 0

    # Determine which balance column to use for sorting and calculations
    # Prioritize 'PRINCIPAL BALANCE' if it exists and 'BALANCE' is not the primary column
    if 'PRINCIPAL BALANCE' in df_loans_filtered.columns:
        df_loans_filtered['PRINCIPAL BALANCE'] = df_loans_filtered['PRINCIPAL BALANCE'].astype(str).str.replace(',', '', regex=False)
        df_loans_filtered['PRINCIPAL BALANCE'] = pd.to_numeric(df_loans_filtered['PRINCIPAL BALANCE'], errors='coerce').fillna(0)
        balance_col = 'PRINCIPAL BALANCE'
    else:
        balance_col = 'BALANCE'

    # Find the latest record for each (Branch, CID, LOAN ACCT.) combination
    # Sort by 'DATE_PARSED' descending to get the latest record for a unique loan, as per user request.
    sort_subset_cols = ['BRANCH', 'CID', 'LOAN ACCT.', 'DATE_PARSED']
    existing_sort_subset = [col for col in df_loans_filtered.columns if col in sort_subset_cols] # Filter for existing columns
    
    if len(existing_sort_subset) < 4:
        print(f"WARNING: Not all expected sort columns found in loan data for deduplication. Found: {existing_sort_subset}")
        # Adjust sort_by_cols and ascending_order if not all columns are present
        sort_by_cols = existing_sort_subset
        # Assuming the last column in existing_sort_subset is the date for descending sort
        ascending_order = [True] * (len(existing_sort_subset) - 1) + [False] if existing_sort_subset else []
    else:
        sort_by_cols = sort_subset_cols
        ascending_order = [True] * (len(sort_subset_cols) - 1) + [False]
        
    if not sort_by_cols: # If no valid sort columns, skip sorting and deduplication
        df_latest_loans = df_loans_filtered.copy()
    else:
        df_loans_sorted = df_loans_filtered.sort_values(
            by=sort_by_cols,
            ascending=ascending_order
        )
        # Ensure subset for drop_duplicates includes all identifying columns to truly get unique loans
        deduplicate_subset = ['BRANCH', 'CID', 'LOAN ACCT.']
        existing_deduplicate_subset = [col for col in df_loans_sorted.columns if col in deduplicate_subset]

        if not existing_deduplicate_subset:
            print("WARNING: No columns found for deduplication subset in loan data. Skipping deduplication.")
            df_latest_loans = df_loans_sorted # Fallback to no deduplication
        else:
            df_latest_loans = df_loans_sorted.drop_duplicates(subset=existing_deduplicate_subset, keep='first')
    
    # Filter out loans with zero or NaN balance after getting the latest record
    df_latest_loans = df_latest_loans[df_latest_loans[balance_col] != 0].copy()
    df_latest_loans.dropna(subset=[balance_col], inplace=True) # Remove rows where balance is NaN

    for _, row in df_latest_loans.iterrows():
        # Standardize branch and CID from the loan data row for lookup
        branch_from_loan_data = str(row.get('BRANCH', '')).strip().replace(' ', '').upper()
        cid_from_loan_data = str(row.get('CID', '')).strip()
        
        member_info = member_branch_cid_name_type.get((branch_from_loan_data, cid_from_loan_data), {'name': 'N/A', 'type': 'N/A'})
        member_name = member_info['name']
        member_type = member_info['type'] # Get the type

        # Ensure values for 'DISBDATE' and 'DUE DATE' are proper datetime objects before formatting
        # They should already be datetime or NaT due to earlier .apply(parse_date_robust)
        disb_date_val = row.get('DISBDATE_PARSED')
        due_date_val = row.get('DATE_PARSED') # This is now the 'DUE DATE' as per user's clarification

        loan_details.append({
            'BRANCH': str(row.get('BRANCH', '')).strip(),
            'CID': cid_from_loan_data,
            'NAME OF MEMBER': member_name,
            'TYPE': member_type, # Add the new TYPE column
            'LOAN ACCT.': str(row.get('LOAN ACCT.', '')).strip(),
            'PRINCIPAL BALANCE': round(row.get(balance_col, 0), 2), # Use numeric balance directly
            'PRODUCT': str(row.get('PRODUCT', '')).strip(),
            'DISBDATE': disb_date_val.strftime('%m/%d/%Y') if pd.notna(disb_date_val) else '',
            'DUE DATE': due_date_val.strftime('%m/%d/%Y') if pd.notna(due_date_val) else '', # Use DATE_PARSED for 'DUE DATE'
            'AGING': str(row.get('AGING', '')).strip()
        })
    return loan_details


def get_deposit_liabilities_details_from_df(df_deposits_filtered, member_list):
    """
    Prepares detailed deposit liabilities data for members (DOSRI or Former Employees) from a filtered DataFrame.
    """
    deposit_details = []
    
    if df_deposits_filtered.empty:
        return []

    # Create a dictionary for quick (BRANCH, CID) to Name and Type lookup from the provided member_list
    # Ensure keys in map are standardized to match how data from CSVs will be processed
    member_branch_cid_name_type = {
        (str(member.get('branch', '')).strip().replace(' ', '').upper(), str(member.get('cid', '')).strip()): 
            {'name': str(member.get('name', '')), 'type': str(member.get('type', ''))} # Include 'type' here
        for member in member_list if isinstance(member, dict) and member.get('branch') is not None and member.get('cid') is not None
    }

    # Ensure all required columns are present and converted to appropriate types before processing
    for col in ['BRANCH', 'ACC', 'CID', 'ACCNAME', 'DOPEN', 'BAL']:
        if col not in df_deposits_filtered.columns:
            df_deposits_filtered[col] = '' # Add missing columns as empty strings to avoid KeyError

    # Convert 'BAL' to numeric, handling potential non-numeric values
    df_deposits_filtered['BAL'] = df_deposits_filtered['BAL'].astype(str).str.replace(',', '', regex=False)
    df_deposits_filtered['BAL'] = pd.to_numeric(df_deposits_filtered['BAL'], errors='coerce').fillna(0) # Fill NaN with 0 after conversion

    # Filter out deposits with zero or NaN balance
    df_deposits_filtered = df_deposits_filtered[df_deposits_filtered['BAL'] != 0].copy()
    df_deposits_filtered.dropna(subset=['BAL'], inplace=True) # Remove rows where balance is NaN

    for _, row in df_deposits_filtered.iterrows():
        # Standardize branch and CID from the deposit data row for lookup
        branch_from_deposit_data = str(row.get('BRANCH', '')).strip().replace(' ', '').upper()
        cid_from_deposit_data = str(row.get('CID', '')).strip()
        
        member_info = member_branch_cid_name_type.get((branch_from_deposit_data, cid_from_deposit_data), {'name': 'N/A', 'type': 'N/A'})
        member_name = member_info['name']
        member_type = member_info['type'] # Get the type

        # Format date for 'OPENED DOPEN'
        opened_date_val = row.get('DOPEN')
        if pd.notna(opened_date_val):
            # Attempt to convert to datetime if it's not already, then format
            try:
                if isinstance(opened_date_val, (datetime, pd.Timestamp)):
                    formatted_date = opened_date_val.strftime('%m/%d/%Y')
                else:
                    # Try to parse string dates
                    parsed_date = pd.to_datetime(str(opened_date_val), errors='coerce')
                    formatted_date = parsed_date.strftime('%m/%d/%Y') if pd.notna(parsed_date) else ''
            except Exception as e:
                print(f"WARNING: Could not parse DOPEN date '{opened_date_val}': {e}. Setting to empty string.")
                formatted_date = '' # Fallback for unparseable dates
        else:
            formatted_date = ''

        deposit_details.append({
            'BRANCH': str(row.get('BRANCH', '')).strip(), # Include BRANCH in output
            'ACCOUNT ACC': str(row.get('ACC', '')).strip(),
            'NAME': member_name,
            'TYPE': member_type, # Add the new TYPE column
            'CID': cid_from_deposit_data,
            'PRODUCT ACCNAME': str(row.get('ACCNAME', '')).strip(),
            'OPENED DOPEN': formatted_date,
            'BALANCE BAL': round(pd.to_numeric(row.get('BAL', 0), errors='coerce'), 2)
        })
    return deposit_details


# --- API Route: Process DOSRI Loan Balances (Reads CSVs) ---
# This route would typically be part of your main app.py or a blueprint.
# @app.route('/api/dosri/loan_balances', methods=['POST'])
def process_dosri_loan_balances(dosri_members, report_date=None): # Added report_date parameter
    """
    Processes loan data for DOSRI members from CSV files in the AGING_PATH.
    Calculates current and past due balances for each DOSRI member, including
    a breakdown of past due amounts by aging buckets.
    The latest record for each loan account is determined by the 'DATE' header in CSVs.
    Filters loan data based on the provided report_date (inclusive).
    """
    if not dosri_members:
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": { # Initialize breakdown
                "1-30 DAYS": 0.0, "31-60 DAYS": 0.0, "61-90 DAYS": 0.0,
                "91-120 DAYS": 0.0, "121-180 DAYS": 0.0, "181-365 DAYS": 0.0,
                "OVER 365 DAYS": 0.0
            },
            "loan_balance_details": []
        })

    total_current_balance = 0.0
    total_past_due_balance = 0.0
    past_due_breakdown = {
        "1-30 DAYS": 0.0,
        "31-60 DAYS": 0.0,
        "61-90 DAYS": 0.0,
        "91-120 DAYS": 0.0,
        "121-180 DAYS": 0.0,
        "181-365 DAYS": 0.0,
        "OVER 365 DAYS": 0.0
    }

    # Parse report_date if provided
    parsed_report_date = None
    if report_date:
        try:
            parsed_report_date = datetime.strptime(report_date, '%Y-%m-%d')
            print(f"DOSRI Loan: Report date received and parsed: {parsed_report_date}") # Debugging print
        except ValueError:
            print(f"Warning: Invalid report_date format received: {report_date}. Skipping date filter for DOSRI loans.")

    # --- PERFORMANCE IMPROVEMENT START ---
    # Step 1: Identify all unique branches that need to be processed from the DOSRI members list
    unique_branches_to_process = set()
    for member in dosri_members:
        if isinstance(member, dict) and member.get('branch'):
            unique_branches_to_process.add(str(member['branch']).strip().replace(' ', '').upper())
    
    if not unique_branches_to_process:
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": past_due_breakdown,
            "loan_balance_details": []
        })

    # Step 2: Pre-process existing branch directories once
    actual_aging_dirs = {}
    if os.path.isdir(AGING_PATH):
        for d_name in os.listdir(AGING_PATH):
            full_path = os.path.join(AGING_PATH, d_name)
            if os.path.isdir(full_path):
                # Ensure the key is normalized (stripped, no spaces, uppercase)
                actual_aging_dirs[d_name.strip().replace(' ', '').upper()] = d_name
    else:
        print(f"ERROR: AGING_PATH '{AGING_PATH}' does not exist or is not a directory.")
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": past_due_breakdown,
            "loan_balance_details": []
        })

    all_aging_data_frames = []
    
    # Step 3: Iterate through unique branches and read all relevant CSV files only once
    for normalized_branch in unique_branches_to_process:
        target_branch_dir_name = actual_aging_dirs.get(normalized_branch)
        
        if not target_branch_dir_name:
            print(f"WARNING: No aging directory found for branch '{normalized_branch}'. Skipping.")
            continue
            
        branch_aging_path = os.path.join(AGING_PATH, target_branch_dir_name)
        csv_files = [f for f in os.listdir(branch_aging_path) if f.lower().endswith('.csv')]

        if not csv_files:
            print(f"WARNING: No CSV files found in aging directory '{branch_aging_path}'. Skipping.")
            continue

        for csv_file in csv_files:
            file_path = os.path.join(branch_aging_path, csv_file)
            try:
                # Explicitly set dtype for 'CID' and 'LOAN ACCT.' columns to string
                # Also set low_memory=False to handle mixed types more efficiently during loading
                df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', low_memory=False, dtype={'CID': str, 'LOAN ACCT.': str})
                df.columns = [col.upper() for col in df.columns] # Standardize column names
                
                # Add the original branch name (from the directory name, not normalized)
                # This ensures the original casing/spacing is preserved for later output/matching
                df['BRANCH'] = target_branch_dir_name 
                
                # Apply robust date parsing for the 'DATE' column (which is the filter target)
                df['DATE_PARSED'] = df['DATE'].apply(parse_date_robust)
                df['DISBDATE_PARSED'] = df['DISBDATE'].apply(parse_date_robust)
                
                # Drop rows where essential parsed dates (DISBDATE_PARSED or DATE_PARSED) couldn't be parsed
                df.dropna(subset=['DISBDATE_PARSED', 'DATE_PARSED'], inplace=True)

                # Apply date filter IMMEDIATELY after reading each DataFrame
                if parsed_report_date:
                    original_len = len(df) # Debugging print
                    df = df[df['DATE_PARSED'] == parsed_report_date].copy() # Filter for exact match
                    print(f"DOSRI Loan: Filtered {csv_file} by date. Original records: {original_len}, Records remaining: {len(df)}") # Debugging print

                if not df.empty: # Only append if there's data after filtering
                    all_aging_data_frames.append(df)

            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='latin-1', on_bad_lines='skip', low_memory=False, dtype={'CID': str, 'LOAN ACCT.': str})
                    df.columns = [col.upper() for col in df.columns] # Standardize column names
                    df['BRANCH'] = target_branch_dir_name
                    
                    df['DATE_PARSED'] = df['DATE'].apply(parse_date_robust)
                    df['DISBDATE_PARSED'] = df['DISBDATE'].apply(parse_date_robust)
                    df.dropna(subset=['DISBDATE_PARSED', 'DATE_PARSED'], inplace=True)

                    if parsed_report_date:
                        original_len = len(df) # Debugging print
                        df = df[df['DATE_PARSED'] == parsed_report_date].copy() # Filter for exact match
                        print(f"DOSRI Loan: Filtered {csv_file} (latin-1) by date. Original records: {original_len}, Records remaining: {len(df)}") # Debugging print

                    if not df.empty:
                        all_aging_data_frames.append(df)

                except Exception as e:
                    print(f"Error reading CSV '{csv_file}' with latin-1 encoding: {e}")
                    pass # Continue to next file
            except Exception as e:
                print(f"Error reading CSV '{csv_file}': {e}")
                pass # Continue to next file

    if not all_aging_data_frames:
        print("DOSRI Loan: No data frames left after initial file reading and date filtering.") # Debugging print
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": past_due_breakdown,
            "loan_balance_details": []
        })

    all_aging_data_combined = pd.concat(all_aging_data_frames, ignore_index=True)
    # Clear list of DataFrames to free up memory
    all_aging_data_frames = [] 
    print(f"DOSRI Loan: Total records after initial file reading and date filtering: {len(all_aging_data_combined)}") # Debugging print


    # Step 4: Centralize column cleaning and type conversions on the combined DataFrame
    # (Most of this is now done per-file, but ensure consistency)
    required_cols_aging = ['BRANCH', 'CID', 'BALANCE', 'DATE', 'AGING', 'LOAN ACCT.', 'PRODUCT', 'DISBDATE']
    for col in required_cols_aging:
        if col not in all_aging_data_combined.columns:
            print(f"WARNING: Missing required column '{col}' in combined aging data. Adding as empty.")
            all_aging_data_combined[col] = '' # Add missing columns as empty
        if all_aging_data_combined[col].dtype == 'object': # Only apply to string/object columns
            all_aging_data_combined[col] = all_aging_data_combined[col].astype(str).fillna('').str.strip()

    # Convert BALANCE to numeric, handling potential non-numeric values
    all_aging_data_combined['BALANCE'] = all_aging_data_combined['BALANCE'].astype(str).str.replace(',', '', regex=False)
    all_aging_data_combined['BALANCE'] = pd.to_numeric(all_aging_data_combined['BALANCE'], errors='coerce')

    # Re-check for NaT after concatenation if any new NaT values were introduced (unlikely if done per-file)
    all_aging_data_combined.dropna(subset=['DISBDATE_PARSED', 'DATE_PARSED'], inplace=True)


    # Step 5: Prepare DOSRI identifiers for efficient filtering
    dosri_identifiers = set()
    for member in dosri_members:
        if isinstance(member, dict) and member.get('branch') and member.get('cid'): # Ensure both exist
            # Use the original branch name (as stored in the member list) for comparison
            branch = str(member['branch']).strip() 
            cid = str(member['cid']).strip() 
            # Create the normalized composite key for lookup
            dosri_identifiers.add((branch.replace(' ', '').upper(), cid))

    if not dosri_identifiers:
        print("DOSRI Loan: No DOSRI identifiers found.") # Debugging print
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": past_due_breakdown,
            "loan_balance_details": []
        })

    # Create a composite key in the combined DataFrame for efficient filtering
    # Normalize BRANCH for the composite key to match DOSRI list
    all_aging_data_combined['NORMALIZED_BRANCH'] = all_aging_data_combined['BRANCH'].astype(str).str.strip().str.replace(' ', '').str.upper()
    all_aging_data_combined['COMPOSITE_KEY'] = all_aging_data_combined['NORMALIZED_BRANCH'] + '_' + all_aging_data_combined['CID'].astype(str).str.strip()
    
    # Filter the combined DataFrame once for all relevant DOSRI members
    # Reconstruct dosri_composite_keys for efficient lookup using the normalized (branch, cid) from dosri_identifiers
    dosri_composite_keys = {f"{b}_{c}" for b, c in dosri_identifiers}

    relevant_aging_data = all_aging_data_combined[
        all_aging_data_combined['COMPOSITE_KEY'].isin(dosri_composite_keys)
    ].copy()

    # Drop the temporary composite keys
    relevant_aging_data.drop(columns=['NORMALIZED_BRANCH', 'COMPOSITE_KEY'], errors='ignore', inplace=True)
    all_aging_data_combined.drop(columns=['NORMALIZED_BRANCH', 'COMPOSITE_KEY'], errors='ignore', inplace=True)

    print(f"DOSRI Loan: Records after DOSRI member filter: {len(relevant_aging_data)}") # Debugging print

    if relevant_aging_data.empty:
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": past_due_breakdown,
            "loan_balance_details": []
        })

    # Find the latest record for each (Branch, CID, LOAN ACCT.) combination to ensure unique loan entry
    # Sort by 'DATE_PARSED' (which is the 'DATE' header from the CSV) descending to get the latest record for a unique loan.
    sort_cols = ['BRANCH', 'CID', 'LOAN ACCT.', 'DATE_PARSED']
    existing_sort_cols = [col for col in relevant_aging_data.columns if col in sort_cols] # Filter for existing columns
    
    if len(existing_sort_cols) < 4:
        print(f"WARNING: Not all sort columns found in relevant_aging_data for final deduplication. Found: {existing_sort_cols}")
        sort_by_cols = existing_sort_cols
        ascending_order = [True] * (len(existing_sort_cols)-1) + [False] if existing_sort_cols else []
    else:
        sort_by_cols = sort_cols
        ascending_order = [True] * (len(sort_cols)-1) + [False]
        
    if not sort_by_cols: # If no valid sort columns, skip sorting and deduplication
        latest_records_idx = relevant_aging_data.copy()
    else:
        latest_records_idx = relevant_aging_data.sort_values(
            by=sort_by_cols,
            ascending=ascending_order
        ).drop_duplicates(subset=['BRANCH', 'CID', 'LOAN ACCT.'], keep='first')

    # Filter out loans with zero or NaN balance after getting the latest record
    latest_records_idx['BALANCE_NUM'] = pd.to_numeric(latest_records_idx['BALANCE'], errors='coerce')
    latest_records_idx = latest_records_idx[latest_records_idx['BALANCE_NUM'] != 0].copy()
    latest_records_idx.dropna(subset=['BALANCE_NUM'], inplace=True) # Remove rows where balance is NaN
    
    # Drop the temporary numeric balance column
    latest_records_idx.drop(columns=['BALANCE_NUM'], errors='ignore', inplace=True)

    print(f"DOSRI Loan: Records after deduplication and zero balance filter: {len(latest_records_idx)}") # Debugging print


    # Calculate total current and past due balances from these latest records
    for _, record in latest_records_idx.iterrows():
        balance = pd.to_numeric(record['BALANCE'], errors='coerce') # Re-parse to ensure numeric after filtering
        aging_status = str(record['AGING']).strip().upper()

        if pd.isna(balance): # Should not happen after previous dropna, but good safeguard
            continue

        if aging_status == 'NOT YET DUE':
            total_current_balance += balance
        else:
            total_past_due_balance += balance
            # Categorize into aging buckets based on exact match or 'in' check
            if aging_status == '1-30 DAYS':
                past_due_breakdown['1-30 DAYS'] += balance
            elif aging_status == '31-60 DAYS' or aging_status == '31-60': # Catch both forms
                past_due_breakdown['31-60 DAYS'] += balance
            elif aging_status == '61-90 DAYS' or aging_status == '61-90':
                past_due_breakdown['61-90 DAYS'] += balance
            elif aging_status == '91-120 DAYS' or aging_status == '91-120':
                past_due_breakdown['91-120 DAYS'] += balance
            elif aging_status == '121-180 DAYS' or aging_status == '121-180':
                past_due_breakdown['121-180 DAYS'] += balance
            elif aging_status == '181-365 DAYS' or aging_status == '181-365':
                past_due_breakdown['181-365 DAYS'] += balance
            elif aging_status == 'OVER 365 DAYS' or aging_status == 'OVER 365':
                past_due_breakdown['OVER 365 DAYS'] += balance
            else:
                print(f"WARNING: Unknown aging status encountered: '{aging_status}'. Balance {balance} not categorized.")
                pass # Continue processing

    # Get detailed loan balance information
    # Pass 'latest_records_idx' which contains the unique and latest loan records for details
    loan_balance_details = get_loan_balance_details_from_df(latest_records_idx, dosri_members)

    # Round all balances in breakdown
    for key in past_due_breakdown:
        past_due_breakdown[key] = round(past_due_breakdown[key], 2)

    return jsonify({
        "current_balance": round(total_current_balance, 2),
        "past_due_balance": round(total_past_due_balance, 2),
        "past_due_breakdown": past_due_breakdown, # Return breakdown
        "loan_balance_details": loan_balance_details # Return detailed data
    })

# --- API Route: Process DOSRI Deposit Liabilities (Reads CSVs/XLSX) ---
# This route would typically be part of your main app.py or a blueprint.
# @app.route('/api/dosri/deposit_liabilities', methods=['POST'])
def process_dosri_deposit_liabilities(dosri_members, report_date=None): # report_date parameter kept for consistency, but not used for filtering
    """
    Processes deposit data for DOSRI members from Excel/CSV files in the SVACC_PATH.
    Categorizes deposits into specific types and sums their balances.
    Now also returns deposit account counts (for non-zero balances) and detailed deposit liabilities.
    No date filter is applied for deposit liabilities.
    """
    if not dosri_members:
        return jsonify({
            "regular_savings": 0.0,
            "share_capital": 0.0,
            "time_deposits": 0.0,
            "youth_savings": 0.0,
            "special_deposits": 0.0,
            "atm_savings": 0.0, # Added ATM Savings
            "total_deposits": 0.0,
            "deposit_accounts_count": {}, # Added for counts
            "deposit_liabilities_details": [] # Added for detailed data
        })

    deposit_summary = {
        "regular_savings": 0.0,
        "share_capital": 0.0,
        "time_deposits": 0.0,
        "youth_savings": 0.0,
        "special_deposits": 0.0,
        "atm_savings": 0.0, # Added ATM Savings
        "total_deposits": 0.0
    }
    
    deposit_accounts_count = {}
    deposit_liabilities_details = []

    if not os.path.isdir(SVACC_PATH):
        print(f"ERROR: SVACC_PATH '{SVACC_PATH}' does not exist or is not a directory.")
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    all_svacc_data_frames = [] # Changed to list for appending DataFrames
    data_files = [f for f in os.listdir(SVACC_PATH) if f.lower().endswith(('.csv', '.xlsx'))]
    
    if not data_files:
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    for data_file in data_files:
        file_path = os.path.join(SVACC_PATH, data_file)
        try:
            if data_file.lower().endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', low_memory=False, dtype={'CID': str, 'ACC': str})
            elif data_file.lower().endswith('.xlsx'):
                # Read first sheet by default for Excel files
                df = pd.read_excel(file_path, dtype={'CID': str, 'ACC': str})
            else:
                print(f"WARNING: Skipping unsupported file type: {data_file}")
                continue

            df.columns = [col.upper() for col in df.columns] # Standardize column names
            
            # Extract branch name from filename: "BRANCH - MM-DD-YYYY.csv"
            # Use regex to extract the part before " - "
            match = re.match(r'(.+?)\s*-\s*\d{2}-\d{2}-\d{4}', os.path.splitext(data_file)[0].strip())
            if match:
                branch_name_from_file = match.group(1).strip()
            else:
                branch_name_from_file = os.path.splitext(data_file)[0].strip() # Fallback to full filename if regex fails
                print(f"WARNING: Could not parse branch from filename '{data_file}'. Using full filename as branch.")

            df['BRANCH'] = branch_name_from_file # Add the extracted branch name

            if 'CID' in df.columns:
                df['CID'] = df['CID'].astype(str).fillna('').str.strip()
            
            if 'BAL' in df.columns:
                # IMPORTANT FIX: Remove commas before converting to numeric
                df['BAL'] = df['BAL'].astype(str).str.replace(',', '', regex=False) # Remove commas
                df['BAL'] = pd.to_numeric(df['BAL'], errors='coerce')

            all_svacc_data_frames.append(df) # Use append for single DataFrame

        except UnicodeDecodeError:
            print(f"WARNING: UTF-8 decoding failed for '{data_file}', trying latin-1...")
            try:
                if data_file.lower().endswith('.csv'):
                    df = pd.read_csv(file_path, encoding='latin-1', on_bad_lines='skip', low_memory=False, dtype={'CID': str, 'ACC': str})
                elif data_file.lower().endswith('.xlsx'):
                    df = pd.read_excel(file_path, dtype={'CID': str, 'ACC': str})
                
                df.columns = [col.upper() for col in df.columns]

                # Extract branch name from filename for latin-1 decoded files too
                match = re.match(r'(.+?)\s*-\s*\d{2}-\d{2}-\d{4}', os.path.splitext(data_file)[0].strip())
                if match:
                    branch_name_from_file = match.group(1).strip()
                else:
                    branch_name_from_file = os.path.splitext(data_file)[0].strip()
                    print(f"WARNING: Could not parse branch from filename '{data_file}' (latin-1). Using full filename as branch.")
                df['BRANCH'] = branch_name_from_file
                
                if 'CID' in df.columns:
                    df['CID'] = df['CID'].astype(str).fillna('').str.strip()
                if 'BAL' in df.columns:
                    df['BAL'] = df['BAL'].astype(str).str.replace(',', '', regex=False) # Remove commas
                    df['BAL'] = pd.to_numeric(df['BAL'], errors='coerce')
                
                all_svacc_data_frames.append(df) # Use append for single DataFrame

            except Exception as e:
                print(f"Error reading data file '{data_file}' with latin-1 encoding: {e}")
                pass
        except Exception as e:
            print(f"Error reading data file '{data_file}': {e}")
            pass

    if not all_svacc_data_frames: # Check if list is empty
        print("DOSRI Deposit: No data frames left after initial file reading.") # Debugging print
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    all_svacc_data_combined = pd.concat(all_svacc_data_frames, ignore_index=True) # Concatenate after loop
    all_svacc_data_frames = [] # Clear list to free memory


    # Required columns for deposit data analysis
    required_cols_svacc = ['CID', 'BAL', 'ACCNAME', 'BRANCH', 'ACC', 'DOPEN']
    for col in required_cols_svacc:
        if col not in all_svacc_data_combined.columns:
            print(f"WARNING: Missing required column '{col}' in combined SVACC data. Adding as empty.")
            all_svacc_data_combined[col] = '' # Add missing columns as empty
        if all_svacc_data_combined[col].dtype == 'object': # Only apply to string/object columns
            all_svacc_data_combined[col] = all_svacc_data_combined[col].astype(str).fillna('').str.strip()

    if not all(col in all_svacc_data_combined.columns for col in required_cols_svacc):
        missing = [col for col in required_cols_svacc if col not in all_svacc_data_combined.columns]
        print(f"Error: Still missing required columns in combined SVACC data: {missing}")
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    dosri_identifiers_deposits = set()
    for member in dosri_members:
        if not isinstance(member, dict):
            continue
        branch = str(member.get('branch', '')).strip().replace(' ', '').upper() # Use lowercase 'branch'
        cid = str(member.get('cid', '')).strip() # Use lowercase 'cid'
        if branch and cid:
            dosri_identifiers_deposits.add((branch, cid))
    
    if not dosri_identifiers_deposits:
        print("DOSRI Deposit: No DOSRI identifiers found.") # Debugging print
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    all_svacc_data_combined['NORMALIZED_BRANCH'] = all_svacc_data_combined['BRANCH'].astype(str).str.strip().replace(' ', '').str.upper()
    all_svacc_data_combined['COMPOSITE_KEY'] = all_svacc_data_combined['NORMALIZED_BRANCH'] + '_' + all_svacc_data_combined['CID'].astype(str).str.strip()
    
    dosri_composite_keys_deposits = {f"{branch}_{cid}" for branch, cid in dosri_identifiers_deposits}

    relevant_svacc_data = all_svacc_data_combined[
        all_svacc_data_combined['COMPOSITE_KEY'].isin(dosri_composite_keys_deposits)
    ].copy()

    print(f"DOSRI Deposit: Records after member filter: {len(relevant_svacc_data)}") # Debugging print

    if relevant_svacc_data.empty:
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    relevant_svacc_data['BAL'] = pd.to_numeric(relevant_svacc_data['BAL'], errors='coerce').fillna(0)
    
    # Filter out deposits with zero or NaN balance BEFORE categorization and summing
    relevant_svacc_data = relevant_svacc_data[relevant_svacc_data['BAL'] != 0].copy()
    relevant_svacc_data.dropna(subset=['BAL'], inplace=True) # Remove rows where balance is NaN

    print(f"DOSRI Deposit: Records after zero balance filter: {len(relevant_svacc_data)}") # Debugging print

    relevant_svacc_data['ACCNAME_NORMALIZED'] = relevant_svacc_data['ACCNAME'].astype(str).str.strip().str.upper()
    grouped_deposits = relevant_svacc_data.groupby('ACCNAME_NORMALIZED')['BAL'].sum()

    deposit_summary["regular_savings"] = grouped_deposits.get('REGULAR SAVINGS', 0.0)
    deposit_summary["share_capital"] = grouped_deposits.get('SHARE CAPITAL', 0.0)
    
    time_deposit_types = ['TIME DEPOSIT - MATURITY', 'TIME DEPOSIT - MONTHLY', 'TIME DEPOSIT -A', 'TIME DEPOSIT -B', 'TIME DEPOSIT -C']
    time_deposits_sum = relevant_svacc_data[relevant_svacc_data['ACCNAME_NORMALIZED'].isin(time_deposit_types)]['BAL'].sum()
    deposit_summary["time_deposits"] = time_deposits_sum

    deposit_summary["youth_savings"] = grouped_deposits.get('YOUTH SAVINGS CLUB', 0.0)
    
    deposit_summary["atm_savings"] = grouped_deposits.get('ATM SAVINGS', 0.0)

    categorized_acc_names = [
        'REGULAR SAVINGS',
        'SHARE CAPITAL',
        'YOUTH SAVINGS CLUB',
        'ATM SAVINGS'
    ] + time_deposit_types

    special_deposits_sum = relevant_svacc_data[~relevant_svacc_data['ACCNAME_NORMALIZED'].isin(categorized_acc_names)]['BAL'].sum()
    deposit_summary["special_deposits"] = special_deposits_sum

    deposit_summary['total_deposits'] = (
        deposit_summary["regular_savings"] +
        deposit_summary["share_capital"] +
        deposit_summary["time_deposits"] +
        deposit_summary["youth_savings"] +
        deposit_summary["atm_savings"] +
        deposit_summary["special_deposits"]
    )

    for key, value in deposit_summary.items():
        deposit_summary[key] = round(value, 2)

    deposit_accounts_count = get_deposit_accounts_count_details(relevant_svacc_data)

    deposit_liabilities_details = get_deposit_liabilities_details_from_df(relevant_svacc_data, dosri_members)

    return jsonify({
        **deposit_summary,
        "deposit_accounts_count": deposit_accounts_count,
        "deposit_liabilities_details": deposit_liabilities_details
    })


# --- API Route: Process Former Employee Loan Balances (Reads CSVs) ---
# This route would typically be part of your main app.py or a blueprint.
# @app.route('/api/form_emp/loan_balances', methods=['POST'])
def process_form_emp_loan_balances(form_emp_members, report_date=None): # Added report_date
    """
    Processes loan data for Former Employee members from CSV files in the AGING_PATH.
    Calculates current and past due balances for each Former Employee member, including
    a breakdown of past due amounts by aging buckets.
    The latest record for each loan account is determined by the 'DATE' header in CSVs.
    Filters loan data based on the provided report_date (inclusive).
    """
    if not form_emp_members:
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": {
                "1-30 DAYS": 0.0, "31-60 DAYS": 0.0, "61-90 DAYS": 0.0,
                "91-120 DAYS": 0.0, "121-180 DAYS": 0.0, "181-365 DAYS": 0.0,
                "OVER 365 DAYS": 0.0
            },
            "loan_balance_details": []
        })

    total_current_balance = 0.0
    total_past_due_balance = 0.0
    past_due_breakdown = {
        "1-30 DAYS": 0.0,
        "31-60 DAYS": 0.0,
        "61-90 DAYS": 0.0,
        "91-120 DAYS": 0.0,
        "121-180 DAYS": 0.0,
        "181-365 DAYS": 0.0,
        "OVER 365 DAYS": 0.0 # Corrected typo from original
    }

    # Parse report_date if provided
    parsed_report_date = None
    if report_date:
        try:
            parsed_report_date = datetime.strptime(report_date, '%Y-%m-%d')
            print(f"Former Employee Loan: Report date received and parsed: {parsed_report_date}") # Debugging print
        except ValueError:
            print(f"Warning: Invalid report_date format received: {report_date}. Skipping date filter for former employee loans.")


    actual_loan_dirs = {}
    if os.path.isdir(AGING_PATH): # Loan data for former employees also uses AGING_PATH
        for d_name in os.listdir(AGING_PATH):
            full_path = os.path.join(AGING_PATH, d_name)
            if os.path.isdir(full_path):
                actual_loan_dirs[d_name.strip().replace(' ', '').upper()] = d_name
    else:
        print(f"ERROR: AGING_PATH '{AGING_PATH}' does not exist or is not a directory for former employee loans.")
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": past_due_breakdown,
            "loan_balance_details": []
        })

    all_loan_data_frames = [] # Changed to list for appending DataFrames
    
    processed_branches_for_aging_form_emp = set()
    for member in form_emp_members:
        if not isinstance(member, dict):
            continue

        # Use .get with default and then .strip().replace(' ', '').upper() for robustness
        branch_raw = member.get('branch') or member.get('BRANCH') # Try both casings
        branch = str(branch_raw).strip() if branch_raw else ''
        normalized_branch_from_form_emp_list = branch.replace(' ', '').upper()
        
        target_branch_dir_name = actual_loan_dirs.get(normalized_branch_from_form_emp_list)
        
        if not target_branch_dir_name:
            continue

        if normalized_branch_from_form_emp_list in processed_branches_for_aging_form_emp:
            continue
        processed_branches_for_aging_form_emp.add(normalized_branch_from_form_emp_list)
        
        branch_loan_path = os.path.join(AGING_PATH, target_branch_dir_name)

        csv_files = [f for f in os.listdir(branch_loan_path) if f.lower().endswith('.csv')]

        if not csv_files:
            continue

        for csv_file in csv_files:
            file_path = os.path.join(branch_loan_path, csv_file)
            try:
                df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', low_memory=False, dtype={'CID': str, 'LOAN ACCT.': str})
                df.columns = [col.upper() for col in df.columns]
                
                if 'CID' in df.columns:
                    df['CID'] = df['CID'].astype(str).fillna('').str.strip()
                if 'BALANCE' in df.columns:
                    df['BALANCE'] = df['BALANCE'].astype(str).str.replace(',', '', regex=False)
                    df['BALANCE'] = pd.to_numeric(df['BALANCE'], errors='coerce')
                df['BRANCH'] = branch # Use the original branch name from Former Emp list
                
                # Apply robust date parsing
                df['DATE_PARSED'] = df['DATE'].apply(parse_date_robust)
                df['DISBDATE_PARSED'] = df['DISBDATE'].apply(parse_date_robust)
                df.dropna(subset=['DISBDATE_PARSED', 'DATE_PARSED'], inplace=True)

                # Apply date filter IMMEDIATELY after reading each DataFrame
                if parsed_report_date:
                    original_len = len(df) # Debugging print
                    print(f"Former Employee Loan: Unique dates in {csv_file} before filter: {df['DATE_PARSED'].unique()}") # Debugging print
                    df = df[df['DATE_PARSED'] == parsed_report_date].copy() # Filter for exact match
                    print(f"Former Employee Loan: Filtered {csv_file} by date. Original records: {original_len}, Records remaining: {len(df)}") # Debugging print

                if not df.empty: # Only append if there's data after filtering
                    all_loan_data_frames.append(df)

            except UnicodeDecodeError:
                print(f"WARNING: UTF-8 decoding failed for '{csv_file}', trying latin-1...")
                try:
                    df = pd.read_csv(file_path, encoding='latin-1', on_bad_lines='skip', low_memory=False, dtype={'CID': str, 'LOAN ACCT.': str})
                    df.columns = [col.upper() for col in df.columns]
                    if 'CID' in df.columns:
                        df['CID'] = df['CID'].astype(str).fillna('').str.strip()
                    if 'BALANCE' in df.columns:
                        df['BALANCE'] = df['BALANCE'].astype(str).str.replace(',', '', regex=False)
                        df['BALANCE'] = pd.to_numeric(df['BALANCE'], errors='coerce')
                    df['BRANCH'] = branch
                    
                    df['DATE_PARSED'] = df['DATE'].apply(parse_date_robust)
                    df['DISBDATE_PARSED'] = df['DISBDATE'].apply(parse_date_robust)
                    df.dropna(subset=['DISBDATE_PARSED', 'DATE_PARSED'], inplace=True)

                    if parsed_report_date:
                        original_len = len(df) # Debugging print
                        print(f"Former Employee Loan: Unique dates in {csv_file} (latin-1) before filter: {df['DATE_PARSED'].unique()}") # Debugging print
                        df = df[df['DATE_PARSED'] == parsed_report_date].copy() # Filter for exact match
                        print(f"Former Employee Loan: Filtered {csv_file} (latin-1) by date. Original records: {original_len}, Records remaining: {len(df)}") # Debugging print

                    if not df.empty:
                        all_loan_data_frames.append(df)

                except Exception as e:
                    print(f"Error reading CSV '{csv_file}' with latin-1 encoding: {e}")
                    pass
            except Exception as e:
                print(f"Error reading CSV '{csv_file}': {e}")
                pass

    if not all_loan_data_frames: # Check if list is empty
        print("Former Employee Loan: No data frames left after initial file reading and date filtering.") # Debugging print
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": past_due_breakdown,
            "loan_balance_details": []
        })

    all_loan_data_combined = pd.concat(all_loan_data_frames, ignore_index=True) # Concatenate after loop
    all_loan_data_frames = [] # Clear list to free memory
    print(f"Former Employee Loan: Total records after initial file reading and date filtering: {len(all_loan_data_combined)}") # Debugging print


    required_cols_form_emp_loan = ['BRANCH', 'CID', 'BALANCE', 'DATE', 'AGING', 'LOAN ACCT.', 'PRODUCT', 'DISBDATE']
    for col in required_cols_form_emp_loan:
        if col not in all_loan_data_combined.columns:
            print(f"WARNING: Missing required column '{col}' in combined former employee loan data. Adding as empty.")
            all_loan_data_combined[col] = '' # Add missing columns as empty
        if all_loan_data_combined[col].dtype == 'object': # Only apply to string/object columns
            all_loan_data_combined[col] = all_loan_data_combined[col].astype(str).fillna('').str.strip()

    # Re-check for NaT after concatenation if any new NaT values were introduced (unlikely if done per-file)
    all_loan_data_combined.dropna(subset=['DISBDATE_PARSED', 'DATE_PARSED'], inplace=True)


    form_emp_identifiers = set()
    for member in form_emp_members:
        if not isinstance(member, dict):
            continue
        branch_raw = member.get('branch') or member.get('BRANCH') # Using get('branch') first, then get('BRANCH')
        branch = str(branch_raw).strip().replace(' ', '').upper() if branch_raw else ''
        cid_raw = member.get('cid') or member.get('CID') # Using get('cid') first, then get('CID')
        cid = str(cid_raw).strip() if cid_raw else ''
        if branch and cid:
            form_emp_identifiers.add((branch, cid))
    
    if not form_emp_identifiers:
        print("Former Employee Loan: No Former Employee identifiers found.") # Debugging print
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": past_due_breakdown,
            "loan_balance_details": []
        })

    all_loan_data_combined['NORMALIZED_BRANCH'] = all_loan_data_combined['BRANCH'].astype(str).str.strip().str.replace(' ', '').str.upper()
    all_loan_data_combined['COMPOSITE_KEY'] = all_loan_data_combined['NORMALIZED_BRANCH'] + '_' + all_loan_data_combined['CID'].astype(str).str.strip()
    
    form_emp_composite_keys = {f"{branch}_{cid}" for branch, cid in form_emp_identifiers}

    relevant_loan_data = all_loan_data_combined[
        all_loan_data_combined['COMPOSITE_KEY'].isin(form_emp_composite_keys)
    ].copy()

    relevant_loan_data.dropna(subset=['DISBDATE_PARSED', 'DATE_PARSED'], inplace=True)

    print(f"Former Employee Loan: Records after member filter: {len(relevant_loan_data)}") # Debugging print

    if relevant_loan_data.empty:
        return jsonify({
            "current_balance": 0.0,
            "past_due_balance": 0.0,
            "past_due_breakdown": past_due_breakdown,
            "loan_balance_details": []
        })

    # Find the latest record for each (Branch, CID, LOAN ACCT.) combination to ensure unique loan entry
    # Sort by 'DATE_PARSED' (which is the DUE DATE from the CSV) descending to get the latest record for a unique loan.
    sort_cols = ['BRANCH', 'CID', 'LOAN ACCT.', 'DATE_PARSED']
    existing_sort_cols = [col for col in relevant_loan_data.columns if col in sort_cols] # Filter for existing columns
    
    if len(existing_sort_cols) < 4:
        print(f"WARNING: Not all sort columns found in relevant_loan_data for final deduplication. Found: {existing_sort_cols}")
        sort_by_cols = existing_sort_cols
        ascending_order = [True] * (len(existing_sort_cols)-1) + [False] if existing_sort_cols else []
    else:
        sort_by_cols = sort_cols
        ascending_order = [True] * (len(sort_cols)-1) + [False]
        
    if not sort_by_cols: # If no valid sort columns, skip sorting and deduplication
        latest_records_idx = relevant_loan_data.copy()
    else:
        latest_records_idx = relevant_loan_data.sort_values(
            by=sort_by_cols,
            ascending=ascending_order
        ).drop_duplicates(subset=['BRANCH', 'CID', 'LOAN ACCT.'], keep='first')

    # Filter out loans with zero or NaN balance after getting the latest record
    latest_records_idx['BALANCE_NUM'] = pd.to_numeric(latest_records_idx['BALANCE'], errors='coerce')
    latest_records_idx = latest_records_idx[latest_records_idx['BALANCE_NUM'] != 0].copy()
    latest_records_idx.dropna(subset=['BALANCE_NUM'], inplace=True) # Remove rows where balance is NaN
    
    # Drop the temporary numeric balance column
    latest_records_idx.drop(columns=['BALANCE_NUM'], errors='ignore', inplace=True)

    print(f"Former Employee Loan: Records after deduplication and zero balance filter: {len(latest_records_idx)}") # Debugging print


    for _, record in latest_records_idx.iterrows():
        balance = pd.to_numeric(record['BALANCE'], errors='coerce') # Re-parse to ensure numeric after filtering
        aging_status = str(record['AGING']).strip().upper()

        if pd.isna(balance): # Should not happen after previous dropna, but good safeguard
            continue

        if aging_status == 'NOT YET DUE':
            total_current_balance += balance
        else:
            total_past_due_balance += balance
            if aging_status == '1-30 DAYS':
                past_due_breakdown['1-30 DAYS'] += balance
            elif aging_status == '31-60 DAYS' or aging_status == '31-60':
                past_due_breakdown['31-60 DAYS'] += balance
            elif aging_status == '61-90 DAYS' or aging_status == '61-90':
                past_due_breakdown['61-90 DAYS'] += balance
            elif aging_status == '91-120 DAYS' or aging_status == '91-120':
                past_due_breakdown['91-120 DAYS'] += balance
            elif aging_status == '121-180 DAYS' or aging_status == '121-180':
                past_due_breakdown['121-180 DAYS'] += balance
            elif aging_status == '181-365 DAYS' or aging_status == '181-365':
                past_due_breakdown['181-365 DAYS'] += balance
            elif aging_status == 'OVER 365 DAYS' or aging_status == 'OVER 365':
                past_due_breakdown['OVER 365 DAYS'] += balance
            else:
                print(f"WARNING: Unknown aging status encountered for former employee: '{aging_status}'. Balance {balance} not categorized.")
                pass

    loan_balance_details = get_loan_balance_details_from_df(latest_records_idx, form_emp_members)

    for key, value in past_due_breakdown.items():
        past_due_breakdown[key] = round(value, 2)

    return jsonify({
        "current_balance": round(total_current_balance, 2),
        "past_due_balance": round(total_past_due_balance, 2),
        "past_due_breakdown": past_due_breakdown,
        "loan_balance_details": loan_balance_details
    })

# --- API Route: Process Former Employee Deposit Liabilities (Reads CSVs/XLSX) ---
# @app.route('/api/form_emp/deposit_liabilities', methods=['POST'])
def process_form_emp_deposit_liabilities(form_emp_members, report_date=None): # report_date parameter kept for consistency, but not used for filtering
    """
    Processes deposit data for Former Employee members from Excel/CSV files in the SVACC_PATH.
    Categorizes deposits into specific types and sums their balances.
    Returns deposit account counts (for non-zero balances) and detailed deposit liabilities.
    No date filter is applied for deposit liabilities.
    """
    if not form_emp_members:
        return jsonify({
            "regular_savings": 0.0,
            "share_capital": 0.0,
            "time_deposits": 0.0,
            "youth_savings": 0.0,
            "special_deposits": 0.0,
            "atm_savings": 0.0,
            "total_deposits": 0.0,
            "deposit_accounts_count": {},
            "deposit_liabilities_details": []
        })

    deposit_summary = {
        "regular_savings": 0.0,
        "share_capital": 0.0,
        "time_deposits": 0.0,
        "youth_savings": 0.0,
        "special_deposits": 0.0,
        "atm_savings": 0.0,
        "total_deposits": 0.0
    }
    
    deposit_accounts_count = {}
    deposit_liabilities_details = []

    if not os.path.isdir(SVACC_PATH):
        print(f"ERROR: SVACC_PATH '{SVACC_PATH}' does not exist or is not a directory for former employee deposits.")
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    all_svacc_data_frames = [] # Changed to list for appending DataFrames
    data_files = [f for f in os.listdir(SVACC_PATH) if f.lower().endswith(('.csv', '.xlsx'))]
    
    if not data_files:
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    for data_file in data_files:
        file_path = os.path.join(SVACC_PATH, data_file)
        try:
            if data_file.lower().endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', low_memory=False, dtype={'CID': str, 'ACC': str})
            elif data_file.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path, dtype={'CID': str, 'ACC': str})
            else:
                print(f"WARNING: Skipping unsupported file type for former employee deposits: {data_file}")
                continue

            df.columns = [col.upper() for col in df.columns]

            # Extract branch name from filename: "BRANCH - MM-DD-YYYY.csv"
            match = re.match(r'(.+?)\s*-\s*\d{2}-\d{2}-\d{4}', os.path.splitext(data_file)[0].strip())
            if match:
                branch_name_from_file = match.group(1).strip()
            else:
                branch_name_from_file = os.path.splitext(data_file)[0].strip() # Fallback
                print(f"WARNING: Could not parse branch from filename '{data_file}' (Former Emp). Using full filename as branch.")
            df['BRANCH'] = branch_name_from_file
            
            if 'CID' in df.columns:
                df['CID'] = df['CID'].astype(str).fillna('').str.strip()
            
            if 'BAL' in df.columns:
                df['BAL'] = df['BAL'].astype(str).str.replace(',', '', regex=False)
                df['BAL'] = pd.to_numeric(df['BAL'], errors='coerce')
            
            all_svacc_data_frames.append(df) # Use append for single DataFrame

        except UnicodeDecodeError:
            print(f"WARNING: UTF-8 decoding failed for '{data_file}', trying latin-1...")
            try:
                if data_file.lower().endswith('.csv'):
                    df = pd.read_csv(file_path, encoding='latin-1', on_bad_lines='skip', low_memory=False, dtype={'CID': str, 'ACC': str})
                elif data_file.lower().endswith('.xlsx'):
                    df = pd.read_excel(file_path, dtype={'CID': str, 'ACC': str})
                
                df.columns = [col.upper() for col in df.columns]

                # Extract branch name from filename for latin-1 decoded files too
                match = re.match(r'(.+?)\s*-\s*\d{2}-\d{2}-\d{4}', os.path.splitext(data_file)[0].strip())
                if match:
                    branch_name_from_file = match.group(1).strip()
                else:
                    branch_name_from_file = os.path.splitext(data_file)[0].strip()
                    print(f"WARNING: Could not parse branch from filename '{data_file}' (Latin-1). Using full filename as branch.")
                df['BRANCH'] = branch_name_from_file

                if 'CID' in df.columns:
                    df['CID'] = df['CID'].astype(str).fillna('').str.strip()
                if 'BAL' in df.columns:
                    df['BAL'] = df['BAL'].astype(str).str.replace(',', '', regex=False)
                    df['BAL'] = pd.to_numeric(df['BAL'], errors='coerce')
                
                all_svacc_data_frames.append(df) # Use append for single DataFrame

            except Exception as e:
                print(f"Error reading data file '{data_file}' with latin-1 encoding: {e}")
                pass
        except Exception as e:
            print(f"Error reading data file '{data_file}': {e}")
            pass

    if not all_svacc_data_frames: # Check if list is empty
        print("Former Employee Deposit: No data frames left after initial file reading.") # Debugging print
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    all_svacc_data_combined = pd.concat(all_svacc_data_frames, ignore_index=True) # Concatenate after loop
    all_svacc_data_frames = [] # Clear list to free memory


    required_cols_form_emp_deposit = ['CID', 'BAL', 'ACCNAME', 'BRANCH', 'ACC', 'DOPEN']
    for col in required_cols_form_emp_deposit:
        if col not in all_svacc_data_combined.columns:
            print(f"WARNING: Missing required column '{col}' in combined former employee SVACC data. Adding as empty.")
            all_svacc_data_combined[col] = '' # Add missing columns as empty
        if all_svacc_data_combined[col].dtype == 'object': # Only apply to string/object columns
            all_svacc_data_combined[col] = all_svacc_data_combined[col].astype(str).fillna('').str.strip()

    if not all(col in all_svacc_data_combined.columns for col in required_cols_form_emp_deposit):
        missing = [col for col in required_cols_form_emp_deposit if col not in all_svacc_data_combined.columns]
        print(f"Error: Still missing required columns in combined former employee SVACC data: {missing}")
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    form_emp_identifiers_deposits = set()
    for member in form_emp_members:
        if not isinstance(member, dict):
            continue
        branch_raw = member.get('branch') or member.get('BRANCH') # Using get('branch') first, then get('BRANCH')
        branch = str(branch_raw).strip().replace(' ', '').upper() if branch_raw else ''
        cid_raw = member.get('cid') or member.get('CID') # Using get('cid') first, then get('CID')
        cid = str(cid_raw).strip() if cid_raw else ''
        if branch and cid:
            form_emp_identifiers_deposits.add((branch, cid))
    
    if not form_emp_identifiers_deposits:
        print("Former Employee Deposit: No Former Employee identifiers found.") # Debugging print
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    all_svacc_data_combined['NORMALIZED_BRANCH'] = all_svacc_data_combined['BRANCH'].astype(str).str.strip().replace(' ', '').str.upper()
    all_svacc_data_combined['COMPOSITE_KEY'] = all_svacc_data_combined['NORMALIZED_BRANCH'] + '_' + all_svacc_data_combined['CID'].astype(str).str.strip()
    
    form_emp_composite_keys_deposits = {f"{branch}_{cid}" for branch, cid in form_emp_identifiers_deposits}

    relevant_svacc_data = all_svacc_data_combined[
        all_svacc_data_combined['COMPOSITE_KEY'].isin(form_emp_composite_keys_deposits)
    ].copy()

    print(f"Former Employee Deposit: Records after member filter: {len(relevant_svacc_data)}") # Debugging print

    if relevant_svacc_data.empty:
        return jsonify({**deposit_summary, "deposit_accounts_count": {}, "deposit_liabilities_details": []})

    relevant_svacc_data['BAL'] = pd.to_numeric(relevant_svacc_data['BAL'], errors='coerce').fillna(0)
    
    # Filter out deposits with zero or NaN balance BEFORE categorization and summing
    relevant_svacc_data = relevant_svacc_data[relevant_svacc_data['BAL'] != 0].copy()
    relevant_svacc_data.dropna(subset=['BAL'], inplace=True) # Remove rows where balance is NaN

    print(f"Former Employee Deposit: Records after zero balance filter: {len(relevant_svacc_data)}") # Debugging print

    relevant_svacc_data['ACCNAME_NORMALIZED'] = relevant_svacc_data['ACCNAME'].astype(str).str.strip().str.upper()
    grouped_deposits = relevant_svacc_data.groupby('ACCNAME_NORMALIZED')['BAL'].sum()

    deposit_summary["regular_savings"] = grouped_deposits.get('REGULAR SAVINGS', 0.0)
    deposit_summary["share_capital"] = grouped_deposits.get('SHARE CAPITAL', 0.0)
    
    time_deposit_types = ['TIME DEPOSIT - MATURITY', 'TIME DEPOSIT - MONTHLY', 'TIME DEPOSIT -A', 'TIME DEPOSIT -B', 'TIME DEPOSIT -C']
    time_deposits_sum = relevant_svacc_data[relevant_svacc_data['ACCNAME_NORMALIZED'].isin(time_deposit_types)]['BAL'].sum()
    deposit_summary["time_deposits"] = time_deposits_sum

    deposit_summary["youth_savings"] = grouped_deposits.get('YOUTH SAVINGS CLUB', 0.0)
    
    deposit_summary["atm_savings"] = grouped_deposits.get('ATM SAVINGS', 0.0)

    categorized_acc_names = [
        'REGULAR SAVINGS',
        'SHARE CAPITAL',
        'YOUTH SAVINGS CLUB',
        'ATM SAVINGS'
    ] + time_deposit_types

    special_deposits_sum = relevant_svacc_data[~relevant_svacc_data['ACCNAME_NORMALIZED'].isin(categorized_acc_names)]['BAL'].sum()
    deposit_summary["special_deposits"] = special_deposits_sum

    deposit_summary['total_deposits'] = (
        deposit_summary["regular_savings"] +
        deposit_summary["share_capital"] +
        deposit_summary["time_deposits"] +
        deposit_summary["youth_savings"] +
        deposit_summary["atm_savings"] +
        deposit_summary["special_deposits"]
    )

    for key, value in deposit_summary.items():
        deposit_summary[key] = round(value, 2)

    deposit_accounts_count = get_deposit_accounts_count_details(relevant_svacc_data)

    deposit_liabilities_details = get_deposit_liabilities_details_from_df(relevant_svacc_data, form_emp_members)

    return jsonify({
        **deposit_summary,
        "deposit_accounts_count": deposit_accounts_count,
        "deposit_liabilities_details": deposit_liabilities_details
    })


# --- NEW API Route: Download DOSRI Summary and Details as Excel ---
# This route would typically be part of your main Flask app (e.g., in app.py)
# from flask import Flask, request, jsonify, send_file
# from operations_dosri import (get_dosri_data, add_dosri_entry, update_dosri_entry,
#                                delete_dosri_entry, upload_dosri_csv_to_db,
#                                process_dosri_loan_balances, process_dosri_deposit_liabilities)

# @app.route('/api/dosri/download_excel', methods=['POST'])
def download_dosri_excel_report():
    """
    Generates and returns an Excel file containing both Loan Balance Details
    and Deposit Liabilities Details in separate sheets.
    Now also includes raw DOSRI list and Former Employee list on separate sheets.
    """
    try:
        data = request.json
        loan_details = data.get('loan_details', [])
        deposit_details = data.get('deposit_details', [])
        form_emp_loan_details = data.get('form_emp_loan_details', [])
        form_emp_deposit_details = data.get('form_emp_deposit_details', [])
        dosri_list_raw = data.get('dosri_list_raw', []) # NEW: Raw DOSRI list
        form_emp_list_raw = data.get('form_emp_list_raw', []) # NEW: Raw Former Employee list


        if not (loan_details or deposit_details or form_emp_loan_details or \
                form_emp_deposit_details or dosri_list_raw or form_emp_list_raw):
            return jsonify({"error": "No data provided for Excel download."}), 400

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # NEW: Add DOSRI List sheet
            if dosri_list_raw:
                dosri_list_df = pd.DataFrame(dosri_list_raw)
                # Ensure column order for DOSRI List
                dosri_list_columns_order = [
                    'id', 'cid', 'branch', 'name', 'type', 'position', 'related_to', 'relationship'
                ]
                # Ensure all columns exist and are ordered
                for col in dosri_list_columns_order:
                    if col not in dosri_list_df.columns:
                        dosri_list_df[col] = ''
                dosri_list_df = dosri_list_df[dosri_list_columns_order]
                dosri_list_df.to_excel(writer, sheet_name='DOSRI List', index=False)
                print("DOSRI List written to Excel.")

            # NEW: Add Former Employee List sheet
            if form_emp_list_raw:
                form_emp_list_df = pd.DataFrame(form_emp_list_raw)
                # Ensure column order for Former Employee List
                form_emp_list_columns_order = [
                    'ID', 'BRANCH', 'NAME', 'CID', 'DATE_RESIGNED', 'STATUS'
                ]
                # Adjust column names from frontend (lowercase) to backend (uppercase) if necessary
                # The frontend sends 'ID', 'BRANCH', 'NAME', 'CID', 'DATE RESIGNED', 'STATUS' (might be mixed case)
                # Standardize to uppercase as per get_form_emp_db_data internal handling
                form_emp_list_df.columns = form_emp_list_df.columns.str.upper().str.replace(' ', '_')

                for col in form_emp_list_columns_order:
                    if col not in form_emp_list_df.columns:
                        form_emp_list_df[col] = ''
                form_emp_list_df = form_emp_list_df[form_emp_list_columns_order]
                form_emp_list_df.to_excel(writer, sheet_name='Former Employee List', index=False)
                print("Former Employee List written to Excel.")

            if loan_details:
                loan_df = pd.DataFrame(loan_details)
                # Reorder columns if necessary to match frontend table display order
                loan_columns_order = [
                    'BRANCH', 'CID', 'NAME OF MEMBER', 'TYPE', 'LOAN ACCT.', # Added 'TYPE'
                    'PRINCIPAL BALANCE', 'PRODUCT', 'DISBDATE', 'DUE DATE', 'AGING'
                ]
                # Ensure all columns exist, fill missing with empty strings, then select and reorder
                for col in loan_columns_order:
                    if col not in loan_df.columns:
                        loan_df[col] = ''
                loan_df = loan_df[loan_columns_order]
                loan_df.to_excel(writer, sheet_name='DOSRI Loan Details', index=False) # Changed sheet name
                print("DOSRI Loan Details written to Excel.")

            if deposit_details:
                deposit_df = pd.DataFrame(deposit_details)
                # Filter out rows where 'BALANCE BAL' is 0
                deposit_df = deposit_df[deposit_df['BALANCE BAL'] != 0]

                # Reorder columns if necessary to match frontend table display order
                deposit_columns_order = [
                    'BRANCH', 'ACCOUNT ACC', 'NAME', 'TYPE', 'CID', # Added 'TYPE'
                    'PRODUCT ACCNAME', 'OPENED DOPEN', 'BALANCE BAL'
                ]
                # Ensure all columns exist, fill missing with empty strings, then select and reorder
                for col in deposit_columns_order:
                    if col not in deposit_df.columns:
                        deposit_df[col] = ''
                deposit_df = deposit_df[deposit_columns_order]
                deposit_df.to_excel(writer, sheet_name='DOSRI Deposit Liabilities', index=False) # Changed sheet name
                print("DOSRI Deposit Liabilities written to Excel.")

            if form_emp_loan_details:
                form_emp_loan_df = pd.DataFrame(form_emp_loan_details)
                form_emp_loan_columns_order = [
                    'BRANCH', 'CID', 'NAME OF MEMBER', 'LOAN ACCT.',
                    'PRINCIPAL BALANCE', 'PRODUCT', 'DISBDATE', 'DUE DATE', 'AGING'
                ]
                for col in form_emp_loan_columns_order:
                    if col not in form_emp_loan_df.columns:
                        form_emp_loan_df[col] = ''
                form_emp_loan_df = form_emp_loan_df[form_emp_loan_columns_order]
                form_emp_loan_df.to_excel(writer, sheet_name='Former Emp Loan Details', index=False)
                print("Former Employee Loan Details written to Excel.")

            if form_emp_deposit_details:
                form_emp_deposit_df = pd.DataFrame(form_emp_deposit_details)
                form_emp_deposit_df = form_emp_deposit_df[form_emp_deposit_df['BALANCE BAL'] != 0]
                form_emp_deposit_columns_order = [
                    'BRANCH', 'ACCOUNT ACC', 'NAME', 'CID',
                    'PRODUCT ACCNAME', 'OPENED DOPEN', 'BALANCE BAL'
                ]
                for col in form_emp_deposit_columns_order:
                    if col not in form_emp_deposit_df.columns:
                        form_emp_deposit_df[col] = ''
                form_emp_deposit_df = form_emp_deposit_df[form_emp_deposit_columns_order]
                form_emp_deposit_df.to_excel(writer, sheet_name='Former Emp Deposit Liabilities', index=False)
                print("Former Employee Deposit Liabilities written to Excel.")
            
        output.seek(0) # Go to the beginning of the stream
        print("Excel file generated successfully in memory.")
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='DOSRI_Summary_Details_Report.xlsx'
        )
    except Exception as e:
        print(f"Error generating Excel report: {e}")
        return jsonify({"error": f"Failed to generate Excel report: {e}"}), 500
