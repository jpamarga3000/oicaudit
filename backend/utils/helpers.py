# audit_tool/backend/utils/helpers.py (Corrected and Merged with get_branches_for_request)
import os
import sys
import tempfile
import shutil
import json
import pandas as pd
import traceback
from werkzeug.utils import secure_filename
# Removed: from flask import request, jsonify # These should be passed as arguments if needed

# Define AREA_BRANCH_MAP here as it's a shared configuration
AREA_BRANCH_MAP = {
    'Area 1': [
        'BAUNGON', "BULUA", "CARMEN", "COGON", "EL SALVADOR",
        "ILIGAN", "TALAKAG", "YACAPIN"
    ],
    'Area 2': [
        "AGLAYAN", "DON CARLOS", "ILUSTRE", "MANOLO", "MARAMAG",
        "TORIL", "VALENCIA"
    ],
    'Area 3': [
        "AGORA", "BALINGASAG", "BUTUAN", "GINGOOG", "PUERTO",
        "TAGBILARAN", "TUBIGON", "UBAY"
    ],
    'Consolidated': [ # This represents a request for all branches combined
        'AGLAYAN', 'AGORA', 'BALINGASAG', 'BAUNGON', 'BULUA', 'BUTUAN',
        'CARMEN', 'COGON', 'DON CARLOS', 'EL SALVADOR', 'GINGOOG', 'ILIGAN',
        'ILUSTRE', 'MANOLO', 'MARAMAG', 'PUERTO', 'TAGBILARAN', 'TALAKAG',
        'TORIL', 'TUBIGON', 'UBAY', 'UNKNOWN' # Added 'UNKNOWN' for files where branch cannot be determined
    ]
}

# Add a comprehensive list of all branches for 'ALL' area selection
AREA_BRANCH_MAP['ALL_BRANCHES_LIST'] = sorted(list(set(
    b for sublist in AREA_BRANCH_MAP.values() if isinstance(sublist, list) for b in sublist
)))


def get_branch_list(area):
    """Returns a list of branches for a given area."""
    return AREA_BRANCH_MAP.get(area, [])

def get_all_branches():
    """Returns a combined list of all unique branches from all areas."""
    all_branches = set()
    for branches in AREA_BRANCH_MAP.values():
        # Ensure we only iterate over lists in AREA_BRANCH_MAP
        if isinstance(branches, list):
            all_branches.update(branches)
    return sorted(list(all_branches))

def get_branches_for_request(area, branch):
    """
    Determines the list of specific branches to process based on the selected area and branch.
    Handles 'ALL' and 'Consolidated' selections.

    Args:
        area (str): The selected area (e.g., 'Area 1', 'CONSOLIDATED', 'ALL').
        branch (str): The selected branch within the area (e.g., 'BAUNGON', 'ALL', '').

    Returns:
        list: A list of specific branch names (strings) to process.
              Returns an empty list if no valid branches are resolved.
    """
    branches_to_process = []

    if area == 'ALL':
        # If 'ALL' areas are selected, return the comprehensive list of all branches
        branches_to_process = AREA_BRANCH_MAP.get('ALL_BRANCHES_LIST', [])
        print(f"Server Log (helpers): Resolved 'ALL' areas to branches: {branches_to_process}")
    elif area == 'Consolidated': # Use 'Consolidated' as per your AREA_BRANCH_MAP key
        # If 'Consolidated' is selected, return only 'Consolidated' as a special branch
        branches_to_process = ['Consolidated'] # Match the key in AREA_BRANCH_MAP
        print(f"Server Log (helpers): Resolved 'Consolidated' area to: {branches_to_process}")
    elif area in AREA_BRANCH_MAP:
        # If a specific area is selected
        if branch and branch != 'ALL':
            # If a specific branch is selected within an an area, validate it
            if branch in AREA_BRANCH_MAP[area]:
                branches_to_process = [branch]
                print(f"Server Log (helpers): Resolved specific branch '{branch}' in area '{area}'.")
            else:
                print(f"Server Log (helpers): Warning: Branch '{branch}' not found in area '{area}'. Returning empty list.")
                branches_to_process = []
        else: # branch is 'ALL' or empty, meaning all branches in the selected area
            branches_to_process = AREA_BRANCH_MAP[area]
            print(f"Server Log (helpers): Resolved all branches in area '{area}': {branches_to_process}")
    else:
        print(f"Server Log (helpers): Warning: Invalid area selected: '{area}'. Returning empty list.")
        branches_to_process = []

    # Ensure uniqueness and sort for consistent processing
    branches_to_process = sorted(list(set(branches_to_process)))
    return branches_to_process


