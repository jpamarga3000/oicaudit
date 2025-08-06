import os
import pandas as pd
from datetime import datetime

# Define path for Former Employee CSV file
FORM_EMP_CSV_PATH = "C:/xampp/htdocs/audit_tool/db/list_former_employee.csv"

# --- CSV Helper Functions for Former Employees ---

def _read_form_emp_csv():
    """
    Reads the Former Employee CSV file into a pandas DataFrame.
    Handles file not found by returning an empty DataFrame.
    Standardizes column names and converts 'id' to int if possible.
    """
    try:
        # Attempt to read with utf-8, then fall back to latin-1 or cp1252 if decoding error occurs
        try:
            df = pd.read_csv(FORM_EMP_CSV_PATH, encoding='utf-8', dtype={'CID': str})
        except UnicodeDecodeError:
            print("Warning: UTF-8 decoding failed for Former Employee CSV, trying latin-1...")
            df = pd.read_csv(FORM_EMP_CSV_PATH, encoding='latin-1', dtype={'CID': str})

        df.columns = df.columns.str.upper().str.replace(' ', '_')

        # Ensure 'ID' column exists and is numeric for internal operations
        if 'ID' in df.columns:
            df['ID'] = pd.to_numeric(df['ID'], errors='coerce').fillna(0).astype(int)
        else:
            df['ID'] = range(1, len(df) + 1) # Assign temporary IDs if missing
        
        # Ensure all relevant columns are treated as strings and stripped for consistency
        for col in ['BRANCH', 'NAME', 'CID', 'DATE_RESIGNED', 'STATUS']:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna('').str.strip()

        return df
    except FileNotFoundError:
        # Define expected columns for a new empty DataFrame
        expected_cols = ['ID', 'BRANCH', 'NAME', 'CID', 'DATE_RESIGNED', 'STATUS']
        return pd.DataFrame(columns=expected_cols)
    except pd.errors.EmptyDataError:
        print(f"Warning: Former Employee CSV file '{FORM_EMP_CSV_PATH}' is empty.")
        expected_cols = ['ID', 'BRANCH', 'NAME', 'CID', 'DATE_RESIGNED', 'STATUS']
        return pd.DataFrame(columns=expected_cols)
    except Exception as e:
        print(f"Error reading Former Employee CSV: {e}")
        raise # Re-raise to indicate a serious problem

def _write_form_emp_csv(df):
    """
    Writes the pandas DataFrame to the Former Employee CSV file.
    Ensures the directory exists.
    """
    os.makedirs(os.path.dirname(FORM_EMP_CSV_PATH), exist_ok=True)
    df.to_csv(FORM_EMP_CSV_PATH, index=False, encoding='utf-8')


# --- CSV Operations for Former Employees List Management ---

def get_form_emp_data(entry_id=None, search_term='', status_filter=''):
    """
    Fetches data from the 'list_former_employee.csv' file.
    Can fetch a single record by ID, or filter all records by search term and status.
    """
    df = _read_form_emp_csv()
    
    if df.empty:
        return [] if entry_id is None else None

    # Apply filters if fetching all records
    if entry_id is None:
        if search_term:
            # Case-insensitive search across relevant columns
            search_lower = search_term.lower()
            df = df[
                df['NAME'].str.lower().str.contains(search_lower, na=False) |
                df['BRANCH'].str.lower().str.contains(search_lower, na=False) |
                df['CID'].str.lower().str.contains(search_lower, na=False)
            ]
        if status_filter:
            df = df[df['STATUS'].str.lower() == status_filter.lower()]
        
        # Convert DataFrame to a list of dictionaries, ensuring consistent keys
        # All column names are already uppercase and stripped due to _read_form_emp_csv
        records = df.to_dict(orient='records')
        return records
    else:
        # Fetch a single record by ID
        record = df[df['ID'] == entry_id].to_dict(orient='records')
        if record:
            return record[0]
        return None

def add_form_emp_entry(data):
    """
    Adds a new entry to the 'list_former_employee.csv' file.
    Generates a new ID and appends the record.
    """
    df = _read_form_emp_csv()
    new_id = 1 if df.empty else df['ID'].max() + 1
    
    new_record = {
        'ID': new_id,
        'BRANCH': str(data.get('branch', '')).strip(),
        'NAME': str(data.get('name', '')).strip(),
        'CID': str(data.get('cid', '')).strip(),
        'DATE_RESIGNED': str(data.get('date_resigned', '')).strip(),
        'STATUS': str(data.get('status', '')).strip()
    }
    
    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    _write_form_emp_csv(df)
    print(f"Successfully added former employee entry for Name: {data.get('name')} with ID: {new_id}")
    return True

