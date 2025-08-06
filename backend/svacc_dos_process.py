# svacc_dos_process.py (Modified: Hardcoded output path, replaced backup with delete, dynamic filename)
import os
import csv
from dbfread import DBF # Make sure you have dbfread installed: pip install dbfread
from datetime import datetime, timedelta
import pandas as pd
import re # Import regex for advanced cleaning

# Hardcoded path for DEPOSIT CODE CSV file
DEPOSIT_CODE_HARDCODED_PATH = r"C:\xampp\htdocs\audit_tool\DEPOSIT CODE.csv"

# Helper for aggressive string cleaning and normalization
def _clean_field(value):
    """Converts to string, strips, and normalizes common numerical representations.
    Returns an empty string '' for effectively blank values after cleaning.
    """
    if value is None:
        return '' 
    s_val = str(value).strip()
    
    # If it's an empty string after stripping, treat as empty string for consistent keys
    if not s_val:
        return '' 

    # Attempt to convert to int and back to string to handle '01' -> '1', '1.0' -> '1'
    try:
        # Check if it's purely numeric before converting to float/int
        if s_val.replace('.', '', 1).isdigit(): # Allows for decimals like '1.0'
            return str(int(float(s_val)))
    except ValueError:
        pass # Not a straightforward number, return original stripped string

    return s_val

