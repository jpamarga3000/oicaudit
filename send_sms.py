import serial
import time
import threading
import pygame

# GSM modem COM port and baud rate
PORT = 'COM4'  # Change this to your actual COM port
BAUDRATE = 9600

# Phone number and audio file
PHONE_NUMBER = '+639953527371'
AUDIO_FILE = r'C:\ACC CLEANING\sound_call.mp3'

def play_audio():
    print("Playing audio...")
    pygame.mixer.init()
    pygame.mixer.music.load(AUDIO_FILE)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(1)

try:
    print(f"Connecting to GSM modem on {PORT}...")
    modem = serial.Serial(PORT, BAUDRATE, timeout=5)
    time.sleep(2)

    modem.write(b'AT\r')
    time.sleep(1)
    print(modem.read_all().decode())

    # Voice mode (optional)
    modem.write(b'AT+FCLASS=8\r')
    time.sleep(1)
    print(modem.read_all().decode())

    # Dial the number
    modem.write(f'ATD{PHONE_NUMBER};\r'.encode())  # Note the semicolon
    print(f"Dialing {PHONE_NUMBER}...")
    time.sleep(8)

    # Start audio playback in parallel
    audio_thread = threading.Thread(target=play_audio)
    audio_thread.start()

    time.sleep(20)  # Wait for the sound to finish or for the call duration

    # Hang up
    modem.write(b'ATH\r')
    print("Call ended.")
    modem.close()

except Exception as e:
    print(f"An error occurred: {e}")
