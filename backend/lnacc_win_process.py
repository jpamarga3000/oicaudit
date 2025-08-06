# lnacc_win_process.py
import pandas as pd
import os
from datetime import datetime # Import datetime for timestamp
import re # Import regex for file pattern matching

# Define the fixed output directory (This will now be passed as output_folder)
# FIXED_OUTPUT_DIR = r"C:\xampp\htdocs\audit_tool\OPERATIONS\LNACC" # Using raw string for path

# MODIFIED: Adjusted function signature to accept output_folder and file_prefix
def process_lnacc_win_data_web(input_dir, output_folder, file_prefix, cid_ref_file=None):
    """
    Processes and combines loan data from multiple LNACC CSV files, performs CID lookup
    using an optional CID reference CSV, formats data, and saves it to a single combined CSV file
    in the specified output_folder.
    Output filename uses the selected branch name (via file_prefix) and the latest DOPEN date.
    Existing files with the same branch name are overwritten.

    Args:
        input_dir (str): The directory containing LNACC CSV files.
        output_folder (str): The specific output directory (branch-specific) where files should be saved.
        file_prefix (str): The 3-character prefix for the output filenames (e.g., "ELS").
        cid_ref_file (werkzeug.datastructures.FileStorage, optional): The uploaded CID reference CSV file.
    """
    # Use the passed output_folder directly
    branch_output_dir = output_folder
    os.makedirs(branch_output_dir, exist_ok=True) # Ensure the output directory exists

    # The sanitized branch name for filtering and folder name is derived from output_folder
    sanitized_branch = os.path.basename(branch_output_dir)

    print(f"Server Log (LNACC WIN): Starting loan data processing from {input_dir} for branch '{sanitized_branch}'")

    # Define the required final headers for the output CSV
    required_final_headers = [
        "ACC", "CID", "GLCODE", "LOANID", "DOPEN", "DOFIRSTI", "DOLASTTRN",
        "BAL", "INTRATE", "CUMINTPD", "MATDATE", "PRINCIPAL", "CUMPENPD",
        "DISBDATE", "INTBAL", "PENBAL"
    ]

    cid_map = {}
    if cid_ref_file:
        print(f"Server Log (LNACC WIN): Processing CID reference file: {cid_ref_file.filename}")
        try:
            # Read the CID reference CSV without forcing dtype initially
            df_cid_ref = pd.read_csv(cid_ref_file)
            # Explicitly convert ALL columns to string after reading and fill NaNs with empty strings.
            df_cid_ref = df_cid_ref.astype(str).fillna('')

            # Ensure required columns exist in CID reference file after type handling
            if 'ACC' in df_cid_ref.columns and 'Chd' in df_cid_ref.columns and 'CID' in df_cid_ref.columns and 'Type' in df_cid_ref.columns:
                df_cid_ref_filtered = df_cid_ref[df_cid_ref['Type'].str.strip() == '10'].copy()

                # Create lookup key: ACC formatted with Chd, then remove hyphens
                def format_acc_chd_ref(row):
                    # Values are already guaranteed to be strings by the explicit astype(str).fillna('') above
                    acc = row['ACC'].zfill(7)
                    chd = row['Chd']
                    return f"{acc[:2]}-{acc[2:]}-{chd}"

                # The result of apply will be a Series of strings, so .str accessor is safe
                df_cid_ref_filtered['lookup_key_cid'] = df_cid_ref_filtered.apply(format_acc_chd_ref, axis=1).str.replace('-', '').str.strip()
                
                # Create the CID lookup map
                cid_map = dict(zip(df_cid_ref_filtered['lookup_key_cid'], df_cid_ref_filtered['CID']))
                print(f"Server Log (LNACC WIN): Successfully loaded CID map from {cid_ref_file.filename} (Entries: {len(cid_map)})")
            else:
                print("Server Log (LNACC WIN): CID reference file missing essential columns ('ACC', 'CID', 'Type', or 'Chd') after type processing. CID lookup will be skipped.")
        except Exception as e:
            print(f"Server Log (LNACC WIN): Error reading CID reference file {cid_ref_file.filename}: {e}. CID lookup will be skipped.")

    # --- Process LNACC CSV files ---
    all_lnacc_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.csv')]
    if not all_lnacc_files:
        raise Exception(f"No LNACC CSV files found in {input_dir}.")

    combined_df_list = []
    
    for filename in all_lnacc_files:
        filepath = os.path.join(input_dir, filename)
        print(f"Server Log (LNACC WIN): Processing {filepath}...")
        try:
            df_lnacc = pd.read_csv(filepath, dtype=str) # Read as string to preserve leading zeros
        except Exception as e:
            print(f"Server Log (LNACC WIN): Error reading {filepath}: {e}. Skipping.")
            continue

        # Check for essential columns before proceeding
        if 'Acc' not in df_lnacc.columns or 'Chd' not in df_lnacc.columns:
            print(f"Server Log (LNACC WIN): Skipping {filename}: 'Acc' or 'Chd' columns not found for ACC/CID lookup.")
            continue
        
        # ACC Formatting: xx-xxxxx-x
        def format_acc_chd(row):
            acc = str(row['Acc']).zfill(7) # Pad with leading zeros to 7 digits
            chd = str(row['Chd'])
            return f"{acc[:2]}-{acc[2:]}-{chd}"

        df_lnacc['ACC'] = df_lnacc.apply(format_acc_chd, axis=1)

        # Perform CID Lookup
        if cid_map:
            # Create lookup key from LNACC ACC: remove hyphens
            df_lnacc['lookup_key_lnacc'] = df_lnacc['ACC'].astype(str).str.replace('-', '').str.strip()
            df_lnacc['CID'] = df_lnacc['lookup_key_lnacc'].map(cid_map).fillna('') # Fill NaN with empty string if no match
            df_lnacc.drop(columns=['lookup_key_lnacc'], inplace=True) # Clean up temp column
            print(f"Server Log (LNACC WIN): CID lookup applied for {filename}.")
        else:
            df_lnacc['CID'] = '' # Initialize CID as empty if no map or error in map loading
            print(f"Server Log (LNACC WIN): CID lookup skipped for {filename} (no CID map available).")


        # Header Mapping for other columns
        # Make sure these columns exist in your input CSVs
        header_mapping = {
            'GLCode': 'GLCODE',
            'LNCode1': 'LOANID',
            'OpenDate': 'DOPEN',
            'FirstPriDueDate': 'DOFIRSTI',
            'LastTrnDate': 'DOLASTTRN',
            'BalAmt': 'BAL',
            'IntRate': 'INTRATE',
            'CumIntPdAmt': 'CUMINTPD',
            'MatDate': 'MATDATE',
            'PrincipalAmt': 'PRINCIPAL',
            'CumPenPdAmt': 'CUMPENPD',
            'IntBalAmt': 'INTBAL',
            'PenBalAmt': 'PENBAL',
        }

        columns_to_select = ['ACC', 'CID'] # Always include ACC and CID
        for original_col, new_col in header_mapping.items():
            if original_col in df_lnacc.columns:
                columns_to_select.append(original_col)
            else:
                print(f"Server Log (LNACC WIN): Warning: Column '{original_col}' not found in {filename}. It will be missing in the output.")

        df_processed = df_lnacc[columns_to_select].rename(columns=header_mapping)

        # Handle 'DISBDATE' separately (it's often 'OpenDate')
        if 'OpenDate' in df_lnacc.columns:
            df_processed['DISBDATE'] = df_lnacc['OpenDate']
        else:
            df_processed['DISBDATE'] = pd.NA

        # Data Type Formatting

        # Dates: mm/dd/yyyy
        date_columns = ['DOPEN', 'DOFIRSTI', 'DOLASTTRN', 'DISBDATE', 'MATDATE']
        for col in date_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce').dt.strftime('%m/%d/%Y').fillna('')
            else:
                if col in header_mapping.values():
                    df_processed[col] = ''

        # Numbers: comma and 2 decimal points, divide by 100
        numeric_columns = ['BAL', 'PRINCIPAL', 'CUMPENPD', 'CUMINTPD', 'INTBAL', 'PENBAL']
        for col in numeric_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
                df_processed[col] = df_processed[col].apply(lambda x: f"{x / 100:,.2f}" if pd.notna(x) else '')
            else:
                if col in header_mapping.values():
                    df_processed[col] = ''

        # INTRATE: multiply by 100 and add %
        if 'INTRATE' in df_processed.columns:
            df_processed['INTRATE'] = pd.to_numeric(df_processed['INTRATE'], errors='coerce')
            # FIX: If the raw value is like 21 (for 21%), then divide by 100 before formatting as percentage.
            # If the raw value is like 0.21 (for 21%), then just format as percentage.
            # Based on the 2100.00% output, it implies the raw value is 21, and then multiplied by 100.
            # So, we need to divide by 100 to get the correct percentage.
            df_processed['INTRATE'] = df_processed['INTRATE'].apply(lambda x: f"{x / 100:.2%}" if pd.notna(x) else '')
        else:
            if 'IntRate' in header_mapping:
                df_processed['INTRATE'] = ''

        combined_df_list.append(df_processed)

    if combined_df_list:
        final_combined_df = pd.concat(combined_df_list, ignore_index=True)
        
        # Ensure all required final headers are present, even if some were missing in source files
        # Reorder columns to match the requested header order
        final_combined_df = final_combined_df.reindex(columns=required_final_headers, fill_value='')

        # Convert 'DOPEN' to datetime objects for finding the latest date
        final_combined_df['DOPEN_DT'] = pd.to_datetime(final_combined_df['DOPEN'], format='%m/%d/%Y', errors='coerce')
        
        latest_dopen_date_str = "UNKNOWN_DATE"
        if not final_combined_df['DOPEN_DT'].dropna().empty:
            latest_dopen = final_combined_df['DOPEN_DT'].max()
            latest_dopen_date_str = latest_dopen.strftime('%m-%d-%Y')

        # MODIFIED: Define the output filename based on the file_prefix and latest DOPEN date
        # Format: BRANCH_PREFIX - MM-DD-YYYY.csv
        new_output_filename = f"{file_prefix} - {latest_dopen_date_str}.csv"
        new_output_filepath = os.path.join(branch_output_dir, new_output_filename)

        # Find and delete existing files for the same branch, regardless of date in their name
        # MODIFIED: Regex to match files starting with the file_prefix and ending with .csv
        branch_file_pattern = re.compile(rf'^{re.escape(file_prefix)} - \d{{2}}-\d{{2}}-\d{{4}}\.csv$', re.IGNORECASE)
        
        for existing_file in os.listdir(branch_output_dir):
            if branch_file_pattern.match(existing_file):
                existing_filepath = os.path.join(branch_output_dir, existing_file)
                try:
                    os.remove(existing_filepath)
                    print(f"Server Log (LNACC WIN): Deleted old file: {existing_filepath}")
                except OSError as e:
                    print(f"Server Log (LNACC WIN): Error deleting old file {existing_filepath}: {e}")

        # Removed backup_existing function and its call to ensure direct overwrite
        # Drop the temporary datetime column before saving
        final_combined_df.drop(columns=['DOPEN_DT'], inplace=True) 
        final_combined_df.to_csv(new_output_filepath, index=False, encoding='utf-8-sig')
        print(f"Server Log (LNACC WIN): Successfully combined and formatted data into {new_output_filepath}")
    else:
        raise Exception("No data was processed or combined for LNACC WIN.")

    print("\nServer Log (LNACC WIN): Processing complete!")
    return {"message": f"LNACC WIN processing completed. Output saved to {new_output_filepath}", "output_path": new_output_filepath}
