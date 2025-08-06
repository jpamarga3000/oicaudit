# win_process.py
import os
import pandas as pd
from datetime import datetime, timedelta
import re # Import regex module
import io # For in-memory file size estimation
import csv # For quoting in CSV writes

# Define the fixed base output directory for TRNM WIN
FIXED_BASE_OUTPUT_DIR = r"C:\\xampp\\htdocs\\audit_tool\\OPERATIONS\\TRNM"

# Constants for categories
LOAN_CATEGORIES_LIST = ['40-45', '46-49', '50-70', '71', '72-73', '74-79', '80 AND ABOVE']
DEPOSIT_CATEGORIES_LIST = ['20', '11', '12', '13', '15', 'SC', '30', 'SD'] # '30' covers 30-33, 'SC' covers 10, 'SD' covers others

MAX_FILE_SIZE_BYTES = 49.9 * 1024 * 1024 # 49.9 MB

# Excel's epoch start date (December 30, 1899) for converting numeric dates
EXCEL_EPOCH = datetime(1899, 12, 30)

def get_acc_prefixes(category_code):
    """Returns a list of account prefixes for a given category code."""
    if category_code == '40-45': return [str(i) for i in range(40, 46)]
    elif category_code == '46-49': return [str(i) for i in range(46, 50)]
    elif category_code == '50-70': return [str(i) for i in range(50, 71)]
    elif category_code == '71': return ['71']
    elif category_code == '72-73': return ['72', '73']
    elif category_code == '74-79': return [str(i) for i in range(74, 80)]
    elif category_code == '80 AND ABOVE': return [str(i) for i in range(80, 100)] # Assuming 2-digit prefixes max
    elif category_code == '20': return ['20']
    elif category_code == '11': return ['11']
    elif category_code == '12': return ['12']
    elif category_code == '13': return ['13']
    elif category_code == '15': return ['15']
    elif category_code == '30': return ['30', '31', '32', '33']
    elif category_code == 'SC': return ['10', '00'] # Added '00' for SC
    # 'SD' is handled by exclusion, so it doesn't have specific prefixes for filtering
    return []

# Date conversion - Excel serial date to datetime object
def convert_trndate_serial(serial):
    """
    Converts Excel serial date to datetime object.
    Handles NaN/empty values by returning pd.NaT.
    """
    if pd.isna(serial) or serial == '':
        return pd.NaT
    try:
        # Excel dates start from 1, but Python datetime starts from 0 for timedelta
        # Add 2 days to account for Excel's 1900 leap year bug and 1-based indexing
        return EXCEL_EPOCH + timedelta(days=float(serial) + 2)
    except (ValueError, TypeError):
        return pd.NaT

