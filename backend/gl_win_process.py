# gl_win_process.py
import pandas as pd
import os
from datetime import datetime, timedelta
import csv
from io import StringIO
import re
import math # MODIFIED: Import the math module

# Define the maximum file size in bytes (49.9 MB)
MAX_FILE_SIZE_BYTES = 49.9 * 1024 * 1024

# Define the fixed base output directory for General Ledger
FIXED_BASE_OUTPUT_DIR = r"C:\xampp\htdocs\audit_tool\ACCOUTNING\GENERAL LEDGER"

def process_gl_win_data_web(input_dir, branch):
    """
    Processes GL WIN CSV files from input_dir, combines them,
    renames/transforms columns, and saves the combined CSV to a branch-specific subfolder
    within FIXED_BASE_OUTPUT_DIR.

    Files are named 'BRANCH - MM-DD-YYYY TO MM-DD-YYYY.csv'.
    New data is appended to the existing file with the latest 'date to'
    if it fits within MAX_FILE_SIZE_BYTES. Otherwise, a new file is created
    with a date range reflecting its content. No '_part_X' suffixes are used.

    Args:
        input_dir (str): The directory containing the GL WIN CSV files.
        branch (str): The selected branch name for output filename and subfolder.
    """
    # Sanitize the branch name for use in filenames and folder names
    sanitized_branch = "".join([c for c in str(branch) if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_').upper()
    if not sanitized_branch:
        sanitized_branch = "UNSPECIFIED_BRANCH"

    # Construct the branch-specific output directory
    branch_output_dir = os.path.join(FIXED_BASE_OUTPUT_DIR, sanitized_branch)
    os.makedirs(branch_output_dir, exist_ok=True)

    print(f"Server Log (GL WIN): Starting CSV data processing from {input_dir} for branch '{branch}'")

    all_data = []
    csv_files_found = False
    
    # Define the mapping from old column names to new column names
    column_mapping = {
        'Trn': 'TRN',
        'GLAcc': 'GLACC',
        'ExpAcc': 'ACCOUNT',
        'PostDate': 'DOCDATE',
        'Ref': 'REF',
        'TrnAmt': 'AMT',
        'FullDesc': 'DESC',
        'BalAmt': 'BAL'
    }

    # Define the final desired order of columns
    final_output_columns = ['TRN', 'GLACC', 'ACCOUNT', 'DOCDATE', 'REF', 'AMT', 'DESC', 'BAL']

    # Function to format ACCOUNT (MODIFIED for more flexibility)
    def format_account(value):
        """
        Formats the account value. If it's a 5 or 9 digit number, it applies the
        specific formatting. Otherwise, it returns the value as is (trimmed string).
        """
        s_value = str(value).strip()
        if len(s_value) == 9 and s_value.isdigit():
            return f"{s_value[0]}-{s_value[1:3]}-{s_value[3:5]}-{s_value[5:]}"
        elif len(s_value) == 5 and s_value.isdigit():
            return f"{s_value[0]}-{s_value[1:3]}-{s_value[3:]}"
        else:
            return s_value

    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.csv'):
            csv_files_found = True
            file_path = os.path.join(input_dir, filename)
            print(f"Server Log (GL WIN): Processing file: {file_path}")

            try:
                df = pd.read_csv(file_path, dtype=str, encoding='latin1')

                required_input_cols = list(column_mapping.keys())
                if not all(col in df.columns for col in required_input_cols):
                    print(f"Server Log (GL WIN): Skipping {filename}: Missing one or more required input columns ({', '.join(required_input_cols)}).")
                    continue

                df.rename(columns=column_mapping, inplace=True)

                if 'ACCOUNT' in df.columns:
                    df['ACCOUNT'] = df['ACCOUNT'].apply(format_account)
                    df['ACCOUNT'] = df['ACCOUNT'].apply(lambda x: f'="{x}"' if x else '')
                else:
                    print(f"Server Log (GL WIN): Warning: 'ExpAcc' (ACCOUNT) column not found in {filename}.")

                if 'DOCDATE' in df.columns:
                    df['DOCDATE'] = pd.to_datetime(df['DOCDATE'], errors='coerce')
                else:
                    print(f"Server Log (GL WIN): Warning: 'PostDate' (DOCDATE) column not found in {filename}.")

                for col in ['AMT', 'BAL']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) / 100
                    else:
                        print(f"Server Log (GL WIN): Warning: '{col}' column not found in {filename}. Skipping transformation.")

                for col in final_output_columns:
                    if col not in df.columns:
                        df[col] = ''
                
                df = df[final_output_columns]
                all_data.append(df)

            except Exception as e:
                print(f"Server Log (GL WIN): ❌ Error processing {filename}: {e}. Skipping this file.")
                continue

    if not csv_files_found:
        raise Exception("No CSV files found in the specified input directory for GL WIN processing.")
    
    if not all_data:
        raise Exception("No valid data was processed or combined for GL WIN. No CSV will be generated.")

    combined_df = pd.concat(all_data, ignore_index=True)
    print("\nServer Log (GL WIN): All relevant CSV data combined.")

    print("Server Log (GL WIN): Sorting combined data by DOCDATE...")
    combined_df['DOCDATE_TEMP'] = pd.to_datetime(combined_df['DOCDATE'], errors='coerce')
    combined_df.sort_values(by='DOCDATE_TEMP', inplace=True)
    combined_df.drop(columns=['DOCDATE_TEMP'], inplace=True)
    combined_df.reset_index(drop=True, inplace=True)

    # --- File Saving and Appending Logic ---
    current_data_start_row = 0
    
    print("Server Log (GL WIN): Starting CSV file saving and appending...")

    # Function to parse date from filename (MM-DD-YYYY)
    def parse_date_from_filename(filename):
        match = re.search(r'TO (\d{2}-\d{2}-\d{4})\.csv$', filename)
        if match:
            try:
                return datetime.strptime(match.group(1), '%m-%d-%Y')
            except ValueError:
                return None
        return None

    # Helper to get the latest file and its end date
    def get_latest_existing_file_info(output_dir, branch_name_prefix):
        latest_file_path = None
        latest_date_to = None
        for fname in os.listdir(output_dir):
            if fname.startswith(branch_name_prefix) and fname.endswith('.csv'):
                file_date_to = parse_date_from_filename(fname)
                if file_date_to:
                    if latest_date_to is None or file_date_to > latest_date_to:
                        latest_date_to = file_date_to
                        latest_file_path = os.path.join(output_dir, fname)
        return latest_file_path, latest_date_to

    # --- Main Loop for Splitting and Saving ---
    while current_data_start_row < len(combined_df):
        latest_file_path, latest_date_to = get_latest_existing_file_info(branch_output_dir, sanitized_branch)
        
        file_written_or_appended = False

        # MODIFIED: Initialize estimated_bytes_per_row and header_size_bytes at the start of the loop
        estimated_bytes_per_row = 100 # Default value
        header_size_bytes = 0 # Default value

        # Calculate header size once per function call, not per loop iteration
        # MODIFIED: Ensure header_size_bytes is calculated only once
        if header_size_bytes == 0:
            temp_s_buf = StringIO()
            pd.DataFrame(columns=final_output_columns).to_csv(temp_s_buf, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8-sig')
            header_size_bytes = len(temp_s_buf.getvalue().encode('utf-8-sig'))


        # Estimate average row size from a sample if data is not empty
        if not combined_df.empty:
            sample_df_for_size = combined_df.head(min(100, len(combined_df)))
            s_buf_sample = StringIO()
            sample_df_for_size.to_csv(s_buf_sample, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8-sig', header=False) # No header
            if len(sample_df_for_size) > 0:
                estimated_bytes_per_row = len(s_buf_sample.getvalue().encode('utf-8-sig')) / len(sample_df_for_size)
            else:
                estimated_bytes_per_row = 100 # Fallback if sample is empty
        else:
            estimated_bytes_per_row = 100 # Default if overall data is empty


        if latest_file_path and os.path.exists(latest_file_path):
            existing_file_size = os.path.getsize(latest_file_path)
            
            # Try to append as many rows as possible without exceeding MAX_FILE_SIZE_BYTES
            rows_to_append = 0
            
            # Calculate how many rows can fit into the remaining space
            remaining_space = MAX_FILE_SIZE_BYTES - existing_file_size
            if remaining_space > 0 and estimated_bytes_per_row > 0:
                max_rows_to_append = math.floor(remaining_space / estimated_bytes_per_row)
                rows_to_append = min(max_rows_to_append, len(combined_df) - current_data_start_row)
            
            if rows_to_append > 0:
                chunk_for_append = combined_df.iloc[current_data_start_row : current_data_start_row + rows_to_append]
                
                # Format the chunk for CSV output (without header)
                chunk_for_csv_output = chunk_for_append.copy()
                for col in ['AMT', 'BAL']:
                    chunk_for_csv_output[col] = pd.to_numeric(chunk_for_csv_output[col], errors='coerce').fillna(0)
                    chunk_for_csv_output[col] = chunk_for_csv_output[col].apply(lambda x: f"{x:,.2f}")
                chunk_for_csv_output['DOCDATE'] = pd.to_datetime(chunk_for_csv_output['DOCDATE'], errors='coerce').dt.strftime('%m/%d/%Y').fillna('')

                s_buf_append = StringIO()
                chunk_for_csv_output.to_csv(s_buf_append, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8-sig', header=False) # No header
                content_to_append = s_buf_append.getvalue()

                # Double check size before writing
                if existing_file_size + len(content_to_append.encode('utf-8-sig')) <= MAX_FILE_SIZE_BYTES:
                    with open(latest_file_path, mode='a', newline='', encoding='utf-8-sig') as f:
                        f.write(content_to_append)
                    print(f"Server Log (GL WIN): Appended {rows_to_append} rows to: {latest_file_path} (New Size: {os.path.getsize(latest_file_path)/ (1024 * 1024):.2f} MB)")
                    
                    # After appending, re-read, deduplicate, and overwrite to update date range
                    temp_df_for_dedup = pd.read_csv(latest_file_path, dtype=str, keep_default_na=False)
                    deduplicated_df = temp_df_for_dedup.drop_duplicates(keep='first').reset_index(drop=True)

                    deduplicated_df['DOCDATE'] = pd.to_datetime(deduplicated_df['DOCDATE'], errors='coerce', format='%m/%d/%Y')
                    actual_min_date = deduplicated_df['DOCDATE'].min() if not deduplicated_df['DOCDATE'].dropna().empty else pd.NaT
                    actual_max_date = deduplicated_df['DOCDATE'].max() if not deduplicated_df['DOCDATE'].dropna().empty else pd.NaT

                    min_date_str = actual_min_date.strftime('%m-%d-%Y') if pd.notna(actual_min_date) else "UNKNOWN_START"
                    max_date_str = actual_max_date.strftime('%m-%d-%Y') if pd.notna(actual_max_date) else "UNKNOWN_END"

                    new_filename_for_updated_file = f"{sanitized_branch} - {min_date_str} TO {max_date_str}.csv"
                    new_file_path_for_updated_file = os.path.join(branch_output_dir, new_filename_for_updated_file)

                    s_buf_dedup = StringIO()
                    deduplicated_df['DOCDATE'] = deduplicated_df['DOCDATE'].dt.strftime('%m/%d/%Y').fillna('') # Re-format DOCDATE to string for saving
                    deduplicated_df.to_csv(s_buf_dedup, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8-sig')
                    deduplicated_content = s_buf_dedup.getvalue()

                    if latest_file_path != new_file_path_for_updated_file:
                        os.remove(latest_file_path)
                        print(f"Server Log (GL WIN): Renamed/Moved old file: {latest_file_path} to {new_file_path_for_updated_file}")
                    
                    with open(new_file_path_for_updated_file, mode='w', newline='', encoding='utf-8-sig') as f:
                        f.write(deduplicated_content)
                    print(f"Server Log (GL WIN): Overwrote/Updated file after deduplication: {new_file_path_for_updated_file} (Size: {os.path.getsize(new_file_path_for_updated_file)/ (1024 * 1024):.2f} MB)")
                    
                    current_data_start_row += rows_to_append
                    file_written_or_appended = True
                else:
                    print(f"Server Log (GL WIN): Appending {rows_to_append} rows would exceed limit. Creating new file.")
            else:
                print(f"Server Log (GL WIN): No space to append to {latest_file_path}. Creating new file.")
        
        if not file_written_or_appended:
            # If no appendable file was found, or the latest was full, create a new file.
            # Calculate how many rows from the current data can fit into a new file (including header)
            
            # Estimate rows per chunk for a new file
            if estimated_bytes_per_row > 0:
                max_rows_for_new_file = math.floor((MAX_FILE_SIZE_BYTES - header_size_bytes) / estimated_bytes_per_row)
                rows_for_new_file = min(max_rows_for_new_file, len(combined_df) - current_data_start_row)
            else:
                rows_for_new_file = len(combined_df) - current_data_start_row # If no estimate, take all remaining

            if rows_for_new_file <= 0: # Ensure at least 1 row if there's data left
                if len(combined_df) - current_data_start_row > 0:
                    rows_for_new_file = 1
                else:
                    break # No more data to process

            current_chunk_df = combined_df.iloc[current_data_start_row : current_data_start_row + rows_for_new_file].copy()

            if current_chunk_df.empty:
                break # No more data to process

            # Ensure DOCDATE column is datetime objects for min/max operations
            if not pd.api.types.is_datetime64_any_dtype(current_chunk_df['DOCDATE']):
                current_chunk_df['DOCDATE'] = pd.to_datetime(current_chunk_df['DOCDATE'], errors='coerce')


            # Determine date range for the current chunk
            valid_dates_in_chunk = current_chunk_df['DOCDATE'].dropna()

            chunk_min_date_val = None
            chunk_max_date_val = None

            if not valid_dates_in_chunk.empty:
                chunk_min_date_val = valid_dates_in_chunk.min()
                chunk_max_date_val = valid_dates_in_chunk.max()
            
            min_date_str = chunk_min_date_val.strftime('%m-%d-%Y') if pd.notna(chunk_min_date_val) else "UNKNOWN_START"
            max_date_str = chunk_max_date_val.strftime('%m-%d-%Y') if pd.notna(chunk_max_date_val) else "UNKNOWN_END"

            new_output_filename = f"{sanitized_branch} - {min_date_str} TO {max_date_str}.csv"
            new_output_file_path = os.path.join(branch_output_dir, new_output_filename)

            # Format the current chunk for CSV output (with header)
            chunk_for_csv_output = current_chunk_df.copy()
            for col in ['AMT', 'BAL']:
                chunk_for_csv_output[col] = pd.to_numeric(chunk_for_csv_output[col], errors='coerce').fillna(0)
                chunk_for_csv_output[col] = chunk_for_csv_output[col].apply(lambda x: f"{x:,.2f}")
            chunk_for_csv_output['DOCDATE'] = pd.to_datetime(chunk_for_csv_output['DOCDATE'], errors='coerce').dt.strftime('%m/%d/%Y').fillna('')

            s_buf_new_file = StringIO()
            chunk_for_csv_output.to_csv(s_buf_new_file, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8-sig')
            content_for_new_file = s_buf_new_file.getvalue()

            with open(new_output_file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                f.write(content_for_new_file)
            print(f"Server Log (GL WIN): ✅ Saved new file: {new_output_file_path} (Size: {os.path.getsize(new_output_file_path)/ (1024 * 1024):.2f} MB)")
            
            current_data_start_row += rows_for_new_file

    print(f"\nServer Log (GL WIN): Processing complete! Output saved to {branch_output_dir}")
    return {"message": f"GL WIN processing completed. Output saved to {branch_output_dir}", "output_path": branch_output_dir}
