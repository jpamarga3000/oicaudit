import serial
import time
import traceback

# Configuration for the GSM modem
# IMPORTANT: Change 'COM4' to your actual GSM modem's COM port.
# You can find this in Device Manager on Windows.
GSM_PORT = 'COM4'
GSM_BAUDRATE = 9600 # Common baud rate for GSM modems

def send_sms_via_modem(phone_number: str, message: str) -> bool:
    """
    Sends an SMS message via a connected GSM modem.

    Args:
        phone_number: The recipient's phone number (e.g., '+639171234567').
                      Assumes it's already formatted with the international prefix.
        message: The text message to send.

    Returns:
        True if the SMS was sent successfully, False otherwise.
    """
    modem = None
    try:
        print(f"SMS Sender: Attempting to connect to GSM modem on {GSM_PORT}...")
        modem = serial.Serial(GSM_PORT, GSM_BAUDRATE, timeout=10)
        time.sleep(2) # Give modem time to initialize

        # Check modem connection (AT command)
        modem.write(b'AT\r\n')
        time.sleep(1)
        response = modem.read_all().decode().strip()
        print(f"SMS Sender: AT response: {response}")
        if "OK" not in response:
            print("SMS Sender: Modem not responding to AT command.")
            return False

        # Set SMS text mode (AT+CMGF=1)
        modem.write(b'AT+CMGF=1\r\n')
        time.sleep(1)
        response = modem.read_all().decode().strip()
        print(f"SMS Sender: CMGF response: {response}")
        if "OK" not in response:
            print("SMS Sender: Failed to set text mode.")
            return False

        # Send SMS (AT+CMGS="phone_number")
        # The modem expects a '>' prompt after this command
        modem.write(f'AT+CMGS="{phone_number}"\r\n'.encode())
        time.sleep(2) # Wait for '>' prompt
        response = modem.read_all().decode()
        print(f"SMS Sender: CMGS prompt response: {response}")
        if ">" not in response:
            print("SMS Sender: Did not receive '>' prompt from modem.")
            return False

        # Send the message content followed by CTRL-Z (ASCII 26)
        modem.write(f'{message}\x1A'.encode()) # \x1A is CTRL-Z
        time.sleep(10) # Give modem time to send SMS
        response = modem.read_all().decode().strip()
        print(f"SMS Sender: Message send response: {response}")

        if "OK" in response and "+CMGS:" in response:
            print(f"SMS Sender: SMS sent successfully to {phone_number}.")
            return True
        else:
            print(f"SMS Sender: Failed to send SMS. Response: {response}")
            return False

    except serial.SerialException as e:
        print(f"SMS Sender Error: Serial port error: {e}")
        print("SMS Sender: Please ensure the modem is connected and the COM port is correct and not in use.")
        return False
    except Exception as e:
        print(f"SMS Sender Error: An unexpected error occurred: {e}")
        print(traceback.format_exc())
        return False
    finally:
        if modem and modem.is_open:
            modem.close()
            print("SMS Sender: Modem port closed.")

if __name__ == '__main__':
    # Example usage (for testing this script directly)
    test_phone = '+639953527371' # Replace with a real number for testing
    test_message = "Hello from GSM modem test!"
    print(f"Attempting to send test SMS to {test_phone}...")
    if send_sms_via_modem(test_phone, test_message):
        print("Test SMS function call successful.")
    else:
        print("Test SMS function call failed.")
