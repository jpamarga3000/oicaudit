import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def select_excel_file():
    """Opens a file dialog to select an Excel file."""
    root = tk.Tk()
    root.withdraw() # Hide the main window
    file_path = filedialog.askopenfilename(
        title="Select Excel File to Process",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    root.destroy() # Destroy the Tkinter root window after use
    print(f"DEBUG: select_excel_file returned: {file_path}")
    return file_path

def select_output_folder():
    """Opens a folder dialog to select the output directory."""
    root = tk.Tk()
    root.withdraw() # Hide the main window
    folder_path = filedialog.askdirectory(
        title="Select Output Folder"
    )
    root.destroy() # Destroy the Tkinter root window after use
    print(f"DEBUG: select_output_folder returned: {folder_path}")
    return folder_path

def consolidate_top_data(all_branches_top_data, output_folder):
    """
    Creates a consolidated Excel file with TOP 50/100 DEL AMT, DEL %, and PROVISION
    for all processed branches.
    """
    print("\nStarting consolidation of TOP data...")
    if not all_branches_top_data:
        print("No TOP data collected from any branch. Skipping consolidated file creation.")
        messagebox.showinfo("Consolidation Skipped", "No TOP data was generated for any branch. Consolidated file will not be created.")
        return

    consolidated_df_rows = []
    
    for branch_data in all_branches_top_data:
        branch_name = branch_data['branch']
        top_50_del_balance_sum = branch_data['top_50_del_balance_sum']
        top_100_del_balance_sum = branch_data['top_100_del_balance_sum']
        top_50_del_percent_val = branch_data['top_50_del_percent_val']
        top_100_del_percent_val = branch_data['top_100_del_percent_val']
        top_50_provision_sum = branch_data['top_50_provision_sum']
        top_100_provision_sum = branch_data['top_100_provision_sum']

        # Add rows for each particular (DEL AMT, DEL %, PROVISION)
        consolidated_df_rows.append({
            'BRANCH': branch_name,
            'PARTICULAR': 'DEL AMT',
            'TOP 50': top_50_del_balance_sum,
            'TOP 100': top_100_del_balance_sum
        })
        consolidated_df_rows.append({
            'BRANCH': '', # Empty for merging
            'PARTICULAR': 'DEL %',
            'TOP 50': top_50_del_percent_val,
            'TOP 100': top_100_del_percent_val
        })
        consolidated_df_rows.append({
            'BRANCH': '', # Empty for merging
            'PARTICULAR': 'PROVISION',
            'TOP 50': top_50_provision_sum,
            'TOP 100': top_100_provision_sum
        })

    consolidated_df = pd.DataFrame(consolidated_df_rows)
    
    if consolidated_df.empty:
        print("Consolidated DataFrame is empty after processing all branches. Skipping file creation.")
        messagebox.showinfo("Consolidation Skipped", "Consolidated TOP data is empty. Consolidated file will not be created.")
        return

    consolidated_filename = "TOP CONSO.xlsx"
    consolidated_filepath = os.path.join(output_folder, consolidated_filename)

    try:
        print(f"Attempting to create consolidated file: {consolidated_filepath}")
        with pd.ExcelWriter(consolidated_filepath, engine='xlsxwriter') as writer:
            consolidated_df.to_excel(writer, sheet_name='Consolidated TOP', index=False)
            worksheet = writer.sheets['Consolidated TOP']
            workbook = writer.book

            # Define formats
            currency_format = workbook.add_format({'num_format': '#,##0.00'})
            percentage_format = workbook.add_format({'num_format': '0.00%'})

            # Apply merging for 'BRANCH' column and formatting
            # Start from row 1 (after header)
            current_row = 1
            for branch_data in all_branches_top_data: # Iterate through the original data source
                # Ensure we don't go out of bounds if consolidated_df_rows was unexpectedly shorter
                # This check is more robust by checking against the actual length of the consolidated_df_rows
                # which is created from all_branches_top_data * 3
                if current_row + 2 < len(consolidated_df_rows) + 1: # +1 for header row offset
                    # Merge 3 cells in 'BRANCH' column (Column A, index 0)
                    # Use the actual branch name from branch_data, not consolidated_df.iloc
                    worksheet.merge_range(current_row, 0, current_row + 2, 0, branch_data['branch'])
                    
                    # Apply formatting to 'TOP 50' and 'TOP 100' columns
                    # DEL AMT row
                    worksheet.write(current_row, 1, 'DEL AMT')
                    worksheet.write(current_row, 2, branch_data['top_50_del_balance_sum'], currency_format)
                    worksheet.write(current_row, 3, branch_data['top_100_del_balance_sum'], currency_format)
                    
                    # DEL % row
                    worksheet.write(current_row + 1, 1, 'DEL %')
                    worksheet.write(current_row + 1, 2, branch_data['top_50_del_percent_val'], percentage_format)
                    worksheet.write(current_row + 1, 3, branch_data['top_100_del_percent_val'], percentage_format)

                    # PROVISION row
                    worksheet.write(current_row + 2, 1, 'PROVISION')
                    worksheet.write(current_row + 2, 2, branch_data['top_50_provision_sum'], currency_format)
                    worksheet.write(current_row + 2, 3, branch_data['top_100_provision_sum'], currency_format)
                
                current_row += 3 # Move to the next branch's data

            print(f"Successfully created consolidated TOP data file: {consolidated_filepath}")
            messagebox.showinfo("Consolidation Complete", f"Consolidated TOP data saved to:\n{consolidated_filepath}")

    except Exception as e:
        messagebox.showerror("Error Creating Consolidated File", f"An error occurred while creating the consolidated TOP file: {e}")
        print(f"ERROR: Failed to create consolidated TOP file: {e}")


def process_excel_by_branch():
    """
    Processes an Excel file, separating data from the 'JUN' sheet
    into multiple Excel files based on the 'BRANCH' column.
    Within each branch's file:
    - 'All Products' sheet contains ALL data, sorted by 'BALANCE' (highest to lowest) and 'AGING'.
    - 'DEL_PRODUCT' sheet contains items where 'AGING' is NOT 'NOT YET DUE', sorted by 'BALANCE' (highest to low),
      and includes a 'PROVISION' column.
    - 'SUMMARY' sheet summarizes products by aging (including 'NOT YET DUE'),
      includes 'Total', 'Del Amt', 'Del %', individual percentage columns, and a 'TOTAL' row.
      It also appends 'Top 50'/'Top 100' summaries with specific headers and formatting.
      The 'SUMMARY' sheet is sorted by 'Del %' (highest to low), with 'REST' products at the bottom.
    - Individual product sheets are created (excluding 'NOT YET DUE') with a link back to 'SUMMARY'.
    """
    print("Starting process_excel_by_branch...")

    input_file = select_excel_file()
    if not input_file:
        messagebox.showwarning("Selection Cancelled", "No input file selected. Process aborted.")
        print("Input file selection cancelled.")
        return

    print(f"Selected input file: {input_file}")

    output_folder = select_output_folder()
    if not output_folder:
        messagebox.showwarning("Selection Cancelled", "No output folder selected. Process aborted.")
        print("Output folder selection cancelled.")
        return

    print(f"Selected output folder: {output_folder}")
    print("DEBUG: Proceeding to initial Excel read and global checks...")

    processed_branches_count = 0
    processed_branch_names = []
    skipped_branch_names = [] # Stores (branch_name, error_message)
    all_branches_top_data = [] # List to store TOP data for consolidation

    try:
        print(f"Attempting to read sheet 'JUN' from {input_file}...")
        df = pd.read_excel(input_file, sheet_name='JUN', engine='openpyxl')
        print("Successfully read Excel sheet 'JUN'.")

        # --- Robust data cleaning for key columns (global check) ---
        for col in ['BRANCH', 'PRODUCT', 'AGING']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('\xa0', ' ').str.strip().str.upper()
                print(f"DEBUG: Global cleaning of '{col}' column (string, replaced non-breaking spaces, stripped, uppercase).")
            else:
                raise KeyError(f"The '{col}' column was not found in the 'JUN' sheet. Cannot proceed.")

        if 'BALANCE' in df.columns:
            df['BALANCE'] = pd.to_numeric(df['BALANCE'], errors='coerce')
            print("DEBUG: Global 'BALANCE' column converted to numeric.")
        else:
            raise KeyError("The 'BALANCE' column was not found in the 'JUN' sheet. Cannot proceed.")
        # --- End of robust data cleaning (global) ---

        unique_branches = df['BRANCH'].dropna().unique()
        print(f"Found unique branches (after global cleaning): {unique_branches}")

        if not unique_branches.size:
            messagebox.showinfo("No Branches Found", "No unique branch names found in the 'BRANCH' column of sheet 'JUN'. No files will be generated.")
            print("No unique branches found.")
            return

        # Define aging bucket headers for sorting 'All Products' and for the SUMMARY sheet amounts
        # This order includes 'NOT YET DUE' for comprehensive sorting and sum in 'All Products' and 'SUMMARY'
        aging_buckets_full_order = ['1-30 DAYS', '31-60', '61-90', '91-120', '121-180', '181-365', 'OVER 365', 'NOT YET DUE']
        aging_buckets_full_order_upper = [bucket.upper() for bucket in aging_buckets_full_order]

        # Define aging buckets for the numerator of 'Del %' and for 'Del Amt'
        # These are also used for individual percentage columns
        aging_buckets_for_del_calc = [
            '1-30 DAYS', '31-60', '61-90', '91-120', '121-180', '181-365', 'OVER 365'
        ]
        aging_buckets_for_del_calc_upper = [bucket.upper() for bucket in aging_buckets_for_del_calc]

        # Define aging buckets for Provision calculation
        provision_buckets_upper = ['31-60', '61-90', '91-120', '121-180', '181-365']
        provision_over_365_bucket_upper = 'OVER 365'


        # Iterate through each unique branch to create separate Excel files
        for branch in unique_branches:
            try:
                print(f"\nProcessing BRANCH: {branch}")
                branch_df = df[df['BRANCH'] == branch].copy() # Use .copy() to avoid SettingWithCopyWarning
                print(f"DEBUG: Filtered branch_df for '{branch}'. Shape: {branch_df.shape}")

                if branch_df.empty:
                    print(f"WARNING: No data found for BRANCH '{branch}' after filtering. Skipping.")
                    skipped_branch_names.append((branch, "No data found for this branch."))
                    continue

                # Calculate total_balance_all_products here, always defined for the branch
                total_balance_all_products = branch_df['BALANCE'].sum() # Denominator for TOP sheet's Del %
                print(f"DEBUG: total_balance_all_products for {branch}: {total_balance_all_products}")

                # --- Data for 'DEL_PRODUCT', individual product sheets (AGING is NOT 'NOT YET DUE') ---
                # Create a copy to avoid modifying the original branch_df for other sheets
                non_not_yet_due_df = branch_df[branch_df['AGING'] != 'NOT YET DUE'].copy()
                print(f"DEBUG: Non 'NOT YET DUE' DF shape for BRANCH {branch}: {non_not_yet_due_df.shape}")

                # Calculate 'PROVISION' column for non_not_yet_due_df (for DEL_PRODUCT and TOP summaries)
                if not non_not_yet_due_df.empty:
                    # Ensure all provision buckets exist and are numeric (fill NaN with 0 for sum)
                    for bucket in provision_buckets_upper + [provision_over_365_bucket_upper]:
                        if bucket not in non_not_yet_due_df.columns:
                            non_not_yet_due_df[bucket] = 0.0 # Add column if missing
                        non_not_yet_due_df[bucket] = pd.to_numeric(non_not_yet_due_df[bucket], errors='coerce').fillna(0)

                    non_not_yet_due_df['PROVISION'] = (
                        non_not_yet_due_df[provision_buckets_upper].sum(axis=1) * 0.35
                    ) + non_not_yet_due_df[provision_over_365_bucket_upper]
                    print(f"DEBUG: 'PROVISION' column calculated for non_not_yet_due_df.")
                else:
                    print(f"DEBUG: No data in non_not_yet_due_df to calculate 'PROVISION'.")

                sanitized_branch_name = str(branch).replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                output_filename = f"{sanitized_branch_name} - JUNE 2025.xlsx"
                output_filepath = os.path.join(output_folder, output_filename)

                print(f"Attempting to create file: {output_filepath}")
                # Changed engine to 'xlsxwriter'
                with pd.ExcelWriter(output_filepath, engine='xlsxwriter') as writer:
                    # --- 1. Write the 'All Products' sheet (ALL data, sorted by BALANCE and AGING) ---
                    if not branch_df.empty: # Use branch_df for 'All Products'
                        # Convert 'AGING' column to a categorical type with the defined full order for sorting
                        branch_df['AGING_SORTED_KEY'] = pd.Categorical(
                            branch_df['AGING'],
                            categories=aging_buckets_full_order_upper,
                            ordered=True
                        )
                        # Sort by BALANCE descending, then by the custom AGING order
                        sorted_all_products_df = branch_df.sort_values(
                            by=['BALANCE', 'AGING_SORTED_KEY'],
                            ascending=[False, True] # Balance descending, Aging ascending by custom order
                        ).drop(columns='AGING_SORTED_KEY') # Drop the temporary sorting column

                        print(f"  Adding 'All Products' sheet for BRANCH: {branch} (all data, sorted by BALANCE and AGING).")
                        sorted_all_products_df.to_excel(writer, sheet_name='All Products', index=False)
                    else:
                        print(f"  No data for 'All Products' sheet for BRANCH: {branch}. Sheet not created.")

                    # --- 2. Write the 'DEL_PRODUCT' sheet (only non 'NOT YET DUE' items, sorted by BALANCE, with PROVISION) ---
                    if not non_not_yet_due_df.empty:
                        # Sort 'DEL_PRODUCT' by BALANCE descending
                        sorted_del_product_df = non_not_yet_due_df.sort_values(by='BALANCE', ascending=False)
                        print(f"  Adding 'DEL_PRODUCT' sheet for BRANCH: {branch} (non 'NOT YET DUE', sorted by BALANCE, with PROVISION).")
                        
                        # Write the main DEL_PRODUCT data
                        sorted_del_product_df.to_excel(writer, sheet_name='DEL_PRODUCT', index=False)
                        
                        # Get the worksheet object to apply formatting
                        del_product_worksheet = writer.sheets['DEL_PRODUCT']
                        
                        # Define formats for this sheet using writer.book
                        currency_format = writer.book.add_format({'num_format': '#,##0.00'})
                        
                        # Apply currency format to 'BALANCE' and 'PROVISION' columns in DEL_PRODUCT
                        # Find column indices based on the DataFrame used for writing
                        balance_col_idx = sorted_del_product_df.columns.get_loc('BALANCE')
                        provision_col_idx = sorted_del_product_df.columns.get_loc('PROVISION')

                        # set_column takes 0-based column index
                        del_product_worksheet.set_column(balance_col_idx, balance_col_idx, None, currency_format)
                        del_product_worksheet.set_column(provision_col_idx, provision_col_idx, None, currency_format)

                    else:
                        print(f"  No non 'NOT YET DUE' products found for BRANCH: {branch}. 'DEL_PRODUCT' sheet not created.")


                    # --- 3. Create and write the 'SUMMARY' sheet for the BRANCH (based on branch_df for full data) ---
                    if not branch_df.empty:
                        print(f"  Creating 'SUMMARY' sheet for BRANCH: {branch}")
                        # Group by PRODUCT and AGING, then sum BALANCE
                        summary_df = branch_df.dropna(subset=['PRODUCT', 'AGING']).groupby(['PRODUCT', 'AGING'])['BALANCE'].sum().unstack(fill_value=0)
                        
                        # Reindex columns to ensure all aging buckets (including 'NOT YET DUE') are present and in desired order
                        summary_df = summary_df.reindex(columns=aging_buckets_full_order_upper, fill_value=0)
                        
                        # Rename columns back to original desired casing for display
                        col_name_map = {upper_bucket: original_bucket for upper_bucket, original_bucket in zip(aging_buckets_full_order_upper, aging_buckets_full_order)}
                        summary_df = summary_df.rename(columns=col_name_map)

                        # Calculate 'Total' column (sum of all aging buckets including 'NOT YET DUE')
                        summary_df['Total'] = summary_df[aging_buckets_full_order].sum(axis=1)

                        # Calculate 'Del Amt' column (sum of 1-30 DAYS to OVER 365)
                        summary_df['Del Amt'] = summary_df[aging_buckets_for_del_calc].sum(axis=1)

                        # Calculate 'Del %' column
                        # Numerator: sum of 1-30 DAYS to OVER 365 ('Del Amt')
                        # Denominator: 'Total' column (sum of all buckets including NOT YET DUE)
                        summary_df['Del %'] = summary_df.apply(
                            lambda row: (row['Del Amt'] / row['Total'] * 100) if row['Total'] != 0 else 0,
                            axis=1
                        )

                        # Calculate individual Percentage Columns (1-30 DAYS % to OVER 365 %)
                        individual_percentage_cols = []
                        for bucket in aging_buckets_for_del_calc: # Only for buckets excluding 'NOT YET DUE'
                            percent_col_name = f"{bucket} %"
                            # Denominator is the overall 'Total' (including 'NOT YET DUE')
                            summary_df[percent_col_name] = summary_df.apply(
                                lambda row: (row[bucket] / row['Total'] * 100) if row['Total'] != 0 else 0,
                                axis=1
                            )
                            individual_percentage_cols.append(percent_col_name)
                        
                        # Define the final desired column order for the SUMMARY sheet
                        final_summary_columns_order = aging_buckets_full_order + ['Total', 'Del Amt', 'Del %'] + individual_percentage_cols
                        summary_df = summary_df[final_summary_columns_order]

                        # Custom sorting for 'SUMMARY' sheet
                        # First, create the sort key for "REST" products
                        summary_df['__sort_key'] = summary_df.index.to_series().apply(lambda x: 1 if 'REST' in str(x).upper() else 0)
                        
                        # Sort by '__sort_key' (to push REST to bottom) then by 'Del %' (descending)
                        summary_df = summary_df.sort_values(by=['__sort_key', 'Del %'], ascending=[True, False]).drop(columns='__sort_key')
                        print(f"DEBUG: 'SUMMARY' sheet sorted for BRANCH {branch} by Del % (high to low) with REST at bottom.")
                        
                        # Calculate 'TOTAL' row (sum of each column)
                        # Sum amount columns directly
                        total_row_data = summary_df[aging_buckets_full_order + ['Total', 'Del Amt']].sum(axis=0)
                        
                        # Recalculate 'Del %' for the total row
                        total_overall_amount_for_del_percent = total_row_data['Total'] # This is the sum of all aging buckets + NOT YET DUE
                        if total_overall_amount_for_del_percent != 0:
                            total_row_data['Del %'] = (total_row_data['Del Amt'] / total_overall_amount_for_del_percent) * 100
                        else:
                            total_row_data['Del %'] = 0.0

                        # Recalculate individual percentage columns for the total row
                        for bucket in aging_buckets_for_del_calc:
                            percent_col_name = f"{bucket} %"
                            if total_overall_amount_for_del_percent != 0:
                                total_row_data[percent_col_name] = (total_row_data[bucket] / total_overall_amount_for_del_percent) * 100
                            else:
                                total_row_data[percent_col_name] = 0.0

                        total_row_df = pd.DataFrame([total_row_data], index=['TOTAL'])
                        summary_df = pd.concat([summary_df, total_row_df])


                        summary_df.to_excel(writer, sheet_name='SUMMARY', index=True)
                        print(f"  Added 'SUMMARY' sheet to {output_filepath}")

                        # --- Apply formatting to the SUMMARY sheet ---
                        workbook = writer.book
                        worksheet = writer.sheets['SUMMARY']

                        # Define formats
                        currency_format = workbook.add_format({'num_format': '#,##0.00'})
                        percentage_format = workbook.add_format({'num_format': '0.00%'})

                        # Apply currency format to amount columns (including 'Total', 'Del Amt', and 'TOTAL' row)
                        # Column A (index 0) is the Product/TOTAL label, so data starts from column B (index 1)
                        # Amount columns are aging_buckets_full_order + ['Total', 'Del Amt']
                        amount_col_names = aging_buckets_full_order + ['Total', 'Del Amt']
                        for col_name in amount_col_names:
                            if col_name in summary_df.columns: # Check if column exists in final summary_df
                                col_idx = summary_df.columns.get_loc(col_name) + 1 # +1 because pandas index is 0-based, Excel is 1-based, and first col is index
                                worksheet.set_column(col_idx, col_idx, None, currency_format)
                        
                        # Apply percentage format to percentage columns ('Del %' and individual percentages)
                        # These are 'Del %' + individual_percentage_cols
                        for p_col in ['Del %'] + individual_percentage_cols:
                            if p_col in summary_df.columns: # Check if column exists in final summary_df
                                col_idx = summary_df.columns.get_loc(p_col) + 1
                                worksheet.set_column(col_idx, col_idx, None, percentage_format)

                        # --- Add Hyperlinks from SUMMARY to individual product sheets ---
                        # Iterate only over the original product rows, excluding 'TOTAL'
                        num_original_product_rows = len(summary_df) - 1 # Subtract the 'TOTAL' row
                        
                        for r_idx in range(num_original_product_rows):
                            product_name_raw = summary_df.index[r_idx]
                            sanitized_product_name = str(product_name_raw).replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('[', '_').replace(']', '_').replace('"', '_')
                            sanitized_sheet_name = sanitized_product_name[:31] # Ensure it matches the actual sheet name
                            # Row index in worksheet is 1-based, plus 1 for header row
                            worksheet.write_url(r_idx + 1, 0, f"internal:'{sanitized_sheet_name}'!A1", string=str(product_name_raw))
                        print(f"DEBUG: Applied number formatting and hyperlinks to 'SUMMARY' sheet for BRANCH {branch}.")

                        # --- Write TOP 50/100 data directly to the SUMMARY sheet ---
                        # Determine the row to start writing TOP data
                        # +1 for header row, +1 for 0-based index, +1 for the empty row, +1 for 'TOTAL' row
                        start_row_for_top = len(summary_df) + 2 # summary_df already includes the 'TOTAL' row

                        # Calculate TOP 50/100 data
                        top_50_del_product = non_not_yet_due_df.sort_values(by='BALANCE', ascending=False).head(50)
                        top_100_del_product = non_not_yet_due_df.sort_values(by='BALANCE', ascending=False).head(100)

                        top_50_del_balance_sum = top_50_del_product['BALANCE'].sum()
                        top_100_del_balance_sum = top_100_del_product['BALANCE'].sum()

                        top_50_del_percent_val = (top_50_del_balance_sum / total_balance_all_products) if total_balance_all_products != 0 else 0
                        top_100_del_percent_val = (top_100_del_balance_sum / total_balance_all_products) if total_balance_all_products != 0 else 0

                        top_50_provision_sum = top_50_del_product['PROVISION'].sum()
                        top_100_provision_sum = top_100_del_product['PROVISION'].sum()

                        # Store TOP data for consolidation
                        all_branches_top_data.append({
                            'branch': branch,
                            'top_50_del_balance_sum': top_50_del_balance_sum,
                            'top_100_del_balance_sum': top_100_del_balance_sum,
                            'top_50_del_percent_val': top_50_del_percent_val,
                            'top_100_del_percent_val': top_100_del_percent_val,
                            'top_50_provision_sum': top_50_provision_sum,
                            'top_100_provision_sum': top_100_provision_sum
                        })

                        # Write TOP headers
                        worksheet.write(start_row_for_top, 0, 'TOP') # Column A
                        worksheet.write(start_row_for_top, 1, 'DEL AMT') # Column B
                        worksheet.write(start_row_for_top, 2, 'DEL %') # Column C
                        worksheet.write(start_row_for_top, 3, 'PROVISION') # Column D

                        # Write Top 50 data
                        worksheet.write(start_row_for_top + 1, 0, 'Top 50')
                        worksheet.write(start_row_for_top + 1, 1, top_50_del_balance_sum, currency_format)
                        worksheet.write(start_row_for_top + 1, 2, top_50_del_percent_val, percentage_format)
                        worksheet.write(start_row_for_top + 1, 3, top_50_provision_sum, currency_format)

                        # Write Top 100 data
                        worksheet.write(start_row_for_top + 2, 0, 'Top 100')
                        worksheet.write(start_row_for_top + 2, 1, top_100_del_balance_sum, currency_format)
                        worksheet.write(start_row_for_top + 2, 2, top_100_del_percent_val, percentage_format)
                        worksheet.write(start_row_for_top + 2, 3, top_100_provision_sum, currency_format)
                        
                        print(f"  Directly wrote TOP 50/100 summary to 'SUMMARY' sheet for BRANCH: {branch}.")

                    else:
                        print(f"  No data to create 'SUMMARY' sheet for BRANCH: {branch}.")


                    # --- 4. Write individual product sheets for the BRANCH's products (based on non_not_yet_due_df) ---
                    unique_products = non_not_yet_due_df['PRODUCT'].dropna().unique()
                    print(f"  Found unique products for BRANCH {branch} (excluding 'NOT YET DUE'): {unique_products}")

                    if not unique_products.size:
                        print(f"  No specific products found for BRANCH {branch} beyond 'All Products', 'DEL_PRODUCT', 'SUMMARY' sheets.")
                    else:
                        for product in unique_products:
                            print(f"    Adding product sheet: {product}")
                            product_df = non_not_yet_due_df[non_not_yet_due_df['PRODUCT'] == product]
                            
                            sanitized_product_name = str(product).replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('[', '_').replace(']', '_').replace('"', '_')
                            sheet_name = sanitized_product_name[:31] # Ensure it matches how SUMMARY links

                            # Write to Excel, starting from row 1 to leave row 0 for the back link
                            product_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1)
                            
                            # Add hyperlink back to SUMMARY sheet in the individual product sheet
                            product_worksheet = writer.sheets[sheet_name]
                            product_worksheet.write_url(0, 0, "internal:'SUMMARY'!A1", string='Back to Summary')

                            print(f"    Added sheet '{sheet_name}' to {output_filepath} with back link.")

                print(f"Finished processing BRANCH: {branch}")
                processed_branches_count += 1
                processed_branch_names.append(branch)

            except Exception as e:
                error_message = f"Error processing BRANCH '{branch}': {e}"
                print(f"ERROR: {error_message}")
                skipped_branch_names.append((branch, str(e)))
                continue # Continue to the next branch in the loop

        # --- Final summary message after all branches are processed ---
        final_message = f"Process Complete!\n\nSuccessfully separated data for {processed_branches_count} branches into {output_folder}."
        if processed_branch_names:
            final_message += "\n\nProcessed Branches:\n" + "\n".join(processed_branch_names)
        if skipped_branch_names:
            final_message += "\n\nSkipped Branches (with errors or no data):\n"
            for branch_name, error_msg in skipped_branch_names:
                final_message += f"- {branch_name}: {error_msg}\n"

        messagebox.showinfo("Process Complete", final_message)
        print("Process completed successfully.")

        # Call the consolidation function after all branches are processed
        print(f"DEBUG: all_branches_top_data before consolidation: {all_branches_top_data}")
        consolidate_top_data(all_branches_top_data, output_folder)

    except FileNotFoundError:
        messagebox.showerror("Error", f"Input file not found: {input_file}")
        print(f"GLOBAL ERROR: Input file not found: {input_file}")
    except ValueError as ve:
        messagebox.showerror("Error", f"Initial sheet or data error: {ve}. Ensure 'JUN' sheet exists and contains valid data.")
        print(f"GLOBAL ERROR: Initial sheet or data error: {ve}")
    except KeyError as ke:
        messagebox.showerror("Error", f"Missing critical column: {ke}. Ensure 'BRANCH', 'PRODUCT', 'AGING', and 'BALANCE' columns exist in the 'JUN' sheet and are spelled correctly (case-sensitive).")
        print(f"GLOBAL ERROR: Missing critical column: {ke}")
    except Exception as e:
        messagebox.showerror("An Unexpected Error Occurred", f"An unexpected error occurred during initial setup: {e}")
        print(f"GLOBAL UNEXPECTED ERROR: {e}")

# Call the main function to start the process when the script is run
if __name__ == "__main__":
    process_excel_by_branch()
