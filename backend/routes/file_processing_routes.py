from flask import Blueprint, request, jsonify, send_file
import sys
import os
import io # Import io for BytesIO if needed for in-memory zipping
import zipfile # Import zipfile for zipping multiple files
import tempfile # Import tempfile for creating temporary directories
import shutil # Import shutil for cleaning up temporary directories
from werkzeug.utils import secure_filename # Import secure_filename

# Import helper functions from the new utils module using absolute import
import backend.utils.helpers as helpers
from backend.db_common import TRNM_BASE_DIR, LNACC_BASE_DIR, SVACC_BASE_DIR, GL_BASE_DIR # Import GL_BASE_DIR

# Import processing functions
from backend.aging_conso import process_excel_files_to_csv
from backend.petty_cash import process_and_combine_excel_data_web
from backend.comtrnm import process_transactions_web # Updated import
from backend.convert_dbf import process_dbf_to_csv_web
from backend.win_process import process_win_data_web
from backend.gl_dos_process import process_gl_dos_data_web
from backend.gl_win_process import process_gl_win_data_web
from backend.lnacc_dos_process import process_lnacc_dos_data_web
from backend.lnacc_win_process import process_lnacc_win_data_web
from backend.svacc_dos_process import process_svacc_dos_data_web
from backend.svacc_win_process import process_svacc_win_data_web
from backend.journal_voucher_process import process_journal_voucher_data
# Removed WP LR imports:
# from wp_lr_reference_process import process_wp_lr_reference_data
from backend.audit_tool_tb_process import process_audit_tool_tb_files as process_audit_tool_tb_logic # Added/Corrected import

file_processing_bp = Blueprint('file_processing_bp', __name__)

# Define a common upload folder for all file processing routes
# This UPLOAD_FOLDER is primarily for temporary uploads before processing
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Ensure the upload directory exists

@file_processing_bp.route('/process_aging_consolidated', methods=['POST'])
def process_aging_consolidated():
    output_dir = request.form.get('output_dir')
    files = request.files.getlist('files')
    branch = request.form.get('branch', default='').strip()

    if not files or not output_dir or not branch:
        return jsonify({"message": "Please upload Excel files, select a branch, and provide an output directory."}), 400

    print(f"Server Log: Received request for Aging Consolidated. Output='{output_dir}', Files Count={len(files)}, Branch='{branch}'")

    response_data, status_code = helpers.handle_file_upload_and_process(
        lambda input_temp_dir, output_folder, branch_val: process_excel_files_to_csv(input_temp_dir, output_folder, branch_val),
        output_dir,
        files,
        additional_params={'branch_val': branch}
    )
    return jsonify(response_data), status_code

@file_processing_bp.route('/process_petty_cash', methods=['POST'])
def process_petty_cash():
    output_dir = request.form.get('output_dir')
    files = request.files.getlist('files')

    if not files or not output_dir:
        return jsonify({"message": "Please upload Excel files and provide an output directory."}), 400

    print(f"Server Log: Received request for Petty Cash. Output='{output_dir}', Files Count={len(files)}")

    response_data, status_code = helpers.handle_file_upload_and_process(
        lambda input_temp_dir, output_folder, dummy_files_arg: process_and_combine_excel_data_web(input_temp_dir, output_folder),
        output_dir,
        files
    )
    return jsonify(response_data), status_code

