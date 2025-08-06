import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
import os

def select_zip_file():
    """Opens a file dialog to let the user select a ZIP file."""
    file_path = filedialog.askopenfilename(
        title="Select a ZIP File",
        filetypes=[("ZIP files", "*.zip")]
    )
    if file_path:
        selected_file_label.config(text=f"Selected: {file_path}")
        convert_button.config(state=tk.NORMAL)  # Enable the convert button
        return file_path
    else:
        selected_file_label.config(text="No file selected.")
        convert_button.config(state=tk.DISABLED) # Disable if no file
        return None

def convert_to_bak():
    """
    Copies the selected ZIP file to a new file with a .bak extension.
    """
    selected_file_path = selected_file_label.cget("text").replace("Selected: ", "")

    if not selected_file_path or not os.path.exists(selected_file_path):
        messagebox.showwarning("No File Selected", "Please select a ZIP file first.")
        return

    # Determine the destination .bak file name
    # Option 1: Append .bak (e.g., my_archive.zip.bak)
    bak_file_path = selected_file_path + ".bak"
    
    # Option 2: Replace .zip with .bak (e.g., my_archive.bak)
    # base_name, ext = os.path.splitext(selected_file_path)
    # bak_file_path = base_name + ".bak"

    try:
        shutil.copyfile(selected_file_path, bak_file_path)
        messagebox.showinfo(
            "Conversion Successful",
            f"Successfully created backup:\n{bak_file_path}"
        )
        # Reset the selection after successful conversion
        selected_file_label.config(text="No file selected.")
        convert_button.config(state=tk.DISABLED)
    except FileNotFoundError:
        messagebox.showerror("Error", "Selected file not found.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during conversion: {e}")

# --- GUI Setup ---
root = tk.Tk()
root.title("ZIP to .bak Converter")
root.geometry("500x200") # Set initial window size

# Frame for file selection
file_frame = tk.Frame(root, padx=10, pady=10)
file_frame.pack(pady=10)

browse_button = tk.Button(
    file_frame,
    text="Browse ZIP File",
    command=select_zip_file
)
browse_button.pack(side=tk.LEFT, padx=5)

selected_file_label = tk.Label(
    file_frame,
    text="No file selected.",
    wraplength=350, # Wrap text if path is too long
    justify=tk.LEFT
)
selected_file_label.pack(side=tk.LEFT, padx=5)

# Convert button
convert_button = tk.Button(
    root,
    text="Convert to .bak (Create Copy)",
    command=convert_to_bak,
    state=tk.DISABLED # Start disabled until a file is selected
)
convert_button.pack(pady=10)

# Run the application
root.mainloop()