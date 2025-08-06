# audit_tool/backend/app.py (Revised for Admin Profile functionality, authentication decorator, enhanced CORS/Session Debugging, robust sys.path setup, and improved error logging during startup, and Game Leaderboard)
from flask import Flask, request, jsonify, render_template, send_file, session, Blueprint
from flask_cors import CORS, cross_origin # Import cross_origin for specific route decorators
import os
import sys
import pymysql # Keep this for other modules using MySQL
import json
import pandas as pd
from datetime import datetime, timedelta
import re
import io
import traceback # Import traceback for detailed error logging
from werkzeug.utils import secure_filename # Import secure_filename
from functools import wraps # Import wraps for decorator
# Removed: import ssl # NEW: Import the ssl module
import shutil # NEW: Import shutil for directory cleanup

# --- IMPORTANT: BEGIN SYS.PATH SETUP ---
# Get the directory of the current file (app.py)
current_dir = os.path.dirname(os.path.abspath(__file__))
# The project root is the parent directory of 'backend'
project_root = os.path.dirname(current_dir)
# Add the project root to sys.path
# This ensures that 'backend' and its sub-packages can be imported correctly
if project_root not in sys.path:
    sys.path.insert(0, project_root) # Use insert(0) to give it high priority
    print(f"Server Log: Added {project_root} to sys.path for module resolution.")
    # Debugging: Print the full sys.path to verify
    print("Server Log: Current sys.path after modification:")
    for p in sys.path:
        print(f"  - {p}")
# --- IMPORTANT: END SYS.PATH SETUP ---


# Import REGISTERED_USERS_PATH and read_csv_to_dataframe from db_common.py
# Assuming db_common.py is directly in 'backend'
from backend.db_common import (
    get_db_connection, format_currency_py, create_tables, RESIDENCE_COORDINATES_PATH,
    LIST_BRANCHES_PATH, ADDITIONAL_LOAN_POLICIES_PATH, read_csv_to_dataframe,
    write_dataframe_to_csv, REGISTERED_USERS_PATH,
    update_user_profile_in_csv, get_profile_picture_path, PROFILE_PICS_DIR,
    read_login_settings, write_login_settings,
    get_user_first_name # NEW: Import get_user_first_name
)
# Import all processing functions that are used by the routes
# These imports will remain here as they are shared by multiple route files or are part of the core app setup
from backend.operations_dc import generate_deposit_counterpart_report_logic
from backend.operations_dl import (
    generate_deposit_liabilities_report_logic, get_deposit_maturity_requirements_from_db,
    save_deposit_maturity_requirements_to_db, delete_deposit_maturity_requirement_from_db,
    get_deposit_interest_rates_from_db, save_deposit_interest_rates_to_db,
    delete_deposit_interest_rate_from_db,
    read_deposit_code_csv_products,
    generate_matured_deposits_report_logic, generate_wrong_application_interest_report_logic,
    seed_deposit_default_data
)
from backend.operations_dosri import (
    get_dosri_data, add_dosri_entry, update_dosri_entry, delete_dosri_entry,
    seed_dosri_data_to_db, upload_dosri_csv_to_db,
    process_dosri_loan_balances, process_dosri_deposit_liabilities,
    download_dosri_excel_report,
    process_form_emp_loan_balances,
    process_form_emp_deposit_liabilities
)
from backend.operations_form_emp import (
    get_form_emp_data, add_form_emp_entry, update_form_emp_entry, delete_form_emp_entry,
    seed_form_emp_data_to_db, upload_form_emp_csv_to_db
)

