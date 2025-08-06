import pandas as pd
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

def process_csv_files():
    """
    Allows the user to select an input folder, specify an output folder,
    and then processes CSV files to rename them based on the latest date
    in the 'DOPEN' column.
    """
    # Initialize Tkinter for file dialogs (hidden root window)
    root = tk.Tk()
    root.withdraw() # Hide the main window

    # 1. Choose input folder
    input_folder = filedialog.askdirectory(title="Select Folder Containing CSV Files")
    if not input_folder:
        messagebox.showinfo("Cancelled", "Input folder selection cancelled. Exiting.")
        return

    # 2. Manually input output folder path
    output_folder = simpledialog.askstring("Output Folder", "Enter the full path for the output folder:")
    if not output_folder:
        messagebox.showinfo("Cancelled", "Output folder path not entered. Exiting.")
        return

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")

    processed_count = 0
    failed_files = []

    # Iterate through all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            base_name = os.path.splitext(filename)[0]

            try:
                # Read the CSV file
                df = pd.read_csv(file_path)

                # Check if 'DOPEN' column exists
                if 'DOPEN' in df.columns:
                    # Convert 'DOPEN' column to datetime objects, coercing errors to NaT
                    # This handles mixed date formats and invalid entries
                    df['DOPEN'] = pd.to_datetime(df['DOPEN'], errors='coerce')

                    # Drop rows where 'DOPEN' conversion failed (NaT)
                    df_cleaned = df.dropna(subset=['DOPEN'])

                    if not df_cleaned.empty:
                        # Find the latest date
                        latest_date = df_cleaned['DOPEN'].max()

                        # Format the date as mm-dd-yyyy
                        formatted_date = latest_date.strftime("%m-%d-%Y")

                        # Construct the new filename
                        new_filename = f"{base_name} - {formatted_date}.csv"
                        new_file_path = os.path.join(output_folder, new_filename)

                        # Save the processed CSV to the output folder with the new name
                        df.to_csv(new_file_path, index=False)
                        print(f"Processed '{filename}' -> Saved as '{new_filename}'")
                        processed_count += 1
                    else:
                        print(f"Skipping '{filename}': No valid dates found in 'DOPEN' column.")
                        failed_files.append(f"{filename} (No valid DOPEN dates)")
                else:
                    print(f"Skipping '{filename}': 'DOPEN' column not found.")
                    failed_files.append(f"{filename} (DOPEN column missing)")

            except Exception as e:
                print(f"Error processing '{filename}': {e}")
                failed_files.append(f"{filename} (Error: {e})")

    messagebox.showinfo("Processing Complete",
                        f"Finished processing CSV files.\n"
                        f"Processed: {processed_count} files.\n"
                        f"Failed/Skipped: {len(failed_files)} files.")

    if failed_files:
        print("\n--- Files that failed or were skipped ---")
        for f in failed_files:
            print(f)

    root.destroy() # Close the hidden Tkinter window

# Run the processing function
if __name__ == "__main__":
    process_csv_files()