def update_form_emp_entry(entry_id, data):
    """
    Updates an existing entry in the 'list_former_employee.csv' file.
    """
    df = _read_form_emp_csv()
    if df.empty:
        print(f"No entry found with ID: {entry_id} to update (CSV is empty).")
        return False

    idx = df[df['ID'] == entry_id].index
    if not idx.empty:
        for key, value in data.items():
            # Convert frontend keys to uppercase database column names (e.g., "date_resigned" to "DATE_RESIGNED")
            df_column_name = key.upper().replace(' ', '_')
            if df_column_name in df.columns:
                df.loc[idx, df_column_name] = str(value).strip() # Ensure all stored as strings
        _write_form_emp_csv(df)
        print(f"Successfully updated former employee entry for ID: {entry_id}")
        return True
    else:
        print(f"No entry found with ID: {entry_id} to update.")
        return False

def delete_form_emp_entry(entry_id):
    """
    Deletes an entry from the 'list_former_employee.csv' file.
    """
    df = _read_form_emp_csv()
    if df.empty:
        print(f"No entry found with ID: {entry_id} to delete (CSV is empty).")
        return False

    initial_len = len(df)
    df = df[df['ID'] != entry_id]
    if len(df) < initial_len:
        _write_form_emp_csv(df)
        print(f"Successfully deleted former employee entry for ID: {entry_id}")
        return True
    else:
        print(f"No entry found with ID: {entry_id} to delete.")
        return False

def seed_form_emp_data_to_db(): # Renamed to reflect CSV seeding
    """
    Seeds initial default data into the 'list_former_employee.csv' file if it's empty or doesn't exist.
    """
    if not os.path.exists(FORM_EMP_CSV_PATH) or _read_form_emp_csv().empty:
        print("Seeding default Former Employee data to CSV...")
        default_data = [
            {'ID': 1, 'BRANCH': 'MAIN', 'NAME': 'JOHNSON, ANNA', 'CID': 'FE001', 'DATE_RESIGNED': '01/15/2022', 'STATUS': 'Resigned'},
            {'ID': 2, 'BRANCH': 'BRANCH C', 'NAME': 'WILLIAMS, MARK', 'CID': 'FE002', 'DATE_RESIGNED': '03/01/2023', 'STATUS': 'Terminated'},
            {'ID': 3, 'BRANCH': 'BRANCH A', 'NAME': 'DAVIS, LARA', 'CID': 'FE003', 'DATE_RESIGNED': '11/30/2021', 'STATUS': 'Retired'}
        ]
        df_default = pd.DataFrame(default_data)
        _write_form_emp_csv(df_default)
        print("Default Former Employee data seeded successfully to CSV.")
    else:
        print(f"Former Employee CSV '{FORM_EMP_CSV_PATH}' already contains data. Skipping seeding.")

def upload_form_emp_csv_to_db(filepath, upload_option='override'):
    """
    Uploads Former Employee data from a CSV file to the 'list_former_employee.csv' file.
    """
    try:
        try:
            df_new = pd.read_csv(filepath, encoding='utf-8', dtype={'CID': str})
        except UnicodeDecodeError:
            print("Warning: UTF-8 decoding failed for Former Employee CSV, trying latin-1...")
            df_new = pd.read_csv(filepath, encoding='latin-1', dtype={'CID': str})

        df_new.columns = df_new.columns.str.upper().str.replace(' ', '_')

        # Ensure required columns exist, mapping frontend keys to expected internal keys
        expected_cols_map = {
            'BRANCH': 'BRANCH', 'NAME': 'NAME', 'CID': 'CID',
            'DATE_RESIGNED': 'DATE_RESIGNED', 'STATUS': 'STATUS'
        }
        
        missing_cols = [col_csv for col_csv, col_df in expected_cols_map.items() if col_csv not in df_new.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in uploaded CSV: {', '.join(missing_cols)}")

        # Select and reorder columns, fill NaN with empty strings
        df_new = df_new[[col_csv for col_csv in expected_cols_map.keys()]]
        df_new = df_new.fillna('').astype(str).apply(lambda x: x.str.strip()) # Ensure all relevant columns are stripped

        current_df = _read_form_emp_csv()

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

        _write_form_emp_csv(df_to_write)
        print(f"Successfully uploaded {len(df_new)} Former Employee records to CSV using '{upload_option}' option.")

    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty.")
    except FileNotFoundError:
        raise ValueError(f"CSV file not found at: {filepath}")
    except Exception as e:
        print(f"Error uploading Former Employee CSV data: {e}")
        raise # Re-raise to indicate a serious problem

