import pandas as pd
import os
import tkinter as tk # Import tkinter for GUI operations
from tkinter import filedialog # Import filedialog for file selection dialog

def process_gl_data(input_file_path, output_folder_path):
    """
    Processes an Excel or CSV file to add a 'NATURE' column (DR/CR) based on GLACC and BAL.

    Args:
        input_file_path (str): The full path to the input Excel or CSV file.
        output_folder_path (str): The path to the folder where the processed
                                  Excel file will be saved.

    Returns:
        str: A message indicating success or an error.
    """
    
    # --- 1. Input Validation and File Reading ---
    if not os.path.exists(input_file_path):
        return f"Error: Input file '{input_file_path}' not found."
    
    # Create output folder if it doesn't exist
    if not os.path.isdir(output_folder_path):
        try:
            os.makedirs(output_folder_path)
        except OSError as e:
            return f"Error creating output folder '{output_folder_path}': {e}"

    # Determine file type and read accordingly
    file_extension = os.path.splitext(input_file_path)[1].lower()
    try:
        if file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(input_file_path)
        elif file_extension == '.csv':
            df = pd.read_csv(input_file_path)
        else:
            return "Error: Unsupported file type. Please select an Excel (.xlsx, .xls) or CSV (.csv) file."
    except Exception as e:
        return f"Error reading file '{os.path.basename(input_file_path)}': {e}. Please ensure it's a valid format."


    # --- 2. Data Preparation ---
    # Check for required columns
    if 'GLACC' not in df.columns:
        return "Error: 'GLACC' column not found in the input file. Please ensure the column header is exactly 'GLACC'."
    if 'BAL' not in df.columns:
        return "Error: 'BAL' column (which holds the balance amount, often Column I) not found. Please ensure the column header is exactly 'BAL'."
    
    # Convert 'GLACC' to string to easily extract the first digit
    df['GLACC'] = df['GLACC'].astype(str)
    
    # Convert 'BAL' to numeric. Coerce errors to NaN (Not a Number) and drop rows with invalid BAL.
    df['BAL'] = pd.to_numeric(df['BAL'], errors='coerce')
    df.dropna(subset=['BAL'], inplace=True) # Remove rows where 'BAL' could not be converted

    # Identify and process a 'Date' column for 'per year' logic
    date_col_exists = False
    original_date_col = None
    # Common date column names to check
    for col_name in ['Date', 'Transaction Date', 'TranDate', 'Posting Date', 'PostDate', 'DocDate']:
        if col_name in df.columns:
            try:
                # Attempt to convert to datetime and extract year
                df['__TEMP_YEAR__'] = pd.to_datetime(df[col_name], errors='coerce').dt.year
                df.dropna(subset=['__TEMP_YEAR__'], inplace=True) # Remove rows where year could not be extracted
                df['__TEMP_YEAR__'] = df['__TEMP_YEAR__'].astype(int) # Convert year to integer
                date_col_exists = True
                original_date_col = col_name # Keep track of the original date column name
                break
            except Exception:
                # If conversion fails for this column, try the next
                pass 
    
    if not date_col_exists:
        print("Warning: No suitable date column found (tried 'Date', 'Transaction Date', 'TranDate', 'Posting Date', 'PostDate', 'DocDate').")
        print("         'Per year' logic will not be applied. 'NATURE' will be calculated based on sequential 'BAL' changes within each 'GLACC' group across the entire dataset.")

    # Create a temporary column to store the original index, crucial for stable sorting
    # This helps in maintaining the original order for rows that have the same GLACC and (optionally) Year.
    df['__ORIGINAL_INDEX__'] = df.index

    # Sort the DataFrame. This is crucial for comparing current 'BAL' with previous 'BAL'.
    # We sort by 'GLACC' first, then by '__TEMP_YEAR__' (if available), and finally by the temporary original index column.
    if date_col_exists:
        df.sort_values(by=['GLACC', '__TEMP_YEAR__', '__ORIGINAL_INDEX__'], inplace=True)
    else:
        df.sort_values(by=['GLACC', '__ORIGINAL_INDEX__'], inplace=True) 
    
    # Drop the temporary original index column after sorting, as it's no longer needed
    df.drop(columns=['__ORIGINAL_INDEX__'], inplace=True)

    # --- 3. Calculate 'NATURE' Column ---
    # Define a helper function to calculate 'NATURE' for each group (GLACC, and optionally Year)
    def calculate_nature_for_group(group):
        prev_bal = None # This will store the balance of the previous row within this specific group
        natures = [] # List to store calculated natures for the rows in this group

        for index, row in group.iterrows():
            glacc = row['GLACC']
            current_bal = row['BAL']
            
            # Extract the first digit of GLACC
            glacc_prefix = glacc[0] if glacc else '' # Handle empty GLACC gracefully
            
            nature = ''

            # Logic for GLACC prefixes 1, 2, 3, 9
            if glacc_prefix in ['1', '2', '3', '9']:
                if prev_bal is None: # This is the very first transaction for this GLACC (and Year)
                    # Apply default logic based on the prefix when no previous balance is available
                    if glacc_prefix in ['1', '9']:
                        nature = 'DR'
                    elif glacc_prefix in ['2', '3']:
                        nature = 'CR'
                    else: 
                        nature = 'UNKNOWN_GLACC_PREFIX' # Should not be reached with current prefix list
                elif current_bal > prev_bal:
                    nature = 'DR'
                elif current_bal < prev_bal:
                    nature = 'CR'
                else: # current_bal == prev_bal (apply default logic as per user request)
                    if glacc_prefix in ['1', '9']:
                        nature = 'DR'
                    elif glacc_prefix in ['2', '3']:
                        nature = 'CR'
                    else:
                        nature = 'UNKNOWN_GLACC_PREFIX' # Should not be reached
            # Logic for GLACC prefixes 4, 5
            elif glacc_prefix == '4':
                # As per interpretation: always 'CR' for GLACC starting with 4 (e.g., Revenue)
                nature = 'CR'
            elif glacc_prefix == '5':
                # As per interpretation: always 'DR' for GLACC starting with 5 (e.g., Expenses)
                nature = 'DR'
            else:
                # For any other GLACC prefix not explicitly defined
                nature = 'UNKNOWN_GLACC_PREFIX' 
            
            natures.append(nature)
            prev_bal = current_bal # Update the previous balance for the next iteration in this group
        
        # Return a pandas Series with the calculated natures, ensuring index alignment with the original group
        return pd.Series(natures, index=group.index)

    # Apply the nature calculation function grouped by GLACC (and Year if available)
    if date_col_exists:
        df['NATURE'] = df.groupby(['GLACC', '__TEMP_YEAR__'], group_keys=False).apply(calculate_nature_for_group)
        df.drop(columns=['__TEMP_YEAR__'], inplace=True) # Clean up temporary year column
    else:
        df['NATURE'] = df.groupby('GLACC', group_keys=False).apply(calculate_nature_for_group)

    # --- 4. Save Output File ---
    # Construct the output filename (e.g., original_file_name_processed.xlsx)
    base_filename = os.path.splitext(os.path.basename(input_file_path))[0] # Get filename without extension
    output_filename = f"{base_filename}_processed.xlsx"
    output_file_path = os.path.join(output_folder_path, output_filename)

    try:
        df.to_excel(output_file_path, index=False) # Save DataFrame to Excel, without writing the DataFrame index
        return f"Successfully processed data. Output saved to: {output_file_path}"
    except Exception as e:
        return f"Error saving output file: {e}"

# --- Main script execution part ---
if __name__ == "__main__":
    print("--- GLACC Data Processor ---")
    print("This script adds a 'NATURE' (DR/CR) column to your Excel or CSV GL data.")

    # Hide the main tkinter window
    root = tk.Tk()
    root.withdraw() 

    # Get input file path from the user using a file dialog
    input_file = filedialog.askopenfilename(
        title="Select your Excel or CSV file",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not input_file: # If user cancels the dialog
        print("File selection cancelled. Exiting.")
    else:
        # Get output folder path from the user (still manual input)
        output_folder = input("Enter the desired output folder path (e.g., C:\\Users\\YourName\\ProcessedData): ")

        # Run the processing function
        result_message = process_gl_data(input_file, output_folder)
        print("\n" + result_message)

    print("\nProcessing complete. Press Enter to exit.")
    input() # Keep the console open until user presses Enter
