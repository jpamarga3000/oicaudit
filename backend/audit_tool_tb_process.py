# audit_tool/backend/audit_tool_tb_process.py
import os
import pandas as pd
import re
from datetime import datetime
import csv # Import the csv module

# Import TB_BASE_DIR from db_common
from backend.db_common import TRIAL_BALANCE_BASE_DIR

# Helper function for GL Code formatting (removes hyphens)
def format_gl_code_for_tb_output(code):
    """
    Formats a GL Code string by removing all non-digit characters.
    This is specifically for the GLCODE column in the new TB output.
    """
    if pd.isna(code) or code is None:
        return ''
    return ''.join(filter(str.isdigit, str(code).strip()))

# Helper function for currency formatting (reused from accounting_process)
def format_currency_for_tb_output(value):
    """
    Formats a numeric value to a currency string with comma separators,
    two decimal places. Returns blank string if value is NaN or None.
    """
    if pd.isna(value) or value is None:
        return ''
    
    num_val = float(value)
    return "{:,.2f}".format(num_val)

def process_audit_tool_tb_files(input_dir):
    """
    Processes uploaded Trial Balance Excel/CSV files, extracts branch and date from content,
    and saves them into branch-specific subfolders within TB_BASE_DIR.
    """
    processed_files_info = []
    skipped_files_info = [] # List to store info about skipped files
    all_data_frames = [] # To collect all dataframes before processing
    overall_output_base_dir = TRIAL_BALANCE_BASE_DIR # Base directory for all TB outputs

    # Ensure the base output directory exists
    os.makedirs(overall_output_base_dir, exist_ok=True)
    print(f"Server Log (TB File Process): Ensuring base output directory exists: {overall_output_base_dir}")

    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        
        # Skip directories and non-file entries
        if not os.path.isfile(file_path):
            continue

        print(f"Server Log (TB File Process): Reading file: {filename}")

        df = None
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='ISO-8859-1')
            elif filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                skip_reason = f"Unsupported file type. Expected .csv, .xls, or .xlsx."
                print(f"Server Log (TB File Process): Skipping {filename}: {skip_reason}")
                skipped_files_info.append(f"{filename}: {skip_reason}")
                continue
        except Exception as e:
            skip_reason = f"Error reading file: {e}"
            print(f"Server Log (TB File Process): Error reading {filename}: {skip_reason}")
            skipped_files_info.append(f"{filename}: {skip_reason}")
            continue

        if df is None or df.empty:
            skip_reason = "No data or empty DataFrame."
            print(f"Server Log (TB File Process): {skip_reason} for {filename}")
            skipped_files_info.append(f"{filename}: {skip_reason}")
            continue

        # Normalize DataFrame column names for robust matching (strip whitespace and convert to uppercase)
        df.columns = [col.strip().upper() for col in df.columns]

        # Ensure required columns exist for the actual TB data (now using normalized names)
        # These are the columns that must be present in the input file for processing
        required_input_columns = ['BRANCH', 'DATE', 'GL CODE', 'DESCRIPTION', 'DEBIT', 'CREDIT']
        
        # Check if all required columns are present after normalization
        if not all(col in df.columns for col in required_input_columns):
            missing_cols = [col for col in required_input_columns if col not in df.columns]
            skip_reason = (f"Missing required input columns. Expected: {', '.join(required_input_columns)}. "
                           f"Missing: {', '.join(missing_cols)}.")
            print(f"Server Log (TB File Process): Skipping {filename}: {skip_reason}")
            skipped_files_info.append(f"{filename}: {skip_reason}")
            continue

        # Filter out rows where 'GL CODE' is NaN or empty
        df_filtered = df[df['GL CODE'].notna() & (df['GL CODE'] != '')].copy()

        if df_filtered.empty:
            skip_reason = "No valid 'GL CODE' entries found after filtering."
            print(f"Server Log (TB File Process): {skip_reason} in {filename}.")
            skipped_files_info.append(f"{filename}: {skip_reason}")
            continue

        # Append the filtered DataFrame to the list
        all_data_frames.append(df_filtered)

    if not all_data_frames:
        response_message = "No valid data frames were processed from the uploaded files."
        if skipped_files_info:
            response_message += "\n" + "The following files were skipped or encountered errors:\n" + "\n".join(skipped_files_info)
        return {"message": response_message, "output_path": overall_output_base_dir}

    # Concatenate all dataframes into one
    combined_df = pd.concat(all_data_frames, ignore_index=True)

    # --- Data Cleaning and Transformation on the combined DataFrame ---

    # Normalize BRANCH column values (strip whitespace and convert to uppercase)
    combined_df['BRANCH'] = combined_df['BRANCH'].astype(str).str.strip().str.upper()

    # Convert 'DATE' column to datetime objects
    # This handles various date formats present in the column
    def parse_date_robustly(date_value):
        if pd.isna(date_value):
            return pd.NaT # Not a Time
        if isinstance(date_value, datetime):
            return date_value
        
        date_str = str(date_value).split(' ')[0] # Take only date part, ignore time
        possible_formats = ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%Y%m%d']
        for fmt in possible_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return pd.NaT # Return Not a Time if no format matches

    combined_df['DATE'] = combined_df['DATE'].apply(parse_date_robustly)
    
    # Remove rows where DATE could not be parsed
    combined_df.dropna(subset=['DATE'], inplace=True)
    if combined_df.empty:
        response_message = "No valid Trial Balance data found after date parsing."
        if skipped_files_info:
            response_message += "\n" + "The following files were skipped or encountered errors:\n" + "\n".join(skipped_files_info)
        return {"message": response_message, "output_path": overall_output_base_dir}

    # 1. Create GLCODE from 'GL CODE' (remove hyphens)
    combined_df['GLCODE'] = combined_df['GL CODE'].apply(format_gl_code_for_tb_output)

    # 2. Rename columns to desired output headers
    combined_df = combined_df.rename(columns={
        'GL CODE': 'GLACC',
        'DESCRIPTION': 'GLNAME',
        'DEBIT': 'DR',
        'CREDIT': 'CR'
    })

    # 3. Convert DR and CR to numeric and apply currency formatting
    combined_df['DR'] = pd.to_numeric(combined_df['DR'], errors='coerce').fillna(0).apply(format_currency_for_tb_output)
    combined_df['CR'] = pd.to_numeric(combined_df['CR'], errors='coerce').fillna(0).apply(format_currency_for_tb_output)
    
    # Define the final output columns
    final_output_columns = ['GLCODE', 'GLACC', 'GLNAME', 'DR', 'CR']

    # Group by BRANCH and DATE to create separate output files
    # Use .dt.date to group by date part only, ignoring time
    grouped_data = combined_df.groupby(['BRANCH', combined_df['DATE'].dt.date])

    for (branch_name, report_date), group_df in grouped_data:
        branch_name_str = str(branch_name).strip().upper()
        report_date_dt = pd.to_datetime(report_date) # Convert to datetime object for formatting
        
        # Define branch-specific output directory
        branch_output_dir = os.path.join(overall_output_base_dir, branch_name_str)
        os.makedirs(branch_output_dir, exist_ok=True) # Create branch-specific subfolder

        # Define the final output CSV filename (MM-DD-YYYY.csv)
        output_file_name = report_date_dt.strftime('%m-%d-%Y') + '.csv'
        output_file_path = os.path.join(branch_output_dir, output_file_name)

        # Select only the required output columns for this specific file
        output_df = group_df[final_output_columns].copy()

        # Save the processed data (overwrite if exists)
        try:
            output_df.to_csv(output_file_path, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_NONNUMERIC)
            print(f"Server Log (TB File Process): Successfully saved {len(output_df)} rows for Branch '{branch_name_str}', Date '{report_date_dt.strftime('%Y-%m-%d')}' to {output_file_path}")
            processed_files_info.append(f"Processed data for Branch '{branch_name_str}', Date '{report_date_dt.strftime('%Y-%m-%d')}', saved to {output_file_path}")
        except Exception as e:
            error_msg = f"Error saving processed data for Branch '{branch_name_str}', Date '{report_date_dt.strftime('%Y-%m-%d')}' to {output_file_path}: {e}"
            print(f"Server Log (TB File Process): {error_msg}")
            skipped_files_info.append(f"Branch '{branch_name_str}', Date '{report_date_dt.strftime('%Y-%m-%d')}': {error_msg}")
            # Do not re-raise, continue processing other groups if possible

    response_message = ""
    if processed_files_info:
        response_message += f"Successfully processed and saved {len(processed_files_info)} unique Trial Balance outputs.\n"
    if skipped_files_info:
        response_message += "The following files were skipped or encountered errors:\n" + "\n".join(skipped_files_info)
    
    if not processed_files_info and not skipped_files_info:
        response_message = "No valid Trial Balance data was processed or saved from the uploaded files."

    return {"message": response_message, "output_path": overall_output_base_dir}
