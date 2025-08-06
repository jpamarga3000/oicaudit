import os
import shutil

def extract_and_copy_contents(input_folder_path, output_folder_path):
    """
    Extracts all files from subfolders within the input_folder_path
    and copies them into the output_folder_path.

    Args:
        input_folder_path (str): The path to the main folder containing subfolders.
        output_folder_path (str): The path to the folder where all contents
                                  will be saved.
    """
    print(f"\n--- Starting content extraction and copying ---")
    print(f"Input Folder: {input_folder_path}")
    print(f"Output Folder: {output_folder_path}")

    # 1. Validate the input folder path
    if not os.path.exists(input_folder_path):
        print(f"Error: The input folder '{input_folder_path}' does not exist.")
        return
    if not os.path.isdir(input_folder_path):
        print(f"Error: The input path '{input_folder_path}' is not a directory.")
        return

    # 2. Create the output folder if it doesn't exist
    try:
        os.makedirs(output_folder_path, exist_ok=True)
        print(f"Ensured output folder '{output_folder_path}' exists.")
    except OSError as e:
        print(f"Error creating output folder '{output_folder_path}': {e}")
        return

    copied_files_count = 0
    overwritten_files_count = 0
    failed_copies_count = 0

    # 3. Walk through the input folder and its subdirectories
    for root, dirs, files in os.walk(input_folder_path):
        # Skip the output folder if it's nested within the input folder
        if os.path.commonpath([root, output_folder_path]) == output_folder_path and root != input_folder_path:
            print(f"Skipping processing of output folder path: {root}")
            continue

        for file_name in files:
            source_file_path = os.path.join(root, file_name)
            destination_file_path = os.path.join(output_folder_path, file_name)

            try:
                # Check if the file already exists in the destination to track overwrites
                if os.path.exists(destination_file_path):
                    print(f"Warning: Overwriting '{file_name}' in output folder. (Source: {root})")
                    overwritten_files_count += 1
                
                shutil.copy2(source_file_path, destination_file_path) # copy2 preserves metadata
                copied_files_count += 1
                # print(f"Copied: '{source_file_path}' to '{destination_file_path}'")
            except Exception as e:
                failed_copies_count += 1
                print(f"Failed to copy '{source_file_path}' to '{destination_file_path}': {e}")

    print(f"\n--- Copying process complete ---")
    print(f"Total files copied: {copied_files_count}")
    print(f"Total files overwritten: {overwritten_files_count}")
    print(f"Total files failed to copy: {failed_copies_count}")
    print(f"Contents of all subfolders have been extracted and saved to: {output_folder_path}")

# --- Main part of the script ---
if __name__ == "__main__":
    while True:
        input_path = input("Please enter the FULL path to the input folder (e.g., C:\\Users\\YourName\\MyDocs\\Photos): ")
        if os.path.exists(input_path) and os.path.isdir(input_path):
            break
        else:
            print("Invalid input path. Please ensure the path exists and is a directory.")

    while True:
        output_path = input("Please enter the FULL path to the output folder where contents will be saved (e.g., C:\\Users\\YourName\\ExtractedFiles): ")
        # Basic validation: allow creation of new folder, but check if it's a valid path structure
        if os.path.isabs(output_path): # Checks if it's an absolute path
            # Further check if the parent directory exists, if not creating it would fail
            parent_dir = os.path.dirname(output_path)
            if parent_dir and not os.path.exists(parent_dir) and parent_dir != output_path:
                print(f"Warning: Parent directory '{parent_dir}' does not exist. It will attempt to be created.")
            break
        else:
            print("Invalid output path. Please enter a full, absolute path.")

    extract_and_copy_contents(input_path, output_path)