# MODIFIED: Adjusted to use TRNM_BASE_DIR and branch subfolder for output_dir
@file_processing_bp.route('/process_trnm', methods=['POST'])
def process_transactions():
    files = request.files.getlist('files')
    branch = request.form.get('branch', default='').strip()

    if not files or not branch:
        return jsonify({"message": "Please upload DBF files and select a branch."}), 400

    print(f"Server Log: Received request for Transactions. Files Count={len(files)}, Branch='{branch}'")

    # Normalize branch name for folder creation (replace spaces with underscores)
    normalized_branch_name = branch.replace(' ', '_').upper()
    
    # Define the specific output directory within TRNM_BASE_DIR
    # Ensure TRNM_BASE_DIR is treated as an absolute path to prevent concatenation issues
    trnm_output_dir = os.path.join(os.path.abspath(TRNM_BASE_DIR), normalized_branch_name)
    os.makedirs(trnm_output_dir, exist_ok=True)
    print(f"Server Log: Defined TRNM output directory: {trnm_output_dir}")

    # Determine the 3-letter prefix for filenames
    file_prefix = branch[:3].upper()

    try:
        response_data, status_code = helpers.handle_file_upload_and_process(
            # Pass the file_prefix to process_transactions_web
            lambda input_temp_dir, output_folder, *args: process_transactions_web(input_temp_dir, output_folder, file_prefix),
            trnm_output_dir, # Pass the specific TRNM output directory here
            files,
            additional_params={'branch_val': branch} # Keep branch_val in additional_params if needed by helper
        )
        # Ensure the output_path in response_data is the trnm_output_dir
        if response_data and 'output_path' not in response_data:
            response_data['output_path'] = trnm_output_dir

        return jsonify(response_data), status_code
    except Exception as e:
        print(f"Error during TRNM processing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during processing: {str(e)}"}), 500
    finally:
        # For TRNM, the output is saved to a permanent location, so no temporary cleanup needed here.
        pass

# MODIFIED: Adjusted to generate output_dir on the backend
@file_processing_bp.route('/process_convert_dbf', methods=['POST'])
def convert_dbf_to_csv():
    files = request.files.getlist('files')

    if not files:
        return jsonify({"message": "Please upload DBF files."}), 400

    print(f"Server Log: Received request for DBF to CSV conversion. Files Count={len(files)}")

    # Create a temporary directory for the *output* CSV files.
    # This directory will be returned to the frontend for download and later cleanup.
    temp_output_dir = tempfile.mkdtemp(dir=UPLOAD_FOLDER, prefix='converted_dbf_output_')
    print(f"Server Log: Created temporary output directory for converted DBF files: {temp_output_dir}")

    try:
        response_data, status_code = helpers.handle_file_upload_and_process(
            # The processing function process_dbf_to_csv_web expects input_dir and output_dir
            lambda input_temp_dir, output_folder, dummy_files_arg: process_dbf_to_csv_web(input_temp_dir, output_folder),
            temp_output_dir, # Pass the generated temporary output directory here
            files
        )
        # Ensure the output_path in response_data is the temp_output_dir
        if response_data and 'output_path' not in response_data:
            response_data['output_path'] = temp_output_dir

        return jsonify(response_data), status_code
    except Exception as e:
        print(f"Error during DBF conversion: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during processing: {str(e)}"}), 500
    finally:
        # The cleanup of temp_output_dir will be handled by the /delete_temp_converted_dbf endpoint
        # after the user downloads the files. So, no need to delete it here.
        pass

@file_processing_bp.route('/process_win_data', methods=['POST'])
def process_win_data():
    output_dir = request.form.get('output_dir')
    files = request.files.getlist('files')
    branch = request.form.get('branch', default='').strip()

    if not files or not output_dir or not branch:
        return jsonify({"message": "Please upload DBF files, select a branch, and provide an output directory."}), 400

    print(f"Server Log: Received request for WIN Data processing. Output='{output_dir}', Files Count={len(files)}, Branch='{branch}'")

    response_data, status_code = helpers.handle_file_upload_and_process(
        lambda input_temp_dir, output_folder, branch_val: process_win_data_web(input_temp_dir, output_folder, branch_val),
        output_dir,
        files,
        additional_params={'branch_val': branch}
    )
    return jsonify(response_data), status_code

