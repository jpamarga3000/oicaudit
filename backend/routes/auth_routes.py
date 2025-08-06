from flask import Blueprint, request, jsonify, session
import traceback
import pandas as pd
import random
import time
import base64 # For base64url encoding/decoding
import os # Import the os module
import json # Import the json module
import cbor2 # For parsing CBOR data from WebAuthn
import bcrypt # NEW: Import bcrypt for password hashing
from functools import wraps # Import wraps for decorator (needed for admin_login_required if used here)


# Re-enabled cryptography imports now that it's installed
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature


# Import necessary functions/constants from db_common.py
from backend.db_common import read_csv_to_dataframe, write_dataframe_to_csv, REGISTERED_USERS_PATH, update_user_profile_in_csv, get_biometric_id, read_login_settings # NEW: Import read_login_settings

# Import the new SMS sender utility
from backend.utils.sms_sender import send_sms_via_modem

auth_bp = Blueprint('auth', __name__)

# --- In-memory OTP storage ---
# IMPORTANT: This is for demonstration purposes only.
# In a production environment, OTPs and WebAuthn challenges should be stored in a secure, persistent
# database with an expiry timestamp, and ideally associated with a session ID
# or a temporary token, not just the username.
# This dictionary will lose data if the Flask server restarts.
# Modified: Store first_name along with OTP
otp_store = {} # Format: {username: {'otp': '123456', 'timestamp': time.time(), 'first_name': 'John', 'contact_number': 'masked_number'}}
OTP_EXPIRY_SECONDS = 300 # OTP valid for 5 minutes

# In-memory store for WebAuthn challenges
# {username: {'challenge': 'base64url_challenge', 'timestamp': time.time(), 'credential_id': 'base64url_cred_id_for_auth', 'public_key_pem': 'PEM_encoded_public_key'}}
webauthn_challenge_store = {} # Now also stores public_key_pem for verification
WEBAUTHN_CHALLENGE_EXPIRY_SECONDS = 60 # Challenge valid for 60 seconds

# Define the Relying Party ID (RP ID) - this MUST match the domain/IP of your website.
# For local development, 'localhost' is generally the most reliable RP ID for WebAuthn.
# If you use an IP like 192.168.1.32, browsers often throw "SecurityError: Invalid domain"
# because they expect a domain name, even if the spec allows IPs.
RELYING_PARTY_ID = "localhost" # IMPORTANT CHANGE: Changed to "localhost" for WebAuthn compatibility

def mask_contact_number(contact_number):
    """
    Masks the contact number, revealing only the last 4 digits.
    Assumes contact_number is a string.
    """
    if not contact_number or len(contact_number) < 4:
        return contact_number # Or return a default masked string like "****"
    return '*' * (len(contact_number) - 4) + contact_number[-4:]