def process_win_data_web(input_dir, branch): # Simplified parameters
    """
    Processes WIN CSV files from input_dir, combines data,
    filters by branch, processes all app types and categories,
    and saves into separate Loan and Deposit CSVs within a branch-specific subfolder.
    Files are appended if they exist (based on latest TRNDATE), and split
    into new files if the size limit (49.99MB) is reached.
    Output filename format: BRANCH (3 CHAR) DEP/LN CATEGORY - MM-DD-YYYY TO MM-DD-YYYY.csv
    No _part_X suffix is used. If splitting occurs, date ranges differentiate files.

    Args:
        input_dir (str): The directory containing the WIN CSV files.
        branch (str): Branch code for filtering and filename.
    """
    # Sanitize the branch name for use in filenames and folder names
    sanitized_branch = "".join([c for c in str(branch) if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_').upper()
    if not sanitized_branch:
        sanitized_branch = "UNSPECIFIED_BRANCH" # Fallback if branch name is empty after sanitization

    # Determine the 3-character abbreviation for the filename
    branch_abbr_for_filename = ""
    if branch.upper() == "EL SALVADOR":
        branch_abbr_for_filename = "ELS"
    elif branch.upper() == "DON CARLOS":
        branch_abbr_for_filename = "DON"
    else:
        # Default to the first three characters of the sanitized branch name
        branch_abbr_for_filename = sanitized_branch[:3]


    # Construct the branch-specific output directory
    branch_output_dir = os.path.join(FIXED_BASE_OUTPUT_DIR, sanitized_branch)

    # Ensure the branch-specific output directory exists
    os.makedirs(branch_output_dir, exist_ok=True)

    print(f"Server Log (TRNM WIN): Processing started for Branch: {branch}. Output will be saved to: {branch_output_dir}")

    # Define the exact names for the output columns after processing
    # These are the target headers for the final CSV files
    output_columns_mapping = {
        "Trn": "TRN",
        "TrnType": "TRNTYPE",
        "Tlr": "TLR",
        "TrnDate": "TRNDATE",
        "TrnAmt": "TRNAMT",
        "TrnPriAmt": "TRNNONC", # Renamed based on internal mapping
        "TrnIntAmt": "TRNINT",
        "TrnPenAmt": "TRNTAXPEN", # Renamed based on internal mapping
        "BalAmt": "BAL",
        "Seq": "SEQ",
        "TrnDesc": "TRNDESC",
        "AppType": "APPTYPE"
    }
    required_columns = [
        "TRN", "ACC", "TRNTYPE", "TLR", "LEVEL", "TRNDATE",
        "TRNAMT", "TRNNONC", "TRNINT", "TRNTAXPEN", "BAL",
        "SEQ", "TRNDESC", "APPTYPE"
    ]


    # Read and combine CSV files from selected input folder
    combined_data = []
    print(f"Server Log (TRNM WIN): Scanning for CSV files in: {input_dir}")
    files_processed = 0
    win_files_found = False # Track if any WIN files were found

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith('.csv'):
            continue
        
        win_files_found = True # Found at least one WIN CSV

        path = os.path.join(input_dir, filename)
        print(f"Server Log (TRNM WIN): Processing file: {path}")
        try:
            df = pd.read_csv(path, dtype=str, low_memory=False) # Read all as string to prevent issues
            combined_data.append(df)
            files_processed += 1
        except UnicodeDecodeError:
            print(f"Server Log (TRNM WIN): Error reading file {path} with default encoding, trying latin1")
            try:
                df = pd.read_csv(path, encoding='latin1', low_memory=False)
                combined_data.append(df)
                files_processed += 1
            except Exception as e:
                print(f"Server Log (TRNM WIN): Error reading file {path}: {e}. Skipping.")
                continue
        except Exception as e:
            print(f"Server Log (TRNM WIN): Error reading file {path}: {e}. Skipping.")
            continue

    if not win_files_found:
        raise Exception("No CSV files found in the specified input directory for TRNM WIN processing.")
    
    if not combined_data:
        raise Exception("No valid WIN CSV files found in the input folder.")

    final_df = pd.concat(combined_data, ignore_index=True)
    print(f"Server Log (TRNM WIN): Combined data from {files_processed} files.")

    # Filter by branch first
    if 'BRANCH' in final_df.columns:
        final_df['BRANCH'] = final_df['BRANCH'].astype(str).str.strip().str.upper()
        final_df = final_df[final_df['BRANCH'] == sanitized_branch]
        if final_df.empty:
            print(f"Server Log (TRNM WIN): No data found for branch '{sanitized_branch}' after filtering.")
            return {"message": f"No data found for branch '{sanitized_branch}'.", "output_path": branch_output_dir}
    else:
        print("Server Log (TRNM WIN): Warning: 'BRANCH' column not found in combined data. Cannot filter by branch.")

    # Standardize column names to lowercase for easier mapping
    final_df.columns = [col.lower() for col in final_df.columns]

    # Map columns to desired output names
    mapped_df = pd.DataFrame()
    # Define a dictionary for column aliases (moved here for clarity)
    column_aliases = {
        "TrnDate": ["transaction_date"],
        "TrnAmt": ["transaction_amount"],
        "TrnPriAmt": ["principal_amount", "trnnoc", "trntaxpen"],
        "TrnIntAmt": ["interest_amount", "trnint"],
        "TrnPenAmt": ["penalty_amount"],
        "BalAmt": ["balance_amount"],
        "TrnDesc": ["transaction_description"],
        "AppType": ["application_type"]
    }

    for original_col_base, new_col_name in output_columns_mapping.items():
        found_col = None
        # Start with the lowercased original_col_base itself
        possible_aliases = [original_col_base.lower()]
        # Extend with other defined aliases, ensuring they are lowercased
        possible_aliases.extend([alias.lower() for alias in column_aliases.get(original_col_base, [])])

        for alias in possible_aliases:
            if alias in final_df.columns:
                found_col = alias
                break
        
        if found_col:
            mapped_df[new_col_name] = final_df[found_col]
        else:
            mapped_df[new_col_name] = '' # Add empty column if not found

    # Helper function for ACC and CHD formatting
    def format_acc_chd(row):
        acc_val_raw = str(row['acc']).strip() if pd.notna(row['acc']) else ''
        chd_val_raw = str(row['chd']).strip() if pd.notna(row['chd']) else ''

        # Extract only digits from acc_val_raw
        acc_digits_only = ''.join(filter(str.isdigit, acc_val_raw))
        
        # Convert to int then format to 7 digits with leading zeros
        # This handles cases like "700014" -> 700014 -> "00700014" (incorrect, should be 0700014)
        # Correct approach: Pad the string of digits directly to 7, then slice
        acc_seven_digits = acc_digits_only.zfill(7)
        
        # Extract only digits from chd_val_raw. If it's empty, default to '0'.
        # If it contains digits, take the first one.
        chd_formatted = ''.join(filter(str.isdigit, chd_val_raw))
        if chd_formatted:
            chd_formatted = chd_formatted[0] # Take only the first digit
        else:
            chd_formatted = '0' # Default to '0' if no digits or empty

        # Format as XX-XXXXX-Y
        # acc_seven_digits is guaranteed to be 7 characters due to zfill(7)
        return f"{acc_seven_digits[:2]}-{acc_seven_digits[2:7]}-{chd_formatted}"
            
    # Handle ACC and CHD combination
    acc_col_found = 'acc' in final_df.columns
    chd_col_found = 'chd' in final_df.columns

    if acc_col_found and chd_col_found:
        mapped_df["ACC"] = final_df.apply(format_acc_chd, axis=1)
    elif acc_col_found:
        # If only ACC is found, format it as XX-XXXXX-0 (defaulting CHD to 0)
        mapped_df["ACC"] = final_df['acc'].astype(str).strip()
        mapped_df["ACC"] = mapped_df["ACC"].apply(
            # Extract digits from ACC, pad to 7, then format XX-XXXXX-0
            lambda x: f"{''.join(filter(str.isdigit, x)).zfill(7)[:2]}-{''.join(filter(str.isdigit, x)).zfill(7)[2:7]}-0"
        )
        print(f"Server Log (TRNM WIN): ⚠️ 'Chd' column not found for ACC formatting. Using ACC as XX-XXXXX-0 or padded raw ACC-0.")
    else:
        print(f"Server Log (TRNM WIN): ⚠️ Neither 'Acc' nor 'Chd' column found for ACC creation. ACC column will be empty.")
        mapped_df["ACC"] = '' # Ensure ACC column exists even if empty

    # Add 'LEVEL' column (empty as per previous logic)
    mapped_df['LEVEL'] = ''

    # Convert numeric columns (before formatting to string)
    numeric_cols_pre_format = ['TRNAMT', 'TRNNONC', 'TRNINT', 'TRNTAXPEN', 'BAL', 'SEQ']
    columns_to_divide_by_100 = ['TRNAMT', 'TRNNONC', 'TRNINT', 'TRNTAXPEN', 'BAL'] # Define columns to divide by 100

    for col in numeric_cols_pre_format:
        if col in mapped_df.columns:
            mapped_df[col] = pd.to_numeric(mapped_df[col], errors='coerce').fillna(0)
            if col in columns_to_divide_by_100: # Apply division by 100 here
                mapped_df[col] = mapped_df[col] / 100
        else:
            mapped_df[col] = 0 # Ensure numeric columns exist and are initialized

    # Convert APPTYPE to integer
    if 'APPTYPE' in mapped_df.columns:
        mapped_df['APPTYPE'] = pd.to_numeric(mapped_df['APPTYPE'], errors='coerce').fillna(0).astype(int)
    else:
        mapped_df['APPTYPE'] = 0 # Default to 0 if APPTYPE is missing

    # Date conversion: TRNDATE to datetime object for sorting and range calculation
    mapped_df['TRNDATE_DT'] = pd.to_datetime(mapped_df['TRNDATE'], errors='coerce')

    # Sort the entire combined DataFrame by 'TRNDATE_DT' in ascending order
    print("Server Log (TRNM WIN): Sorting combined data by TRNDATE...")
    mapped_df.sort_values(by='TRNDATE_DT', inplace=True)
    mapped_df.reset_index(drop=True, inplace=True)

    # Filter out rows where TRNDATE_DT is NaT after sorting to avoid issues with date range calculations
    initial_rows = len(mapped_df)
    mapped_df.dropna(subset=['TRNDATE_DT'], inplace=True)
    if len(mapped_df) < initial_rows:
        print(f"Server Log (TRNM WIN): Removed {initial_rows - len(mapped_df)} rows with invalid TRNDATE.")

    # --- File Splitting and Saving Logic ---
    total_files_generated = 0

    # Define a helper function to perform APPTYPE and category filtering
    def filter_and_categorize_data(df):
        loan_df = df[df['APPTYPE'] == 4].copy()
        deposit_df = df[df['APPTYPE'].isin([1, 2, 3, 7])].copy() # Include APPTYPE 7 in general deposit_df for SD filtering

        categorized_data = {} # {('LOAN', '40-45'): df, ('DEPOSIT', '20'): df, ...}

        # Process Loan Categories
        for category in LOAN_CATEGORIES_LIST:
            prefixes = get_acc_prefixes(category)
            if prefixes:
                # Filter for rows where ACC starts with any of the category's prefixes
                filtered_loan_df = loan_df[loan_df['ACC'].astype(str).str.startswith(tuple(prefixes), na=False)].copy()
                if not filtered_loan_df.empty:
                    categorized_data[('LOAN', category)] = filtered_loan_df

        # Process Deposit Categories
        for category in DEPOSIT_CATEGORIES_LIST:
            # For 'SD', include APPTYPE 7 and exclude '00' ACC prefix
            if category == 'SD':
                # 'SD' is the catch-all for deposit APPTYPEs 1,2,3,7 that are NOT specifically categorized by ACC prefix.
                # First, get all prefixes used by other *specific* deposit categories (excluding 'SD' itself and 'ALL').
                all_other_deposit_prefixes = []
                for other_cat in DEPOSIT_CATEGORIES_LIST:
                    if other_cat not in ['SD', 'ALL', 'SC']: # Exclude 'SC' prefixes as well from the general SD filter
                        all_other_deposit_prefixes.extend(get_acc_prefixes(other_cat))
                
                # Filter deposit_df for APPTYPE 1, 2, 3, 7
                sd_filtered_df = deposit_df[deposit_df['APPTYPE'].isin([1, 2, 3, 7])].copy()
                
                # Exclude accounts that start with prefixes of other *specific* deposit categories
                if all_other_deposit_prefixes:
                    sd_filtered_df = sd_filtered_df[~sd_filtered_df['ACC'].astype(str).str.startswith(tuple(all_other_deposit_prefixes), na=False)].copy()
                
                # Additionally exclude accounts starting with '00' and '10' (SC prefixes)
                sd_filtered_df = sd_filtered_df[~sd_filtered_df['ACC'].astype(str).str.startswith(('00', '10'), na=False)].copy()

                if not sd_filtered_df.empty:
                    categorized_data[('DEPOSIT', category)] = sd_filtered_df
            elif category == 'SC': # Share Capital - only '00' and '10' ACC prefixes, APPTYPE 7
                # SC should specifically target APPTYPE 7 and ACC starting with '00' or '10'
                sc_prefixes = ['00', '10'] # Explicitly define SC prefixes
                
                filtered_sc_df = deposit_df[
                    (deposit_df['APPTYPE'] == 7) & # SC is APPTYPE 7
                    deposit_df['ACC'].astype(str).str.startswith(tuple(sc_prefixes), na=False) # Filter by '00' or '10'
                ].copy()
                
                if not filtered_sc_df.empty:
                    categorized_data[('DEPOSIT', category)] = filtered_sc_df
            else: # For other specific deposit categories (e.g., '20', '11', '12', '13', '15', '30')
                prefixes = get_acc_prefixes(category)
                if prefixes:
                    # Filter for APPTYPEs 1, 2, 3 and specific ACC prefixes
                    filtered_deposit_df = deposit_df[
                        deposit_df['APPTYPE'].isin([1, 2, 3]) &
                        df['ACC'].astype(str).str.startswith(tuple(prefixes), na=False)
                    ].copy()
                    if not filtered_deposit_df.empty:
                        categorized_data[('DEPOSIT', category)] = filtered_deposit_df
        return categorized_data

    categorized_dfs = filter_and_categorize_data(mapped_df)

    total_files_generated = 0

    for (app_type, category), df_to_process_for_category in categorized_dfs.items():
        if df_to_process_for_category.empty:
            print(f"Server Log (TRNM WIN): No data for {app_type} - {category}. Skipping.")
            continue

        # Sort by TRNDATE_DT before saving/splitting to ensure proper appending order
        df_to_process_for_category.sort_values(by='TRNDATE_DT', inplace=True)
        df_to_process_for_category.reset_index(drop=True, inplace=True)

        # Apply final formatting for numeric and date columns before saving
        # This DataFrame will be the source for chunks
        df_to_save_formatted = df_to_process_for_category.copy()
        for col in numeric_cols_pre_format: # Use the list of numeric columns
            if col in df_to_save_formatted.columns:
                df_to_save_formatted[col] = df_to_save_formatted[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else '')
        df_to_save_formatted['TRNDATE'] = df_to_save_formatted['TRNDATE_DT'].dt.strftime('%m/%d/%Y').fillna('')
        
        # Ensure 'TRNDESC' and 'ACC' are treated as strings and quoted if they start with '='
        if 'TRNDESC' in df_to_save_formatted.columns:
            df_to_save_formatted['TRNDESC'] = df_to_save_formatted['TRNDESC'].astype(str).apply(lambda x: f'="{x}"' if x.startswith('=') else x)
        if 'ACC' in df_to_save_formatted.columns:
            df_to_save_formatted['ACC'] = df_to_save_formatted['ACC'].astype(str).apply(lambda x: f'="{x}"' if x.startswith('=') else x)


        file_type_abbr = 'LN' if app_type == 'LOAN' else 'DEP'
        
        # Base filename prefix (e.g., YAC LN 40-45) - without date range or part number
        base_filename_prefix = f"{branch_abbr_for_filename} {file_type_abbr} {category}"
        
        # Regex to match files starting with the base_filename_prefix and having a date range suffix
        # The regex should only match the base prefix and the date format, not the part_X suffix
        existing_file_regex = re.compile(rf'^{re.escape(base_filename_prefix)} - \d{{2}}-\d{{2}}-\d{{4}} TO \d{{2}}-\d{{2}}-\d{{4}}\.csv$', re.IGNORECASE)
        
        files_removed_for_category = 0
        for existing_file_name in os.listdir(branch_output_dir):
            if existing_file_regex.match(existing_file_name):
                file_to_remove_path = os.path.join(branch_output_dir, existing_file_name)
                try:
                    os.remove(file_to_remove_path)
                    print(f"Server Log (TRNM WIN): Removed old file: {file_to_remove_path}")
                    files_removed_for_category += 1
                except OSError as e:
                    print(f"Server Log (TRNM WIN): Error removing old file {file_to_remove_path}: {e}")
        if files_removed_for_category > 0:
            print(f"Server Log (TRNM WIN): Removed {files_removed_for_category} old files for category {base_filename_prefix}.")


        # Estimate rows per chunk for the *entire* df_to_save_formatted
        if not df_to_save_formatted.empty:
            # Estimate size of a typical row by converting a small sample to CSV
            sample_df_for_size = df_to_save_formatted.head(min(100, len(df_to_save_formatted)))
            s_buf_sample = io.StringIO()
            sample_df_for_size.to_csv(s_buf_sample, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8-sig')
            estimated_bytes_per_row = len(s_buf_sample.getvalue().encode('utf-8-sig')) / len(sample_df_for_size) if len(sample_df_for_size) > 0 else MAX_FILE_SIZE_BYTES / 1000 # Fallback
        else:
            estimated_bytes_per_row = MAX_FILE_SIZE_BYTES / 1000 # Default if empty data

        # Adjust the estimated bytes per row to try and get closer to the target file size
        # If files are consistently much smaller, reduce this factor (e.g., 0.8 to make rows_per_chunk larger)
        # If files are overshooting, increase this factor (e.g., 1.1 to make rows_per_chunk smaller)
        SIZE_ADJUSTMENT_FACTOR = 0.9 # Example: try to make chunks ~10% larger in terms of rows
        adjusted_estimated_bytes_per_row = estimated_bytes_per_row * SIZE_ADJUSTMENT_FACTOR

        # Calculate approximate rows per chunk for each file
        rows_per_chunk = int(MAX_FILE_SIZE_BYTES / adjusted_estimated_bytes_per_row) if adjusted_estimated_bytes_per_row > 0 else len(df_to_save_formatted)
        if rows_per_chunk <= 0: # Ensure at least 1 row per chunk
             rows_per_chunk = len(df_to_save_formatted) if len(df_to_save_formatted) > 0 else 1

        print(f"Server Log (TRNM WIN): Estimated bytes per row: {estimated_bytes_per_row:.2f}. Adjusted bytes per row: {adjusted_estimated_bytes_per_row:.2f}. Rows per chunk: {rows_per_chunk}.")


        # --- Split df_to_save_formatted into chunks and save with dynamic date ranges ---
        
        if df_to_save_formatted.empty:
            print(f"Server Log (TRNM WIN): No data to save for {app_type} - {category} after formatting.")
            continue # Skip to next category

        num_chunks = (len(df_to_save_formatted) + rows_per_chunk - 1) // rows_per_chunk
        
        for i in range(num_chunks):
            start_idx = i * rows_per_chunk
            end_idx = min((i + 1) * rows_per_chunk, len(df_to_save_formatted))
            current_chunk_df = df_to_save_formatted.iloc[start_idx:end_idx].copy()

            if current_chunk_df.empty:
                continue

            # Ensure TRNDATE_DT column is datetime objects for min/max operations
            if not pd.api.types.is_datetime64_any_dtype(current_chunk_df['TRNDATE_DT']):
                current_chunk_df['TRNDATE_DT'] = pd.to_datetime(current_chunk_df['TRNDATE_DT'], errors='coerce')


            # Determine date range for the current chunk
            valid_dates_in_chunk = current_chunk_df['TRNDATE_DT'].dropna()

            chunk_min_date_val = None
            chunk_max_date_val = None

            if not valid_dates_in_chunk.empty:
                chunk_min_date_val = valid_dates_in_chunk.min()
                chunk_max_date_val = valid_dates_in_chunk.max()
            
            # Format dates for filename
            min_trn_date_str_chunk = chunk_min_date_val.strftime('%m-%d-%Y') if pd.notna(chunk_min_date_val) else "UNKNOWN_START"
            max_trn_date_str_chunk = chunk_max_date_val.strftime('%m-%d-%Y') if pd.notna(chunk_max_date_val) else "UNKNOWN_END"
            
            # Construct filename without _part_X suffix
            new_filename_date_range = f"{min_trn_date_str_chunk} TO {max_trn_date_str_chunk}"
            output_file_name = f"{base_filename_prefix} - {new_filename_date_range}.csv"
            output_file_path = os.path.join(branch_output_dir, output_file_name)

            try:
                # Save the current chunk to CSV
                # Reindex current_chunk_df to ensure only output_headers are present and in order
                current_chunk_df[required_columns].to_csv(output_file_path, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8-sig')
                print(f"Server Log (TRNM WIN): Saved chunk {i+1}/{num_chunks} to: {output_file_path} (Size: {os.path.getsize(output_file_path)/ (1024 * 1024):.2f} MB)")
                total_files_generated += 1
            except Exception as e:
                print(f"Server Log (TRNM WIN): ❌ Error writing CSV chunk '{output_file_name}': {e}")
                # Continue to next chunk/category even if one fails
                continue

    print(f"\nServer Log (TRNM WIN): Processing complete! Total files generated: {total_files_generated}")
    return {"message": f"TRNM WIN processing completed. Total files generated: {total_files_generated}. Output saved to {branch_output_dir}", "output_path": branch_output_dir}
