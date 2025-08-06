# audit_tool/backend/comtrnm.py
import os
import pandas as pd
from datetime import datetime, timedelta
import re # Import regex module
import io # For in-memory file size estimation
import csv # For quoting in CSV writes

print("Server Log (TRNM): comtrnm.py module is being loaded...")

# Define the fixed base output directory for TRNM
# This is now primarily for reference; the actual output_dir is passed from the route
FIXED_BASE_OUTPUT_DIR = r"C:\\xampp\\\\htdocs\\\\audit_tool\\\\OPERATIONS\\\\TRNM"

# Constants for categories (used internally for processing, not directly from UI anymore)
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
    elif category_code == 'SC': return ['10']
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

# MODIFIED: Adjusted function signature to accept output_folder and file_prefix
def process_transactions_web(input_dir, output_folder, file_prefix):
    """
    Processes TRNM CSV files from input_dir, combines data,
    filters by branch, processes all app types and categories,
    and saves into separate Loan and Deposit CSVs within a branch-specific subfolder.
    Files are appended if they exist (based on latest TRNDATE), and split
    into new files if the size limit (49.99MB) is reached.
    Output filename format: BRANCH (3 CHAR) DEP/LN CATEGORY - MM-DD-YYYY TO MM-DD-YYYY.csv
    No _part_X suffix is used. If splitting occurs, date ranges differentiate files.

    Args:
        input_dir (str): The directory containing the TRNM CSV files.
        output_folder (str): The specific output directory (branch-specific) where files should be saved.
        file_prefix (str): The 3-character prefix for the output filenames (e.g., "ELS").
    """
    # The branch name for filtering is derived from the output_folder now
    sanitized_branch_for_folder = os.path.basename(output_folder)
    
    # The file_prefix is already passed and used directly for filenames
    # branch_abbr_for_filename = file_prefix # This is now directly the passed file_prefix

    # Construct the branch-specific output directory
    # This should now just use the output_folder directly, as it's already the target folder.
    branch_output_dir = output_folder # Use the passed output_folder directly

    # Ensure the branch-specific output directory exists (redundant if route already created, but safe)
    os.makedirs(branch_output_dir, exist_ok=True)

    print(f"Server Log (TRNM): Processing started for Branch Folder: {sanitized_branch_for_folder}. Output will be saved to: {branch_output_dir}")

    # Define the STRICT output headers and their desired order
    output_headers = [
        'TRN', 'ACC', 'TRNTYPE', 'TLR', 'LEVEL', 'TRNDATE',
        'TRNAMT', 'TRNNONC', 'TRNINT', 'TRNTAXPEN', 'BAL', 'SEQ', 'TRNDESC', 'APPTYPE'
    ]

    # Read and combine CSV files from selected input folder
    combined_data = []
    print(f"Server Log (TRNM): Scanning for CSV files in: {input_dir}")
    files_processed = 0
    trnm_files_found = False # Track if any TRNM files were found

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith('.csv') or not filename.upper().startswith('TRNM'):
            continue
        
        trnm_files_found = True # Found at least one TRNM CSV

        path = os.path.join(input_dir, filename)
        print(f"Server Log (TRNM): Processing file: {path}")
        try:
            # Try reading with utf-8 first, then fall back to latin1 for robustness
            try:
                df = pd.read_csv(path, encoding='utf-8', low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding='latin1', low_memory=False)
            combined_data.append(df)
            files_processed += 1
        except Exception as e: # Catch all other exceptions during read
            print(f"Server Log (TRNM): Error reading file {path}: {e}. Skipping.")
            continue

    if not trnm_files_found:
        raise Exception("No TRNM CSV files found in the specified input directory.")
    
    if not combined_data:
        raise Exception("No valid TRNM CSV files found in the input folder.")

    final_df = pd.concat(combined_data, ignore_index=True)
    print(f"Server Log (TRNM): Combined data from {files_processed} files.")

    # Filter by branch first
    if 'BRANCH' in final_df.columns:
        final_df['BRANCH'] = final_df['BRANCH'].astype(str).str.strip().str.upper()
        # Filter using the sanitized branch name derived from the output_dir
        final_df = final_df[final_df['BRANCH'] == sanitized_branch_for_folder]
        if final_df.empty:
            print(f"Server Log (TRNM): No data found for branch '{sanitized_branch_for_folder}'.")
            return {"message": f"No data found for branch '{sanitized_branch_for_folder}'.", "output_path": branch_output_dir}
    else:
        print("Server Log (TRNM): Warning: 'BRANCH' column not found in combined data. Cannot filter by branch.")

    # Convert columns to numeric, handling potential non-numeric values
    # Apply division by 100 here for relevant numeric columns
    for col in ['TRNAMT', 'TRNNONC', 'TRNINT', 'TRNTAXPEN', 'BAL', 'SEQ', 'APPTYPE']:
        if col in final_df.columns:
            try:
                if col == 'APPTYPE':
                    final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0).astype(int) # Convert to int
                else:
                    final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)
                    # Apply division by 100 for specified columns
                    if col in ['TRNAMT', 'TRNNONC', 'TRNINT', 'TRNTAXPEN', 'BAL']:
                        final_df[col] = final_df[col] / 100
            except Exception as e:
                print(f"Server Log (TRNM): Error converting column '{col}' to numeric: {e}. Values might be NaN.")
                final_df[col] = pd.NaT
        else:
            print(f"Server Log (TRNM): Warning: Column '{col}' not found in combined data. Skipping numeric conversion for this column.")

    # Ensure TRNDATE_DT column exists and is datetime dtype
    if 'TRNDATE' in final_df.columns:
        final_df['TRNDATE_DT'] = final_df['TRNDATE'].apply(convert_trndate_serial)
    else:
        final_df['TRNDATE_DT'] = pd.Series([pd.NaT] * len(final_df), index=final_df.index)
        print("Server Log (TRNM): Warning: 'TRNDATE' column not found in new data. 'TRNDATE_DT' initialized to NaT.")

    # Remove rows where TRNDATE_DT is blank/NaT
    initial_rows = len(final_df)
    final_df.dropna(subset=['TRNDATE_DT'], inplace=True)
    rows_removed = initial_rows - len(final_df)
    if rows_removed > 0:
        print(f"Server Log (TRNM): Removed {rows_removed} rows with blank or invalid TRNDATE.")

    # Compute TRNNONC (only if necessary columns exist)
    if all(col in final_df.columns for col in ['TRNAMT', 'TRNINT', 'TRNTAXPEN']):
        final_df['TRNNONC'] = final_df['TRNAMT'] - final_df['TRNINT'] - final_df['TRNTAXPEN']
    else:
        print("Server Log (TRNM): Warning: Missing columns for 'TRNNONC' calculation (TRNAMT, TRNINT, TRNTAXPEN). Skipping calculation.")
        if 'TRNNONC' not in final_df.columns:
            final_df['TRNNONC'] = pd.NA


    # Format ACC: xx-xxxxx-y (ACC -X and CHD -Y)
    def format_acc(row):
        # Ensure ACC and CHD are treated as strings for zfill and slicing
        acc_part = str(row['ACC']).split('.')[0] if pd.notna(row['ACC']) else ''
        chd_part = str(row.get('CHD', '')).split('.')[0] if pd.notna(row.get('CHD')) else '' # Use .get for safety
        
        # Pad ACC part to 7 digits, then combine with CHD part
        combined_acc_chd = acc_part.zfill(7) + chd_part.zfill(1) # Ensure CHD is also padded if needed, assuming 1 digit
        
        # Apply xx-xxxxx-y format if combined string is long enough
        if len(combined_acc_chd) >= 8:
            return f"{combined_acc_chd[:2]}-{combined_acc_chd[2:7]}-{combined_acc_chd[7:]}"
        else:
            return acc_part # Fallback if not enough digits for full format

    if 'ACC' in final_df.columns:
        # Check for 'CHD' column presence for ACC formatting
        if 'CHD' in final_df.columns:
            final_df['ACC'] = final_df.apply(format_acc, axis=1)
        else:
            print("Server Log (TRNM): Warning: 'CHD' column not found for ACC formatting. Using raw ACC.")
            final_df['ACC'] = final_df['ACC'].astype(str) # Ensure it's string
    else:
        print("Server Log (TRNM): Warning: 'ACC' column not found. Account formatting skipped.")

    # Define numeric columns for final formatting (comma and 2 decimal points)
    numeric_cols_for_final_format = ['TRNAMT', 'TRNNONC', 'TRNINT', 'TRNTAXPEN', 'BAL']


    # Define a helper function to perform APPTYPE and category filtering
    def filter_and_categorize_data(df):
        loan_df = df[df['APPTYPE'] == 4].copy()
        deposit_df = df[df['APPTYPE'].isin([1, 2, 3])].copy()

        categorized_data = {} # {('LOAN', '40-45'): df, ('DEPOSIT', '20'): df, ...}

        # Process Loan Categories
        for category in LOAN_CATEGORIES_LIST:
            prefixes = get_acc_prefixes(category)
            if prefixes:
                filtered_loan_df = loan_df[loan_df['ACC'].astype(str).str.startswith(tuple(prefixes), na=False)].copy()
                if not filtered_loan_df.empty:
                    categorized_data[('LOAN', category)] = filtered_loan_df
            elif category == 'ALL': # Handle 'ALL' for loans if it means "all loans not covered by specific categories"
                # For 'ALL' loans, we'd typically take all loans, but since we're categorizing,
                # 'ALL' here means all loans that *don't* fit other explicit categories, or simply all loans if no other categories apply.
                pass # Specific categories are handled above. 'ALL' loan data is implicitly handled by processing all categories.


        # Process Deposit Categories
        for category in DEPOSIT_CATEGORIES_LIST:
            if category == 'SD': # Special handling for SD: Exclude other deposit categories
                excluded_prefixes = []
                for cat in DEPOSIT_CATEGORIES_LIST:
                    if cat not in ['ALL', 'SD']:
                        excluded_prefixes.extend(get_acc_prefixes(cat))
                
                filtered_deposit_df = deposit_df[~deposit_df['ACC'].astype(str).str[:2].isin(excluded_prefixes)].copy()
                if not filtered_deposit_df.empty:
                    categorized_data[('DEPOSIT', category)] = filtered_deposit_df
            else: # For specific deposit categories (e.g., '20', '11')
                prefixes = get_acc_prefixes(category)
                if prefixes:
                    filtered_deposit_df = deposit_df[deposit_df['ACC'].astype(str).str.startswith(tuple(prefixes), na=False)].copy()
                    if not filtered_deposit_df.empty:
                        categorized_data[('DEPOSIT', category)] = filtered_deposit_df
            # If category is 'ALL', no further ACC filtering for deposits.
            # 'ALL' deposit data is implicitly handled by processing all categories.

        return categorized_data


    categorized_dfs = filter_and_categorize_data(final_df)

    total_files_generated = 0

    for (app_type, category), df_to_save_original in categorized_dfs.items():
        if df_to_save_original.empty:
            print(f"Server Log (TRNM): No data for {app_type} - {category}. Skipping.")
            continue

        # Sort by TRNDATE_DT before saving/splitting to ensure proper appending order
        # This sort is applied to the *original* DataFrame for saving, ensuring consistent internal ordering
        df_to_save_original.sort_values(by='TRNDATE_DT', inplace=True)
        df_to_save_original.reset_index(drop=True, inplace=True)

        # Apply final formatting for numeric and date columns before saving
        df_to_save_formatted = df_to_save_original.copy()
        for col in numeric_cols_for_final_format: # Use new list for final formatting
            if col in df_to_save_formatted.columns:
                df_to_save_formatted[col] = df_to_save_formatted[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else '')
        df_to_save_formatted['TRNDATE'] = df_to_save_formatted['TRNDATE_DT'].dt.strftime('%m/%d/%Y').fillna('')
        
        # Ensure 'TRNDESC' and 'ACC' are treated as strings and quoted if they start with '='
        if 'TRNDESC' in df_to_save_formatted.columns:
            df_to_save_formatted['TRNDESC'] = df_to_save_formatted['TRNDESC'].astype(str).apply(lambda x: f'="{x}"' if x.startswith('=') else x)
        if 'ACC' in df_to_save_formatted.columns:
            df_to_save_formatted['ACC'] = df_to_save_formatted['ACC'].astype(str).apply(lambda x: f'="{x}"' if x.startswith('=') else x)


        file_type_abbr = 'LN' if app_type == 'LOAN' else 'DEP'
        
        # MODIFIED: Use the passed file_prefix here
        base_filename_prefix = f"{file_prefix} {file_type_abbr} {category}"
        
        # Regex to extract the "TO" date from existing filenames (no _part_X in this regex)
        date_extract_regex = re.compile(r' - (\d{2}-\d{2}-\d{4}) TO (\d{2}-\d{2}-\d{4})\.csv$', re.IGNORECASE)

        # Find existing files for this specific base pattern (BRANCH TYPE CATEGORY)
        existing_files_for_category = []
        for f in os.listdir(branch_output_dir):
            if f.startswith(base_filename_prefix) and f.endswith('.csv'):
                existing_files_for_category.append(f)

        latest_existing_file_path = None
        latest_existing_start_date = None # Track existing file's start date
        latest_existing_end_date = None

        # Sort existing files by their end date to find the true latest file
        if existing_files_for_category:
            sorted_files_with_dates = []
            for f_name in existing_files_for_category:
                match = date_extract_regex.search(f_name)
                if match:
                    try:
                        file_start_date = datetime.strptime(match.group(1), "%m-%d-%Y")
                        file_end_date = datetime.strptime(match.group(2), "%m-%d-%Y")
                        sorted_files_with_dates.append((file_end_date, file_start_date, f_name))
                    except ValueError:
                        print(f"Warning: Could not parse date from existing TRNM filename for sorting: {f_name}")
                        continue
            
            if sorted_files_with_dates:
                sorted_files_with_dates.sort() # Sorts by end_date
                latest_file_name = sorted_files_with_dates[-1][2]
                latest_existing_file_path = os.path.join(branch_output_dir, latest_file_name)
                latest_existing_end_date = sorted_files_with_dates[-1][0]
                latest_existing_start_date = sorted_files_with_dates[-1][1] # Get existing file's start date
                print(f"Server Log (TRNM): Found latest existing file for category: {latest_existing_file_path}")
            else:
                print(f"Server Log (TRNM): No parsable existing files for category {base_filename_prefix}. Starting new file.")
        else:
            print(f"Server Log (TRNM): No existing files for category {base_filename_prefix}. Creating first file.")


        # --- Determine if appending or new file creation is needed, and handle splitting ---
        data_to_process = df_to_save_formatted # Start with the new data to save
        
        # If an existing file is found, read it, combine, and deduplicate
        if latest_existing_file_path and os.path.exists(latest_existing_file_path):
            try:
                existing_df = pd.read_csv(latest_existing_file_path, dtype=str, keep_default_na=False, encoding='utf-8-sig') # Ensure encoding
                
                # Ensure TRNDATE_DT is datetime dtype in existing_df before concatenation
                if 'TRNDATE' in existing_df.columns:
                    existing_df['TRNDATE_DT'] = existing_df['TRNDATE'].apply(convert_trndate_serial)
                else:
                    existing_df['TRNDATE_DT'] = pd.Series([pd.NaT] * len(existing_df), index=existing_df.index)


                # Combine existing and new data for the total dataset to be managed
                # Ensure all required columns (including TRNDATE_DT) are present for concatenation
                combined_for_dedup = pd.concat([existing_df, df_to_save_formatted.reindex(columns=output_headers + ['TRNDATE_DT'], fill_value='')], ignore_index=True)
                data_to_process = combined_for_dedup.drop_duplicates(keep='first').reset_index(drop=True)
                
                # Removed: data_to_process.sort_values(by='TRNDATE_DT', inplace=True)
                # This ensures new data is appended after existing data, preserving concatenation order.
                data_to_process.reset_index(drop=True, inplace=True)
                print(f"Server Log (TRNM): Combined existing data with new data. Total rows after deduplication: {len(data_to_process)}.")
            except Exception as e:
                print(f"Server Log (TRNM): Error reading existing file {latest_existing_file_path} for appending: {e}. Treating new data as a fresh start.")
                # If existing file is problematic, proceed with only the new data
                latest_existing_file_path = None 
                latest_existing_start_date = None # Reset if treating as fresh start
                latest_existing_end_date = None

        # Estimate rows per chunk for the *entire* data_to_process
        if not data_to_process.empty:
            # Estimate size of a typical row by converting a small sample to CSV
            sample_df_for_size = data_to_process.head(min(100, len(data_to_process)))
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
        rows_per_chunk = int(MAX_FILE_SIZE_BYTES / adjusted_estimated_bytes_per_row) if adjusted_estimated_bytes_per_row > 0 else len(data_to_process)
        if rows_per_chunk <= 0: # Ensure at least 1 row per chunk
             rows_per_chunk = len(data_to_process) if len(data_to_process) > 0 else 1

        print(f"Server Log (TRNM): Estimated bytes per row: {estimated_bytes_per_row:.2f}. Adjusted bytes per row: {adjusted_estimated_bytes_per_row:.2f}. Rows per chunk: {rows_per_chunk}.")

        # --- Remove all previous files for this base_filename_prefix ---
        # This ensures that old date range files are removed before new ones are written
        # Regex to match files starting with the base_filename_prefix and having a date range suffix
        # The regex should only match the base prefix and the date format, not the part_X suffix
        existing_file_regex = re.compile(rf'^{re.escape(base_filename_prefix)} - \d{{2}}-\d{{2}}-\d{{4}} TO \d{{2}}-\d{{2}}-\d{{4}}\.csv$', re.IGNORECASE)
        
        files_removed = 0
        for existing_file_name in os.listdir(branch_output_dir):
            if existing_file_regex.match(existing_file_name):
                file_to_remove_path = os.path.join(branch_output_dir, existing_file_name)
                try:
                    os.remove(file_to_remove_path)
                    print(f"Server Log (TRNM): Removed old file: {file_to_remove_path}")
                    files_removed += 1
                except OSError as e:
                    print(f"Server Log (TRNM): Error removing old file {file_to_remove_path}: {e}")
        if files_removed > 0:
            print(f"Server Log (TRNM): Removed {files_removed} old files for category {base_filename_prefix}.")


        # --- Split data_to_process into chunks and save with dynamic date ranges ---
        total_files_generated = 0
        
        if data_to_process.empty:
            print(f"Server Log (TRNM): No data to save for {app_type} - {category}.")
            return {"message": f"TRNM processing completed for {app_type} - {category}. No data to save.", "output_path": branch_output_dir}


        num_chunks = (len(data_to_process) + rows_per_chunk - 1) // rows_per_chunk
        
        for i in range(num_chunks):
            start_idx = i * rows_per_chunk
            end_idx = min((i + 1) * rows_per_chunk, len(data_to_process))
            current_chunk_df = data_to_process.iloc[start_idx:end_idx].copy()

            if current_chunk_df.empty:
                continue

            # Ensure TRNDATE_DT column is datetime objects for min/max operations
            # This is a crucial re-check/conversion if concatenation changed dtype
            # Use .copy() to avoid SettingWithCopyWarning if original df_to_save_original was a slice
            if not pd.api.types.is_datetime64_any_dtype(current_chunk_df['TRNDATE_DT']):
                current_chunk_df['TRNDATE_DT'] = pd.to_datetime(current_chunk_df['TRNDATE_DT'], errors='coerce')


            # Determine date range for the current chunk
            # Filter out NaT values before min/max to avoid errors on empty chunks or all NaT
            valid_dates_in_chunk = current_chunk_df['TRNDATE_DT'].dropna()

            # Initialize with default placeholders
            chunk_min_date_val = None
            chunk_max_date_val = None

            if not valid_dates_in_chunk.empty:
                chunk_min_date_val = valid_dates_in_chunk.min()
                chunk_max_date_val = valid_dates_in_chunk.max()
            
            # Use existing file's start date if appending and valid, otherwise use chunk's min date
            # This logic now correctly combines the start date from the existing file (if first chunk)
            # with the new data's min date.
            final_chunk_start_date = chunk_min_date_val
            if latest_existing_start_date and i == 0: # Only for the very first chunk of the new processing session
                if pd.notna(chunk_min_date_val):
                    final_chunk_start_date = min(latest_existing_start_date, chunk_min_date_val)
                else:
                    final_chunk_start_date = latest_existing_start_date # If current chunk has no valid dates, use existing start
            
            # Use existing file's end date if appending and valid, otherwise use chunk's max date
            # This logic now correctly combines the end date from the existing file (if last chunk)
            # with the new data's max date.
            final_chunk_end_date = chunk_max_date_val
            if latest_existing_end_date and i == num_chunks - 1: # Only for the very last chunk of the new processing session
                 if pd.notna(chunk_max_date_val):
                    final_chunk_end_date = max(latest_existing_end_date, chunk_max_date_val)
                 else:
                    final_chunk_end_date = latest_existing_end_date # If current chunk has no valid dates, use existing end


            # Format dates for filename
            min_trn_date_str_chunk = final_chunk_start_date.strftime('%m-%d-%Y') if pd.notna(final_chunk_start_date) else "UNKNOWN_START"
            max_trn_date_str_chunk = final_chunk_end_date.strftime('%m-%d-%Y') if pd.notna(final_chunk_end_date) else "UNKNOWN_END"
            
            # Construct filename without _part_X suffix
            new_filename_date_range = f"{min_trn_date_str_chunk} TO {max_trn_date_str_chunk}"
            output_file_name = f"{base_filename_prefix} - {new_filename_date_range}.csv"
            output_file_path = os.path.join(branch_output_dir, output_file_name)

            try:
                # Save the current chunk to CSV
                # Reindex current_chunk_df to ensure only output_headers are present and in order
                current_chunk_df[output_headers].to_csv(output_file_path, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8-sig')
                print(f"Server Log (TRNM): Saved chunk {i+1}/{num_chunks} to: {output_file_path} (Size: {os.path.getsize(output_file_path)/ (1024 * 1024):.2f} MB)")
                total_files_generated += 1
            except Exception as e:
                print(f"Server Log (TRNM): ❌ Error writing CSV chunk '{output_file_name}': {e}")
                # Continue to next chunk/category even if one fails
                continue

    print(f"\nServer Log (TRNM): Processing complete! Total files generated: {total_files_generated}")
    return {"message": f"TRNM processing completed. Total files generated: {total_files_generated}. Output saved to {branch_output_dir}", "output_path": branch_output_dir}
