# audit_tool/backend/wp_lr_reference_process.py
import os
import pandas as pd
from datetime import datetime

# Assuming a base directory for Loan Receivables data
LR_BASE_DIR = r"C:\xampp\htdocs\audit_tool\WORKING PAPER\LOAN RECEIVABLES"

def process_wp_lr_reference_data(input_file_path, output_dir, branch):
    """
    Processes Loan Receivables Reference data from a CSV file, formats it,
    and saves it to a specified output directory.

    Args:
        input_file_path (str): The path to the input CSV file (e.g., RELACC.csv).
        output_dir (str): The directory where the processed CSV will be saved.
        branch (str): The selected branch name for filtering and output filename.
    """
    os.makedirs(output_dir, exist_ok=True)

    sanitized_branch = "".join([c for c in str(branch) if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch:
        raise ValueError("Invalid branch name provided.")

    print(f"Server Log (WP LR Reference): Processing '{os.path.basename(input_file_path)}' for branch '{branch}'")

    try:
        df = pd.read_csv(input_file_path, dtype=str, encoding='latin1', low_memory=False)
        df.columns = [col.strip().upper() for col in df.columns]

        # Example: Filter by branch if a 'BRANCH' column exists in the input file
        if 'BRANCH' in df.columns:
            df = df[df['BRANCH'].astype(str).str.strip().str.upper() == branch.upper()].copy()
            if df.empty:
                raise ValueError(f"No data found for branch '{branch}' in the input file.")
        else:
            print("Server Log (WP LR Reference): 'BRANCH' column not found in input file. Skipping branch filtering.")

        # Required columns for the output (adjust based on actual RELACC structure)
        required_cols = ['ACC', 'CID', 'NAME', 'PRODUCT', 'DOPEN', 'MATDATE']
        for col in required_cols:
            if col not in df.columns:
                df[col] = '' # Add missing columns as empty

        # Data Formatting (example)
        for date_col in ['DOPEN', 'MATDATE']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%m/%d/%Y').fillna('')

        # Filter relevant columns and reorder
        df_output = df[required_cols].copy()

        output_filename = f"{sanitized_branch}_LR_Reference.csv"
        output_filepath = os.path.join(output_dir, output_filename)

        # Backup existing file before saving
        if os.path.exists(output_filepath):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = output_filepath.replace('.csv', f'_{timestamp}.csv')
            os.rename(output_filepath, backup_name)
            print(f"Server Log (WP LR Reference): Backed up existing file to: {backup_name}")

        df_output.to_csv(output_filepath, index=False, encoding='utf-8-sig')
        print(f"Server Log (WP LR Reference): Processed data saved to: {output_filepath}")

        return df_output.to_dict(orient='records')

    except Exception as e:
        print(f"Server Log (WP LR Reference): Error processing file: {e}")
        raise Exception(f"Failed to process Loan Receivables Reference data: {e}")