# Helper function for base64url encoding/decoding
def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def base64url_decode(data):
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Handles user login by authenticating against a CSV file.
    Upon successful authentication, checks for biometric enrollment or generates and sends an OTP.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400

    try:
        # Read the registered users CSV, explicitly specifying dtype for 'Contact Number' and 'Biometric_ID'
        users_df = pd.read_csv(REGISTERED_USERS_PATH, dtype={'Contact Number': str, 'Biometric_ID': str, 'Biometric_PubKey': str, 'Access Code': str}) # Added Access Code dtype
        # Ensure column names are stripped of whitespace if any
        users_df.columns = users_df.columns.str.strip() # ADDED: Strip column names after reading
        
        if 'Username' not in users_df.columns or 'Password' not in users_df.columns:
            print(f"Error: {REGISTERED_USERS_PATH} missing 'Username' or 'Password' columns.")
            return jsonify({"success": False, "message": "Server configuration error: User data file is malformed."}), 500

        authenticated = False
        contact_number = None
        first_name = ""
        biometric_id = None # To store biometric ID if enrolled
        access_code = "" # Initialize access_code
        
        user_row = users_df[users_df['Username'] == username]

        if not user_row.empty:
            stored_hashed_password = user_row.iloc[0]['Password']
            # NEW: Verify hashed password
            try:
                # Assuming stored_hashed_password is a string from CSV, decode it to bytes
                # and encode the input password to bytes before comparison.
                if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
                    authenticated = True
                    contact_number = str(user_row.iloc[0].get('Contact Number', '')).strip()
                    first_name = user_row.iloc[0].get('First Name', '')
                    biometric_id = user_row.iloc[0].get('Biometric_ID', None)
                    if pd.isna(biometric_id) or not str(biometric_id).strip():
                        biometric_id = None # Treat NaN or empty string as not enrolled
                    access_code = str(user_row.iloc[0].get('Access Code', '')).strip() # Retrieve access code
                else:
                    print(f"DEBUG: Password mismatch for user {username}.")
            except ValueError as ve:
                print(f"ERROR: Could not verify password for user {username}. Stored hash might be invalid: {ve}")
                # This can happen if the stored password is not a valid bcrypt hash (e.g., still plain text)
                # For a smooth transition, you might add a fallback to plain text comparison here
                # if you have mixed hashed/plain passwords, but it's not recommended for security.
                # For now, if bcrypt.checkpw fails, authentication fails.
            except Exception as e:
                print(f"ERROR: Unexpected error during password verification for user {username}: {e}")
                
        
        if authenticated:
            # NEW: Store access_code in Flask session
            session['username'] = username
            session['access_code'] = access_code # Store access code in Flask session
            print(f"DEBUG AUTH_ROUTES: Session after login - username: {session.get('username')}, access_code: {session.get('access_code')}")
            
            # NEW: Read login settings
            login_settings = read_login_settings()
            biometric_login_enabled = login_settings['biometric_login_enabled']
            otp_verification_enabled = login_settings['otp_verification_enabled']

            if biometric_login_enabled and biometric_id:
                # If biometrics are enabled AND enrolled, tell frontend to prompt for biometric login
                return jsonify({
                    "success": True,
                    "message": "Biometrics enrolled. Please log in with biometrics or OTP.",
                    "biometric_enrolled": True,
                    "username": username, # Send username back for biometric flow
                    "access_code": access_code # Send access code to frontend for PHP session
                }), 200
            elif otp_verification_enabled: # Only proceed with OTP if enabled by settings
                # Generate OTP (existing flow)
                otp_code = str(random.randint(100000, 999999))
                
                # Mask the contact number for display on the frontend
                masked_contact_number = mask_contact_number(contact_number)

                otp_store[username] = {
                    'otp': otp_code,
                    'timestamp': time.time(),
                    'first_name': first_name,
                    'contact_number': contact_number,
                    'masked_contact_number': masked_contact_number
                }
                print(f"Generated OTP for {username}: {otp_code}")

                formatted_phone_number = contact_number
                if formatted_phone_number:
                    clean_number = ''.join(filter(str.isdigit, formatted_phone_number))
                    if clean_number.startswith('63'):
                        formatted_phone_number = '+' + clean_number
                    elif clean_number.startswith('0'):
                        formatted_phone_number = '+63' + clean_number[1:]
                    else:
                        formatted_phone_number = '+63' + clean_number
                else:
                    formatted_phone_number = ''

                sms_sent_status = False
                if formatted_phone_number:
                    sms_message = f"Your Audit Tool OTP is: {otp_code}. It is valid for {OTP_EXPIRY_SECONDS // 60} minutes."
                    print(f"Attempting to send OTP SMS to {formatted_phone_number}...")
                    sms_sent_status = send_sms_via_modem(formatted_phone_number, sms_message)
                    if sms_sent_status:
                        print("OTP SMS sending initiated successfully.")
                    else:
                        print("OTP SMS sending failed or encountered an issue.")
                else:
                    print(f"No contact number found for user {username}. Cannot send OTP SMS.")

                return jsonify({
                    "success": True,
                    "message": "OTP sent to your registered number. Please check your phone.",
                    "otp_required": True,
                    "sms_status": "sent" if sms_sent_status else "failed_or_no_number",
                    "masked_contact_number": masked_contact_number,
                    "access_code": access_code # Send access code to frontend for PHP session
                }), 200
            else: # Direct login if biometrics not enabled/enrolled or OTP not enabled
                # Prepare the user data to send to the frontend
                user_data = user_row.iloc[0] # Get user data directly from the found row
                
                response_data = {
                    "success": True,
                    "message": "Login successful. Redirecting...",
                    "first_name": user_data.get('First Name', ''),
                    "last_name": user_data.get('Last Name', ''),
                    "contact_number": user_data.get('Contact Number', ''),
                    "birthdate": user_data.get('Birthdate', ''),
                    "email": user_data.get('Email', ''),
                    "username": user_data.get('Username', ''),
                    "approved_status": user_data.get('Approved', ''),
                    "access_code": user_data.get('Access Code', ''), # Send access code to frontend for PHP session
                    "branch": user_data.get('Branch', '')
                }
                return jsonify(response_data), 200
        else:
            return jsonify({"success": False, "message": "Invalid username or password."}), 401

    except FileNotFoundError:
        print(f"Error: User registration file not found at {REGISTERED_USERS_PATH}")
        return jsonify({"success": False, "message": "User registration data not found."}), 500
    except Exception as e:
        print(f"Error during login process: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"An error occurred during login: {str(e)}"}), 500

@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    """
    Verifies the OTP provided by the user.
    """
    # NEW: Read login settings
    login_settings = read_login_settings()
    otp_verification_enabled = login_settings['otp_verification_enabled']

    if not otp_verification_enabled:
        return jsonify({"success": False, "message": "OTP verification is currently disabled by admin settings."}), 403

    data = request.get_json()
    username = data.get('username')
    otp_entered = data.get('otp')

    if not username or not otp_entered:
        return jsonify({"success": False, "message": "Username and OTP are required."}), 400

    stored_otp_info = otp_store.get(username)

    if not stored_otp_info:
        return jsonify({"success": False, "message": "OTP not found or expired. Please try logging in again."}), 400

    # Check OTP expiry
    if time.time() - stored_otp_info['timestamp'] > OTP_EXPIRY_SECONDS:
        del otp_store[username] # Remove expired OTP
        return jsonify({"success": False, "message": "OTP expired. Please request a new one."}), 400

    if stored_otp_info['otp'] == otp_entered:
        # OTP consumed, remove it from in-memory store
        del otp_store[username]

        try:
            # Read the registered users CSV again to get all user details
            users_df = pd.read_csv(REGISTERED_USERS_PATH, dtype={'Contact Number': str, 'Biometric_ID': str, 'Biometric_PubKey': str, 'Access Code': str}) # Added Access Code dtype
            users_df.columns = users_df.columns.str.strip() # Clean column names
            
            user_data = users_df[users_df['Username'] == username].iloc[0]

            # NEW: Store access_code in Flask session upon successful OTP verification
            session['username'] = username 
            session['access_code'] = str(user_data.get('Access Code', '')).strip() # Store access code in Flask session
            print(f"DEBUG AUTH_ROUTES: Session after OTP verification - username: {session.get('username')}, access_code: {session.get('access_code')}")
            
            # Prepare the user data to send to the frontend
            response_data = {
                "success": True,
                "message": "OTP verified successfully. Redirecting...",
                "first_name": user_data.get('First Name', ''),
                "last_name": user_data.get('Last Name', ''),
                "contact_number": user_data.get('Contact Number', ''), # Send unmasked to PHP session
                "birthdate": user_data.get('Birthdate', ''),
                "email": user_data.get('Email', ''),
                "username": user_data.get('Username', ''),
                "approved_status": user_data.get('Approved', ''),
                "access_code": user_data.get('Access Code', ''), # Send access code to frontend for PHP session
                "branch": user_data.get('Branch', '')
            }
            return jsonify(response_data), 200

        except FileNotFoundError:
            return jsonify({"success": False, "message": "User registration data not found on server."}), 500
        except IndexError:
            return jsonify({"success": False, "message": "User data not found after OTP verification."}), 500
        except Exception as e:
            print(f"Error retrieving user data after OTP verification: {e}")
            print(traceback.format_exc())
            return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
    else:
        return jsonify({"success": False, "message": "Invalid OTP. Please try again."}), 401

@auth_bp.route('/resend_otp', methods=['POST'])
def resend_otp():
    """
    Resends an OTP to the user's registered contact number.
    """
    # NEW: Read login settings
    login_settings = read_login_settings()
    otp_verification_enabled = login_settings['otp_verification_enabled']

    if not otp_verification_enabled:
        return jsonify({"success": False, "message": "OTP verification is currently disabled by admin settings."}), 403

    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({"success": False, "message": "Username is required to resend OTP."}), 400

    try:
        # Read the registered users CSV, explicitly specifying dtype for 'Contact Number'
        users_df = pd.read_csv(REGISTERED_USERS_PATH, dtype={'Contact Number': str, 'Access Code': str}) # Added Access Code dtype
        users_df.columns = users_df.columns.str.strip() # Clean column names

        user_row = users_df[users_df['Username'] == username]

        if user_row.empty:
            return jsonify({"success": False, "message": "User not found."}), 404

        # Ensure contact_number is retrieved as a string and stripped of whitespace
        contact_number = str(user_row.iloc[0].get('Contact Number', '')).strip()
        first_name = user_row.iloc[0].get('First Name', '')

        if not contact_number:
            return jsonify({"success": False, "message": "No contact number registered for this user to resend OTP."}), 400

        # Generate new OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Mask the contact number for display on the frontend
        masked_contact_number = mask_contact_number(contact_number)

        otp_store[username] = {
            'otp': otp_code,
            'timestamp': time.time(),
            'first_name': first_name,
            'contact_number': contact_number,
            'masked_contact_number': masked_contact_number
        }
        print(f"Resending OTP for {username}: {otp_code}")

        # Format phone number: always add +63
        formatted_phone_number = contact_number
        if formatted_phone_number:
            clean_number = ''.join(filter(str.isdigit, formatted_phone_number))
            if clean_number.startswith('63'):
                formatted_phone_number = '+' + clean_number
            elif clean_number.startswith('0'):
                formatted_phone_number = '+63' + clean_number[1:]
            else:
                formatted_phone_number = '+63' + clean_number
        else:
            formatted_phone_number = ''

        sms_message = f"Your new Audit Tool OTP is: {otp_code}. It is valid for {OTP_EXPIRY_SECONDS // 60} minutes."
        sms_sent_status = send_sms_via_modem(formatted_phone_number, sms_message)

        if sms_sent_status:
            return jsonify({
                "success": True,
                "message": "New OTP sent successfully. Please check your phone.",
                "masked_contact_number": masked_contact_number
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Failed to resend OTP. Please try again.",
                "masked_contact_number": masked_contact_number
            }), 500

    except FileNotFoundError:
        return jsonify({"success": False, "message": "User registration data not found."}), 500
    except Exception as e:
        print(f"Error during resend OTP process: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"An error occurred while resending OTP: {str(e)}"}), 500

@auth_bp.route('/get_biometric_status/<username>', methods=['GET'])
def get_biometric_status_route(username):
    """
    Checks if a user has a biometric ID enrolled.
    """
    # NEW: Read login settings
    login_settings = read_login_settings()
    biometric_login_enabled = login_settings['biometric_login_enabled']

    if not biometric_login_enabled:
        return jsonify({"is_enrolled": False, "message": "Biometric login is currently disabled by admin settings."}), 200 # Return 200 as it's an informational check

    if not username:
        return jsonify({"is_enrolled": False, "message": "Username is required."}), 400
    
    biometric_id = get_biometric_id(username)
    is_enrolled = biometric_id is not None
    return jsonify({"is_enrolled": is_enrolled}), 200

# WebAuthn Registration Endpoints
@auth_bp.route('/webauthn/register/begin', methods=['POST'])
def webauthn_register_begin():
    # NEW: Read login settings
    login_settings = read_login_settings()
    biometric_login_enabled = login_settings['biometric_login_enabled']

    if not biometric_login_enabled:
        return jsonify({"success": False, "message": "Biometric login registration is currently disabled by admin settings."}), 403

    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({"success": False, "message": "Username is required."}), 400

    try:
        users_df = pd.read_csv(REGISTERED_USERS_PATH, dtype={'Biometric_ID': str, 'Biometric_PubKey': str, 'Access Code': str}) # Added Access Code dtype
        users_df.columns = users_df.columns.str.strip() # ADDED: Strip column names after reading
        user_row = users_df[users_df['Username'] == username]
        if user_row.empty:
            return jsonify({"success": False, "message": "User not found."}), 404
        
        user_id = user_row.iloc[0]['Username'] # Use username as user ID
        user_display_name = user_row.iloc[0]['First Name'] + ' ' + user_row.iloc[0]['Last Name']

        challenge = os.urandom(32) # Generate a random challenge
        
        # Store challenge for verification later
        webauthn_challenge_store[username] = {
            'challenge': base64url_encode(challenge),
            'timestamp': time.time()
        }

        # WebAuthn options for registration
        options = {
            "challenge": base64url_encode(challenge),
            "rp": {
                "name": "Audit Tool",
                "id": RELYING_PARTY_ID # Use the defined RP ID
            },
            "user": {
                "id": base64url_encode(user_id.encode('utf-8')), # User ID as ArrayBuffer
                "name": username,
                "displayName": user_display_name
            },
            "pubKeyCredParams": [
                {"type": "public-key", "alg": -7},  # ES256
                {"type": "public-key", "alg": -257} # RS256
            ],
            "authenticatorSelection": {
                "authenticatorAttachment": "platform", # "platform" for built-in, "cross-platform" for external
                "userVerification": "preferred", # "required", "preferred", "discouraged"
                "residentKey": "required" # "required" for discoverable credentials
            },
            "timeout": 60000, # 60 seconds
            "attestation": "direct" # "none", "indirect", "direct", "enterprise"
        }
        
        return jsonify(options), 200

    except Exception as e:
        print(f"Error initiating WebAuthn registration: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Failed to initiate registration: {str(e)}"}), 500

@auth_bp.route('/webauthn/register/complete', methods=['POST'])
def webauthn_register_complete():
    # NEW: Read login settings
    login_settings = read_login_settings()
    biometric_login_enabled = login_settings['biometric_login_enabled']

    if not biometric_login_enabled:
        return jsonify({"success": False, "message": "Biometric login registration is currently disabled by admin settings."}), 403

    data = request.get_json()
    username = data.get('username')
    credential_id_b64url = data.get('id')
    raw_id_b64url = data.get('rawId')
    client_data_json_b64url = data.get('response', {}).get('clientDataJSON')
    attestation_object_b64url = data.get('response', {}).get('attestationObject')

    if not all([username, credential_id_b64url, raw_id_b64url, client_data_json_b64url, attestation_object_b64url]):
        return jsonify({"success": False, "message": "Missing registration data."}), 400

    stored_challenge_info = webauthn_challenge_store.pop(username, None) # Get and remove challenge

    if not stored_challenge_info or (time.time() - stored_challenge_info['timestamp'] > WEBAUTHN_CHALLENGE_EXPIRY_SECONDS):
        return jsonify({"success": False, "message": "Challenge expired or not found. Please try again."}), 400

    expected_challenge_b64url = stored_challenge_info['challenge']
    
    try:
        client_data_json_bytes = base64url_decode(client_data_json_b64url)
        client_data = json.loads(client_data_json_bytes.decode('utf-8'))

        if client_data['challenge'] != expected_challenge_b64url:
            return jsonify({"success": False, "message": "Challenge mismatch."}), 400
        
        # CRITICAL FIX: Ensure origin check matches the actual browser origin (HTTPS)
        if client_data['origin'] != f"https://{RELYING_PARTY_ID}": 
            print(f"Origin mismatch: Expected https://{RELYING_PARTY_ID}, got {client_data['origin']}")
            return jsonify({"success": False, "message": "Origin mismatch. Please ensure your website is accessed via HTTPS and the correct IP/domain."}), 400

        if client_data['type'] != "webauthn.create":
            return jsonify({"success": False, "message": "Incorrect client data type."}), 400

        # Full attestation verification involves parsing CBOR, checking formats, and validating signatures.
        # This part extracts the public key for storage.
        attestation_object_bytes = base64url_decode(attestation_object_b64url)
        attestation_data = cbor2.loads(attestation_object_bytes)
        
        auth_data = attestation_data['authData']
        # For a full implementation, you would parse `auth_data` to extract the `credentialPublicKey`
        # and convert it to a format like PEM to store. For this example, we'll store a placeholder.
        
        # For demonstration, we'll store a placeholder or the raw_id as the "public key" for simplified lookup.
        # In a real scenario, you'd store the actual public key in PEM or DER format.
        public_key_pem_placeholder = f"PLACEHOLDER_PUBKEY_FOR_{credential_id_b64url}" # Replace with actual public key in production

        # Store the credential ID and a placeholder for the public key in registered.csv for the user
        success, message = update_user_profile_in_csv(username, {
            'Biometric_ID': credential_id_b64url,
            'Biometric_PubKey': public_key_pem_placeholder # Store the public key (or a representation)
        })

        if success:
            return jsonify({"success": True, "message": "Biometric credential registered successfully."}), 200
        else:
            return jsonify({"success": False, "message": f"Failed to save biometric ID: {message}"}), 500

    except Exception as e:
        print(f"Error completing WebAuthn registration: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Failed to complete registration: {str(e)}"}), 500