def handle_file_upload_and_process(process_function, output_folder, files, files_key='files', jsonify_func=None, additional_params=None):
    """
    Handles file uploads, saves them to a temporary directory,
    calls a specified processing function, and then cleans up.

    Args:
        process_function (callable): The function to call for processing.
                                     It should accept (input_temp_dir, output_folder, additional_params).
        output_folder (str): The desired output folder for processed files.
        files (list): The list of files from request.files.getlist(files_key).
        files_key (str): The key under which files are expected in the request.
        jsonify_func (callable, optional): The jsonify function from Flask. Defaults to None.
        additional_params (dict, optional): Additional parameters to pass to the process_function.

    Returns:
        tuple: A tuple containing (response_data, status_code).
    """
    if jsonify_func is None:
        # Fallback if jsonify_func is not provided (e.g., for testing outside Flask context)
        def default_jsonify(data):
            return data
        jsonify_func = default_jsonify

    temp_input_dir = None
    try:
        # Create a temporary directory for uploaded files
        temp_input_dir = tempfile.mkdtemp()
        print(f"Server Log: Created temporary directory: {temp_input_dir}")

        uploaded_file_paths = []
        for file in files:
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(temp_input_dir, filename)
                file.save(filepath)
                uploaded_file_paths.append(filepath)

        if not uploaded_file_paths:
            return jsonify_func({"message": "No files uploaded for processing."}), 400

        # Call the processing function with the temporary input directory and output folder
        # The process_function is expected to handle its own output file naming/paths
        # within the specified output_folder.
        # We pass additional_params directly to the process_function.
        
        # The lambda in file_processing_routes.py will adapt the arguments
        # to what the specific process_function expects.
        result = process_function(temp_input_dir, output_folder, uploaded_file_paths) # Pass uploaded_file_paths as dummy_files_arg

        if result and isinstance(result, dict):
            # If the processing function returns a dictionary, assume it's a direct response
            return jsonify_func(result), 200
        elif result is not None:
            # If the processing function returns a DataFrame or other data,
            # you might want to convert it to a more suitable format for the frontend.
            # For now, we'll assume the process_function handles its own saving
            # and returns a success message.
            return jsonify_func({"message": "Processing successful", "data": str(result)}), 200
        else:
            return jsonify_func({"message": "Processing completed, but no specific result returned."}), 200

    except Exception as e:
        print(f"Error during file processing: {e}")
        traceback.print_exc()
        return jsonify_func({"message": f"An error occurred during processing: {str(e)}"}), 500
    finally:
        # Clean up the temporary directory
        if temp_input_dir and os.path.exists(temp_input_dir):
            shutil.rmtree(temp_input_dir)
            print(f"Server Log: Cleaned up temporary directory: {temp_input_dir}")


def handle_single_file_upload_and_process(process_function, request_obj, files_key='files', app_config_upload_folder=None, jsonify_func=None, additional_params=None):
    """
    Handles single file uploads, saves them, calls a specified processing function,
    and returns the result. This is a simplified version for single file processing
    that expects the process_function to return a DataFrame.

    Args:
        process_function (callable): The function to call for processing.
                                     It should accept (file_paths, output_folder, additional_params).
        request_obj (object): The Flask request object.
        files_key (str): The key under which files are expected in the request.
        app_config_upload_folder (str): The configured upload folder path.
        jsonify_func (callable, optional): The jsonify function from Flask. Defaults to None.
        additional_params (dict, optional): Additional parameters to pass to the process_function.

    Returns:
        tuple: A tuple containing (response_data, status_code).
    """
    if jsonify_func is None:
        def default_jsonify(data):
            return data
        jsonify_func = default_jsonify

    if app_config_upload_folder is None:
        return jsonify_func({"error": "Upload folder not configured."}), 500

    try:
        uploaded_files = []
        output_folder = request_obj.form.get('output_dir', app_config_upload_folder)

        if files_key in request_obj.files: # For single file input
            file = request_obj.files[files_key]
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app_config_upload_folder, filename)
                file.save(filepath)
                uploaded_files.append(filepath)

        if not uploaded_files:
            return jsonify_func({"error": "No files uploaded for processing."}), 400

        params = {
            'file_paths': uploaded_files,
            'output_folder': output_folder
        }
        if additional_params:
            params.update(additional_params)

        result_df = process_function(**params)

        if result_df is not None and not result_df.empty:
            result_df_cleaned = result_df.fillna('').astype(str)
            html_table = result_df_cleaned.to_html(classes="min-w-full bg-white", index=False)
            return jsonify_func({"message": "Processing successful", "table_html": html_table})
        else:
            return jsonify_func({"message": "Processing completed, but no data to display or DataFrame is empty."})

    except Exception as e:
        print(f"Error during processing: {e}") # Use print as app.logger is not available here
        print(traceback.format_exc())
        return jsonify_func({"error": f"An error occurred during processing: {str(e)}"}), 500