try:
    # Removed: from backend.aging_conso import process_excel_files_to_csv # No longer needed, data from MySQL
    from backend.petty_cash import process_and_combine_excel_data_web
    from backend.comtrnm import process_transactions_web
    # Removed the problematic import: from backend.convert_dbf import convert_dbf_to_csv
    # from backend.convert_dbf import process_dbf_to_csv_web # This import is now handled by file_processing_routes.py
    # from backend.win_process import process_win_data_web # This import is now handled by file_processing_routes.py
    from backend.gl_dos_process import process_gl_dos_data_web
    from backend.gl_win_process import process_gl_win_data_web
    from backend.lnacc_dos_process import process_lnacc_dos_data_web
    from backend.lnacc_win_process import process_lnacc_win_data_web
    from backend.svacc_dos_process import process_svacc_dos_data_web
    from backend.svacc_win_process import process_svacc_win_data_web
    from backend.accounting_process import get_gl_names_and_codes_from_file, process_gl_report
    from backend.trial_balance_process import get_tb_as_of_dates, process_trial_balance_data
    from backend.reference_process import process_ref_report
    from backend.description_process import process_desc_report
    from backend.trend_process import process_trend_report
    from backend.financial_statement_process import process_financial_statement
    from backend.operations_process import get_aging_names_and_cids, get_aging_summary_data, get_aging_history_per_member_loan, get_accounts_contribute_to_provisions_report, get_top_borrowers_report, get_new_loans_with_past_due_history_report, get_new_loans_details
    from backend.operations_soa import process_statement_of_account_report
    from backend.journal_voucher_process import process_journal_voucher_data
    import backend.operations_rest_process as operations_rest_process # NEW: Import operations_rest_process
    import backend.game_leaderboard_process as game_leaderboard_process # NEW: Import game_leaderboard_process
    from backend.audit_tool_tb_process import process_audit_tool_tb_files # Moved inside try block
    from backend.mon_reg_aud_process import get_regular_audit_report_data
except ImportError as e:
    print(f"Server Log: Error importing processing scripts: {e}")
    print("Server Log: Please ensure all Python scripts are in the correct package structure relative to the project root.")
    sys.exit(1)

app = Flask(__name__)
# Global CORS configuration: Ensure supports_credentials=True is explicitly set
# IMPORTANT: For local development with different ports (PHP on 80, Flask on 5000),
# the origin should be explicitly listed. Using "*" is okay for development but not production.
# For HTTPS on localhost, ensure your browser trusts the self-signed cert.
CORS(app, resources={r"/*": {"origins": ["http://localhost", "https://localhost", "http://192.168.68.118"], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}}, supports_credentials=True)

# IMPORTANT: Ensure this SECRET_KEY is a strong, random, and FIXED string.
# It MUST NOT change between server restarts, or existing sessions will be invalidated.
app.config['SECRET_KEY'] = 'a_very_strong_and_fixed_secret_key_for_your_audit_tool_app_12345' # Corrected typo here

# --- Flask Session Cookie Configuration (CRITICAL for cross-origin development) ---
# For local development, setting SESSION_COOKIE_DOMAIN to None is often the most reliable
# as it allows the cookie to be set for the current host/IP without strict domain matching.
# This works well when PHP is on an IP and Flask is on the same IP (different port/protocol).
app.config['SESSION_COOKIE_DOMAIN'] = None # IMPORTANT CHANGE: Set to None for broader local compatibility
app.config['SESSION_COOKIE_PATH'] = '/' # Ensure the cookie is valid for all paths
app.config['SESSION_COOKIE_SECURE'] = False # Set to False for HTTP development. MUST be True for HTTPS in production.
app.config['SESSION_COOKIE_SAMESITE'] = 'None' # Allows cross-site cookies. MUST be 'Lax' or 'Strict' in production with Secure=True.
# --- End Flask Session Cookie Configuration ---


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define the directory for profile pictures
# This path is now imported from db_common.py
# PROFILE_PICS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'images')
# if not os.path.exists(PROFILE_PICS_DIR):
#     os.makedirs(PROFILE_PICS_DIR)

# Import helper functions from the new utils module using absolute import
import backend.utils.helpers as helpers

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"\n--- DEBUG: Request to {request.path} ---")
        print(f"DEBUG: Request Headers: {request.headers}")
        print(f"DEBUG: Request Cookies: {request.cookies}") # Check if session cookie is sent by browser
        print(f"DEBUG: Flask session content at start of login_required: {session}") # Check what Flask sees in session
        
        if 'username' not in session:
            print(f"DEBUG: login_required decorator - User NOT authenticated. 'username' not in session.")
            return jsonify({"success": False, "message": "User not authenticated."}), 401
        
        print(f"DEBUG: login_required decorator - User '{session.get('username')}' IS authenticated.")
        return f(*args, **kwargs)
    return decorated_function