# MODIFIED: Changed route name from /process_gl_dos_data to /process_gl_dos
# MODIFIED: Adjusted to use GL_BASE_DIR and branch subfolder for output_dir
@file_processing_bp.route('/process_gl_dos', methods=['POST'])
def process_gl_dos_data():
    files = request.files.getlist('files')
    branch = request.form.get('branch', default='').strip() # Assuming frontend sends 'branch'

    if not files or not branch:
        print(f"Server Log: Validation failed for GL DOS. Files: {len(files)}, Branch: '{branch}'")
        return jsonify({"message": "Please upload DBF files and select a branch."}), 400

    print(f"Server Log: Received request for GL DOS processing. Files Count={len(files)}, Branch='{branch}'")

    # Normalize branch name for folder creation (replace spaces with underscores)
    normalized_branch_name = branch.replace(' ', '_').upper()
    
    # Define the specific output directory within GL_BASE_DIR
    # Ensure GL_BASE_DIR is treated as an absolute path to prevent concatenation issues
    gl_output_dir = os.path.join(os.path.abspath(GL_BASE_DIR), normalized_branch_name)
    os.makedirs(gl_output_dir, exist_ok=True)
    print(f"Server Log: Defined GL DOS output directory: {gl_output_dir}")

    try:
        # Pass the constructed output_dir and branch to process_gl_dos_data_web
        response_data, status_code = helpers.handle_file_upload_and_process(
            lambda input_temp_dir, output_folder, *args: process_gl_dos_data_web(input_temp_dir, branch),
            gl_output_dir, # Pass the GL_BASE_DIR as the output folder
            files,
            additional_params={'branch_val': branch} # Keep branch_val in additional_params if needed by helper
        )
        # Ensure the output_path in response_data is the gl_output_dir
        if response_data and 'output_path' not in response_data:
            response_data['output_path'] = gl_output_dir

        return jsonify(response_data), status_code
    except Exception as e:
        print(f"Error during GL DOS processing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during processing: {str(e)}"}), 500
    finally:
        # For GL DOS, the output is saved to a permanent location, so no temporary cleanup needed here.
        pass


# MODIFIED: Changed route name from /process_gl_win_data to /process_gl_win
# MODIFIED: Adjusted to use GL_BASE_DIR and branch subfolder for output_dir
@file_processing_bp.route('/process_gl_win', methods=['POST'])
def process_gl_win_data():
    files = request.files.getlist('files')
    branch = request.form.get('branch', default='').strip() # Assuming frontend sends 'branch'

    if not files or not branch:
        print(f"Server Log: Validation failed for GL WIN. Files: {len(files)}, Branch: '{branch}'")
        return jsonify({"message": "Please upload CSV files and select a branch."}), 400

    print(f"Server Log: Received request for GL WIN processing. Files Count={len(files)}, Branch='{branch}'")

    # Normalize branch name for folder creation (replace spaces with underscores)
    normalized_branch_name = branch.replace(' ', '_').upper()
    
    # Define the specific output directory within GL_BASE_DIR
    # Ensure GL_BASE_DIR is treated as an absolute path to prevent concatenation issues
    gl_output_dir = os.path.join(os.path.abspath(GL_BASE_DIR), normalized_branch_name)
    os.makedirs(gl_output_dir, exist_ok=True)
    print(f"Server Log: Defined GL WIN output directory: {gl_output_dir}")

    try:
        # Pass the constructed output_dir and branch to process_gl_win_data_web
        response_data, status_code = helpers.handle_file_upload_and_process(
            lambda input_temp_dir, output_folder, *args: process_gl_win_data_web(input_temp_dir, branch),
            gl_output_dir, # Pass the GL_BASE_DIR as the output folder
            files,
            additional_params={'branch_val': branch} # Keep branch_val in additional_params if needed by helper
        )
        # Ensure the output_path in response_data is the gl_output_dir
        if response_data and 'output_path' not in response_data:
            response_data['output_path'] = gl_output_dir

        return jsonify(response_data), status_code

    except Exception as e:
        print(f"Error during GL WIN processing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during processing: {str(e)}"}), 500
    finally:
        # For GL WIN, the output is saved to a permanent location, so no temporary cleanup needed here.
        pass


