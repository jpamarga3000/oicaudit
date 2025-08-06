# petty_cash.py (Revised for Web Integration)
import pandas as pd
import os
# Removed tkinter imports as GUI is handled by the web frontend

def col_letter_to_index(letter):
    """Converts an Excel column letter (e.g., 'A', 'AB') to a 0-based index."""
    index = 0
    for i, char in enumerate(reversed(letter.upper())):
        index += (ord(char) - ord('A') + 1) * (26 ** i)
    return index - 1 # Convert to 0-based index

def process_and_combine_excel_data_web(input_dir, output_dir):
    """
    Combines data from selected Excel files, extracts specific columns (B to F)
    starting from row 6, and dynamically creates 'CHARGE' and 'EXP' columns
    based on amounts found from column G onwards and headers in row 5.
    Disregards rows if Column B (DATE) and Column C (NAME) are blank or zero.
    Saves all combined data into a single CSV.

    Args:
        input_dir (str): The directory containing the Excel files.
        output_dir (str): The directory where the combined CSV will be saved.
    """
    # Define the fixed columns and their 0-based indices (Excel columns B to F)
    fixed_column_map = {
        'DATE': 1,          # Column B
        'NAME': 2,          # Column C
        'PARTICULARS': 3,   # Column D
        'PCV': 4,           # Column E
        'AMT': 5            # Column F
    }

    # Define the desired order of columns in the final CSV, with 'SHEET' added
    final_output_columns = [
        'SHEET', 'DATE', 'NAME', 'PARTICULARS', 'PCV', 'AMT', 'CHARGE', 'EXP'
    ]

    all_combined_rows = [] # List to store all processed rows from all files/sheets

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Server Log (Petty Cash): Created output directory: {output_dir}")

    print(f"Server Log (Petty Cash): Starting Excel processing in {input_dir}...")

    # Iterate through all files in the input directory
    excel_files_found = False
    for filename in os.listdir(input_dir):
        if filename.endswith(('.xls', '.xlsx')):
            excel_files_found = True
            file_path = os.path.join(input_dir, filename)
            print(f"Server Log (Petty Cash): Processing file: {filename}")
            try:
                # Read all sheets from the Excel file without assuming any header
                excel_data = pd.read_excel(file_path, sheet_name=None, header=None)

                for sheet_name, df_raw in excel_data.items():
                    print(f"Server Log (Petty Cash):   Processing sheet: {sheet_name}")

                    # Check if the sheet has enough rows for headers (row 5) and data (row 6+)
                    if df_raw.shape[0] < 6:
                        print(f"Server Log (Petty Cash):     Warning: Sheet '{sheet_name}' in '{filename}' has fewer than 6 rows. Skipping.")
                        continue

                    # Extract dynamic headers from Row 5 (0-based index 4)
                    dynamic_headers = df_raw.iloc[4, 6:].dropna().to_dict()

                    if not dynamic_headers:
                        print(f"Server Log (Petty Cash):     Info: No dynamic 'CHARGE' headers found from Column G onwards in Row 5 of sheet '{sheet_name}'.")
                        pass

                    # Process data rows starting from Row 6 (0-based index 5)
                    for r_idx, row_data in df_raw.iloc[5:].iterrows():
                        current_row_fixed_data = {}
                        current_row_fixed_data['SHEET'] = sheet_name

                        for header, col_idx in fixed_column_map.items():
                            if col_idx < len(row_data):
                                value = row_data.iloc[col_idx]
                                if pd.notna(value) and str(value).strip() != '':
                                    if isinstance(value, (int, float)) and value == 0:
                                        pass
                                    else:
                                        pass
                                current_row_fixed_data[header] = value
                            else:
                                current_row_fixed_data[header] = ''

                        # Disregard row if Column B (DATE) AND Column C (NAME) are blank or zero
                        date_val = current_row_fixed_data.get('DATE')
                        name_val = current_row_fixed_data.get('NAME')

                        is_date_blank_or_zero = not (pd.notna(date_val) and str(date_val).strip() != '' and not (isinstance(date_val, (int, float)) and date_val == 0))
                        is_name_blank_or_zero = not (pd.notna(name_val) and str(name_val).strip() != '' and not (isinstance(name_val, (int, float)) and name_val == 0))

                        if is_date_blank_or_zero and is_name_blank_or_zero:
                            continue

                        # Extract dynamic charge amounts from Column G onwards
                        current_row_charge_data = row_data.iloc[6:]

                        charge_found_in_row = False

                        for charge_col_idx_relative, charge_amount in current_row_charge_data.items():
                            if pd.notna(charge_amount) and str(charge_amount).strip() != '':
                                charge_found_in_row = True
                                output_row = current_row_fixed_data.copy()
                                output_row['CHARGE'] = charge_amount

                                exp_header = dynamic_headers.get(charge_col_idx_relative, 'UNKNOWN_EXPENSE')
                                output_row['EXP'] = exp_header

                                all_combined_rows.append(output_row)

                        if not charge_found_in_row:
                            output_row = current_row_fixed_data.copy()
                            output_row['CHARGE'] = ''
                            output_row['EXP'] = ''
                            all_combined_rows.append(output_row)

            except Exception as e:
                print(f"Server Log (Petty Cash): Error processing file {filename}: {e}")
                raise Exception(f"Failed to process file {filename}: {e}")

    if not excel_files_found:
        raise Exception("No Excel files (.xls or .xlsx) found in the specified input directory for Petty Cash.")

    if not all_combined_rows:
        raise Exception("No valid data found in any selected Excel files for Petty Cash. No CSV will be generated.")

    # Create a DataFrame from all collected rows
    combined_df = pd.DataFrame(all_combined_rows)

    # Ensure all required final columns exist, filling missing with empty string
    for col in final_output_columns:
        if col not in combined_df.columns:
            combined_df[col] = ''

    # Reorder columns to the specified final output order
    combined_df = combined_df[final_output_columns]

    # --- Date Formatting ---
    if 'DATE' in combined_df.columns:
        combined_df['DATE'] = pd.to_datetime(combined_df['DATE'], errors='coerce')
        combined_df['DATE'] = combined_df['DATE'].dt.strftime('%m/%d/%Y')
        combined_df['DATE'] = combined_df['DATE'].replace({pd.NaT: ''})

    # Define the output CSV file path
    output_csv_path = os.path.join(output_dir, "combined_petty_cash_data.csv")

    try:
        combined_df.to_csv(output_csv_path, index=False)
        print(f"Server Log (Petty Cash): Successfully combined all data into: {output_csv_path}")
    except Exception as e:
        print(f"Server Log (Petty Cash): Error saving combined CSV: {e}")
        raise Exception(f"Failed to save combined Petty Cash CSV: {e}")

    print("\nServer Log (Petty Cash): Process completed successfully!")