# Test connection endpoint - kept in app.py as a basic health check
@app.route('/test_connection')
def test_connection():
    return jsonify({"message": "Backend connected successfully!"})

# REMOVED: Directly added /process_win route. This will now be handled by file_processing_bp.
# @app.route('/process_win', methods=['POST'])
# @cross_origin(supports_credentials=True)
# def process_win_route():
#     print("Server Log: /process_win route hit!") # Log when this route is accessed
#     if 'files' not in request.files:
#         print("Server Log: No files part in request.")
#         return jsonify({"error": "No files part"}), 400
    
#     files = request.files.getlist('files')
#     branch = request.form.get('branch')
    
#     if not files or not branch:
#         print(f"Server Log: Missing files ({len(files)}) or branch ({branch}).")
#         return jsonify({"error": "Missing files or branch"}), 400

#     # Create a temporary directory to save uploaded files
#     temp_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_win_uploads_' + str(os.getpid()))
#     os.makedirs(temp_upload_dir, exist_ok=True)
#     print(f"Server Log: Created temporary upload directory: {temp_upload_dir}")

#     try:
#         # Save each uploaded file to the temporary directory
#         for file in files:
#             filename = secure_filename(file.filename)
#             file_path = os.path.join(temp_upload_dir, filename)
#             file.save(file_path)
#             print(f"Server Log: Saved uploaded file: {file_path}")

#         # Call the processing function from win_process.py
#         # process_win_data_web expects input_dir and branch
#         print(f"Server Log: Calling process_win_data_web with input_dir='{temp_upload_dir}' for branch '{branch}'.")
        
#         # The process_win_data_web function returns a dictionary with 'message' and 'output_path'
#         processing_result = process_win_data_web(temp_upload_dir, branch)
        
#         # Check if processing_result is a dictionary and contains expected keys
#         if isinstance(processing_result, dict) and 'message' in processing_result and 'output_path' in processing_result:
#             success_message = processing_result['message']
#             output_path = processing_result['output_path']
#             print(f"Server Log: Successfully processed WIN files. Message: {success_message}")
#             return jsonify({"message": success_message, "output_path": output_path}), 200
#         else:
#             # Handle unexpected return format from process_win_data_web
#             error_message = "Processing function returned an unexpected format."
#             print(f"Server Log: {error_message} Result: {processing_result}")
#             return jsonify({"error": error_message}), 500

#     except Exception as e:
#         print(f"Server Log: Error processing WIN files: {e}")
#         traceback.print_exc()
#         return jsonify({"error": f"Internal server error during processing: {str(e)}"}), 500
#     finally:
#         # Clean up the temporary directory after processing
#         if os.path.exists(temp_upload_dir):
#             try:
#                 shutil.rmtree(temp_upload_dir)
#                 print(f"Server Log: Cleaned up temporary upload directory: {temp_upload_dir}")
#             except OSError as e:
#                 print(f"Server Log: Error removing temporary directory {temp_upload_dir}: {e}")

# REMOVED: Directly added /process_convert_dbf route. This will now be handled by file_processing_bp.
# @app.route('/process_convert_dbf', methods=['POST'])
# @cross_origin(supports_credentials=True)
# def process_convert_dbf_route():
#     print("Server Log: /process_convert_dbf route hit!")
#     if 'files' not in request.files:
#         print("Server Log: No files part in request for DBF conversion.")
#         return jsonify({"error": "No files part"}), 400

#     files = request.files.getlist('files')
#     if not files:
#         print("Server Log: No DBF files selected for conversion.")
#         return jsonify({"error": "No DBF files selected"}), 400

#     temp_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_dbf_uploads_' + str(os.getpid()))
#     os.makedirs(temp_upload_dir, exist_ok=True)
#     print(f"Server Log: Created temporary upload directory for DBF: {temp_upload_dir}")

#     # Define the output directory for converted DBF files
#     # This should be a persistent location where the user can access the converted CSVs
#     # For now, let's place it in a subfolder within UPLOAD_FOLDER or a more specific path
# #    dbf_output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'Converted_DBF_CSVs')
# #    os.makedirs(dbf_output_dir, exist_ok=True)
# #    print(f"Server Log: Converted DBF output directory: {dbf_output_dir}")