# MODIFIED: Changed route name from /process_lnacc_dos_data to /process_lnacc_dos
@file_processing_bp.route('/process_lnacc_dos', methods=['POST'])
def process_lnacc_dos_data():
    # --- START DEBUG LOGGING ---
    print("Server Log (LNACC DOS Route): Received POST request for /process_lnacc_dos")
    files = request.files.getlist('files')
    branch = request.form.get('branch', default='').strip()
    
    print(f"Server Log (LNACC DOS Route): Files received count: {len(files)}")
    print(f"Server Log (LNACC DOS Route): Branch received: '{branch}'")
    # --- END DEBUG LOGGING ---

    # Modified validation to remove output_dir check
    if not files or not branch:
        print(f"Server Log (LNACC DOS Route): Validation failed. Files empty: {not bool(files)}, Branch empty: {not bool(branch)}")
        return jsonify({"message": "Please upload DBF files and select a branch."}), 400

    print(f"Server Log: Received request for LNACC DOS processing. Files Count={len(files)}, Branch='{branch}'")

    # The output directory for LNACC DOS is fixed within lnacc_dos_process.py,
    # so we don't need to pass it here or create a subfolder.
    # We pass a dummy value for 'output_folder' to the helper as it expects it,
    # but the lambda ensures it's not passed to the actual processing function.
    try:
        response_data, status_code = helpers.handle_file_upload_and_process(
            # Corrected lambda: only pass input_temp_dir and branch to process_lnacc_dos_data_web
            lambda input_temp_dir, *args: process_lnacc_dos_data_web(input_temp_dir, branch),
            "dummy_output_dir", # This is a dummy argument for the helper, not used by process_lnacc_dos_data_web
            files,
            additional_params={'branch_val': branch}
        )
        # The output_path is generated by process_lnacc_dos_data_web and returned in its message.
        # We can extract it from the response_data if needed, but it's not directly set by the helper here.
        return jsonify(response_data), status_code
    except Exception as e:
        print(f"Error during LNACC DOS processing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during processing: {str(e)}"}), 500


# MODIFIED: Changed route name from /process_lnacc_win_data to /process_lnacc_win
# MODIFIED: Adjusted to use LNACC_BASE_DIR and remove subfolder creation
@file_processing_bp.route('/process_lnacc_win', methods=['POST'])
def process_lnacc_win_data():
    files = request.files.getlist('files')
    cid_ref_file = request.files.get('cid_ref_file') # Use .get() for single optional file
    branch = request.form.get('selected_branch', default='').strip() # Assuming frontend sends 'selected_branch'

    if not files or not branch:
        print(f"Server Log: Validation failed for LNACC WIN. Files: {len(files)}, Branch: '{branch}'")
        return jsonify({"message": "Please upload CSV files and select a branch."}), 400

    print(f"Server Log: Received request for LNACC WIN processing. Files Count={len(files)}, Branch='{branch}'")

    # The output directory is now directly LNACC_BASE_DIR, no subfolder
    lnacc_output_dir = os.path.abspath(LNACC_BASE_DIR)
    os.makedirs(lnacc_output_dir, exist_ok=True)
    print(f"Server Log: Defined LNACC output directory: {lnacc_output_dir}")

    # Determine the 3-letter prefix for filenames (e.g., ELS for EL SALVADOR)
    file_prefix = branch[:3].upper()

    try:
        # Pass the constructed output_dir, file_prefix, and cid_ref_file to process_lnacc_win_data_web
        response_data, status_code = helpers.handle_file_upload_and_process(
            lambda input_temp_dir, output_folder, *args: process_lnacc_win_data_web(input_temp_dir, output_folder, file_prefix, cid_ref_file=cid_ref_file),
            lnacc_output_dir, # Pass the LNACC_BASE_DIR as the output folder
            files,
            additional_params={'branch_val': branch}
        )
        if response_data and 'output_path' not in response_data:
            response_data['output_path'] = lnacc_output_dir

        return jsonify(response_data), status_code

    except Exception as e:
        print(f"Error during LNACC WIN processing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during processing: {str(e)}"}), 500
    finally:
        # For LNACC WIN, the output is saved to a permanent location, so no temporary cleanup needed here.
        pass


