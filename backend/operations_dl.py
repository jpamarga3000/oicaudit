# audit_tool/backend/operations_dl.py
import pandas as pd
import os
import uuid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re # Import regex for advanced cleaning

# Import common utilities and database connection from db_common.py
from db_common import (
    get_db_connection, DEPOSIT_CODE_HARDCODED_PATH, SVACC_BASE_DIR, TRNM_BASE_DIR,
    format_currency_py, _clean_numeric_string_for_conversion
)


# Default data for Maturity Requirements - Product names match SQL insert (original format)
_INITIAL_DEFAULT_MATURITY_DATA = [
    {"product": "PEARLS - Retirement", "maturity_years": 12, "int_adj_rate": 2.00},
    {"product": "PEARLS - Pension", "maturity_years": 10, "int_adj_rate": 2.00},
    {"product": "Build Savings Fund", "maturity_years": 3, "int_adj_rate": 2.00},
    {"product": "Dream Savings", "maturity_years": 5, "int_adj_rate": 2.00},
    {"product": "SAFE", "maturity_years": 7, "int_adj_rate": 2.00},
    {"product": "Pocket Savings", "maturity_years": 1, "int_adj_rate": 2.00},
    {"product": "SAFE Plus", "maturity_years": 10, "int_adj_rate": 2.00},
    {"product": "Kabayani Savings", "maturity_years": 5, "int_adj_rate": 2.00},
]

# Default data for Interest Rates - Product names match SQL insert (original format)
_INITIAL_DEFAULT_INTEREST_DATA = [
    {"product": "Time Deposit -A", "interest_rate": 9.00},
    {"product": "Time Deposit -B", "interest_rate": 6.00},
    {"product": "Time Deposit -C", "interest_rate": 7.50},
    {"product": "Health and Disaster", "interest_rate": 5.00},
    {"product": "PEARLS - Retirement", "interest_rate": 10.00},
    {"product": "PEARLS - Pension", "interest_rate": 9.00},
    {"product": "Build Savings Fund", "interest_rate": 6.00},
    {"product": "Emergency Fund", "interest_rate": 5.00},
    {"product": "Share Capital", "interest_rate": 0.00},
    {"product": "Regular Savings", "interest_rate": 2.00},
    {"product": "Youth Savings Club", "interest_rate": 2.00},
    {"product": "Transit Savings", "interest_rate": 0.00}, 
    {"product": "Dream Savings", "interest_rate": 7.00},
    {"product": "SAFE", "interest_rate": 7.00},
    {"product": "Compulsory Savings Deposit", "interest_rate": 2.00},
    {"product": "Member Contigency Savings", "interest_rate": 6.00},
    {"product": "Pocket Savings", "interest_rate": 3.00},
    {"product": "SAFE Plus", "interest_rate": 3.00},
    {"product": "ATM Savings", "interest_rate": 6.00},
    {"product": "Kabayani Savings", "interest_rate": 5.00},
    {"product": "Time Deposit - Monthly", "interest_rate": 5.00},
    {"product": "Time Deposit - Maturity", "interest_rate": 1.50},
    {"product": "Home Savings", "interest_rate": 5.00},
]


# NEW: Mapping of human-readable product names to their numerical codes
# This map is the central source of product codes for lookup
PRODUCT_TO_CODE_MAP = {
    "Time Deposit -A": 1,
    "Time Deposit -B": 2,
    "Time Deposit -C": 3,
    "Health and Disaster": 4,
    "PEARLS - Retirement": 5,
    "PEARLS - Pension": 6,
    "Build Savings Fund": 7,
    "Emergency Fund": 8,
    "Share Capital": 9,
    "Regular Savings": 10,
    "Youth Savings Club": 11,
    "Transit Savings": 12,
    "Dream Savings": 13,
    "SAFE": 14,
    "Compulsory Savings Deposit": 15,
    "Member Contigency Savings": 16,
    "Pocket Savings": 17,
    "SAFE Plus": 18,
    "ATM Savings": 19,
    "Kabayani Savings": 20,
    "Time Deposit - Monthly": 21,
    "Time Deposit - Maturity": 22,
    "Home Savings": 23
}

# Helper for robust product name normalization
def _normalize_product_name(name):
    """
    Normalizes a product name by removing non-alphanumeric characters (except spaces),
    stripping whitespace, converting to uppercase, and removing all spaces.
    This creates a consistent string for matching or deriving product codes.
    """
    if pd.isna(name) or not isinstance(name, str):
        return ""
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name).strip().upper().replace(' ', '')
    return cleaned

# Helper to get product code from product name
def _get_product_code_from_name(product_name_raw):
    """
    Looks up the product code for a given raw product name using the PRODUCT_TO_CODE_MAP.
    Returns None if not found.
    """
    normalized_name = _normalize_product_name(product_name_raw)
    # Iterate through the map to find the code by normalized name
    for name, code in PRODUCT_TO_CODE_MAP.items():
        if _normalize_product_name(name) == normalized_name:
            return code
    return None

# Update the default data with product codes for seeding
DEFAULT_MATURITY_DATA = []
for item in _INITIAL_DEFAULT_MATURITY_DATA:
    code = _get_product_code_from_name(item['product'])
    if code is not None:
        DEFAULT_MATURITY_DATA.append({**item, 'product_code': code})
    else:
        pass # Removed log

DEFAULT_INTEREST_DATA = []
for item in _INITIAL_DEFAULT_INTEREST_DATA:
    code = _get_product_code_from_name(item['product'])
    if code is not None:
        DEFAULT_INTEREST_DATA.append({**item, 'product_code': code})
    else:
        pass # Removed log


# --- DB Functions for Maturity Requirements ---
def get_deposit_maturity_requirements_from_db():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Fetch product_code along with other fields
            cursor.execute("SELECT id, product, product_code, maturity_years, int_adj_rate FROM dep_mat_db")
            result = cursor.fetchall()
            
            return result # Return data as is, the lookup will use product_code
    except Exception as e:
        print(f"Error fetching deposit maturity requirements from DB: {e}")
        return []
    finally:
        if conn:
            conn.close()