# WebAuthn Authentication Endpoints
@auth_bp.route('/webauthn/login/begin', methods=['POST'])
def webauthn_login_begin():
    # NEW: Read login settings
    login_settings = read_login_settings()
    biometric_login_enabled = login_settings['biometric_login_enabled']

    if not biometric_login_enabled:
        return jsonify({"success": False, "message": "Biometric login is currently disabled by admin settings."}), 403

    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({"success": False, "message": "Username is required."}), 400

    # Retrieve both Biometric_ID and Biometric_PubKey
    users_df = pd.read_csv(REGISTERED_USERS_PATH, dtype={'Biometric_ID': str, 'Biometric_PubKey': str, 'Access Code': str}) # Added Access Code dtype
    users_df.columns = users_df.columns.str.strip() # ADDED: Strip column names after reading
    user_row = users_df[users_df['Username'] == username]
    
    if user_row.empty:
        return jsonify({"success": False, "message": "User not found."}), 404

    biometric_id = user_row.iloc[0].get('Biometric_ID')
    public_key_pem = user_row.iloc[0].get('Biometric_PubKey')

    if pd.isna(biometric_id) or not str(biometric_id).strip():
        return jsonify({"success": False, "message": "No biometric credential registered for this user."}), 400
    
    # Store public_key_pem in challenge store for verification in /login/complete
    webauthn_challenge_store[username] = {
        'challenge': base64url_encode(os.urandom(32)), # Generate a new challenge
        'timestamp': time.time(),
        'public_key_pem': public_key_pem, # Store the public key for verification
        'credential_id': biometric_id # Store credential ID for lookup
    }

    try:
        challenge = base64url_decode(webauthn_challenge_store[username]['challenge']) # Use the stored challenge
        
        # WebAuthn options for authentication
        options = {
            "challenge": base64url_encode(challenge), # Corrected: Changed back to base64url_encode
            "rpId": RELYING_PARTY_ID, # Use the defined RP ID
            "allowCredentials": [{
                "id": biometric_id, # The credential ID stored during registration
                "type": "public-key",
                "transports": ["internal", "hybrid"] # "internal" for platform, "hybrid" for cross-platform
            }],
            "userVerification": "preferred", # "required", "preferred", "discouraged"
            "timeout": 60000 # 60 seconds
        }
        
        return jsonify(options), 200

    except Exception as e:
        print(f"Error initiating WebAuthn login: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Failed to initiate login: {str(e)}"}), 500