@file_processing_bp.route('/process_svacc_dos_data', methods=['POST'])
def process_svacc_dos_data():
    output_dir = request.form.get('output_dir')
    files = request.files.getlist('files')
    branch = request.form.get('branch', default='').strip()

    if not files or not output_dir or not branch:
        return jsonify({"message": "Please upload DBF files, select a branch, and provide an output directory."}), 400

    print(f"Server Log: Received request for SVACC DOS processing. Output='{output_dir}', Files Count={len(files)}, Branch='{branch}'")

    response_data, status_code = helpers.handle_file_upload_and_process(
        lambda input_temp_dir, output_folder, branch_val: process_svacc_dos_data_web(input_temp_dir, output_folder, branch_val),
        output_dir,
        files,
        additional_params={'branch_val': branch}
    )
    return jsonify(response_data), status_code

# MODIFIED: Changed route name from /process_svacc_win_data to /process_svacc_win
# MODIFIED: Adjusted to use SVACC_BASE_DIR and remove subfolder creation
@file_processing_bp.route('/process_svacc_win', methods=['POST'])
def process_svacc_win_data():
    files = request.files.getlist('files')
    lnhist_file = request.files.get('lnhist_file') # Use .get() for single optional file
    branch = request.form.get('selected_branch', default='').strip() # Assuming frontend sends 'selected_branch'

    # MODIFIED: Changed validation to expect CSV files
    if not files or not branch:
        print(f"Server Log: Validation failed for SVACC WIN. Files: {len(files)}, Branch: '{branch}'")
        return jsonify({"message": "Please upload CSV files and select a branch."}), 400

    print(f"Server Log: Received request for SVACC WIN processing. Files Count={len(files)}, Branch='{branch}'")

    # The output directory is now directly SVACC_BASE_DIR, no subfolder
    svacc_output_dir = os.path.abspath(SVACC_BASE_DIR)
    os.makedirs(svacc_output_dir, exist_ok=True)
    print(f"Server Log: Defined SVACC output directory: {svacc_output_dir}")

    # Determine the 3-letter prefix for filenames (e.g., AGA for AGORA)
    # MODIFIED: Use the full normalized branch name for the output filename
    file_prefix_for_output = branch.replace(' ', '_').upper()

    try:
        # Pass the constructed output_dir, file_prefix_for_output, and lnhist_file to process_svacc_win_data_web
        response_data, status_code = helpers.handle_file_upload_and_process(
            lambda input_temp_dir, output_folder, *args: process_svacc_win_data_web(input_temp_dir, output_folder, file_prefix_for_output, lnhist_file=lnhist_file),
            svacc_output_dir, # Pass the SVACC_BASE_DIR as the output folder
            files,
            additional_params={'branch_val': branch} # Keep branch_val in additional_params if needed by helper
        )
        # Ensure the output_path in response_data is the svacc_output_dir
        if response_data and 'output_path' not in response_data:
            response_data['output_path'] = svacc_output_dir

        return jsonify(response_data), status_code

    except Exception as e:
        print(f"Error during SVACC WIN processing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during processing: {str(e)}"}), 500
    finally:
        # For SVACC WIN, the output is saved to a permanent location, so no temporary cleanup needed here.
        pass


@file_processing_bp.route('/process_journal_voucher', methods=['POST'])
def process_journal_voucher():
    output_dir = request.form.get('output_dir')
    files = request.files.getlist('files')
    branch = request.form.get('branch', default='').strip()

    if not files or not output_dir or not branch:
        return jsonify({"message": "Please upload DBF files, select a branch, and provide an output directory."}), 400

    print(f"Server Log: Received request for Journal Voucher processing. Output='{output_dir}', Files Count={len(files)}, Branch='{branch}'")

    response_data, status_code = helpers.handle_file_upload_and_process(
        lambda input_temp_dir, output_folder, branch_val: process_journal_voucher_data(input_temp_dir, output_folder, branch_val),
        output_dir,
        files,
        additional_params={'branch_val': branch}
    )
    return jsonify(response_data), status_code

