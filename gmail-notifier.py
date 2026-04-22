import os
import time
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
running = True 

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def show_popup():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True) # Ensure it pops up over other windows
    messagebox.showinfo("Email Alert", "WAR ALERT!")
    root.destroy()

def monitor_emails():
    """Background task to check emails."""
    print("Monitor thread started.")

    while running:
        try:
            service = get_gmail_service()
            
            # REFINED QUERY: Must have subject "WAR ALERT!", must be UNREAD, and must NOT be in Trash
            query = "subject:WAR ALERT! is:unread"
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])

            if messages:
                show_popup()
        except Exception as e:
            print(f"Error: {e}")
        
        # Check every 60 seconds, but break early if 'running' becomes False
        for _ in range(60):
            if not running: break
            time.sleep(1)

def create_image():
    """Create a simple blue square icon for the tray."""
    image = Image.new('RGB', (64, 64), color=(30, 144, 255))
    d = ImageDraw.Draw(image)
    d.text((10, 10), "WAR ALERT!", fill=(255, 255, 255))
    return image

def on_quit(icon, item):
    global running
    running = False
    print("App stopped")
    icon.stop()

# --- Main Setup ---
if __name__ == '__main__':
    # 1. Start the email checker in a separate thread
    email_thread = threading.Thread(target=monitor_emails, daemon=True)
    email_thread.start()

    # 2. Setup the System Tray Icon
    icon = Icon("GmailCheck", create_image(), "Gmail WAR-ALERT Monitor", menu=Menu(
        MenuItem("Status: Running", lambda: None, enabled=False),
        MenuItem("Stop and Exit", on_quit)
    ))

    print("App is running in the system tray. Right-click the icon to stop.")
    icon.run()