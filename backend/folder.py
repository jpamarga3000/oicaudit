import os
import tkinter as tk
from tkinter import filedialog, messagebox

def create_subfolders():
    # Hide the main Tkinter window
    root = tk.Tk()
    root.withdraw()

    # Ask the user to select a folder
    selected_folder = filedialog.askdirectory(
        title="Select the parent folder to create subfolders in"
    )

    # If a folder is selected, proceed
    if selected_folder:
        folder_names = [
            "AGLAYAN", "AGORA", "BALINGASAG", "BAUNGON", "BULUA", "BUTUAN",
            "CARMEN", "COGON", "DON CARLOS", "EL SALVADOR", "GINGOOG", "ILIGAN",
            "ILUSTRE", "MANOLO", "MARAMAG", "PUERTO", "TAGBILARAN", "TALAKAG",
            "TORIL", "TUBIGON", "UBAY", "VALENCIA", "YACAPIN"
        ]

        # Create each subfolder
        for folder_name in folder_names: # CORRECTED LINE HERE
            folder_path = os.path.join(selected_folder, folder_name)
            try:
                os.makedirs(folder_path)
                print(f"Created folder: {folder_path}")
            except FileExistsError:
                print(f"Folder already exists: {folder_path}")
            except Exception as e:
                print(f"Error creating folder {folder_path}: {e}")

        messagebox.showinfo("Folders Created", "All specified folders have been processed.")
    else:
        messagebox.showwarning("No Folder Selected", "No folder was selected. No folders were created.")

if __name__ == "__main__":
    create_subfolders()