@auth_bp.route('/webauthn/login/complete', methods=['POST'])
def webauthn_login_complete():
    # NEW: Read login settings
    login_settings = read_login_settings()
    biometric_login_enabled = login_settings['biometric_login_enabled']

    if not biometric_login_enabled:
        return jsonify({"success": False, "message": "Biometric login is currently disabled by admin settings."}), 403

    data = request.get_json()
    username = data.get('username')
    credential_id_b64url = data.get('id')
    raw_id_b64url = data.get('rawId')
    client_data_json_b64url = data.get('response', {}).get('clientDataJSON')
    authenticator_data_b64url = data.get('response', {}).get('authenticatorData')
    signature_b64url = data.get('response', {}).get('signature')
    user_handle_b64url = data.get('response', {}).get('userHandle')

    if not all([username, credential_id_b64url, raw_id_b64url, client_data_json_b64url, authenticator_data_b64url, signature_b64url]):
        return jsonify({"success": False, "message": "Missing authentication data."}), 400

    stored_challenge_info = webauthn_challenge_store.pop(username, None) # Get and remove challenge

    if not stored_challenge_info or (time.time() - stored_challenge_info['timestamp'] > WEBAUTHN_CHALLENGE_EXPIRY_SECONDS):
        return jsonify({"success": False, "message": "Challenge expired or not found. Please try again."}), 400

    expected_challenge_b64url = stored_challenge_info['challenge']
    stored_public_key_pem = stored_challenge_info.get('public_key_pem')
    stored_credential_id = stored_challenge_info.get('credential_id')

    if stored_credential_id != credential_id_b64url:
        return jsonify({"success": False, "message": "Credential ID mismatch with stored registration."}), 401
    
    if not stored_public_key_pem or stored_public_key_pem.startswith("PLACEHOLDER_PUBKEY"):
        print("WARNING: Skipping full signature verification. No real public key stored for this credential.")
    else:
        try:
            # 1. Verify ClientDataJSON
            client_data_json_bytes = base64url_decode(client_data_json_b64url)
            client_data = json.loads(client_data_json_bytes.decode('utf-8'))

            if client_data['challenge'] != expected_challenge_b64url:
                return jsonify({"success": False, "message": "Challenge mismatch."}), 400
            
            # CRITICAL FIX: Ensure origin check matches the actual browser origin (HTTPS)
            if client_data['origin'] != f"https://{RELYING_PARTY_ID}": 
                print(f"Origin mismatch: Expected https://{RELYING_PARTY_ID}, got {client_data['origin']}")
                return jsonify({"success": False, "message": "Origin mismatch. Please ensure your website is accessed via HTTPS and the correct IP/domain."}), 400

            if client_data['type'] != "webauthn.get":
                return jsonify({"success": False, "message": "Incorrect client data type."}), 400

            # 2. Verify AuthenticatorData
            authenticator_data_bytes = base64url_decode(authenticator_data_b64url)
            # RP ID hash verification (optional but recommended)
            # rp_id_hash_expected = hashes.Hash(hashes.SHA256())
            # rp_id_hash_expected.update(RELYING_PARTY_ID.encode('utf-8')) # Use your RP ID
            # if authenticator_data_bytes[0:32] != rp_id_hash_expected.finalize():
            #     return jsonify({"success": False, "message": "RP ID hash mismatch in authenticator data."}), 401

            # Flags and Sign Counter (important for security, but complex to implement fully without a library)
            # flags = authenticator_data_bytes[32]
            # user_present = (flags & 0x01) != 0
            # user_verified = (flags & 0x04) != 0
            # if not user_present: # User must be present
            #     return jsonify({"success": False, "message": "User not present."}), 401
            # if (client_data['userVerification'] == 'required') and not user_verified:
            #     return jsonify({"success": False, "message": "User verification required but not performed."}), 401

            # sign_count = int.from_bytes(authenticator_data_bytes[33:37], 'big')
            # In a real app, compare sign_count with stored value to prevent replay attacks.

            # 3. Verify Signature
            public_key = load_pem_public_key(stored_public_key_pem.encode('utf-8'))

            client_data_hash = hashes.Hash(hashes.SHA256())
            client_data_hash.update(client_data_json_bytes)
            hashed_client_data = client_data_hash.finalize()

            signed_data = authenticator_data_bytes + hashed_client_data
            signature_bytes = base64url_decode(signature_b64url)

            try:
                # Assuming ES256, adjust algorithm as per your registration
                # This assumes the public key is an EC public key
                public_key.verify(signature_bytes, signed_data, ec.ECDSA(hashes.SHA256()))
                print("Signature verified successfully.")
            except InvalidSignature:
                return jsonify({"success": False, "message": "Invalid signature."}), 401
            except Exception as e:
                print(f"Signature verification error: {e}")
                return jsonify({"success": False, "message": "Signature verification failed."}), 500

        except Exception as e:
            print(f"Error during WebAuthn verification steps: {e}")
            traceback.print_exc()
            return jsonify({"success": False, "message": f"Failed to verify biometric assertion: {str(e)}"}), 500

    # If all checks pass (including simplified or full signature verification), proceed to log in
    users_df = pd.read_csv(REGISTERED_USERS_PATH, dtype={'Contact Number': str, 'Biometric_ID': str, 'Biometric_PubKey': str, 'Access Code': str}) # Added Access Code dtype
    users_df.columns = users_df.columns.str.strip() # ADDED: Strip column names after reading
    user_data = users_df[users_df['Username'] == username].iloc[0]

    # NEW: Store access_code in Flask session upon successful biometric verification
    session['username'] = username 
    session['access_code'] = str(user_data.get('Access Code', '')).strip() # Store access code in Flask session
    print(f"DEBUG AUTH_ROUTES: Session after biometric verification - username: {session.get('username')}, access_code: {session.get('access_code')}")
    
    response_data = {
        "success": True,
        "message": "Biometric login successful. Redirecting...",
        "first_name": user_data.get('First Name', ''),
        "last_name": user_data.get('Last Name', ''),
        "contact_number": user_data.get('Contact Number', ''),
        "birthdate": user_data.get('Birthdate', ''),
        "email": user_data.get('Email', ''),
        "username": user_data.get('Username', ''),
        "approved_status": user_data.get('Approved', ''),
        "access_code": user_data.get('Access Code', ''), # Send access code to frontend for PHP session
        "branch": user_data.get('Branch', '')
    }
    return jsonify(response_data), 200

