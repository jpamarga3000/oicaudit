# aging_conso.py (Revised for Web Integration with Append and Robust Deduplication)
import pandas as pd
import os

def col_letter_to_index(letter):
    """Converts an Excel column letter (e.g., 'A', 'AB') to a 0-based index."""
    index = 0
    for i, char in enumerate(reversed(letter.upper())):
        index += (ord(char) - ord('A') + 1) * (26 ** i)
    return index - 1 # Convert to 0-based index

def standardize_dataframe_for_deduplication(df, required_output_columns):
    """
    Applies consistent standardization across relevant columns of a DataFrame
    to ensure robust deduplication and correct handling of blank values.
    """
    # Ensure all required columns are present and in the correct order, fill missing with empty strings
    df = df.reindex(columns=required_output_columns).fillna('')

    # Process each column based on its expected type/behavior
    for col in required_output_columns:
        # Convert to string first to ensure .str accessor works and for consistency
        df[col] = df[col].astype(str)

        # Standardize common representations of blank/missing data to actual empty string
        # This handles 'nan', 'NAN', 'N/A', 'NA', 'None' strings, ensuring they become ''
        df[col] = df[col].replace(['nan', 'NAN', 'N/A', 'NA', 'None'], '', regex=True)
        
        # Remove leading/trailing whitespace for all string values
        df[col] = df[col].str.strip()

        # Specific handling for numerical columns (e.g., 'PRINCIPAL', 'BALANCE')
        # Removed 'AGING' from this list
        if col in ['PRINCIPAL', 'BALANCE']:
            # Log raw values before numeric conversion for debugging
            # print(f"Server Log: Standardizing '{col}' column - Raw values before numeric conversion (first 5): {df[col].head().tolist()}")
            
            # Convert to numeric, coerce errors to NaN (e.g., non-numeric text becomes NaN)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Log values after numeric conversion, before rounding
            # print(f"Server Log: Standardizing '{col}' column - Values after numeric conversion (first 5): {df[col].head().tolist()}")
            
            # Round to 2 decimal places if it's a float, then convert to string
            df[col] = df[col].round(2)
            df[col] = df[col].astype(str).replace({'nan': ''}) # Replace NaN with empty string after numeric conversion
            
            # Log values after rounding and final string conversion
            # print(f"Server Log: Standardizing '{col}' column - Final values after rounding and string conversion (first 5): {df[col].head().tolist()}")


        # Specific handling for date columns
        elif col in ['DISBDATE', 'DUE DATE']:
            # Convert to datetime, coerce errors to NaT, format to mm/dd/yyyy, then replace NaT with empty string
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%m/%d/%Y').replace({pd.NaT: ''})

        # Specific handling for 'ACCOUNT' column (to preserve ="..." format)
        elif col == 'ACCOUNT':
            df[col] = df[col].apply(
                lambda x: f'="{x.strip().upper()[1:-1]}"' if isinstance(x, str) and x.startswith('="') and x.endswith('"') else x.strip().upper()
            )
        # General string columns (applies to 'BRANCH', 'DATE', 'CID', 'NAME OF MEMBER', 'LOAN ACCT.', 'GL CODE', 'PRODUCT', 'REF', 'DESC', 'GROUP', 'TRN' and now 'AGING')
        else:
            df[col] = df[col].str.upper() # Apply uppercase after stripping and specific replacements

    return df # Return the standardized DataFrame