#     try:
#         for file in files:
#             filename = secure_filename(file.filename)
#             file_path = os.path.join(temp_upload_dir, filename)
#             file.save(file_path)
#             print(f"Server Log: Saved uploaded DBF file: {file_path}")

#         print(f"Server Log: Calling process_dbf_to_csv_web with input_dir='{temp_upload_dir}' and output_dir='{dbf_output_dir}'.")
#         # process_dbf_to_csv_web now expects two arguments and returns a dict
#         processing_result = process_dbf_to_csv_web(temp_upload_dir, dbf_output_dir)

#         if isinstance(processing_result, dict) and 'message' in processing_result and 'output_path' in processing_result:
#             success_message = processing_result['message']
#             output_path = processing_result['output_path']
#             print(f"Server Log: Successfully converted DBF files. Message: {success_message}")
#             return jsonify({"message": success_message, "output_path": output_path}), 200
#         else:
#             error_message = "DBF conversion function returned an unexpected format."
#             print(f"Server Log: {error_message} Result: {processing_result}")
#             return jsonify({"error": error_message}), 500

#     except Exception as e:
#         print(f"Server Log: Error converting DBF files: {e}")
#         traceback.print_exc()
#         return jsonify({"error": f"Internal server error during DBF conversion: {str(e)}"}), 500
#     finally:
#         if os.path.exists(temp_upload_dir):
#             try:
#                 shutil.rmtree(temp_upload_dir)
#                 print(f"Server Log: Cleaned up temporary DBF upload directory: {temp_upload_dir}")
#             except OSError as e:
#                 print(f"Server Log: Error removing temporary DBF directory {temp_upload_dir}: {e}")


# Import and register blueprints for each route group using absolute imports
# MODIFIED: Changed import statements to directly import blueprint objects
from backend.routes.auth_routes import auth_bp
from backend.routes.reference_data_routes import reference_data_bp
from backend.routes.file_processing_routes import file_processing_bp # UNCOMMENTED: Re-enable file_processing_bp
from backend.routes.accounting_routes import accounting_bp
from backend.routes.operations_aging_routes import operations_aging_bp
from backend.routes.operations_soa_routes import operations_soa_bp
from backend.routes.operations_dc_routes import operations_dc_bp
from backend.routes.operations_dl_routes import operations_dl_bp
from backend.routes.operations_dosri_routes import operations_dosri_bp
from backend.routes.operations_form_emp_routes import operations_form_emp_bp
from backend.routes.admin_set_routes import admin_set_bp
from backend.routes.admin_database_routes import admin_database_bp
from backend.routes.operations_rest_routes import operations_rest_bp
from backend.routes.game_leaderboard_routes import game_leaderboard_bp
from backend.routes.monitoring_routes import monitoring_bp # NEW: Import the new monitoring blueprint
from backend.routes.get_branches_routes import get_branches_bp


app.register_blueprint(auth_bp)
app.register_blueprint(reference_data_bp)
app.register_blueprint(file_processing_bp) # UNCOMMENTED: Re-enable file_processing_bp
app.register_blueprint(accounting_bp)
app.register_blueprint(operations_aging_bp)
app.register_blueprint(operations_soa_bp)
app.register_blueprint(operations_dc_bp)
app.register_blueprint(operations_dl_bp)
app.register_blueprint(operations_dosri_bp)
app.register_blueprint(operations_form_emp_bp)
app.register_blueprint(admin_set_bp)
app.register_blueprint(admin_database_bp)
app.register_blueprint(operations_rest_bp)
app.register_blueprint(game_leaderboard_bp)
app.register_blueprint(monitoring_bp) # NEW: Register the new monitoring blueprint
app.register_blueprint(get_branches_bp)


