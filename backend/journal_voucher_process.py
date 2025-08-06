# audit_tool/backend/journal_voucher_process.py
import os
import csv
from dbfread import DBF
from datetime import datetime, timedelta # Import timedelta
import pandas as pd

def process_journal_voucher_data(input_dir, output_dir, branch):
    """
    Processes Journal Voucher DBF files from input_dir, applies specific mapping and formatting,
    and combines them into a single CSV file in output_dir.

    Args:
        input_dir (str): The directory containing the DBF files.
        output_dir (str): The directory where the combined CSV will be saved.
        branch (str): The selected branch name for output filename.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"Server Log (Journal Voucher): Starting DBF processing from {input_dir} for branch '{branch}'")

    # Sanitize branch name for filename
    sanitized_branch = "".join([c for c in str(branch) if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not sanitized_branch:
        sanitized_branch = "UNSPECIFIED_BRANCH"

    # Define the output headers and their order
    target_headers = ['ACCOUNT', 'TITLE', 'DATE', 'DESCRIPTION', 'REF', 'DR', 'CR'] # Added 'REF'

    # Helper function to format amount fields (DR/CR)
    def format_amount(value):
        try:
            numeric_val = float(value)
            if numeric_val == 0:
                return ''  # Blank if zero
            return f"{numeric_val / 100:,.2f}"
        except (ValueError, TypeError):
            return '' # Return blank for non-numeric or errors

    # Collect combined data and document dates
    combined_data_rows = []
    dbf_files_found = False
    all_doc_dates = []

    # Process each DBF file
    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith('.dbf') and not file_name.startswith('~'):
            dbf_files_found = True
            dbf_path = os.path.join(input_dir, file_name)

            print(f"Server Log (Journal Voucher): Processing file: {file_name}...")

            try:
                table = DBF(dbf_path, load=True, encoding='latin-1', ignore_missing_memofile=True)
                
                # Check for essential input headers for mapping
                required_input_cols = ['EXPDRACC', 'EXPCRACC', 'DRSTITLE', 'CRSTITLE', 'DOCDATE', 'DESC', 'REF', 'DRAMT', 'CRAMT'] # Added 'REF' to required_input_cols
                if not all(col.upper() in [f.name.upper() for f in table.fields] for col in required_input_cols):
                    missing_cols = [col for col in required_input_cols if col.upper() not in [f.name.upper() for f in table.fields]]
                    print(f"Server Log (Journal Voucher): Skipping {file_name} - Missing required headers: {', '.join(missing_cols)}")
                    continue

                for record in table:
                    # Account Logic
                    expdracc = str(record.get('EXPDRACC', '') or '').strip()
                    expcracc = str(record.get('EXPCRACC', '') or '').strip()
                    account = ''
                    if not expdracc and expcracc:
                        account = expcracc
                    elif expdracc: # If EXPDRACC has data, use it (even if EXPCRACC also has data or is blank)
                        account = expdracc
                    
                    # Title Logic
                    drstitle = str(record.get('DRSTITLE', '') or '').strip()
                    crstitle = str(record.get('CRSTITLE', '') or '').strip()
                    title = ''
                    if not drstitle and crstitle:
                        title = crstitle
                    elif drstitle: # If DRSTITLE has data, use it (even if CRSTITLE also has data or is blank)
                        title = drstitle

                    # Date Formatting
                    docdate_raw = str(record.get('DOCDATE', '') or '').strip()
                    date_formatted = ''
                    try:
                        # Attempt to parse as Excel serial date first, then other formats
                        if docdate_raw.isdigit():
                            excel_serial_date = int(docdate_raw)
                            # Excel's 1900 date system has a bug where 1900 is treated as a leap year.
                            # Base date for Excel serial is Dec 30, 1899.
                            parsed_date = datetime(1899, 12, 30) + timedelta(days=excel_serial_date)
                            # Ensure date is not before a reasonable start year (e.g., 1900)
                            if parsed_date.year < 1900:
                                parsed_date = pd.NaT # Treat as Not a Time
                        else:
                            parsed_date = pd.to_datetime(docdate_raw, errors='coerce')
                        
                        if pd.notna(parsed_date):
                            all_doc_dates.append(parsed_date)
                            date_formatted = parsed_date.strftime('%m/%d/%Y')
                    except (ValueError, TypeError):
                        pass # Keep date_formatted as empty string

                    # DR and CR Amount Formatting
                    dramt_val = record.get('DRAMT', 0)
                    cramt_val = record.get('CRAMT', 0)

                    row = {
                        'ACCOUNT': account,
                        'TITLE': title,
                        'DATE': date_formatted,
                        'DESCRIPTION': str(record.get('DESC', '') or ''),
                        'REF': str(record.get('REF', '') or ''), # Added 'REF' to row data
                        'DR': format_amount(dramt_val),
                        'CR': format_amount(cramt_val),
                    }
                    combined_data_rows.append(row)
                
                print(f"Server Log (Journal Voucher): ✅ Processed: {file_name} with {len(table)} records.")

            except Exception as e:
                print(f"Server Log (Journal Voucher): ❌ Error processing {file_name}: {e}")
                continue # Continue to next file even if one fails

    if not dbf_files_found:
        raise Exception("No DBF files found in the specified input directory for Journal Voucher processing.")
    
    if not combined_data_rows:
        raise Exception("No valid data was processed or combined from any DBF files for Journal Voucher.")

    print("\nServer Log (Journal Voucher): All DBF files processed. Combining and saving results...")

    # Determine earliest and latest DOCDATE for filename
    min_date_str = "UNKNOWN_START"
    max_date_str = "UNKNOWN_END"
    if all_doc_dates:
        min_date = min(all_doc_dates)
        max_date = max(all_doc_dates)
        min_date_str = min_date.strftime('%m-%d-%Y')
        max_date_str = max_date.strftime('%m-%d-%Y')
    else:
        print("Server Log (Journal Voucher): Warning: No valid DOCDATEs found to determine date range for filename.")

    # Construct the output filename
    output_filename = f"{sanitized_branch.upper()} JV - {min_date_str} TO {max_date_str}.csv"
    output_filepath = os.path.join(output_dir, output_filename)

    # Create DataFrame from all collected rows
    final_combined_df = pd.DataFrame(combined_data_rows, columns=target_headers)

    # Backup existing file before saving new one
    if os.path.exists(output_filepath):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = output_filepath.replace('.csv', f'_{timestamp}.csv')
        try:
            os.rename(output_filepath, new_name)
            print(f"Server Log (Journal Voucher): Backed up existing file to: {new_name}")
        except OSError as e:
            print(f"Server Log (Journal Voucher): Error backing up {output_filepath}: {e}")

    # Save the combined DataFrame to CSV
    try:
        final_combined_df.to_csv(output_filepath, index=False, encoding='utf-8-sig')
        print(f"Server Log (Journal Voucher): ✅ Combined CSV saved to: {output_filepath}")
    except Exception as e:
        print(f"Server Log (Journal Voucher): ❌ Error writing CSV: {e}")
        raise Exception(f"Error writing combined Journal Voucher CSV: {e}")

    print("Server Log (Journal Voucher): Processing complete!")
