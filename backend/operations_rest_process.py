# audit_tool/backend/operations_rest_process.py
import pandas as pd
import os
from datetime import datetime
import traceback

# Import common utility functions from db_common.py
# Removed get_latest_data_for_month as its logic will be integrated directly
from backend.db_common import read_csv_to_dataframe, AGING_BASE_DIR, format_currency_py, REST_LN_CSV_PATH # Import REST_LN_CSV_PATH directly

def get_restructured_loan_data_logic(report_date_str):
    """
    Processes restructured loan data, joins with aging data, and calculates summaries.

    Args:
        report_date_str (str): The date for the report in YYYY-MM-DD format.

    Returns:
        dict: A dictionary containing 'summary' and 'details' data.
              Returns None or raises an exception if data cannot be processed.
    """
    # Initialize summary with default zero values to ensure consistent structure
    summary = {
        "current": {"REMEDIAL": 0.0, "REGULAR": 0.0, "BRL": 0.0, "TOTAL": 0.0},
        "past_due": {"REMEDIAL": 0.0, "REGULAR": 0.0, "BRL": 0.0, "TOTAL": 0.0}
    }
    details_list = []
    message = "Restructured Loans report generated successfully."

    try:
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d')

        print(f"Server Log (Restructured Loan): Generating report for date: {report_date_str}")

        # 1. Load Restructured Loans (rest_ln.csv)
        rest_ln_df = read_csv_to_dataframe(REST_LN_CSV_PATH)
        if rest_ln_df.empty:
            print("Server Log (Restructured Loan): rest_ln.csv is empty or not found.")
            message = "No restructured loan data found in rest_ln.csv."
            return {"summary": summary, "details": details_list, "message": message}
        print(f"DEBUG: rest_ln_df head:\n{rest_ln_df.head()}")
        print(f"DEBUG: rest_ln_df columns: {rest_ln_df.columns.tolist()}")


        # Normalize column names
        rest_ln_df.columns = rest_ln_df.columns.str.strip().str.upper()
        required_rest_ln_cols = ['BRANCH', 'CID', 'NAME', 'ACCOUNT', 'TYPE']
        if not all(col in rest_ln_df.columns for col in required_rest_ln_cols):
            print(f"Server Log (Restructured Loan): Missing required columns in rest_ln.csv. Expected: {required_rest_ln_cols} but got {rest_ln_df.columns.tolist()}.")
            message = "Restructured loan data file (rest_ln.csv) is malformed."
            return {"summary": summary, "details": details_list, "message": message}

        # Ensure types are consistent for merging
        rest_ln_df['BRANCH'] = rest_ln_df['BRANCH'].astype(str).str.strip().str.upper()
        rest_ln_df['ACCOUNT'] = rest_ln_df['ACCOUNT'].astype(str).str.strip()
        rest_ln_df['CID'] = rest_ln_df['CID'].astype(str).str.strip()
        rest_ln_df['TYPE'] = rest_ln_df['TYPE'].astype(str).str.strip() # Used for Remedial/Regular/BRL
        print(f"DEBUG: rest_ln_df after normalization:\n{rest_ln_df.head()}")


        # 2. Load and Combine Aging Data
        all_aging_data = []
        # Iterate through subfolders (branches) in AGING_BASE_DIR
        print(f"DEBUG: Scanning for aging data in: {AGING_BASE_DIR}")
        for branch_folder in os.listdir(AGING_BASE_DIR):
            branch_path = os.path.join(AGING_BASE_DIR, branch_folder)
            if os.path.isdir(branch_path):
                # Look for CSV files within each branch folder
                for aging_file in os.listdir(branch_path):
                    if aging_file.lower().endswith('.csv'):
                        aging_file_path = os.path.join(branch_path, aging_file)
                        try:
                            # Read CSV without specific date_parser initially
                            # Let pandas infer or read as object, then convert explicitly
                            aging_df = pd.read_csv(aging_file_path)
                            if not aging_df.empty:
                                all_aging_data.append(aging_df)
                        except Exception as e:
                            print(f"Server Log (Restructured Loan): Error reading aging file {aging_file_path}: {e}")

        if not all_aging_data:
            print("Server Log (Restructured Loan): No aging data found in OPERATIONS\\AGING subfolders.")
            message = "No aging data available for processing. Ensure files are in OPERATIONS\\AGING\\<BRANCH_NAME>."
            return {"summary": summary, "details": details_list, "message": message}

        combined_aging_df = pd.concat(all_aging_data, ignore_index=True)
        
        # Normalize aging column names
        combined_aging_df.columns = combined_aging_df.columns.str.strip().str.upper()
        
        # --- CRITICAL FIX: Rename 'LOAN ACCT.' to 'ACCOUNT' in aging data ---
        if 'LOAN ACCT.' in combined_aging_df.columns:
            combined_aging_df.rename(columns={'LOAN ACCT.': 'ACCOUNT'}, inplace=True)
            print("DEBUG: Renamed 'LOAN ACCT.' to 'ACCOUNT' in combined_aging_df.")
        # --- END CRITICAL FIX ---

        # --- CRITICAL FIX: Adjust required_aging_cols and handle PRINCIPAL/BALANCE ---
        # The aging data has 'PRINCIPAL' and 'BALANCE' separately, not 'PRINCIPAL BALANCE'
        required_aging_cols = ['BRANCH', 'DATE', 'ACCOUNT', 'BALANCE', 'AGING', 'PRINCIPAL', 'DISBDATE', 'DUE DATE']
        if not all(col in combined_aging_df.columns for col in required_aging_cols):
            print(f"Server Log (Restructured Loan): Missing required columns in aging data. Expected: {required_aging_cols} but got {combined_aging_df.columns.tolist()}.")
            message = "Aging data files are malformed. Missing critical columns."
            return {"summary": summary, "details": details_list, "message": message}

        print(f"DEBUG: combined_aging_df head (after renaming):\n{combined_aging_df.head()}")
        print(f"DEBUG: combined_aging_df columns (after renaming): {combined_aging_df.columns.tolist()}")

        # Convert 'DATE' column to datetime objects using a robust strategy
        # Rely on inference for mixed formats, coercing errors
        combined_aging_df['DATE'] = pd.to_datetime(
            combined_aging_df['DATE'], 
            errors='coerce', 
            infer_datetime_format=True, # Rely on inference for mixed formats
            dayfirst=False,             # Prefer MM/DD/YYYY if ambiguous
            yearfirst=False             # Prefer MM/DD/YYYY if ambiguous
        )
        combined_aging_df.dropna(subset=['DATE'], inplace=True) # Drop rows where date conversion failed
        
        # --- ADDED DEBUG: Inspect combined_aging_df after date parsing and dropna ---
        print(f"DEBUG: combined_aging_df after date parsing and dropna (head):\n{combined_aging_df.head()}")
        print(f"DEBUG: combined_aging_df after date parsing and dropna (shape): {combined_aging_df.shape}")
        print(f"DEBUG: combined_aging_df['DATE'] dtypes: {combined_aging_df['DATE'].dtype}")
        print(f"DEBUG: Years found in combined_aging_df['DATE'] (after dropna): {combined_aging_df['DATE'].dt.year.value_counts().index.tolist()}")
        print(f"DEBUG: Months found in combined_aging_df['DATE'] (after dropna): {combined_aging_df['DATE'].dt.month.value_counts().index.tolist()}")
        # --- END ADDED DEBUG ---

        # --- Filter combined_aging_df by target month and year using YYYYMM integer ---
        # Convert to YYYYMM integer for robust filtering
        if not combined_aging_df.empty:
            combined_aging_df['DATE_YYYYMM'] = combined_aging_df['DATE'].dt.year * 100 + combined_aging_df['DATE'].dt.month
        else:
            # If combined_aging_df is empty, ensure 'DATE_YYYYMM' column exists for consistency
            combined_aging_df['DATE_YYYYMM'] = pd.Series(dtype='int64') 

        target_yyyymm = report_date.year * 100 + report_date.month
        print(f"DEBUG: Filtering by YYYYMM: Target={target_yyyymm}, Sample DF_YYYYMM: {combined_aging_df['DATE_YYYYMM'].head().tolist()}")


        initial_filtered_aging_df = combined_aging_df[
            combined_aging_df['DATE_YYYYMM'] == target_yyyymm
        ].copy()
        
        print(f"DEBUG: initial_filtered_aging_df shape (after YYYYMM filter): {initial_filtered_aging_df.shape}")
        if initial_filtered_aging_df.empty:
            print(f"Server Log (Restructured Loan): initial_filtered_aging_df is empty after YYYYMM filter for {report_date_str}.")
            message = "No aging data found for the selected month and year in the aging files."
            return {"summary": summary, "details": details_list, "message": message}
        print(f"DEBUG: initial_filtered_aging_df head:\n{initial_filtered_aging_df.head()}")
        # --- END NEW FILTER ---


        # Ensure types are consistent for merging
        # These operations should now be on initial_filtered_aging_df
        initial_filtered_aging_df['BRANCH'] = initial_filtered_aging_df['BRANCH'].astype(str).str.strip().str.upper()
        initial_filtered_aging_df['ACCOUNT'] = initial_filtered_aging_df['ACCOUNT'].astype(str).str.strip()
        initial_filtered_aging_df['AGING'] = initial_filtered_aging_df['AGING'].astype(str).str.strip().str.upper()

        # Get the latest aging data for the report month/year for each account
        # Logic from get_latest_data_for_month integrated directly here
        print(f"DEBUG: Getting latest data for month from initial_filtered_aging_df (shape: {initial_filtered_aging_df.shape})")
        
        if initial_filtered_aging_df.empty:
            latest_aging_data_for_month = pd.DataFrame()
        else:
            initial_filtered_aging_df.sort_values(by='DATE', ascending=True, inplace=True)
            latest_aging_data_for_month = initial_filtered_aging_df.drop_duplicates(subset=['ACCOUNT'], keep='last').copy()

        if latest_aging_data_for_month.empty:
            print(f"Server Log (Restructured Loan): No latest aging data found for {report_date_str} after final deduplication.")
            message = "No relevant aging data found for the selected report date in the aging files (after deduplication)."
            return {"summary": summary, "details": details_list, "message": message}
        print(f"DEBUG: latest_aging_data_for_month head:\n{latest_aging_data_for_month.head()}")
        print(f"DEBUG: latest_aging_data_for_month shape: {latest_aging_data_for_month.shape}")


        # 3. Merge Restructured Loans with Latest Aging Data
        # Merge on 'BRANCH' and 'ACCOUNT'
        merged_df = pd.merge(
            rest_ln_df,
            latest_aging_data_for_month,
            on=['BRANCH', 'ACCOUNT'],
            how='left', # Use left merge to keep all restructured loans
            suffixes=('_REST', '_AGING')
        )
        print(f"DEBUG: merged_df head:\n{merged_df.head()}")
        print(f"DEBUG: merged_df shape: {merged_df.shape}")
        print(f"DEBUG: Merged DF columns for summary: {merged_df.columns.tolist()}")


        # Handle cases where a restructured loan might not have a matching aging record for the date
        # Use BALANCE_AGING for summary calculations
        # CRITICAL FIX: Access 'BALANCE' and 'PRINCIPAL' directly from merged_df as suffixes are not applied if no conflict
        merged_df['BALANCE_FOR_SUMMARY'] = pd.to_numeric(merged_df['BALANCE'], errors='coerce').fillna(0) 
        # Calculate 'PRINCIPAL BALANCE' for the details table by summing 'PRINCIPAL' and 'BALANCE_FOR_SUMMARY'
        merged_df['PRINCIPAL BALANCE_CALCULATED'] = pd.to_numeric(merged_df['PRINCIPAL'], errors='coerce').fillna(0) + merged_df['BALANCE_FOR_SUMMARY']

        # Convert date columns to MM/DD/YYYY format for output
        # Use the original date columns from merged_df (which came from aging)
        merged_df['DISBDATE'] = pd.to_datetime(merged_df['DISBDATE'], errors='coerce').dt.strftime('%m/%d/%Y').fillna('')
        merged_df['DUE DATE'] = pd.to_datetime(merged_df['DUE DATE'], errors='coerce').dt.strftime('%m/%d/%Y').fillna('')
        
        # Classify loan types for summary
        def classify_loan_type(loan_type_str):
            if pd.isna(loan_type_str):
                return 'OTHER'
            loan_type_str = str(loan_type_str).upper()
            if 'REMEDIAL' in loan_type_str:
                return 'REMEDIAL'
            elif 'REGULAR' in loan_type_str:
                return 'REGULAR'
            elif 'BUSINESS RECOVERY LOAN' in loan_type_str or 'BRL' in loan_type_str:
                return 'BRL'
            return 'OTHER' # Fallback for unclassified types

        merged_df['CLASSIFIED_TYPE'] = merged_df['TYPE'].apply(classify_loan_type) # FIX: Use 'TYPE' not 'TYPE_REST'


        # 4. Calculate Summary Balances
        # Initialize summary (already done at the top to ensure consistent structure)
        
        print(f"DEBUG: Sample AGING values in merged_df: {merged_df['AGING'].value_counts()}") # Access 'AGING' directly

        for index, row in merged_df.iterrows():
            balance = row['BALANCE_FOR_SUMMARY'] # Use the new column for summary calculation
            classified_type = row['CLASSIFIED_TYPE']
            aging_status = row['AGING'] # Access 'AGING' directly

            if pd.isna(aging_status): # If no aging data found, treat as unknown/skip from summary
                print(f"DEBUG: Skipping row due to NaN aging_status for account {row['ACCOUNT']}.")
                continue

            # Debugging individual row processing
            # print(f"DEBUG: Processing row for summary: Account={row['ACCOUNT']}, Balance={balance}, Aging={aging_status}, Type={classified_type}")


            if aging_status.upper() == 'NOT YET DUE':
                # Current Accounts
                if classified_type in summary['current']:
                    summary['current'][classified_type] += balance
                summary['current']['TOTAL'] += balance
            else:
                # Past Due Loans
                if classified_type in summary['past_due']:
                    summary['past_due'][classified_type] += balance
                summary['past_due']['TOTAL'] += balance
        
        # 5. Prepare Details Table Data
        details_cols = [
            'BRANCH_REST', 'CID_REST', 'NAME_REST', 'ACCOUNT', 'TYPE', # FIX: Use 'TYPE' not 'TYPE_REST'
            'PRINCIPAL', 'BALANCE', 'DISBDATE', 'DUE DATE' # Use separate PRINCIPAL and BALANCE
        ]
        
        # Filter merged_df to only include columns that actually exist before selecting
        existing_details_cols = [col for col in details_cols if col in merged_df.columns]
        final_details_df = merged_df[existing_details_cols].copy()

        # Rename columns for final output (only if necessary)
        final_details_df.rename(columns={
            'BRANCH_REST': 'BRANCH',
            'CID_REST': 'CID',
            'NAME_REST': 'NAME',
            # No need to rename TYPE, PRINCIPAL or BALANCE if they are already correctly named
        }, inplace=True)

        # Format 'PRINCIPAL' and 'BALANCE' for display in the details table
        if 'PRINCIPAL' in final_details_df.columns:
            final_details_df['PRINCIPAL'] = final_details_df['PRINCIPAL'].apply(format_currency_py)
        if 'BALANCE' in final_details_df.columns:
            final_details_df['BALANCE'] = final_details_df['BALANCE'].apply(format_currency_py)
        
        # Convert DataFrame to list of dictionaries for JSON response
        details_list = final_details_df.to_dict(orient='records')

        print(f"DEBUG: Final Summary before return:\n{summary}")
        print(f"DEBUG: Final Details count: {len(details_list)}")

        print("Server Log (Restructured Loan): Report generation complete.")
        return {
            "summary": summary,
            "details": details_list,
            "message": message # Use the default success message or updated info message
        }

    except Exception as e:
        print(f"Server Log (Restructured Loan): Error processing restructured loan data: {e}")
        traceback.print_exc()
        # Ensure summary and details are always returned in the expected format even on error
        return {"summary": summary, "details": details_list, "message": f"Error generating report: {str(e)}"}