# NEW: Route to update user profile data
@app.route('/update_user_profile', methods=['POST'])
# TEMPORARY: Removed @login_required for debugging purposes as requested.
# WARNING: This makes the endpoint insecure. Re-add @login_required in production.
# @login_required 
@cross_origin(supports_credentials=True) # DEBUGGING: Explicit CORS for this route
def update_user_profile_route():
    try:
        # Get the username from the Flask session, not from the request payload
        # This ensures only the logged-in user's profile can be updated.
        username_from_session = session.get('username') 
        
        # This check is now redundant without @login_required, but kept for clarity.
        # In a production setup, you would rely on @login_required or explicitly check session.get('username').
        if not username_from_session:
            print("DEBUG: update_user_profile_route accessed without Flask session 'username'.")
            # For temporary debugging, we will proceed without authentication.
            # In production, this would return 401.
            # return jsonify({"success": False, "message": "User not authenticated."}), 401 
            
            # Fallback to username from request if session is not working (for debugging only)
            # This is highly insecure and should NOT be used in production.
            username_from_session = request.json.get('Username')
            if not username_from_session:
                return jsonify({"success": False, "message": "Username not provided in request. Cannot update."}), 400

        data = request.json # Get the data from the frontend payload
        
        # Pass the username from the session (or request for temporary bypass) to the update function
        success, message = update_user_profile_in_csv(username_from_session, data)
        
        if success:
            return jsonify({"success": True, "message": message}), 200
        else:
            return jsonify({"success": False, "message": message}), 400
    except Exception as e:
        print(f"Error updating user profile: {e}")
        traceback.print_exc() # Print full traceback for debugging
        return jsonify({"success": False, "message": "An internal server error occurred."}), 500

# NEW: Route to upload profile picture
@app.route('/upload_profile_picture', methods=['POST'])
# TEMPORARY: Removed @login_required for debugging purposes as requested.
# WARNING: This makes the endpoint insecure. Re-add @login_required in production.
# @login_required 
@cross_origin(supports_credentials=True) # DEBUGGING: Explicit CORS for this route
def upload_profile_picture_route():
    try:
        # Get username from session for secure identification
        username_from_session = session.get('username')
        
        # This check is now redundant without @login_required, but kept for clarity.
        # In a production setup, you would rely on @login_required or explicitly check session.get('username').
        if not username_from_session:
            print("DEBUG: upload_profile_picture_route accessed without Flask session 'username'.")
            # For temporary debugging, we will try to get username from form data.
            # This is highly insecure and should NOT be used in production.
            username_from_session = request.form.get('username') # For multipart/form-data
            if not username_from_session:
                return jsonify({"success": False, "message": "Username not provided in form data. Cannot upload."}), 400


        if 'profile_picture' not in request.files:
            return jsonify({"success": False, "message": "No file part"}), 400
        
        file = request.files['profile_picture']
        
        if file.filename == '':
            return jsonify({"success": False, "message": "No selected file"}), 400

        if file:
            # Get the file extension
            file_ext = os.path.splitext(file.filename)[1].lower()
            # Construct the new filename as username.extension
            filename = secure_filename(f"{username_from_session}{file_ext}")
            file_path = os.path.join(PROFILE_PICS_DIR, filename) # Use the imported PROFILE_PICS_DIR

            # Delete any existing profile pictures for this user (regardless of extension)
            # This ensures only one picture per user and handles format changes
            for existing_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                existing_file = os.path.join(PROFILE_PICS_DIR, f"{username_from_session}{existing_ext}")
                if os.path.exists(existing_file):
                    os.remove(existing_file)
                    print(f"Server Log: Removed existing profile picture: {existing_file}")

            # Save the new file
            file.save(file_path)
            print(f"Server Log: Saved new profile picture: {file_path}")

            # Update the user's profile in CSV to store the image filename
            # This will update the 'ProfilePicture' column for the user
            update_user_profile_in_csv(username_from_session, {'ProfilePicture': filename})

            # Return the URL for the saved image (relative to htdocs)
            # Adjust the URL to include the 'profile' subdirectory
            image_url = f"images/profile/{filename}" 
            return jsonify({"success": True, "message": "Profile picture uploaded successfully.", "image_url": image_url}), 200
    except Exception as e:
        print(f"Error uploading profile picture: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": "An internal server error occurred."}), 500