def process_excel_files_to_csv(input_dir, output_dir):
    """
    Combines data from multiple Excel files, extracts specific columns based on
    their column letters from only specified monthly sheets (JAN-DEC),
    starting data from row 2, and generates separate CSV files for each unique branch.
    Ensures DISBDATE and DUE DATE are formatted as mm/dd/yyyy.
    Branch names are treated as case-insensitive for grouping.

    If a CSV file for a branch already exists, new data for that branch will be
    appended, and then all duplicate rows (across existing and new data) will be
    removed before saving. Data standardization is applied for robust deduplication,
    and existing files with spaces in their names are also considered for appending.

    Args:
        input_dir (str): The directory containing the Excel files.
        output_dir (str): The directory where the CSV files will be saved.
    """

    # New mapping: Desired output header name -> Excel column letter
    column_letter_map = {
        'BRANCH': 'B',
        'DATE': 'C',
        'CID': 'D',
        'NAME OF MEMBER': 'E',
        'LOAN ACCT.': 'F',
        'PRINCIPAL': 'G',
        'BALANCE': 'H',
        'GL CODE': 'I',
        'PRODUCT': 'J',
        'DISBDATE': 'S',
        'DUE DATE': 'T',
        'AGING': 'AB',
        'GROUP': 'AD'
    }

    # The exact order of columns for the final CSV output
    required_output_columns = [
        'BRANCH', 'DATE', 'CID', 'NAME OF MEMBER', 'LOAN ACCT.',
        'PRINCIPAL', 'BALANCE', 'GL CODE', 'PRODUCT', 'DISBDATE',
        'DUE DATE', 'AGING', 'GROUP'
    ]

    # Define the specific sheet names to process (case-insensitive check will be used)
    allowed_sheet_names = [
        'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
        'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'
    ]

    all_data_frames = [] # List to store data from all allowed sheets across all files

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Server Log: Created output directory: {output_dir}")

    print(f"Server Log: Scanning for Excel files in: {input_dir}")
    # Iterate through all files in the input directory
    excel_files_found = False
    for filename in os.listdir(input_dir):
        if filename.endswith(('.xls', '.xlsx')):
            excel_files_found = True
            file_path = os.path.join(input_dir, filename)
            print(f"Server Log: Processing file: {filename}")
            try:
                # Read all sheets from the Excel file without assuming any header
                excel_data = pd.read_excel(file_path, sheet_name=None, header=None)

                for sheet_name, df_raw in excel_data.items():
                    # Only process sheets that are in our allowed_sheet_names list (case-insensitive)
                    if sheet_name.upper() in allowed_sheet_names:
                        print(f"Server Log:   Processing sheet: {sheet_name}")

                        df_filtered = pd.DataFrame()
                        found_all_columns = True

                        for new_header, col_letter in column_letter_map.items():
                            col_idx = col_letter_to_index(col_letter)

                            if col_idx < df_raw.shape[1]:
                                # Extract data from the raw DataFrame
                                df_filtered[new_header] = df_raw.iloc[:, col_idx]

                                # --- START OF NEW LOGGING FOR AGING COLUMN ---
                                if new_header == 'AGING':
                                    print(f"Server Log:     Raw '{new_header}' (Column {col_letter}) data from sheet '{sheet_name}' (first 5 rows):")
                                    print(df_raw.iloc[:, col_idx].head().tolist())
                                # --- END OF NEW LOGGING ---

                            else:
                                print(f"Server Log:     Warning: Column '{col_letter}' for '{new_header}' not found in sheet '{sheet_name}' of '{filename}'. Skipping sheet.")
                                found_all_columns = False
                                break

                        if not found_all_columns:
                            continue

                        # Data starts from row 2, so skip the first row (index 0)
                        # --- START OF NEW LOGGING FOR AGING COLUMN ---
                        if 'AGING' in df_filtered.columns:
                            print(f"Server Log:     'AGING' column after initial extraction, before row 1 skip (first 5 rows):")
                            print(df_filtered['AGING'].head().tolist())
                        # --- END OF NEW LOGGING ---

                        df_filtered = df_filtered.iloc[1:].reset_index(drop=True)

                        # --- START OF NEW LOGGING FOR AGING COLUMN ---
                        if 'AGING' in df_filtered.columns:
                            print(f"Server Log:     'AGING' column after skipping first row (first 5 rows):")
                            print(df_filtered['AGING'].head().tolist())
                        # --- END OF NEW LOGGING ---


                        # --- Initial Date Formatting for new data (will be re-standardized later) ---
                        for date_col in ['DISBDATE', 'DUE DATE']:
                            if date_col in df_filtered.columns:
                                df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')
                                df_filtered[date_col] = df_filtered[date_col].dt.strftime('%m/%d/%Y')
                                df_filtered[date_col] = df_filtered[date_col].replace({pd.NaT: ''})

                        # Ensure the columns are in the specified output order
                        df_filtered = df_filtered[required_output_columns]

                        all_data_frames.append(df_filtered)
                    else:
                        print(f"Server Log:   Disregarding sheet: {sheet_name} (not a monthly sheet)")

            except Exception as e:
                print(f"Server Log: Error processing file {filename}: {e}")
                # Re-raise the exception to be caught by the Flask app for error reporting
                raise Exception(f"Failed to process file {filename}: {e}")

    if not excel_files_found:
        raise Exception("No Excel files (.xls or .xlsx) found in the specified input directory.")

    if not all_data_frames:
        raise Exception("No valid data found in any allowed monthly sheets across Excel files. No CSV files will be generated.")

    # Concatenate all collected data frames into a single DataFrame
    combined_df = pd.concat(all_data_frames, ignore_index=True)
    print("Server Log: All relevant Excel data combined.")

    # --- Case-insensitive Branch Grouping ---
    combined_df['BRANCH'] = combined_df['BRANCH'].astype(str).str.upper()
    unique_branches = combined_df['BRANCH'].unique()
    print(f"Server Log: Found {len(unique_branches)} unique branches.")

    # Generate CSV for each unique branch
    for branch_name in unique_branches:
        # Sanitize the branch name for the target output filename (using underscores)
        sanitized_branch_name_for_output = "".join([c for c in str(branch_name) if c.isalnum() or c in (' ', '_')]).strip()
        sanitized_branch_name_for_output = sanitized_branch_name_for_output.replace(' ', '_')

        if not sanitized_branch_name_for_output:
            print(f"Server Log: Warning: Skipping branch with empty or invalid name: '{branch_name}'")
            continue

        # Define the target CSV filename using the sanitized (underscore) format
        target_csv_filename = f"{sanitized_branch_name_for_output}.csv"
        target_csv_path = os.path.join(output_dir, target_csv_filename)

        # Check for an existing file to append to.
        # This could be the target_csv_path itself, or an equivalent name with spaces.
        existing_file_to_append_path = None

        # 1. Check if the target (underscore) format file already exists
        if os.path.exists(target_csv_path):
            existing_file_to_append_path = target_csv_path
        else:
            # 2. If not, iterate through files in the output directory
            #    to find if a file with spaces exists that corresponds to this branch.
            for existing_filename in os.listdir(output_dir):
                if existing_filename.lower().endswith('.csv'):
                    # Normalize the existing filename for comparison (convert spaces to underscores)
                    normalized_existing_filename = existing_filename.lower().replace(' ', '_').replace('.csv', '')
                    
                    # Compare the normalized existing filename with our sanitized branch name (lowercase)
                    if normalized_existing_filename == sanitized_branch_name_for_output.lower():
                        # Found a match, use this existing file path
                        existing_file_to_append_path = os.path.join(output_dir, existing_filename)
                        break # Found it, no need to check further

        branch_df = combined_df[combined_df['BRANCH'] == branch_name].copy() 

        # --- Append and Deduplicate Logic ---
        if existing_file_to_append_path:
            print(f"Server Log: Existing file found for '{branch_name}' (normalized to '{sanitized_branch_name_for_output}'): {existing_file_to_append_path}. Appending new data.")
            try:
                # Read existing CSV, treating all columns as strings initially to prevent type issues
                existing_df = pd.read_csv(existing_file_to_append_path, dtype=str, keep_default_na=False)
                
                # Standardize both dataframes before concatenation for robust deduplication
                existing_df_standardized = standardize_dataframe_for_deduplication(existing_df, required_output_columns)
                branch_df_standardized = standardize_dataframe_for_deduplication(branch_df, required_output_columns)

                # Concatenate existing data with new data
                combined_branch_df = pd.concat([existing_df_standardized, branch_df_standardized], ignore_index=True)

                # Remove duplicates from the combined DataFrame based on all columns
                # Keep 'first' to retain the first occurrence in case of exact duplicates.
                deduplicated_branch_df = combined_branch_df.drop_duplicates(keep='first').reset_index(drop=True)
                print(f"Server Log: Deduplicated {len(combined_branch_df) - len(deduplicated_branch_df)} duplicate rows for '{branch_name}'.")

                # After successful deduplication and before saving, if the original
                # existing_file_to_append_path was different from target_csv_path (i.e., had spaces),
                # delete the old file before saving the new, canonical one.
                if existing_file_to_append_path != target_csv_path:
                    print(f"Server Log: Replacing '{existing_file_to_append_path}' with '{target_csv_path}' for consistency.")
                    os.remove(existing_file_to_append_path) # Remove the old file with spaces
                
                # Save the deduplicated combined data back to the CSV
                # No need for specific 'ACCOUNT' formatting here as it's handled in standardize_dataframe_for_deduplication
                deduplicated_branch_df.to_csv(target_csv_path, index=False) # Always save to the target_csv_path
                print(f"Server Log: Appended and deduplicated data for branch '{branch_name}': {target_csv_path}")

            except Exception as e:
                print(f"Server Log: Error appending/deduplicating to file {existing_file_to_append_path}: {e}")
                # If there's an error in appending, still try to save the new data (without append/dedup logic)
                # Ensure the new data is standardized even if append failed.
                branch_df_standardized_on_error = standardize_dataframe_for_deduplication(branch_df, required_output_columns)
                branch_df_standardized_on_error.to_csv(target_csv_path, index=False)
                print(f"Server Log: Saved new data only for branch '{branch_name}' due to append error: {e}")
        else:
            # If no existing file found (either underscore or space format matching the branch),
            # just save the new data to the target (underscore) format.
            # Apply standardization to branch_df before saving for the first time.
            branch_df_standardized = standardize_dataframe_for_deduplication(branch_df, required_output_columns)
            try:
                branch_df_standardized.to_csv(target_csv_path, index=False)
                print(f"Server Log: Generated new CSV for branch '{branch_name}': {target_csv_path}")
            except Exception as e:
                print(f"Server Log: Error generating CSV for branch '{branch_name}': {e}")
                raise Exception(f"Failed to generate CSV for branch '{branch_name}': {e}")

    print("\nServer Log: Process completed successfully!")