# Removed WP LR imports:
# @file_processing_bp.route('/process_wp_lr_reference', methods=['POST'])
# def process_wp_lr_reference():
#     files = request.files.getlist('files')
#     output_dir = request.form.get('output_dir')
#     branch = request.form.get('branch', default='').strip()

#     if not files or not output_dir or not branch:
#         return jsonify({"message": "Please upload files, select a branch, and provide an output directory."}), 400

#     print(f"Server Log: Received request for WP LR Reference processing. Output='{output_dir}', Files Count={len(files)}, Branch='{branch}'")

#     response_data, status_code = helpers.handle_file_upload_and_process(
#         lambda input_temp_dir, output_folder, branch_val: process_wp_lr_reference_data(input_temp_dir, output_folder, branch_val),
#         output_dir,
#         files,
#         additional_params={'branch_val': branch}
#     )
#     return jsonify(response_data), status_code

@file_processing_bp.route('/process_audit_tool_tb_files', methods=['POST'])
def process_audit_tool_tb_files_route(): # Renamed to avoid conflict with imported function
    # The output_dir from frontend is no longer used by process_audit_tool_tb_logic,
    # as it determines its own output path internally.
    # output_dir = request.form.get('output_dir') # This line can be commented out or removed

    files = request.files.getlist('files')
    if not files:
        return jsonify({"message": "Please upload Excel/CSV files."}), 400

    print(f"Server Log: Received request for Audit Tool TB. Files Count={len(files)}")

    # Corrected call to helper.handle_file_upload_and_process:
    # Use a lambda with *args to consume the extra arguments passed by the helper,
    # as 'process_audit_tool_tb_logic' only needs the 'input_temp_dir'.
    response_data, status_code = helpers.handle_file_upload_and_process(
        lambda input_temp_dir, *args: process_audit_tool_tb_logic(input_temp_dir),
        "dummy_output_dir", # This argument is required by helpers.handle_file_upload_and_process, but *args will consume it
        files=files # Pass files to the helper for it to handle saving them to input_temp_dir
    )
    return jsonify(response_data), status_code

# NEW: Route to download converted DBF files (as a zip)
@file_processing_bp.route('/download_converted_dbf', methods=['POST'])
def download_converted_dbf():
    output_path = request.form.get('output_path')
    if not output_path or not os.path.isdir(output_path):
        return jsonify({"message": "Invalid or missing output directory for download."}), 400

    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(output_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Add file to zip, preserving its relative path within the output_path
                    zipf.write(file_path, os.path.relpath(file_path, output_path))
        zip_buffer.seek(0)

        # Generate a unique zip file name
        zip_filename = f"converted_dbf_files_{os.path.basename(output_path)}.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        print(f"Error during download of converted DBF files: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during file download: {str(e)}"}), 500

# NEW: Route to delete temporary converted DBF files
@file_processing_bp.route('/delete_temp_converted_dbf', methods=['POST'])
def delete_temp_converted_dbf():
    output_path = request.json.get('output_path')
    if not output_path:
        return jsonify({"message": "Missing output path for cleanup."}), 400

    # Basic security check: Ensure the path is within the UPLOAD_FOLDER
    # to prevent arbitrary file deletion.
    if not os.path.abspath(output_path).startswith(os.path.abspath(UPLOAD_FOLDER)):
        return jsonify({"message": "Invalid path for cleanup."}), 403 # Forbidden

    try:
        if os.path.exists(output_path) and os.path.isdir(output_path):
            shutil.rmtree(output_path)
            print(f"Server Log: Cleaned up temporary converted DBF directory: {output_path}")
            return jsonify({"message": "Temporary files cleaned up successfully."}), 200
        else:
            return jsonify({"message": "Directory not found or already cleaned up."}), 404
    except Exception as e:
        print(f"Error during cleanup of temporary DBF directory {output_path}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during cleanup: {str(e)}"}), 500

