# svacc_win_process.py
import pandas as pd
import os
from datetime import datetime # Import datetime for timestamp
import re # Import regex for file pattern matching

# Define the fixed output directory (This will now be passed as output_folder)
# FIXED_OUTPUT_DIR = r"C:\xampp\htdocs\audit_tool\OPERATIONS\SVACC"

# MODIFIED: Adjusted function signature to accept output_folder, file_prefix, and lnhist_file in correct order
def process_svacc_win_data_web(input_dir, output_folder, file_prefix, lnhist_file=None):
    """
    Processes and combines savings data from multiple SVACC CSV files, performs CID lookup
    using LNHIST CSV (now optional upload), ACCNAME lookup using DEPOSIT CODE CSV (hardcoded path)
    and selected branch, formats data, and saves it to a single combined CSV file
    in the specified output_folder.
    Output filename uses the selected branch name (via file_prefix) and the latest DOPEN date.
    Existing files with the same branch name are overwritten.

    Args:
        input_dir (str): The directory containing SVACC CSV files.
        output_folder (str): The specific output directory (SVACC_BASE_DIR) where files should be saved.
        file_prefix (str): The 3-character prefix for the output filenames (e.g., "AGA").
        lnhist_file (werkzeug.datastructures.FileStorage, optional): The uploaded LNHIST CSV file for CID lookup.
    """
    # Use the passed output_folder directly
    branch_output_dir = output_folder
    os.makedirs(branch_output_dir, exist_ok=True) # Ensure the output directory exists

    # The sanitized branch name for filtering and folder name is derived from output_folder
    # For SVACC, the output_folder is SVACC_BASE_DIR, so we use the file_prefix for logging.
    # MODIFIED: Get the full normalized branch name from the output_folder path
    sanitized_branch_for_filename = os.path.basename(branch_output_dir) 

    print(f"Server Log (SVACC WIN): Starting savings data processing from {input_dir} for branch prefix '{file_prefix}'")

    # Define the required final headers for the output CSV
    required_final_headers = [
        "ACC", "TYPE", "GLCODE", "CID", "ACCNAME", "DOPEN", "DOLASTTRN",
        "BAL", "INTRATE", "MATDATE", "CUMINTPD", "CUMTAXW"
    ]

    # --- Hardcoded path for DEPOSIT CODE CSV file (LNHist is now an upload) ---
    DEPOSIT_CODE_HARDCODED_PATH = r"C:\xampp\htdocs\audit_tool\DEPOSIT CODE.csv"

    # --- Read LNHIST CSV for CID lookup (now from uploaded file) ---
    df_lnhist = pd.DataFrame()
    cid_map = {}
    if lnhist_file:
        # MODIFIED: Added a check to ensure lnhist_file is not a string (e.g., from a mis-passed file_prefix)
        if hasattr(lnhist_file, 'filename'):
            print(f"Server Log (SVACC WIN): Processing LNHIST file: {lnhist_file.filename}")
            try:
                # Read LNHIST with encoding fallback for robustness
                try:
                    df_lnhist = pd.read_csv(lnhist_file, encoding='utf-8')
                except UnicodeDecodeError:
                    df_lnhist = pd.read_csv(lnhist_file, encoding='latin1')
                
                # Explicitly convert ALL columns to string and fill NaNs
                df_lnhist = df_lnhist.astype(str).fillna('')

                # Ensure 'ACC', 'Chd', 'CID', and 'Type' columns exist in LNHIST for lookup
                if 'ACC' in df_lnhist.columns and 'Chd' in df_lnhist.columns and 'CID' in df_lnhist.columns and 'Type' in df_lnhist.columns:
                    df_lnhist_filtered = df_lnhist[df_lnhist['Type'].str.strip() == '10'].copy()

                    # Create lookup key: ACC formatted with Chd, then remove hyphens
                    def format_acc_chd_lnhist(row):
                        acc = row['ACC'].zfill(7)
                        chd = row['Chd']
                        return f"{acc[:2]}-{acc[2:]}-{chd}"

                    df_lnhist_filtered['lookup_key_cid'] = df_lnhist_filtered.apply(format_acc_chd_lnhist, axis=1).str.replace('-', '').str.strip()
                    cid_map = dict(zip(df_lnhist_filtered['lookup_key_cid'], df_lnhist_filtered['CID']))
                    print(f"Server Log (SVACC WIN): Successfully loaded CID map from {lnhist_file.filename} (Entries: {len(cid_map)})")
                else:
                    print("Server Log (SVACC WIN): LNHIST data insufficient for CID lookup (missing ACC, Chd, CID, or Type columns).")
            except Exception as e:
                print(f"Server Log (SVACC WIN): Error reading LNHIST file {lnhist_file.filename}: {e}. CID lookup will be skipped.")
        else:
            print("Server Log (SVACC WIN): LNHIST file provided was not a valid file object. CID lookup will be skipped.")
    else:
        print("Server Log (SVACC WIN): No LNHIST file provided. CID lookup will be skipped.")

    # --- Read DEPOSIT CODE.csv for ACCNAME lookup ---
    df_deposit_code = pd.DataFrame()
    deposit_code_map = {}
    if not os.path.exists(DEPOSIT_CODE_HARDCODED_PATH):
        print(f"Server Log (SVACC WIN): DEPOSIT CODE file not found at {DEPOSIT_CODE_HARDCODED_PATH}. ACCNAME lookup will be skipped.")
    else:
        try:
            # Read DEPOSIT CODE with encoding fallback for robustness
            try:
                df_deposit_code = pd.read_csv(DEPOSIT_CODE_HARDCODED_PATH, encoding='utf-8')
            except UnicodeDecodeError:
                df_deposit_code = pd.read_csv(DEPOSIT_CODE_HARDCODED_PATH, encoding='latin1')
            
            # Explicitly convert ALL columns to string and fill NaNs
            df_deposit_code = df_deposit_code.astype(str).fillna('')

            # Ensure 'TYPE' and 'PRODUCT' columns exist in DEPOSIT CODE.csv for lookup map creation
            if 'TYPE' in df_deposit_code.columns and 'PRODUCT' in df_deposit_code.columns:
                # Create lookup map using only 'TYPE' from DEPOSIT CODE.csv
                # Use .str.strip() for robustness after astype(str)
                df_deposit_code['TYPE_normalized'] = pd.to_numeric(df_deposit_code['TYPE'].str.strip(), errors='coerce').astype(float).astype(int).astype(str)
                deposit_code_map = dict(zip(df_deposit_code['TYPE_normalized'], df_deposit_code['PRODUCT']))
                print(f"Server Log (SVACC WIN): Using DEPOSIT CODE file for ACCNAME lookup: {DEPOSIT_CODE_HARDCODED_PATH}")
            else:
                print("Server Log (SVACC WIN): DEPOSIT CODE data insufficient for ACCNAME lookup (missing TYPE or PRODUCT columns).")
        except Exception as e:
            print(f"Server Log (SVACC WIN): Error reading DEPOSIT CODE file {DEPOSIT_CODE_HARDCODED_PATH}: {e}. ACCNAME lookup will be skipped.")
    
    # --- Process SVACC CSV files ---
    all_svacc_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.csv')]
    if not all_svacc_files:
        raise Exception(f"No SVACC CSV files found in {input_dir}.")

    combined_df_list = []

    for filename in all_svacc_files:
        filepath = os.path.join(input_dir, filename)
        print(f"Server Log (SVACC WIN): Processing {filepath}...")
        try:
            # Attempt to read CSV with utf-8, fallback to latin1 if UnicodeDecodeError occurs
            try:
                df_svacc = pd.read_csv(filepath, dtype=str, encoding='utf-8') # Read as string to preserve leading zeros
            except UnicodeDecodeError:
                df_svacc = pd.read_csv(filepath, dtype=str, encoding='latin1') # Fallback to latin1
        except Exception as e:
            print(f"Server Log (SVACC WIN): Error reading {filepath}: {e}. Skipping.")
            continue

        # Check for essential columns before proceeding
        if 'Acc' not in df_svacc.columns or 'Chd' not in df_svacc.columns:
            print(f"Server Log (SVACC WIN): Skipping {filename}: 'Acc' or 'Chd' columns not found for ACC/CID lookup.")
            continue
        
        # CID Lookup and ACC Formatting
        # Create lookup key for SVACC data consistent with LNHIST/LNACC WIN logic
        def format_acc_chd_svacc(row):
            acc_part = str(row['Acc']).strip().zfill(7)
            chd_part = str(row['Chd']).strip()
            return f"{acc_part[:2]}-{acc_part[2:]}-{chd_part}"

        df_svacc['ACC'] = df_svacc.apply(format_acc_chd_svacc, axis=1)
        
        # Perform CID Lookup using the new consistent key format
        if cid_map:
            # Create lookup key from SVACC ACC: remove hyphens
            df_svacc['lookup_key_cid_svacc'] = df_svacc['ACC'].astype(str).str.replace('-', '').str.strip()
            df_svacc['CID'] = df_svacc['lookup_key_cid_svacc'].map(cid_map).fillna('')
            df_svacc.drop(columns=['lookup_key_cid_svacc'], inplace=True) # Clean up temp column
            print(f"Server Log (SVACC WIN): CID lookup applied for {filename}.")
        else:
            df_svacc['CID'] = '' # Initialize CID as empty if no map or error in map loading
            print(f"Server Log (SVACC WIN): CID lookup skipped for {filename} (no CID map available).")


        # ACCNAME Lookup Logic
        df_svacc['ACCNAME'] = '' # Initialize ACCNAME column
        # Ensure 'PrType' column exists in the SVACC file for lookup
        if 'PrType' in df_svacc.columns and deposit_code_map:
            # FIX: Create lookup key from SVACC: only 'PrType' (normalized)
            svacc_type_normalized = pd.to_numeric(df_svacc['PrType'].astype(str).str.strip(), errors='coerce').astype(float).astype(int).astype(str) # Use 'PrType' from SVACC
            df_svacc['ACCNAME'] = svacc_type_normalized.map(deposit_code_map).fillna('') # Map directly using normalized type
        else:
            print(f"Server Log (SVACC WIN): ACCNAME lookup skipped for {filename} (missing 'PrType' in SVACC or DEPOSIT CODE map is empty).")

        # Header Mapping for Savings Data
        header_mapping = {
            'PrType': 'TYPE',
            'GLCode': 'GLCODE',
            'OpenDate': 'DOPEN',
            'LastTrnDate': 'DOLASTTRN',
            'BalAmt': 'BAL',
            'IntRate': 'INTRATE',
            'MatDate': 'MATDATE',
            'CumIntPdAmt': 'CUMINTPD',
            'CumTaxWAmt': 'CUMTAXW',
        }

        columns_to_select = ['ACC', 'CID', 'ACCNAME']
        for original_col, new_col in header_mapping.items():
            if original_col in df_svacc.columns:
                columns_to_select.append(original_col)
            else:
                print(f"Server Log (SVACC WIN): Warning: Column '{original_col}' not found in {filename}. It will be missing in the output.")

        df_processed = df_svacc[columns_to_select].rename(columns=header_mapping)

        # Data Type Formatting
        date_columns = ['DOPEN', 'DOLASTTRN', 'MATDATE']
        for col in date_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce').dt.strftime('%m/%d/%Y').fillna('')
            else:
                if col in header_mapping.values():
                    df_processed[col] = ''

        numeric_columns = ['BAL', 'CUMINTPD', 'CUMTAXW']
        for col in numeric_columns: # Corrected: changed 'numeric_processed.columns' to 'numeric_columns'
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
                df_processed[col] = df_processed[col].apply(lambda x: f"{x / 100:,.2f}" if pd.notna(x) else '')
            else:
                if col in header_mapping.values():
                    df_processed[col] = ''

        if 'INTRATE' in df_processed.columns:
            df_processed['INTRATE'] = pd.to_numeric(df_processed['INTRATE'], errors='coerce')
            df_processed['INTRATE'] = df_processed['INTRATE'].apply(lambda x: f"{x / 100:.2%}" if pd.notna(x) else '')
        else:
            if 'IntRate' in header_mapping:
                df_processed['INTRATE'] = ''

        combined_df_list.append(df_processed)

    if combined_df_list:
        final_combined_df = pd.concat(combined_df_list, ignore_index=True)
        
        for col in required_final_headers:
            if col not in final_combined_df.columns:
                final_combined_df[col] = ''
        
        final_combined_df = final_combined_df[required_final_headers]

        # Convert 'DOPEN' to datetime objects for finding the latest date
        # Ensure 'DOPEN' column exists before attempting conversion
        if 'DOPEN' in final_combined_df.columns:
            final_combined_df['DOPEN_DT'] = pd.to_datetime(final_combined_df['DOPEN'], format='%m/%d/%Y', errors='coerce')
        else:
            # If DOPEN column is missing, create DOPEN_DT as all NaT
            final_combined_df['DOPEN_DT'] = pd.Series([pd.NaT] * len(final_combined_df), index=final_combined_df.index)
            print("Server Log (SVACC WIN): Warning: 'DOPEN' column not found in combined data. Latest date will be 'UNKNOWN_DATE'.")

        latest_dopen_date_str = "UNKNOWN_DATE"
        if not final_combined_df['DOPEN_DT'].dropna().empty:
            latest_dopen = final_combined_df['DOPEN_DT'].max()
            latest_dopen_date_str = latest_dopen.strftime('%m-%d-%Y')
        else:
            # If DOPEN_DT is still all NaT, set latest_dopen_date_str to '-'
            latest_dopen_date_str = "-"

        # MODIFIED: Define the output filename based on the file_prefix and latest DOPEN date
        # Format: BRANCH_PREFIX - MM-DD-YYYY.csv
        new_output_filename = f"{file_prefix} - {latest_dopen_date_str}.csv"
        # MODIFIED: Use branch_output_dir (which is SVACC_BASE_DIR) for the path
        new_output_filepath = os.path.join(branch_output_dir, new_output_filename)

        # Find and delete existing files for the same branch, regardless of date in their name
        # MODIFIED: Regex to match files starting with the file_prefix and ending with .csv
        branch_file_pattern = re.compile(rf'^{re.escape(file_prefix)} - \d{{2}}-\d{{2}}-\d{{4}}\.csv$', re.IGNORECASE)
        
        for existing_file in os.listdir(branch_output_dir): # Use branch_output_dir here
            if branch_file_pattern.match(existing_file):
                existing_filepath = os.path.join(branch_output_dir, existing_file)
                try:
                    os.remove(existing_filepath)
                    print(f"Server Log (SVACC WIN): Deleted old file: {existing_filepath}")
                except OSError as e:
                    print(f"Server Log (SVACC WIN): Error deleting old file {existing_filepath}: {e}")

        # Removed backup_existing function and its call to ensure direct overwrite
        # Drop the temporary datetime column before saving
        if 'DOPEN_DT' in final_combined_df.columns: # Added check here
            final_combined_df.drop(columns=['DOPEN_DT'], inplace=True) 
        final_combined_df.to_csv(new_output_filepath, index=False, encoding='utf-8-sig')
        print(f"Server Log (SVACC WIN): Successfully combined and formatted savings data into {new_output_filepath}")
    else:
        raise Exception("No data was processed or combined for SVACC WIN.")

    print("\nServer Log (SVACC WIN): Processing complete!")
    return {"message": f"SVACC WIN processing completed. Output saved to {new_output_filepath}", "output_path": new_output_filepath}