# NEW: Route to get profile picture URL for a user
@app.route('/get_profile_picture/<username>', methods=['GET'])
# This route does NOT need login_required if you intend for profile pictures to be publicly viewable
# or viewable by other authenticated users without needing to be the owner of the profile.
# If it should ONLY be viewable by the logged-in user for their own profile, add @login_required
@cross_origin(supports_credentials=True) # DEBUGGING: Explicit CORS for this route
def get_profile_picture_url(username):
    try:
        # For this route, we'll allow fetching by username directly.
        # If strict ownership is needed, add:
        # username_from_session = session.get('username')
        # if not username_from_session or username_from_session != username:
        #     return jsonify({"image_url": "", "message": "Unauthorized access to profile picture."}), 403
        
        # Get the stored filename from CSV
        stored_filename = get_profile_picture_path(username)
        
        if stored_filename:
            # Adjust the URL to include the 'profile' subdirectory
            image_url = f"images/profile/{stored_filename}" 
            return jsonify({"image_url": image_url}), 200
        else:
            # No specific picture found or stored, return empty URL or a default placeholder URL
            return jsonify({"image_url": ""}), 200 # Or return a default image URL
    except Exception as e:
        print(f"Error getting profile picture URL: {e}")
        traceback.print_exc()
        return jsonify({"image_url": ""}), 500


if __name__ == '__main__':
    print("Server Log: Ensuring database tables exist (for remaining MySQL usage)...")
    try:
        create_tables()
        print("Server Log: Database tables checked/created successfully.")
    except Exception as e:
        print(f"Server Log: Error during table creation: {e}")
        # IMPORTANT: If create_tables() fails, we should not proceed.
        # This sys.exit(1) will stop the Flask app from trying to start further
        # and will make the error immediately visible.
        sys.exit(1) # Exit the application if table creation fails

    print("Server Log: Attempting to seed default deposit data (MySQL-based)...\r\n")
    try:
        seed_deposit_default_data()
        print("Server Log: Default deposit data seeding completed.")
    except Exception as e:
        print(f"Server Log: Error during default deposit data seeding: {e}")
        # Continue even if seeding fails, as it might not be critical for app startup

    print("Server Log: Attempting to seed default DOSRI data (CSV-based)...\r\n")
    try:
        seed_dosri_data_to_db()
        print("Server Log: Default DOSRI data seeding completed.")
    except Exception as e:
        print(f"Server Log: Error during default DOSRI data seeding: {e}")
        # Continue even if seeding fails

    # New: Seed default Former Employee data (CSV-based)
    print("Server Log: Attempting to seed default Former Employee data (CSV-based)..\r\n")
    try:
        seed_form_emp_data_to_db()
        print("Server Log: Default Former Employee data seeding completed.")
    except Exception as e:
        print(f"Server Log: Error during default Former Employee data seeding: {e}")
        # Continue even if seeding fails

    # Removed SSL context configuration
    # CERT_PATH = r"C:\xampp\apache\conf\ssl.crt\server.crt"
    # KEY_PATH = r"C:\xampp\apache\conf\ssl.key\server.key"

    # Removed SSL certificate and key file existence checks
    # if not os.path.exists(CERT_PATH):
    #     print(f"ERROR: SSL certificate file not found at {CERT_PATH}. Flask HTTPS will not work.")
    #     print("Please ensure you have configured XAMPP Apache SSL and the path is correct.")
    #     app.run(debug=True, host='0.0.0.0', port=5000)
    # elif not os.path.exists(KEY_PATH):
    #     print(f"ERROR: SSL key file not found at {KEY_PATH}. Flask HTTPS will not work.")
    #     print("Please ensure you have configured XAMPP Apache SSL and the path is correct.")
    #     app.run(debug=True, host='0.0.0.0', port=5000)
    # else:
    #     print(f"Server Log: Running Flask app with HTTPS on port 5000 using {CERT_PATH} and {KEY_PATH}")
    #     ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    #     ssl_context.load_cert_chain(CERT_PATH, KEY_PATH)
    #     app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=ssl_context)

    # Run the Flask app over HTTP
    print(f"Server Log: Running Flask app with HTTP on port 5000.")
    app.run(debug=True, host='0.0.0.0', port=5000)

    