def save_deposit_maturity_requirements_to_db(data):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM dep_mat_db") 
            for item in data:
                # Ensure product_code is present when saving
                cursor.execute(
                    "INSERT INTO dep_mat_db (id, product, product_code, maturity_years, int_adj_rate) VALUES (%s, %s, %s, %s, %s)",
                    (item['id'], item['product'], item['product_code'], item['maturity_years'], item['int_adj_rate'])
                )
            conn.commit()
        return {"message": "Maturity requirements saved successfully."}
    except Exception as e:
        print(f"Error saving deposit maturity requirements to DB: {e}")
        if conn: conn.rollback()
        raise Exception(f"Failed to save maturity requirements: {str(e)}")
    finally:
        if conn:
            conn.close()

def delete_deposit_maturity_requirement_from_db(item_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM dep_mat_db WHERE id = %s", (item_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return {"message": f"Maturity requirement {item_id} deleted successfully."}
            else:
                return {"message": f"Maturity requirement {item_id} not found."}
    except Exception as e:
        print(f"Error deleting deposit maturity requirement from DB: {e}")
        if conn: conn.rollback()
        raise Exception(f"Failed to delete maturity requirement: {str(e)}")
    finally:
        if conn:
            conn.close()

# --- DB Functions for Interest Rates ---
def get_deposit_interest_rates_from_db():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, product, product_code, interest_rate FROM dep_int_db")
            result = cursor.fetchall()
            
            return result # Return data as is, the lookup will use product_code
    except Exception as e:
        print(f"Error fetching deposit interest rates from DB: {e}")
        return []
    finally:
        if conn:
            conn.close()

def save_deposit_interest_rates_to_db(data):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM dep_int_db") 
            for item in data:
                # Ensure product_code is present when saving
                cursor.execute(
                    "INSERT INTO dep_int_db (id, product, product_code, interest_rate) VALUES (%s, %s, %s, %s)",
                    (item['id'], item['product'], item['product_code'], item['interest_rate'])
                )
            conn.commit()
        return {"message": "Interest rates saved successfully."}
    except Exception as e:
        print(f"Error saving deposit interest rates to DB: {e}")
        if conn: conn.rollback()
        raise Exception(f"Failed to save interest rates: {str(e)}")
    finally:
        if conn:
            conn.close()

def delete_deposit_interest_rate_from_db(item_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM dep_int_db WHERE id = %s", (item_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return {"message": f"Interest rate {item_id} deleted successfully."}
            else:
                return {"message": f"Interest rate {item_id} not found."}
    except Exception as e:
        print(f"Error deleting deposit interest rate from DB: {e}")
        if conn: conn.rollback()
        raise Exception(f"Failed to delete interest rate: {str(e)}")
    finally:
        if conn:
            conn.close()

# Function to seed default data if tables are empty
def seed_deposit_default_data():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Create dep_mat_db table if not exists with product_code
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dep_mat_db (
                    id VARCHAR(255) PRIMARY KEY,
                    product VARCHAR(255) NOT NULL,
                    product_code INT NOT NULL, -- NEW COLUMN
                    maturity_years INT NOT NULL,
                    int_adj_rate DECIMAL(5, 2) NOT NULL
                )
            """)
            # Create dep_int_db table if not exists with product_code
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dep_int_db (
                    id VARCHAR(255) PRIMARY KEY,
                    product VARCHAR(255) NOT NULL,
                    product_code INT NOT NULL, -- NEW COLUMN
                    interest_rate DECIMAL(5, 2) NOT NULL
                )
            """)
            conn.commit()

            # Seed Maturity Data
            cursor.execute("SELECT COUNT(*) FROM dep_mat_db")
            if cursor.fetchone()['COUNT(*)'] == 0:
                for item in DEFAULT_MATURITY_DATA:
                    item_id = str(uuid.uuid4())
                    cursor.execute(
                        "INSERT INTO dep_mat_db (id, product, product_code, maturity_years, int_adj_rate) VALUES (%s, %s, %s, %s, %s)",
                        (item_id, item['product'], item['product_code'], item['maturity_years'], item['int_adj_rate'])
                    )
                conn.commit()
            else:
                pass # No print on skipping

            # Seed Interest Data
            cursor.execute("SELECT COUNT(*) FROM dep_int_db")
            if cursor.fetchone()['COUNT(*)'] == 0:
                for item in DEFAULT_INTEREST_DATA:
                    item_id = str(uuid.uuid4())
                    # CORRECTED TYPO: Changed 'product' to 'product_code' in the INSERT SQL string
                    cursor.execute(
                        "INSERT INTO dep_int_db (id, product, product_code, interest_rate) VALUES (%s, %s, %s, %s)",
                        (item_id, item['product'], item['product_code'], item['interest_rate']) 
                    )
                conn.commit()
            else:
                pass # No print on skipping
            
        return {"message": "Default data seeding process completed."}
    except Exception as e:
        print(f"Error during seeding: {e}")
        if conn: conn.rollback()
        raise Exception(f"Failed to seed default data: {str(e)}")
    finally:
        if conn:
            conn.close()

# --- Read Deposit Code CSV for Product list (for dropdowns in modals) ---
def read_deposit_code_csv_products():
    """
    Reads the DEPOSIT CODE.csv file and returns a list of unique product names.
    """
    if not os.path.exists(DEPOSIT_CODE_HARDCODED_PATH):
        print(f"Error: DEPOSIT CODE file not found at {DEPOSIT_CODE_HARDCODED_PATH}.")
        return []
    try:
        df = pd.read_csv(DEPOSIT_CODE_HARDCODED_PATH, dtype=str)
        df.columns = [col.strip().upper() for col in df.columns]
        if 'PRODUCT' in df.columns:
            return df['PRODUCT'].dropna().unique().tolist()
        return []
    except Exception as e:
        print(f"Error reading DEPOSIT CODE.csv for products: {e}")
        return []

# --- New Report Logic for Deposit Liabilities Summary ---
def generate_deposit_liabilities_report_logic(selected_branches):
    """
    Generates a summary report of deposit liabilities per product for selected branches.
    """
    
    deposit_products_summary = []
    
    # 1. Load DEPOSIT CODE.csv to get unique product names
    deposit_code_df = pd.DataFrame()
    if os.path.exists(DEPOSIT_CODE_HARDCODED_PATH):
        try:
            df_ = pd.read_csv(DEPOSIT_CODE_HARDCODED_PATH, dtype=str)
            df_.columns = [col.strip().upper() for col in df_.columns]
            if 'PRODUCT' not in df_.columns:
                print(f"Error: DEPOSIT CODE file missing 'PRODUCT' column.")
                return {"message": "DEPOSIT CODE file missing 'PRODUCT' column.", "data": []}
            
            # unique_products here should be the raw names from the CSV for proper display in frontend dropdowns
            unique_products_raw = df_['PRODUCT'].dropna().unique().tolist()
        except Exception as e:
            print(f"Error loading DEPOSIT CODE.csv: {e}")
            return {"message": f"Error loading DEPOSIT CODE file: {e}", "data": []}
    else:
        print(f"Error: DEPOSIT CODE file not found at {DEPOSIT_CODE_HARDCODED_PATH}.")
        return {"message": "DEPOSIT CODE file not found. Please ensure it's in the correct path.", "data": []}

    # 2. Load SVACC CSV files for selected branches
    all_svacc_data_frames = []
    for branch_name in selected_branches:
        sanitized_branch = "".join([c for c in str(branch_name) if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
        svacc_filepath = os.path.join(SVACC_BASE_DIR, f"{sanitized_branch.upper()}.csv")

        if os.path.exists(svacc_filepath):
            try:
                df_svacc = pd.read_csv(svacc_filepath, encoding='utf-8-sig', dtype=str, low_memory=False)
                df_svacc.columns = [col.strip().upper() for col in df_svacc.columns]
                
                # Ensure required columns exist
                required_svacc_cols = ['ACC', 'BAL', 'ACCNAME', 'DOPEN', 'INTRATE'] # Added DOPEN and INTRATE for robustness
                for col in required_svacc_cols:
                    if col not in df_svacc.columns:
                        df_svacc[col] = pd.NA # Add missing column with NaN
                        print(f"Server Log (Deposit Liabilities Summary): Warning: Column '{col}' not found in SVACC file {os.path.basename(svacc_filepath)}. Adding as NaN.")


                df_svacc['DOPEN_DT'] = pd.to_datetime(df_svacc['DOPEN'], errors='coerce')
                df_svacc['BAL_NUM'] = pd.to_numeric(df_svacc['BAL'].apply(_clean_numeric_string_for_conversion), errors='coerce').fillna(0.0) # Convert to numeric and fill NaN
                df_svacc['INTRATE_NUM'] = pd.to_numeric(df_svacc['INTRATE'].apply(_clean_numeric_string_for_conversion), errors='coerce').fillna(0.0) # Convert to numeric and fill NaN
                df_svacc = df_svacc.dropna(subset=['DOPEN_DT']).copy()
                all_svacc_data_frames.append(df_svacc) # Append df_svacc here if valid
            except Exception as e:
                print(f"Error loading SVACC file {os.path.basename(svacc_filepath)}: {e}")
                df_svacc = pd.DataFrame()
        else:
            pass # No print on file not found
            
    if not all_svacc_data_frames:
        return {"message": "No valid SVACC data found across selected branches.", "data": []}

    combined_svacc_df = pd.concat(all_svacc_data_frames, ignore_index=True)
    
    # Normalize ACCNAME from SVACC for consistent matching against backend lookup keys
    combined_svacc_df['ACCNAME_NORMALIZED'] = combined_svacc_df['ACCNAME'].astype(str).apply(_normalize_product_name)


    # 3. Process data for each unique product
    # Iterate over the raw product names for display
    for product_name_raw in unique_products_raw: 
        # Filter combined SVACC data using the normalized version of the current raw product name
        product_name_normalized_for_filter = _normalize_product_name(product_name_raw)
        product_df = combined_svacc_df[combined_svacc_df['ACCNAME_NORMALIZED'] == product_name_normalized_for_filter].copy()

        total_amount = product_df['BAL_NUM'].sum()
        num_accounts = product_df['ACC'].nunique() # Count unique accounts

        average_balance = 0.0
        if num_accounts > 0:
            average_balance = total_amount / num_accounts
        
        # Only add to summary if there's actual data for the product
        if total_amount > 0 or num_accounts > 0:
            deposit_products_summary.append({
                "PRODUCT_NAME": product_name_raw, # Use the raw name for display
                "TOTAL_AMOUNT": total_amount,
                "NUM_ACCOUNTS": num_accounts,
                "AVERAGE_BALANCE_PER_ACCOUNT": average_balance
            })
    
    # Sort the summary by product name for consistent display
    deposit_products_summary.sort(key=lambda x: x['PRODUCT_NAME'])

    return {"message": "Deposit Liabilities Report generated successfully!", "data": deposit_products_summary}


# --- New Report Logic for Matured Deposits ---
def generate_matured_deposits_report_logic(branch_name, month, year, maturity_requirements_data):

    report_data = []
    
    sanitized_branch_name = "".join([c for c in branch_name if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch_name:
        return {"message": "Invalid branch name provided.", "data": []}

    svacc_filepath = os.path.join(SVACC_BASE_DIR, f"{sanitized_branch_name.upper()}.csv")
    trnm_branch_folder_path = os.path.join(TRNM_BASE_DIR, sanitized_branch_name.upper())

    # Load SVACC data
    df_svacc = pd.DataFrame()
    svacc_file_found = False
    if os.path.exists(svacc_filepath):
        svacc_file_found = True
        try:
            df_svacc = pd.read_csv(svacc_filepath, encoding='utf-8-sig', dtype=str, low_memory=False)
            df_svacc.columns = [col.strip().upper() for col in df_svacc.columns]
            required_svacc_cols = ['ACC', 'CID', 'BAL', 'ACCNAME', 'DOPEN', 'INTRATE']
            for col in required_svacc_cols: # Ensure all required columns exist
                if col not in df_svacc.columns:
                    df_svacc[col] = pd.NA # Add missing column with NaN
                    print(f"Server Log (Matured Deposits): Warning: Column '{col}' not found in SVACC file {os.path.basename(svacc_filepath)}. Adding as NaN.")


            df_svacc['DOPEN_DT'] = pd.to_datetime(df_svacc['DOPEN'], errors='coerce')
            df_svacc['BAL_NUM'] = pd.to_numeric(df_svacc['BAL'].apply(_clean_numeric_string_for_conversion), errors='coerce').fillna(0.0) # Convert to numeric and fill NaN
            
            # Correctly handle INTRATE column for INTRATE_NUM in Matured Deposits Report
            # Remove '%' if present, then convert to numeric. DO NOT divide by 100 here.
            df_svacc['INTRATE_NUM'] = df_svacc['INTRATE'].astype(str).str.replace('%', '', regex=False).apply(_clean_numeric_string_for_conversion)
            df_svacc['INTRATE_NUM'] = pd.to_numeric(df_svacc['INTRATE_NUM'], errors='coerce').fillna(0.0) # Removed / 100 here

            df_svacc = df_svacc.dropna(subset=['DOPEN_DT']).copy()
            # Filter out accounts with zero or negative balance
            df_svacc = df_svacc[df_svacc['BAL_NUM'] > 0].copy() # ADDED FILTER
        except Exception as e:
            print(f"Error loading SVACC file {svacc_filepath}: {e}")
            df_svacc = pd.DataFrame()
    else:
        pass # No print on file not found
            
    if df_svacc.empty and not svacc_file_found:
        return {"message": "No SVACC data found for the selected branch to generate Matured Deposits Report.", "data": []}
    elif df_svacc.empty and svacc_file_found:
         return {"message": f"SVACC data file found ({os.path.basename(svacc_filepath)}) but contains no valid data for Matured Deposits Report.", "data": []}


    # Load TRNM data (only DEP type)
    all_trnm_data = []
    df_trnm_combined = pd.DataFrame(columns=['ACC', 'TRNINT', 'TRNDATE', 'TRNDATE_DT', 'TRNINT_NUM'])
    if os.path.exists(trnm_branch_folder_path):
        for filename in os.listdir(trnm_branch_folder_path):
            current_filepath = os.path.join(trnm_branch_folder_path, filename)
            if os.path.isfile(current_filepath) and \
               f"{sanitized_branch_name[:3].upper()} DEP".upper() in filename.upper() and \
               filename.lower().endswith('.csv'):
                try:
                    df_trnm = pd.read_csv(current_filepath, encoding='latin1', dtype=str, low_memory=False)
                    df_trnm.columns = [col.strip().upper() for col in df_trnm.columns]
                    req_trnm_cols = ['ACC', 'TRNINT', 'TRNDATE']
                    for col in req_trnm_cols: # Ensure all required columns exist
                        if col not in df_trnm.columns:
                            df_trnm[col] = pd.NA # Add missing column with NaN
                            print(f"Server Log (Matured Deposits): Warning: Column '{col}' not found in TRNM file {os.path.basename(current_filepath)}. Adding as NaN.")


                    df_trnm['TRNDATE_DT'] = pd.to_datetime(df_trnm['TRNDATE'], errors='coerce')
                    df_trnm['TRNINT_NUM'] = pd.to_numeric(df_trnm['TRNINT'].apply(_clean_numeric_string_for_conversion), errors='coerce').fillna(0.0) # Convert to numeric and fill NaN
                    df_trnm = df_trnm.dropna(subset=['TRNDATE_DT']).copy()
                    all_trnm_data.append(df_trnm)
                except Exception as e:
                    print(f"Error loading TRNM file {current_filepath}: {e}")
    else:
        pass # No print on file not found

    if all_trnm_data:
        df_trnm_combined = pd.concat(all_trnm_data, ignore_index=True)
    else:
        pass # No print on no files found

    # Convert maturity_requirements_data list of dicts to DataFrame for merging
    maturity_df = pd.DataFrame(maturity_requirements_data)

    if maturity_df.empty:
        merged_df = df_svacc.copy()
        merged_df['maturity_years'] = pd.NA
        merged_df['int_adj_rate'] = pd.NA
        print("Server Log (Matured Deposits): Maturity requirements data is empty. Proceeding without specific maturity config.")
    else:
        # Check for required columns before proceeding
        required_mat_cols = ['product_code', 'maturity_years', 'int_adj_rate']
        if not all(col in maturity_df.columns for col in required_mat_cols):
            print(f"Server Log (Matured Deposits): Maturity requirements data is malformed (missing one of {required_mat_cols}). Proceeding without specific maturity config.")
            merged_df = df_svacc.copy()
            merged_df['maturity_years'] = pd.NA
            merged_df['int_adj_rate'] = pd.NA
        else:
            # Explicitly ensure these columns are numeric (float) before use
            maturity_df['product_code'] = pd.to_numeric(maturity_df['product_code'], errors='coerce').fillna(0).astype(float)
            maturity_df['maturity_years'] = pd.to_numeric(maturity_df['maturity_years'], errors='coerce').fillna(0).astype(float)
            maturity_df['int_adj_rate'] = pd.to_numeric(maturity_df['int_adj_rate'], errors='coerce').fillna(0.0).astype(float)
            maturity_df = maturity_df.dropna(subset=['product_code']) # Drop rows where product_code couldn't be converted

            # Ensure 'product_code' in SVACC is numeric for merging
            df_svacc['product_code'] = df_svacc['ACCNAME'].astype(str).apply(_get_product_code_from_name)
            df_svacc = df_svacc.dropna(subset=['product_code'])
            df_svacc['product_code'] = df_svacc['product_code'].astype(int) # Ensure integer type for merge key

            # Merge SVACC with maturity requirements
            merged_df = pd.merge(df_svacc, maturity_df[['product_code', 'maturity_years', 'int_adj_rate']],
                                 on='product_code', how='left')


    # Filter accounts that have exceeded their maturity date and calculate relevant fields
    cut_off_date = datetime(year, month, 1) + relativedelta(months=1, days=-1)
    prev_year_end_date = datetime(year - 1, 12, 31)

    # Calculate maturity_date
    merged_df['MATURITY_DATE'] = merged_df.apply(
        lambda row: row['DOPEN_DT'] + relativedelta(years=int(row['maturity_years']))
        if pd.notna(row['DOPEN_DT']) and pd.notna(row['maturity_years'])
        else pd.NaT, axis=1
    )

    # Filter for matured accounts
    matured_accounts_df = merged_df[merged_df['MATURITY_DATE'] <= cut_off_date].copy()
    matured_accounts_df = matured_accounts_df.dropna(subset=['MATURITY_DATE'])

    if matured_accounts_df.empty:
        return {"message": "No Matured Deposits data found for the specified criteria.", "data": []}

    # Calculate DAYS_LAPSED (vectorized)
    matured_accounts_df['DAYS_LAPSED'] = (cut_off_date - matured_accounts_df['MATURITY_DATE']).dt.days

    # Calculate TOTAL_INT_EARNED_AFTER_MATURITY (requires joining with TRNM)
    # Aggregate TRNM data first
    if not df_trnm_combined.empty:
        # For TOTAL_INT_EARNED_AFTER_MATURITY
        trnm_after_maturity = df_trnm_combined.merge(
            matured_accounts_df[['ACC', 'MATURITY_DATE']], on='ACC', how='inner'
        )
        trnm_after_maturity = trnm_after_maturity[
            trnm_after_maturity['TRNDATE_DT'] > trnm_after_maturity['MATURITY_DATE']
        ]
        total_int_after_maturity_sums = trnm_after_maturity.groupby('ACC')['TRNINT_NUM'].sum().reset_index()
        total_int_after_maturity_sums.rename(columns={'TRNINT_NUM': 'TOTAL_INTEREST_EARNED_AFTER_MATURITY'}, inplace=True)
        
        matured_accounts_df = pd.merge(
            matured_accounts_df, total_int_after_maturity_sums, on='ACC', how='left'
        )
        matured_accounts_df['TOTAL_INTEREST_EARNED_AFTER_MATURITY'] = matured_accounts_df['TOTAL_INTEREST_EARNED_AFTER_MATURITY'].fillna(0.0)

        # For TOTAL_INT_EARNED_IN_YEAR
        # Calculate start_date_for_year_interest for each account
        matured_accounts_df['start_date_for_year_interest'] = matured_accounts_df.apply(
            lambda row: max(row['MATURITY_DATE'], prev_year_end_date), axis=1
        )

        trnm_in_year = df_trnm_combined.merge(
            matured_accounts_df[['ACC', 'start_date_for_year_interest']], on='ACC', how='inner'
        )
        trnm_in_year = trnm_in_year[
            (trnm_in_year['TRNDATE_DT'] > trnm_in_year['start_date_for_year_interest']) &
            (trnm_in_year['TRNDATE_DT'].dt.year == year)
        ]
        total_int_earned_in_year_sums = trnm_in_year.groupby('ACC')['TRNINT_NUM'].sum().reset_index()
        total_int_earned_in_year_sums.rename(columns={'TRNINT_NUM': f'TOTAL_INT_EARNED_IN_{year}'}, inplace=True)

        matured_accounts_df = pd.merge(
            matured_accounts_df, total_int_earned_in_year_sums, on='ACC', how='left'
        )
        matured_accounts_df[f'TOTAL_INT_EARNED_IN_{year}'] = matured_accounts_df[f'TOTAL_INT_EARNED_IN_{year}'].fillna(0.0)

    else:
        matured_accounts_df['TOTAL_INTEREST_EARNED_AFTER_MATURITY'] = 0.0
        matured_accounts_df[f'TOTAL_INT_EARNED_IN_{year}'] = 0.0
        
    # Calculate SHOULD_BE_INTEREST_IN_YEAR and ADJUSTMENT (vectorized)
    matured_accounts_df[f'SHOULD_BE_INTEREST_IN_{year}'] = 0.0
    
    # Ensure relevant columns are float for calculations
    matured_accounts_df[f'TOTAL_INT_EARNED_IN_{year}'] = pd.to_numeric(matured_accounts_df[f'TOTAL_INT_EARNED_IN_{year}'], errors='coerce').fillna(0.0).astype(float)
    matured_accounts_df['INTRATE_NUM'] = pd.to_numeric(matured_accounts_df['INTRATE_NUM'], errors='coerce').fillna(0.0).astype(float)
    matured_accounts_df['int_adj_rate'] = pd.to_numeric(matured_accounts_df['int_adj_rate'], errors='coerce').fillna(0.0).astype(float)

    valid_rate_mask = (matured_accounts_df['INTRATE_NUM'] != 0) & (matured_accounts_df['int_adj_rate'] != 0)

    matured_accounts_df.loc[valid_rate_mask, f'SHOULD_BE_INTEREST_IN_{year}'] = (
        matured_accounts_df.loc[valid_rate_mask, f'TOTAL_INT_EARNED_IN_{year}'] /
        (matured_accounts_df.loc[valid_rate_mask, 'INTRATE_NUM'] / 100)
    ) * (matured_accounts_df.loc[valid_rate_mask, 'int_adj_rate'] / 100) # Ensure int_adj_rate is treated as a percentage for multiplication

    matured_accounts_df['ADJUSTMENT_RAW'] = matured_accounts_df[f'TOTAL_INT_EARNED_IN_{year}'] - matured_accounts_df[f'SHOULD_BE_INTEREST_IN_{year}']

    # Format output
    report_data = matured_accounts_df.copy()
    report_data['BRANCH'] = branch_name
    report_data['CID'] = report_data['CID'].astype(str)
    report_data['ACCOUNT'] = report_data['ACC'].astype(str)
    report_data['BALANCE'] = report_data['BAL_NUM'].apply(format_currency_py)
    report_data['PRODUCT'] = report_data['ACCNAME'].astype(str)
    report_data['OPENED'] = report_data['DOPEN_DT'].dt.strftime('%m/%d/%Y')
    report_data['MATURITY'] = report_data['MATURITY_DATE'].dt.strftime('%m/%d/%Y')
    report_data['DAYS_LAPSED'] = matured_accounts_df['DAYS_LAPSED'].astype(int) # Corrected to use raw value
    report_data['TOTAL_INTEREST_EARNED_AFTER_MATURITY'] = report_data['TOTAL_INTEREST_EARNED_AFTER_MATURITY'].apply(format_currency_py)
    report_data[f'TOTAL_INT_EARNED_IN_{year}'] = report_data[f'TOTAL_INT_EARNED_IN_{year}'].apply(format_currency_py)
    report_data[f'SHOULD_BE_INTEREST_IN_{year}'] = report_data[f'SHOULD_BE_INTEREST_IN_{year}'].apply(format_currency_py)
    report_data['ADJUSTMENT'] = report_data['ADJUSTMENT_RAW'].apply(format_currency_py)

    final_columns = [
        'BRANCH', 'CID', 'ACCOUNT', 'BALANCE', 'PRODUCT', 'OPENED', 'MATURITY',
        'DAYS_LAPSED', 'TOTAL_INTEREST_EARNED_AFTER_MATURITY', f'TOTAL_INT_EARNED_IN_{year}',
        f'SHOULD_BE_INTEREST_IN_{year}', 'ADJUSTMENT', 'ADJUSTMENT_RAW'
    ]
    report_data = report_data[final_columns].sort_values(by='ADJUSTMENT_RAW', ascending=False)

    return {"message": "Matured Deposits Report generated successfully!", "data": report_data.to_dict(orient='records')}

# --- New Report Logic for Wrong Application of Interest ---
def generate_wrong_application_interest_report_logic(branch_name, month, year, interest_rates_data):
    
    report_data = []

    sanitized_branch_name = "".join([c for c in branch_name if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch_name:
        return {"message": "Invalid branch name provided.", "data": []}

    svacc_filepath = os.path.join(SVACC_BASE_DIR, f"{sanitized_branch_name.upper()}.csv")
    trnm_branch_folder_path = os.path.join(TRNM_BASE_DIR, sanitized_branch_name.upper())

    # Load SVACC data
    df_svacc = pd.DataFrame()
    svacc_file_found = False
    if os.path.exists(svacc_filepath):
        svacc_file_found = True
        try:
            df_svacc = pd.read_csv(svacc_filepath, encoding='utf-8-sig', dtype=str, low_memory=False)
            df_svacc.columns = [col.strip().upper() for col in df_svacc.columns]
            
            req_svacc_cols = ['ACC', 'CID', 'BAL', 'ACCNAME', 'DOPEN', 'INTRATE']
            for col in req_svacc_cols: # Ensure all required columns exist
                if col not in df_svacc.columns:
                    df_svacc[col] = pd.NA # Add missing column with NaN
                    print(f"Server Log (Wrong Interest): Warning: Column '{col}' not found in SVACC file {os.path.basename(svacc_filepath)}. Adding as NaN.")


            df_svacc['DOPEN_DT'] = pd.to_datetime(df_svacc['DOPEN'], errors='coerce')
            df_svacc['BAL_NUM'] = pd.to_numeric(df_svacc['BAL'].apply(_clean_numeric_string_for_conversion), errors='coerce').fillna(0.0) # Convert to numeric and fill NaN
            
            # Correctly handle INTRATE column for INTRATE_NUM
            # Remove '%' if present, then convert to numeric and DO NOT divide by 100 here
            df_svacc['INTRATE_NUM'] = df_svacc['INTRATE'].astype(str).str.replace('%', '', regex=False).apply(_clean_numeric_string_for_conversion)
            df_svacc['INTRATE_NUM'] = pd.to_numeric(df_svacc['INTRATE_NUM'], errors='coerce').fillna(0.0) # Removed / 100 here

            df_svacc = df_svacc.dropna(subset=['DOPEN_DT']).copy()
            # Filter out accounts with zero or negative balance
            df_svacc = df_svacc[df_svacc['BAL_NUM'] > 0].copy() # ADDED FILTER
        except Exception as e:
            print(f"Error loading SVACC file {svacc_filepath}: {e}")
            df_svacc = pd.DataFrame()
    else:
        pass # No print on file not found

    if df_svacc.empty and not svacc_file_found:
        return {"message": "No SVACC data found for the selected branch to generate Wrong Application of Interest Report.", "data": []}
    elif df_svacc.empty and svacc_file_found:
         return {"message": f"SVACC data file found ({os.path.basename(svacc_filepath)}) but contains no valid data for Wrong Application of Interest Report.", "data": []}


    # Load TRNM data (only DEP type) and pre-calculate sums
    all_trnm_data = []
    df_trnm_combined = pd.DataFrame() # Initialize as empty DataFrame
    if os.path.exists(trnm_branch_folder_path):
        for filename in os.listdir(trnm_branch_folder_path):
            current_filepath = os.path.join(trnm_branch_folder_path, filename)
            if os.path.isfile(current_filepath) and \
               f"{sanitized_branch_name[:3].upper()} DEP".upper() in filename.upper() and \
               filename.lower().endswith('.csv'):
                try:
                    df_trnm = pd.read_csv(current_filepath, encoding='latin1', dtype=str, low_memory=False)
                    df_trnm.columns = [col.strip().upper() for col in df_trnm.columns]
                    req_trnm_cols = ['ACC', 'TRNINT', 'TRNDATE']
                    for col in req_trnm_cols: # Ensure all required columns exist
                        if col not in df_trnm.columns:
                            df_trnm[col] = pd.NA # Add missing column with NaN
                            print(f"Server Log (Wrong Interest): Warning: Column '{col}' not found in TRNM file {os.path.basename(current_filepath)}. Adding as NaN.")


                    df_trnm['TRNDATE_DT'] = pd.to_datetime(df_trnm['TRNDATE'], errors='coerce')
                    df_trnm['TRNINT_NUM'] = pd.to_numeric(df_trnm['TRNINT'].apply(_clean_numeric_string_for_conversion), errors='coerce').fillna(0.0) # Convert to numeric and fill NaN
                    df_trnm = df_trnm.dropna(subset=['TRNDATE_DT']).copy()
                    all_trnm_data.append(df_trnm)
                except Exception as e:
                    print(f"Error loading TRNM file {current_filepath}: {e}")
    else:
        pass # No print on file not found

    if all_trnm_data:
        df_trnm_combined = pd.concat(all_trnm_data, ignore_index=True)
    else:
        pass # No print on no files found


    # Process interest rates lookup - Convert to DataFrame for merging
    interest_config_df = pd.DataFrame(interest_rates_data)
    
    # Check if the DataFrame is empty immediately after creation
    if interest_config_df.empty:
        return {"message": "Interest rates configuration is empty. Please configure interest rates in the Interest Rate Configuration modal.", "data": []}

    # Explicitly ensure 'product' and 'interest_rate' columns exist, filling with NaN if missing
    for col_name in ['product', 'interest_rate']:
        if col_name not in interest_config_df.columns:
            interest_config_df[col_name] = pd.NA
            print(f"Server Log (Wrong Interest): Warning: Column '{col_name}' not found in interest_rates_data. Adding as NaN.")

    # Now that it's renamed, ensure CONFIG_INTEREST_RATE is float for calculation
    interest_config_df = interest_config_df.rename(columns={'interest_rate': 'CONFIG_INTEREST_RATE'})
    
    # Ensure product_code is numeric (it comes from the DB as well, so it needs to be robust)
    interest_config_df['product_code'] = pd.to_numeric(interest_config_df['product_code'], errors='coerce').fillna(0).astype(int) 
    interest_config_df = interest_config_df.dropna(subset=['product_code']) # Drop rows where product_code couldn't be converted

    # Now that it's renamed, ensure CONFIG_INTEREST_RATE is float for calculation
    interest_config_df['CONFIG_INTEREST_RATE'] = pd.to_numeric(interest_config_df['CONFIG_INTEREST_RATE'], errors='coerce').fillna(0.0).astype(float)
    interest_config_df['CONFIG_INTEREST_RATE_DECIMAL'] = interest_config_df['CONFIG_INTEREST_RATE'] / 100

    # Prepare SVACC data for merging
    df_svacc['product_code'] = df_svacc['ACCNAME'].astype(str).apply(_get_product_code_from_name)
    df_svacc = df_svacc.dropna(subset=['product_code'])
    df_svacc['product_code'] = df_svacc['product_code'].astype(int) # Ensure integer type for merge key

    # Merge SVACC with interest rate configuration
    merged_df = pd.merge(df_svacc, interest_config_df[['product_code', 'CONFIG_INTEREST_RATE', 'CONFIG_INTEREST_RATE_DECIMAL']],
                         on='product_code', how='left')

    # Filter out accounts where no config interest rate was found
    merged_df = merged_df.dropna(subset=['CONFIG_INTEREST_RATE_DECIMAL'])

    if merged_df.empty:
        return {"message": "No matching accounts found for the configured interest rates.", "data": []}

    # FILTERING STEP: Remove specific products
    products_to_exclude = [
        _normalize_product_name("Time Deposit - Monthly"),
        _normalize_product_name("Time Deposit - Maturity")
    ]
    # Filter based on the normalized ACCNAM
    initial_rows = len(merged_df)
    merged_df['ACCNAME_NORMALIZED'] = merged_df['ACCNAME'].astype(str).apply(_normalize_product_name)
    merged_df = merged_df[~merged_df['ACCNAME_NORMALIZED'].isin(products_to_exclude)].copy()
    if len(merged_df) < initial_rows:
        print(f"Server Log (Wrong Interest): Filtered out {initial_rows - len(merged_df)} rows due to excluded products.")
    del merged_df['ACCNAME_NORMALIZED'] # Remove temp column


    # Filter accounts where ACTUAL INTEREST and SHOULD BE INTEREST are different
    # (i.e., where SVACC INTRATE_NUM is not close to CONFIG_INTEREST_RATE_DECIMAL)
    
    # Calculate difference and create a mask for discrepancies
    merged_df['DIFF_PERCENT'] = abs(merged_df['INTRATE_NUM'] - merged_df['CONFIG_INTEREST_RATE_DECIMAL'])
    discrepancy_df = merged_df[merged_df['DIFF_PERCENT'] >= 0.0001].copy()

    if discrepancy_df.empty:
        return {"message": "No discrepancies found between actual and configured interest rates.", "data": []}

    # Define prev_year_end_date here for the correct scope
    prev_year_end_date = datetime(year - 1, 12, 31)

    # Now, calculate total interest earned and total interest earned in the specified year efficiently
    if not df_trnm_combined.empty:
        # Explicitly convert 'TRNINT_NUM' in df_trnm_combined to float before groupby/sum
        df_trnm_combined['TRNINT_NUM'] = pd.to_numeric(df_trnm_combined['TRNINT_NUM'], errors='coerce').fillna(0.0)

        # Calculate total_int_earned (from DOPEN_DT until now) for each account
        trnm_with_dopen = df_trnm_combined.merge(
            discrepancy_df[['ACC', 'DOPEN_DT']], on='ACC', how='inner'
        )
        trnm_earned = trnm_with_dopen[
            trnm_with_dopen['TRNDATE_DT'] >= trnm_with_dopen['DOPEN_DT']
        ]
        total_int_earned_sums = trnm_earned.groupby('ACC')['TRNINT_NUM'].sum().reset_index()
        total_int_earned_sums.rename(columns={'TRNINT_NUM': 'TOTAL_INTEREST_EARNED'}, inplace=True)
        
        discrepancy_df = pd.merge(
            discrepancy_df, total_int_earned_sums, on='ACC', how='left'
        )
        discrepancy_df['TOTAL_INTEREST_EARNED'] = discrepancy_df['TOTAL_INTEREST_EARNED'].fillna(0.0)


        # Calculate total_int_earned_in_year (from prev_year_end_date of selected year)
        trnm_in_year = df_trnm_combined[
            (df_trnm_combined['TRNDATE_DT'] > prev_year_end_date) &
            (df_trnm_combined['TRNDATE_DT'].dt.year == year)
        ]
        total_int_earned_in_year_sums = trnm_in_year.groupby('ACC')['TRNINT_NUM'].sum().reset_index()
        total_int_earned_in_year_sums.rename(columns={'TRNINT_NUM': f'TOTAL_INT_EARNED_IN_{year}'}, inplace=True)

        discrepancy_df = pd.merge(
            discrepancy_df, total_int_earned_in_year_sums, on='ACC', how='left'
        )
        discrepancy_df[f'TOTAL_INT_EARNED_IN_{year}'] = discrepancy_df[f'TOTAL_INT_EARNED_IN_{year}'].fillna(0.0)

    else:
        discrepancy_df['TOTAL_INTEREST_EARNED'] = 0.0
        discrepancy_df[f'TOTAL_INT_EARNED_IN_{year}'] = 0.0

    # Explicitly ensure columns are numeric (float) before calculations
    # This is a defensive measure to prevent type errors in case of unexpected data types
    discrepancy_df['INTRATE_NUM'] = pd.to_numeric(discrepancy_df['INTRATE_NUM'], errors='coerce').fillna(0.0).astype(float)
    discrepancy_df[f'TOTAL_INT_EARNED_IN_{year}'] = pd.to_numeric(discrepancy_df[f'TOTAL_INT_EARNED_IN_{year}'], errors='coerce').fillna(0.0).astype(float)
    discrepancy_df['CONFIG_INTEREST_RATE_DECIMAL'] = pd.to_numeric(discrepancy_df['CONFIG_INTEREST_RATE_DECIMAL'], errors='coerce').fillna(0.0).astype(float)

    # Calculate SHOULD_BE_INTEREST_IN_YEAR and ADJUSTMENT (vectorized)
    discrepancy_df[f'SHOULD_BE_INTEREST_IN_{year}'] = 0.0
    
    # Calculate should_be_interest_in_year only for valid INTRATE_NUM (actual SVACC rate)
    valid_actual_rate_mask = (discrepancy_df['INTRATE_NUM'] != 0) & pd.notna(discrepancy_df['INTRATE_NUM'])

    discrepancy_df.loc[valid_actual_rate_mask, f'SHOULD_BE_INTEREST_IN_{year}'] = (
        discrepancy_df.loc[valid_actual_rate_mask, f'TOTAL_INT_EARNED_IN_{year}'].astype(float) / # Explicitly cast to float
        (discrepancy_df.loc[valid_actual_rate_mask, 'INTRATE_NUM'].astype(float) / 100) # Divide INTRATE_NUM by 100 here
    ) * discrepancy_df.loc[valid_actual_rate_mask, 'CONFIG_INTEREST_RATE_DECIMAL'].astype(float) # Explicitly cast to float

    discrepancy_df['ADJUSTMENT_RAW'] = discrepancy_df[f'TOTAL_INT_EARNED_IN_{year}'] - discrepancy_df[f'SHOULD_BE_INTEREST_IN_{year}']

    # Format output DataFrame to desired report structure
    report_data = discrepancy_df.copy()
    report_data['BRANCH'] = branch_name
    report_data['CID'] = report_data['CID'].astype(str)
    report_data['ACCOUNT'] = report_data['ACC'].astype(str)
    report_data['BALANCE'] = report_data['BAL_NUM'].apply(format_currency_py)
    report_data['PRODUCT'] = report_data['ACCNAME'].astype(str)
    report_data['OPENED'] = report_data['DOPEN_DT'].dt.strftime('%m/%d/%Y')
    report_data['ACTUAL_INTEREST'] = report_data['INTRATE_NUM'].apply(lambda x: f"{x:.2f}%") # Use INTRATE_NUM directly as a percentage
    report_data['SHOULD_BE_INTEREST'] = report_data['CONFIG_INTEREST_RATE'].apply(lambda x: f"{x:.2f}%") # Use CONFIG_INTEREST_RATE directly as a percentage
    report_data['TOTAL_INTEREST_EARNED'] = report_data['TOTAL_INTEREST_EARNED'].apply(format_currency_py)
    report_data[f'TOTAL_INT_EARNED_IN_{year}'] = report_data[f'TOTAL_INT_EARNED_IN_{year}'].apply(format_currency_py)
    report_data[f'SHOULD_BE_INTEREST_IN_{year}'] = report_data[f'SHOULD_BE_INTEREST_IN_{year}'].apply(format_currency_py)
    report_data['ADJUSTMENT'] = report_data['ADJUSTMENT_RAW'].apply(format_currency_py)

    final_columns = [
        'BRANCH', 'CID', 'ACCOUNT', 'BALANCE', 'PRODUCT', 'OPENED',
        'ACTUAL_INTEREST', 'SHOULD_BE_INTEREST', 'TOTAL_INTEREST_EARNED',
        f'TOTAL_INT_EARNED_IN_{year}', f'SHOULD_BE_INTEREST_IN_{year}', 'ADJUSTMENT', 'ADJUSTMENT_RAW'
    ]
    report_data = report_data[final_columns].sort_values(by='ADJUSTMENT_RAW', ascending=False)

    return {"message": "Wrong Application of Interest Report generated successfully!", "data": report_data.to_dict(orient='records')}