def process_svacc_dos_data_web(input_dir, selected_branch): # Removed output_dir parameter
    """
    Processes DBF files from input_dir, extracts/formats SVACC DOS data,
    and combines them into a single CSV file in the hardcoded output directory.
    Output filename uses the selected branch name and the latest DOPEN date.
    Existing files with the same branch name are overwritten.

    Args:
        input_dir (str): The directory containing the DBF files.
        selected_branch (str): The branch selected by the user for output filename.
    """
    # Hardcoded output directory
    output_dir = r"C:\xampp\htdocs\audit_tool\OPERATIONS\SVACC"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Server Log (SVACC DOS): Starting DBF processing from {input_dir} for branch '{selected_branch}'")

    # Sanitize branch name for filename
    sanitized_branch = "".join([c for c in str(selected_branch) if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch:
        sanitized_branch = "UNSPECIFIED_BRANCH"

    # Define the output headers for the combined CSV
    headers = [
        'ACC', 'TYPE', 'GLCODE', 'CID', 'ACCNAME', 'DOPEN', 'DOLASTTRN',
        'BAL', 'INTRATE', 'MATDATE', 'CUMINTPD', 'CUMTAXW'
    ]

    # --- Read DEPOSIT CODE.csv for ACCNAME lookup ---
    # This will be a flat dictionary: {(type, glcode): product_name}
    deposit_code_lookup_map = {} 
    if not os.path.exists(DEPOSIT_CODE_HARDCODED_PATH):
        print(f"Server Log (SVACC DOS): DEPOSIT CODE file not found at {DEPOSIT_CODE_HARDCODED_PATH}. ACCNAME lookup will be skipped.")
    else:
        try:
            # Determine file type based on extension and read accordingly
            file_extension = os.path.splitext(DEPOSIT_CODE_HARDCODED_PATH)[1].lower()
            df_deposit_code = None
            loaded_file_type = "Unknown" 
            if file_extension == '.csv':
                df_deposit_code = pd.read_csv(DEPOSIT_CODE_HARDCODED_PATH, dtype=str)
                loaded_file_type = "CSV"
            elif file_extension in ('.xls', '.xlsx'):
                df_deposit_code = pd.read_excel(DEPOSIT_CODE_HARDCODED_PATH, dtype=str)
                loaded_file_type = "Excel"
            
            if df_deposit_code is not None:
                df_deposit_code.columns = [col.strip().upper() for col in df_deposit_code.columns] # Normalize column names

                if 'TYPE' in df_deposit_code.columns and 'GL CODE' in df_deposit_code.columns and 'PRODUCT' in df_deposit_code.columns:
                    # Iterate to build the lookup map
                    for index, row in df_deposit_code.iterrows():
                        type_val = _clean_field(row['TYPE']) # Use new cleaning function
                        gl_code_val_from_file = _clean_field(row['GL CODE']) # Cleaned GLCODE from DEPOSIT_CODE.csv row
                        product_name = str(row['PRODUCT']).strip() 

                        if type_val is None: # Skip entries without a valid type
                            continue

                        # Determine the GLCODE to use for the map key based on TYPE from DEPOSIT_CODE.csv
                        map_gl_key = gl_code_val_from_file # Default to original from file
                        if type_val != '14':
                            map_gl_key = 'xx' # Force 'xx' if TYPE is not '14' for mapping key

                        # Store mapping: (type, map_gl_key) -> product_name
                        deposit_code_lookup_map[(type_val, map_gl_key)] = product_name
                            
                    print(f"Server Log (SVACC DOS): Successfully loaded ACCNAME lookup map from {os.path.basename(DEPOSIT_CODE_HARDCODED_PATH)} ({loaded_file_type}).")
                else:
                    print(f"Server Log (SVACC DOS): DEPOSIT CODE file missing 'TYPE', 'GL CODE', or 'PRODUCT' columns. ACCNAME lookup skipped.")
            else:
                print(f"Server Log (SVACC DOS): Could not read DEPOSIT CODE file at {DEPOSIT_CODE_HARDCODED_PATH}. Unsupported format or error.")
        except Exception as e:
            print(f"Server Log (SVACC DOS): Error reading DEPOSIT CODE file {DEPOSIT_CODE_HARDCODED_PATH}: {e}. ACCNAME lookup will be skipped.")


    # Convert numeric date to real date with +2 days
    def convert_date(value, allow_blank=False):
        try:
            if allow_blank and (value in [None, '', 0]):
                return ''
            base_date = datetime(1899, 12, 30) + timedelta(days=int(value) + 2)
            return base_date.strftime('%m/%d/%Y')
        except (ValueError, TypeError):
            return ''

    # Format amount fields
    def format_amount(value):
        try:
            numeric_val = float(value)
            return f"{numeric_val / 100:,.2f}"
        except (ValueError, TypeError):
            return '0.00'

    # Format percentage
    def format_rate(value):
        try:
            numeric_val = float(value)
            return f"{numeric_val / 10000:.2%}" # Assuming rate is stored as integer * 10000
        except (ValueError, TypeError):
            return '0.00%'

    dbf_files_found = False
    processed_files_count = 0
    combined_data_rows = [] # List to collect all processed rows

    # Process each DBF file
    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith('.dbf') and not file_name.startswith('~'):
            dbf_files_found = True
            dbf_path = os.path.join(input_dir, file_name) # Correctly define dbf_path here

            print(f"Server Log (SVACC DOS): Processing file: {file_name}...")

            try:
                table = DBF(dbf_path, load=True, encoding='latin-1', ignore_missing_memofile=True)
                
                rows_in_current_dbf = []
                for record in table: 
                    # Compose ACC as XX-XXXXX-Y
                    acc_raw = str(record.get('ACC', '')).strip().zfill(7)
                    chd_raw = str(record.get('CHD', '')).strip().zfill(1)
                    acc = f"{acc_raw[:2]}-{acc_raw[2:]}-{chd_raw}"

                    # Get TYPE and GLCODE from DBF record and normalize them
                    record_type_cleaned = _clean_field(record.get('TYPE', '')) 
                    original_record_glcode_cleaned = _clean_field(record.get('GLCODE', '')) 
                    
                    # Determine the GLCODE that will be put into the output CSV AND used for lookup
                    final_glcode_for_output_and_lookup = original_record_glcode_cleaned # Default to original cleaned GLCODE from DBF
                    if record_type_cleaned != '14':
                        final_glcode_for_output_and_lookup = 'xx' # Force 'xx' if TYPE is not '14'
                        
                    # --- ACCNAME lookup logic (Uses (TYPE, final_glcode_for_output_and_lookup) for lookup) ---
                    accname = ''
                    
                    # The lookup key is the tuple (cleaned_TYPE_from_DBF, final_glcode_for_output_and_lookup)
                    lookup_key = (record_type_cleaned, final_glcode_for_output_and_lookup)
                    accname = deposit_code_lookup_map.get(lookup_key, '') 


                    row = {
                        'ACC': acc,
                        'TYPE': record_type_cleaned, # Use cleaned TYPE for output
                        'GLCODE': final_glcode_for_output_and_lookup, # Use the conditionally 'xx'-ed GLCODE for output CSV
                        'CID': str(record.get('CID', '') or ''),
                        'ACCNAME': accname, # Use the looked-up ACCNAME
                        'DOPEN': convert_date(record.get('DOPEN', 0)),
                        'DOLASTTRN': convert_date(record.get('DOLASTTRN', 0)),
                        'BAL': format_amount(record.get('BAL', 0)),
                        'INTRATE': format_rate(record.get('INTRATE', 0)),
                        'MATDATE': convert_date(record.get('MATDATE', 0), allow_blank=True),
                        'CUMINTPD': format_amount(record.get('CUMINTPD', 0)),
                        'CUMTAXW': format_amount(record.get('CUMTAXW', 0)),
                    }
                    rows_in_current_dbf.append(row)
                
                if rows_in_current_dbf:
                    combined_data_rows.extend(rows_in_current_dbf)
                    processed_files_count += 1
                    print(f"Server Log (SVACC DOS): ✅ Processed: {file_name} with {len(rows_in_current_dbf)} rows.")
                else:
                    print(f"Server Log (SVACC DOS): No valid records found in {file_name}.")

            except Exception as e:
                print(f"Server Log (SVACC DOS): ❌ Error processing {file_name}: {e}")
                # Do not re-raise here, allow other files to be processed
                continue

    if not dbf_files_found:
        raise Exception("No DBF files found in the specified input directory for SVACC DOS processing.")
    
    if not combined_data_rows:
        raise Exception("No valid data was processed or combined from any DBF files for SVACC DOS.")

    print("\nServer Log (SVACC DOS): All DBF files processed. Combining and saving results...")

    # Create DataFrame from all collected rows
    final_combined_df = pd.DataFrame(combined_data_rows, columns=headers)

    # Convert 'DOPEN' to datetime objects for finding the latest date
    final_combined_df['DOPEN_DT'] = pd.to_datetime(final_combined_df['DOPEN'], format='%m/%d/%Y', errors='coerce')
    
    latest_dopen_date_str = "UNKNOWN_DATE"
    if not final_combined_df['DOPEN_DT'].dropna().empty:
        latest_dopen = final_combined_df['DOPEN_DT'].max()
        latest_dopen_date_str = latest_dopen.strftime('%m-%d-%Y')

    # Define the output filename based on the selected branch and latest DOPEN date
    # Format: BRANCH - MM-DD-YYYY.csv
    new_output_filename = f"{sanitized_branch.upper()} - {latest_dopen_date_str}.csv"
    new_output_filepath = os.path.join(output_dir, new_output_filename)

    # Find and delete existing files for the same branch, regardless of date in their name
    # Regex to match files starting with the sanitized branch name and ending with .csv
    # Use re.escape to handle branch names with special regex characters (e.g., "DON CARLOS")
    branch_file_pattern = re.compile(rf'^{re.escape(sanitized_branch.upper())} - \d{{2}}-\d{{2}}-\d{{4}}\.csv$', re.IGNORECASE)
    
    for existing_file in os.listdir(output_dir):
        if branch_file_pattern.match(existing_file):
            existing_filepath = os.path.join(output_dir, existing_file)
            try:
                os.remove(existing_filepath)
                print(f"Server Log (SVACC DOS): Deleted old file: {existing_filepath}")
            except OSError as e:
                print(f"Server Log (SVACC DOS): Error deleting old file {existing_filepath}: {e}")

    # Save the combined DataFrame to CSV (this will be the new file)
    # Drop the temporary datetime column before saving
    final_combined_df.drop(columns=['DOPEN_DT'], inplace=True) 
    final_combined_df.to_csv(new_output_filepath, index=False, encoding='utf-8-sig')
    print(f"Server Log (SVACC DOS): ✅ Successfully combined and saved {len(final_combined_df)} rows to: {new_output_filepath}")

    print("\nServer Log (SVACC DOS): Processing complete!")
    return {"message": f"SVACC DOS processing completed. Output saved to {new_output_filepath}", "output_path": new_output_filepath}