# NEW: Route to download processed TRNM files (as a zip)
@file_processing_bp.route('/download_trnm_files', methods=['POST'])
def download_trnm_files():
    output_path = request.form.get('output_path')
    if not output_path or not os.path.isdir(output_path):
        return jsonify({"message": "Invalid or missing output directory for download."}), 400

    # For TRNM, the files are saved to a permanent location, so we should not delete them
    # after download. This route will just serve the files from the specified path.
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(output_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Add file to zip, preserving its relative path within the output_path
                    zipf.write(file_path, os.path.relpath(file_path, output_path))
        zip_buffer.seek(0)

        # Generate a unique zip file name
        zip_filename = f"processed_trnm_files_{os.path.basename(output_path)}.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        print(f"Error during download of processed TRNM files: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during file download: {str(e)}"}), 500

# NEW: Route to delete temporary processed TRNM files (This route is not needed if output is permanent)
# If the TRNM output is meant to be permanent, this route should be removed or modified to reflect that.
# For now, I'm keeping it as a placeholder if future changes require temporary TRNM outputs.
@file_processing_bp.route('/delete_temp_trnm_files', methods=['POST'])
def delete_temp_trnm_files():
    output_path = request.json.get('output_path')
    if not output_path:
        return jsonify({"message": "Missing output path for cleanup."}), 400

    # Basic security check: Ensure the path is within the UPLOAD_FOLDER
    # to prevent arbitrary file deletion.
    # For TRNM, the output is in TRNM_BASE_DIR, not UPLOAD_FOLDER, so adjust check
    if not os.path.abspath(output_path).startswith(os.path.abspath(TRNM_BASE_DIR)):
        return jsonify({"message": "Invalid path for cleanup."}), 403 # Forbidden

    try:
        if os.path.exists(output_path) and os.path.isdir(output_path):
            shutil.rmtree(output_path)
            print(f"Server Log: Cleaned up TRNM output directory: {output_path}")
            return jsonify({"message": "TRNM output files cleaned up successfully."}), 200
        else:
            return jsonify({"message": "Directory not found or already cleaned up."}), 404
    except Exception as e:
        print(f"Error during cleanup of TRNM directory {output_path}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during cleanup: {str(e)}"}), 500

# NEW: Routes for LNACC WIN download and cleanup
@file_processing_bp.route('/download_lnacc_win_files', methods=['POST'])
def download_lnacc_win_files():
    output_path = request.form.get('output_path')
    if not output_path or not os.path.isdir(output_path):
        return jsonify({"message": "Invalid or missing output directory for download."}), 400

    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(output_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, output_path))
        zip_buffer.seek(0)

        zip_filename = f"processed_lnacc_win_files_{os.path.basename(output_path)}.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        print(f"Error during download of processed LNACC WIN files: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during file download: {str(e)}"}), 500

@file_processing_bp.route('/delete_temp_lnacc_win_files', methods=['POST'])
def delete_temp_lnacc_win_files():
    output_path = request.json.get('output_path')
    if not output_path:
        return jsonify({"message": "Missing output path for cleanup."}), 400

    # Security check: Ensure path is within LNACC_BASE_DIR
    if not os.path.abspath(output_path).startswith(os.path.abspath(LNACC_BASE_DIR)):
        return jsonify({"message": "Invalid path for cleanup."}), 403

    try:
        if os.path.exists(output_path) and os.path.isdir(output_path):
            shutil.rmtree(output_path)
            print(f"Server Log: Cleaned up LNACC WIN output directory: {output_path}")
            return jsonify({"message": "LNACC WIN output files cleaned up successfully."}), 200
        else:
            return jsonify({"message": "Directory not found or already cleaned up."}), 404
    except Exception as e:
        print(f"Error during cleanup of LNACC WIN directory {output_path}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": f"An error occurred during cleanup: {str(e)}"}), 500