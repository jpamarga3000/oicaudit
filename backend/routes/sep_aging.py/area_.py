import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os

# Define the areas and their constituent branches
# IMPORTANT: Branch names here should be in uppercase as they will be compared
# against the cleaned (uppercase) 'BRANCH' column from the Excel file.
AREA_BRANCH_MAP = {
    "AREA 1": ["BAUNGON", "BULUA", "CARMEN", "COGON", "EL SALVADOR", "TALAKAG", "YACAPIN"],
    "AREA 2": ["AGLAYAN", "DON CARLOS", "ILUSTRE", "MANOLO", "MARAMAG", "TORIL", "VALENCIA"],
    "AREA 3": ["AGORA", "BALINGASAG", "BAYUGAN", "BUTUAN", "GINGOOG", "PUERTO", "TAGBILARAN", "TUBIGON", "UBAY"]
}

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

def process_excel_by_area():
    """
    Processes an Excel file, separating data from the 'JUN' sheet
    into multiple Excel files based on predefined 'AREAs'.
    Within each area's file:
    - 'All Products' sheet contains ALL data for the area, sorted by 'BALANCE' (highest to lowest) and 'AGING'.
    - 'DEL_PRODUCT' sheet contains items where 'AGING' is NOT 'NOT YET DUE' for the area, sorted by 'BALANCE' (highest to low).
    - 'SUMMARY' sheet summarizes products by aging (including 'NOT YET DUE') for the area,
      includes 'Total', 'Del Amt', 'Del %', individual percentage columns, and a 'TOTAL' row,
      with specific number formatting and hyperlinks to product sheets.
      The 'SUMMARY' sheet is sorted by 'Del %' (highest to lowest), with 'REST' products at the bottom.
    - Individual product sheets are created (excluding 'NOT YET DUE') with a link back to 'SUMMARY'.
    """
    print("Starting process_excel_by_area...")

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

    processed_areas_count = 0
    processed_area_names = []
    skipped_area_names = [] # Stores (area_name, error_message)

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

        # Define aging bucket headers for sorting 'All Products' and for the SUMMARY sheet amounts
        # This order includes 'NOT YET DUE' for comprehensive sorting and sum in 'All Products' and 'SUMMARY'
        aging_buckets_full_order = ['1-30 DAYS', '31-60', '61-90', '91-120', '121-180', '181-365', 'OVER 365', 'NOT YET DUE']
        aging_buckets_full_order_upper = [bucket.upper() for bucket in aging_buckets_full_order]

        # Define aging buckets for the numerator of 'Del %' and for individual percentage columns
        aging_buckets_for_del_percent_numerator = [
            '1-30 DAYS', '31-60', '61-90', '91-120', '121-180', '181-365', 'OVER 365'
        ]
        aging_buckets_for_del_percent_numerator_upper = [bucket.upper() for bucket in aging_buckets_for_del_percent_numerator]


        # Iterate through each defined area to create separate Excel files
        for area_name, branches_in_area in AREA_BRANCH_MAP.items():
            try:
                print(f"\nProcessing AREA: {area_name}")
                
                # Filter the DataFrame for the current area's branches
                # Ensure branches_in_area are also uppercase for matching
                area_df = df[df['BRANCH'].isin([b.upper() for b in branches_in_area])]
                
                print(f"DEBUG: Filtered area_df for '{area_name}'. Shape: {area_df.shape}")

                if area_df.empty:
                    print(f"WARNING: No data found for AREA '{area_name}' (branches: {branches_in_area}) after filtering. Skipping.")
                    skipped_area_names.append((area_name, "No data found for this area's branches."))
                    continue

                # --- Data for 'DEL_PRODUCT', individual product sheets (AGING is NOT 'NOT YET DUE') ---
                non_not_yet_due_df = area_df[area_df['AGING'] != 'NOT YET DUE']
                print(f"DEBUG: Non 'NOT YET DUE' DF shape for AREA {area_name}: {non_not_yet_due_df.shape}")


                sanitized_area_name = str(area_name).replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                output_filename = f"{sanitized_area_name} - JUNE 2025.xlsx"
                output_filepath = os.path.join(output_folder, output_filename)

                print(f"Attempting to create file: {output_filepath}")
                with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
                    # --- 1. Write the 'All Products' sheet (ALL data for the area, sorted by BALANCE and AGING) ---
                    if not area_df.empty: # Use area_df for 'All Products'
                        # Convert 'AGING' column to a categorical type with the defined full order for sorting
                        area_df['AGING_SORTED_KEY'] = pd.Categorical(
                            area_df['AGING'],
                            categories=aging_buckets_full_order_upper,
                            ordered=True
                        )
                        # Sort by BALANCE descending, then by the custom AGING order
                        sorted_all_products_df = area_df.sort_values(
                            by=['BALANCE', 'AGING_SORTED_KEY'],
                            ascending=[False, True] # Balance descending, Aging ascending by custom order
                        ).drop(columns='AGING_SORTED_KEY') # Drop the temporary sorting column

                        print(f"  Adding 'All Products' sheet for AREA: {area_name} (all data, sorted by BALANCE and AGING).")
                        sorted_all_products_df.to_excel(writer, sheet_name='All Products', index=False)
                    else:
                        print(f"  No data for 'All Products' sheet for AREA: {area_name}. Sheet not created.")

                    # --- 2. Write the 'DEL_PRODUCT' sheet (only non 'NOT YET DUE' items for the area, sorted by BALANCE) ---
                    if not non_not_yet_due_df.empty:
                        # Sort 'DEL_PRODUCT' by BALANCE descending
                        sorted_del_product_df = non_not_yet_due_df.sort_values(by='BALANCE', ascending=False)
                        print(f"  Adding 'DEL_PRODUCT' sheet for AREA: {area_name} (non 'NOT YET DUE', sorted by BALANCE).")
                        sorted_del_product_df.to_excel(writer, sheet_name='DEL_PRODUCT', index=False)
                    else:
                        print(f"  No non 'NOT YET DUE' products found for AREA: {area_name}. 'DEL_PRODUCT' sheet not created.")


                    # --- 3. Create and write the 'SUMMARY' sheet for the AREA (based on area_df for full data) ---
                    if not area_df.empty:
                        print(f"  Creating 'SUMMARY' sheet for AREA: {area_name}")
                        # Group by PRODUCT and AGING, then sum BALANCE
                        summary_df = area_df.dropna(subset=['PRODUCT', 'AGING']).groupby(['PRODUCT', 'AGING'])['BALANCE'].sum().unstack(fill_value=0)
                        
                        # Reindex columns to ensure all aging buckets (including 'NOT YET DUE') are present and in desired order
                        summary_df = summary_df.reindex(columns=aging_buckets_full_order_upper, fill_value=0)
                        
                        # Rename columns back to original desired casing for display
                        col_name_map = {upper_bucket: original_bucket for upper_bucket, original_bucket in zip(aging_buckets_full_order_upper, aging_buckets_full_order)}
                        summary_df = summary_df.rename(columns=col_name_map)

                        # Calculate 'Total' column (sum of all aging buckets including 'NOT YET DUE')
                        summary_df['Total'] = summary_df[aging_buckets_full_order].sum(axis=1)

                        # Calculate 'Del Amt' column (sum of 1-30 DAYS to OVER 365)
                        summary_df['Del Amt'] = summary_df[aging_buckets_for_del_percent_numerator].sum(axis=1)

                        # Calculate 'Del %' column
                        # Numerator: sum of 1-30 DAYS to OVER 365 ('Del Amt')
                        # Denominator: 'Total' column (sum of all buckets including NOT YET DUE)
                        summary_df['Del %'] = summary_df.apply(
                            lambda row: (row['Del Amt'] / row['Total'] * 100) if row['Total'] != 0 else 0,
                            axis=1
                        )

                        # Calculate individual Percentage Columns (1-30 DAYS % to OVER 365 %)
                        individual_percentage_cols = []
                        for bucket in aging_buckets_for_del_percent_numerator: # Only for buckets excluding 'NOT YET DUE'
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
                        print(f"DEBUG: 'SUMMARY' sheet sorted for AREA {area_name} by Del % (high to low) with REST at bottom.")
                        
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
                        for bucket in aging_buckets_for_del_percent_numerator:
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
                        # Amount columns are aging_buckets_full_order + 'Total' + 'Del Amt'
                        amount_col_names = aging_buckets_full_order + ['Total', 'Del Amt']
                        for col_name in amount_col_names:
                            col_idx = summary_df.columns.get_loc(col_name) + 1 # +1 because pandas index is 0-based, Excel is 1-based, and first col is index
                            worksheet.set_column(col_idx, col_idx, None, currency_format)
                        
                        # Apply percentage format to percentage columns ('Del %' and individual percentages)
                        # These are 'Del %' + individual_percentage_cols
                        for p_col in ['Del %'] + individual_percentage_cols:
                            col_idx = summary_df.columns.get_loc(p_col) + 1
                            worksheet.set_column(col_idx, col_idx, None, percentage_format)

                        # --- Add Hyperlinks from SUMMARY to individual product sheets ---
                        for r_idx, product_name_raw in enumerate(summary_df.index):
                            if product_name_raw != 'TOTAL': # Don't link the TOTAL row
                                sanitized_product_name = str(product_name_raw).replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('[', '_').replace(']', '_').replace('"', '_')
                                sanitized_sheet_name = sanitized_product_name[:31] # Ensure it matches the actual sheet name
                                # Row index in worksheet is 1-based, plus 1 for header row
                                worksheet.write_url(r_idx + 1, 0, f"internal:'{sanitized_sheet_name}'!A1", string=str(product_name_raw))
                        print(f"DEBUG: Applied number formatting and hyperlinks to 'SUMMARY' sheet for AREA {area_name}.")

                    else:
                        print(f"  No data to create 'SUMMARY' sheet for AREA: {area_name}.")


                    # --- 4. Write individual product sheets for the AREA's products (based on non_not_yet_due_df) ---
                    unique_products = non_not_yet_due_df['PRODUCT'].dropna().unique()
                    print(f"  Found unique products for AREA {area_name} (excluding 'NOT YET DUE'): {unique_products}")

                    if not unique_products.size:
                        print(f"  No specific products found for AREA {area_name} beyond 'All Products', 'DEL_PRODUCT' and 'SUMMARY' sheets.")
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

                print(f"Finished processing AREA: {area_name}")
                processed_areas_count += 1
                processed_area_names.append(area_name)

            except Exception as e:
                error_message = f"Error processing AREA '{area_name}': {e}"
                print(f"ERROR: {error_message}")
                skipped_area_names.append((area_name, str(e)))
                continue # Continue to the next area in the loop

        # --- Final summary message after all areas are processed ---
        final_message = f"Process Complete!\n\nSuccessfully separated data for {processed_areas_count} areas into {output_folder}."
        if processed_area_names:
            final_message += "\n\nProcessed Areas:\n" + "\n".join(processed_area_names)
        if skipped_area_names:
            final_message += "\n\nSkipped Areas (with errors or no data):\n"
            for area_name, error_msg in skipped_area_names:
                final_message += f"- {area_name}: {error_msg}\n"

        messagebox.showinfo("Process Complete", final_message)
        print("Process completed successfully.")

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
    process_excel_by_area()
