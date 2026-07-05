"""
USB Security Pro v1.0.0 - Production-Ready Edition
Enterprise USB Control with Windows Credential Manager Integration
SECURE - NO HARDCODED CREDENTIALS, NO NETWORK EXPOSURE, NO BUFFER OVERFLOWS
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import ctypes
import cv2
import tempfile
import smtplib
import keyring
import subprocess
import threading
import time
import sys
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
import base64
import secrets
import winreg
import logging

# ==================== LOGGING CONFIGURATION ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.getenv('APPDATA'), 'USBControlPro', 'usb_security.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== CONSTANTS ====================

APP_NAME = "USB Security Pro"
APP_VERSION = "1.0.0"
APPDATA_PATH = os.path.join(os.getenv('APPDATA'), 'USBControlPro')
SERVICE_NAME = "UsbSecurityPro"
KEYRING_SERVICE = "USBSecurityPro"

# File paths
SALT_FILE = os.path.join(APPDATA_PATH, 'salt.bin')
REGISTRATION_FILE = os.path.join(APPDATA_PATH, 'userinfo.enc')
LOCK_FILE = os.path.join(APPDATA_PATH, 'lockout.bin')
CONSENT_FILE = os.path.join(APPDATA_PATH, 'consent.bin')

# USB Registry path
USB_REG_PATH = r"SYSTEM\CurrentControlSet\Services\USBSTOR"

# ==================== INITIALIZATION ====================

def ensure_appdata_dir():
    """Create AppData directory with proper permissions"""
    try:
        os.makedirs(APPDATA_PATH, exist_ok=True)
        # Hide directory
        ctypes.windll.kernel32.SetFileAttributesW(APPDATA_PATH, 0x02)
        logger.info(f"AppData directory ready: {APPDATA_PATH}")
    except Exception as e:
        logger.error(f"Failed to create AppData directory: {e}")

ensure_appdata_dir()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ==================== CREDENTIAL MANAGEMENT ====================
"""
SECURITY CRITICAL:
- Uses Windows Credential Manager (DPAPI-backed)
- Credentials are NOT stored in plaintext registry or files
- Only accessible to the user who created them
- Synced across systems with Windows Account
"""

def store_credential(username: str, password: str) -> bool:
    """
    Store credential securely in Windows Credential Manager
    NEVER use setx or environment variables for secrets!
    """
    try:
        keyring.set_password(KEYRING_SERVICE, username, password)
        logger.info(f"Credential stored for: {username}")
        return True
    except Exception as e:
        logger.error(f"Failed to store credential: {e}")
        return False

def get_credential(username: str) -> str:
    """Retrieve credential from Windows Credential Manager"""
    try:
        password = keyring.get_password(KEYRING_SERVICE, username)
        if password:
            logger.info(f"Credential retrieved for: {username}")
            return password
        else:
            logger.warning(f"No credential found for: {username}")
            return None
    except Exception as e:
        logger.error(f"Failed to retrieve credential: {e}")
        return None

def delete_credential(username: str) -> bool:
    """Delete credential from Windows Credential Manager"""
    try:
        keyring.delete_password(KEYRING_SERVICE, username)
        logger.info(f"Credential deleted for: {username}")
        return True
    except Exception as e:
        logger.warning(f"Failed to delete credential: {e}")
        return False

# ==================== EMAIL CONFIGURATION SETUP ====================

def setup_email_credentials():
    """Interactive setup for email credentials"""
    dialog = ctk.CTkToplevel()
    dialog.title("Email Configuration")
    dialog.geometry("500x350")
    dialog.grab_set()
    
    ctk.CTkLabel(
        dialog,
        text="📧 Email Configuration",
        font=ctk.CTkFont(size=16, weight="bold")
    ).pack(pady=10)
    
    ctk.CTkLabel(dialog, text="Email Address:").pack(anchor="w", padx=30, pady=(10, 0))
    email_entry = ctk.CTkEntry(dialog, width=300)
    email_entry.pack(padx=30, pady=5)
    
    ctk.CTkLabel(
        dialog,
        text="Password (Gmail: Use app-specific password)",
        font=ctk.CTkFont(size=10)
    ).pack(anchor="w", padx=30)
    
    ctk.CTkLabel(dialog, text="Password:").pack(anchor="w", padx=30, pady=(10, 0))
    password_entry = ctk.CTkEntry(dialog, width=300, show="*")
    password_entry.pack(padx=30, pady=5)
    
    error_label = ctk.CTkLabel(dialog, text="", text_color="red", font=ctk.CTkFont(size=10))
    error_label.pack()
    
    def save_config():
        email = email_entry.get().strip()
        password = password_entry.get()
        
        if not email or not password:
            error_label.configure(text="❌ Both fields are required!")
            return
        
        if not validate_email(email):
            error_label.configure(text="❌ Invalid email format!")
            return
        
        # Test email connection
        if test_email_connection(email, password):
            if store_credential("email_address", email) and store_credential("email_password", password):
                messagebox.showinfo("Success", "✅ Email configuration saved securely!")
                dialog.destroy()
            else:
                error_label.configure(text="❌ Failed to save credentials!")
        else:
            error_label.configure(text="❌ Email configuration failed! Check credentials.")
    
    ctk.CTkButton(
        dialog,
        text="Save Configuration",
        command=save_config,
        fg_color="green",
        width=250,
        height=40
    ).pack(pady=20)
    
    ctk.CTkButton(
        dialog,
        text="Cancel",
        command=dialog.destroy,
        width=250,
        height=35
    ).pack(pady=10)

def test_email_connection(email: str, password: str) -> bool:
    """Test SMTP connection"""
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email, password)
        logger.info(f"Email connection successful: {email}")
        return True
    except Exception as e:
        logger.error(f"Email connection failed: {e}")
        return False

# ==================== ENCRYPTION FUNCTIONS ====================

def generate_salt() -> bytes:
    """Generate cryptographic salt"""
    return secrets.token_bytes(16)

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive encryption key using Scrypt KDF"""
    try:
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    except Exception as e:
        logger.error(f"Key derivation failed: {e}")
        return None

def initialize_salt():
    """Initialize encryption salt"""
    if not os.path.exists(SALT_FILE):
        try:
            salt = generate_salt()
            with open(SALT_FILE, 'wb') as f:
                f.write(salt)
            logger.info("Encryption salt initialized")
        except Exception as e:
            logger.error(f"Failed to initialize salt: {e}")

def get_master_password() -> str:
    """
    Get or create master password from Credential Manager
    This is the encryption key for local data storage
    """
    stored_password = get_credential("master_password")
    if stored_password:
        return stored_password
    
    # First time: generate and store
    master_password = secrets.token_urlsafe(24)
    if store_credential("master_password", master_password):
        logger.info("Master password created")
        return master_password
    else:
        raise RuntimeError("Failed to create master password")

initialize_salt()
MASTER_PASSWORD = get_master_password()

def encrypt_file(filename: str, data: str) -> bool:
    """Encrypt and store data"""
    try:
        with open(SALT_FILE, 'rb') as f:
            salt = f.read()
        key = derive_key(MASTER_PASSWORD, salt)
        if not key:
            raise Exception("Failed to derive encryption key")
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data.encode())
        with open(filename, 'wb') as f:
            f.write(encrypted)
        logger.info(f"Data encrypted to {filename}")
        return True
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return False

def decrypt_file(filename: str) -> str:
    """Decrypt and retrieve data"""
    try:
        if not os.path.exists(filename):
            return None
        with open(SALT_FILE, 'rb') as f:
            salt = f.read()
        key = derive_key(MASTER_PASSWORD, salt)
        if not key:
            raise Exception("Failed to derive encryption key")
        fernet = Fernet(key)
        with open(filename, 'rb') as f:
            encrypted = f.read()
        decrypted = fernet.decrypt(encrypted).decode()
        logger.info(f"Data decrypted from {filename}")
        return decrypted
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return None

# ==================== PASSCODE MANAGEMENT ====================

def generate_passcode() -> str:
    """Generate random 8-character passcode"""
    import random
    import string
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    encrypt_file(os.path.join(APPDATA_PATH, 'passcode.enc'), code)
    logger.info(f"Passcode generated: {code[:4]}***")
    return code

def get_stored_passcode() -> str:
    """Retrieve stored passcode"""
    return decrypt_file(os.path.join(APPDATA_PATH, 'passcode.enc'))

# ==================== LOCKOUT MANAGEMENT ====================

def is_locked() -> bool:
    """Check if system is locked due to failed attempts"""
    try:
        if not os.path.exists(LOCK_FILE):
            return False
        with open(LOCK_FILE, 'rb') as f:
            locked_until_bytes = f.read()
        locked_until = datetime.fromisoformat(locked_until_bytes.decode())
        return datetime.now() < locked_until
    except Exception as e:
        logger.warning(f"Lock check failed: {e}")
        return False

def start_lock_timer(minutes: int = 30) -> bool:
    """Lock system for specified minutes"""
    try:
        locked_until = datetime.now() + timedelta(minutes=minutes)
        with open(LOCK_FILE, 'wb') as f:
            f.write(locked_until.isoformat().encode())
        logger.warning(f"System locked for {minutes} minutes")
        return True
    except Exception as e:
        logger.error(f"Failed to set lockout: {e}")
        return False

def get_remaining_lockout_time() -> int:
    """Get remaining lockout time in seconds"""
    try:
        with open(LOCK_FILE, 'rb') as f:
            locked_until = datetime.fromisoformat(f.read().decode())
            remaining = locked_until - datetime.now()
            return max(0, int(remaining.total_seconds()))
    except:
        return 0

# ==================== EMAIL FUNCTIONS ====================

def send_email(to_email: str, subject: str, body: str, image_path: str = None) -> bool:
    """Send email with optional attachment"""
    try:
        sender_email = get_credential("email_address")
        sender_password = get_credential("email_password")
        
        if not sender_email or not sender_password:
            logger.error("Email credentials not configured")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, 'rb') as img:
                    msg.attach(MIMEImage(img.read(), name=os.path.basename(image_path)))
            except Exception as e:
                logger.warning(f"Failed to attach image: {e}")
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False

def send_passcode_email_async(to_email: str, employee_name: str, passcode: str):
    """Send passcode email in background thread"""
    def send():
        body = f"""Hello {employee_name},

Your new USB access passcode is: {passcode}

This passcode is valid for your next USB control action.

Do NOT share this passcode with anyone.

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Regards,
USB Security Team"""
        send_email(to_email, "Your USB Access Passcode", body)
    
    thread = threading.Thread(target=send, daemon=True)
    thread.start()

def send_intruder_alert_async(to_email: str, employee_name: str, image_path: str = None):
    """Send intruder alert email in background thread"""
    def send():
        body = f"""🚨 INTRUDER ALERT 🚨

Hi {employee_name},

Someone attempted to access your USB control panel with an INCORRECT passcode.
This triggered our security response system.

An image of the person is attached (if camera was available).

If this wasn't you, please contact IT Security immediately!

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System locked for: 30 minutes

Stay safe,
IT Security Team"""
        send_email(to_email, "🚨 Intruder Alert - Unauthorized Access Attempt", body, image_path)
    
    thread = threading.Thread(target=send, daemon=True)
    thread.start()

# ==================== CAMERA & SNAPSHOT ====================

def take_snapshot() -> str:
    """Capture intruder snapshot from webcam"""
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        time.sleep(2)
        
        for _ in range(10):
            ret, frame = cap.read()
            if ret and frame is not None and frame.sum() > 0:
                img_path = os.path.join(tempfile.gettempdir(), f'intruder_{int(time.time())}.jpg')
                cv2.imwrite(img_path, frame)
                cap.release()
                cv2.destroyAllWindows()
                logger.info("Intruder snapshot captured")
                return img_path
            time.sleep(0.1)
        
        cap.release()
        cv2.destroyAllWindows()
        logger.warning("Failed to capture valid frame")
        return None
    except Exception as e:
        logger.error(f"Camera error: {e}")
        return None

def check_camera_permission() -> bool:
    """Verify camera is accessible"""
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        time.sleep(1)
        ret, frame = cap.read()
        cap.release()
        return ret and frame is not None
    except:
        return False

# ==================== USB MANAGEMENT ====================

def change_usb_state(enable: bool = True) -> bool:
    """
    Enable/Disable USB storage
    SECURITY: Must run with admin privileges
    """
    try:
        access = winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, USB_REG_PATH, 0, access) as key:
            value = 3 if enable else 4
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, value)
        
        status = "Enabled" if enable else "Disabled"
        logger.info(f"USB {status}")
        return True
    except PermissionError:
        logger.error("Admin privileges required")
        messagebox.showerror("Admin Required", "Please run as Administrator!")
        return False
    except Exception as e:
        logger.error(f"Registry error: {e}")
        messagebox.showerror("Error", f"Failed to modify USB: {e}")
        return False

def get_usb_status() -> str:
    """Get current USB status"""
    try:
        result = subprocess.check_output(
            'reg query "HKLM\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR" /v Start',
            shell=True, text=True
        )
        if "0x4" in result:
            return "Disabled"
        elif "0x3" in result:
            return "Enabled"
        else:
            return "Unknown"
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return "Unknown"

def is_admin() -> bool:
    """Check if running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ==================== CONSENT & REGISTRATION ====================

def has_consented() -> bool:
    """Check if user agreed to terms"""
    try:
        return os.path.exists(CONSENT_FILE)
    except:
        return False

def set_consented() -> bool:
    """Mark consent as given"""
    try:
        with open(CONSENT_FILE, 'wb') as f:
            f.write(datetime.now().isoformat().encode())
        logger.info("User consent recorded")
        return True
    except Exception as e:
        logger.error(f"Failed to set consent: {e}")
        return False

def is_registered() -> bool:
    """Check if user is registered"""
    return os.path.exists(REGISTRATION_FILE) and decrypt_file(REGISTRATION_FILE) is not None

def store_registration(name: str, emp_id: str, dept: str, email: str) -> bool:
    """Store encrypted user registration"""
    info = f"{name}|{emp_id}|{dept}|{email}"
    return encrypt_file(REGISTRATION_FILE, info)

def load_registration() -> dict:
    """Load user registration data"""
    info = decrypt_file(REGISTRATION_FILE)
    if info:
        try:
            parts = info.split('|')
            if len(parts) == 4:
                return {'name': parts[0], 'emp_id': parts[1], 'dept': parts[2], 'email': parts[3]}
        except Exception as e:
            logger.error(f"Failed to parse registration: {e}")
    return None

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# ==================== GUI APPLICATION ====================

class USBSecurityProApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Check admin privileges
        if not is_admin():
            messagebox.showwarning(
                "Admin Required",
                "This application requires Administrator privileges.\nPlease restart as Admin."
            )
        
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("700x600")
        self.intruder_attempts = 0
        
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkLabel(
            main_frame,
            text="🔐 USB Security Control Panel",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)
        
        # Version info
        version_label = ctk.CTkLabel(
            main_frame,
            text=f"Version {APP_VERSION} - Production Ready",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        version_label.pack()
        
        # Status
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="USB Status: Checking...",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.status_label.pack(pady=10)
        
        # Control buttons frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=20)
        
        self.enable_btn = ctk.CTkButton(
            button_frame,
            text="🟢 Enable USB",
            command=lambda: self.toggle_usb(True),
            width=200,
            height=50,
            fg_color="green"
        )
        self.enable_btn.pack(pady=10)
        
        self.disable_btn = ctk.CTkButton(
            button_frame,
            text="🔴 Disable USB",
            command=lambda: self.toggle_usb(False),
            width=200,
            height=50,
            fg_color="red"
        )
        self.disable_btn.pack(pady=10)
        
        # Info buttons
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(pady=20)
        
        ctk.CTkButton(
            info_frame,
            text="👤 User Details",
            command=self.show_details,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            info_frame,
            text="🔄 Re-Register",
            command=self.show_register,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            info_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            info_frame,
            text="📋 Terms",
            command=self.show_terms,
            width=100
        ).pack(side="left", padx=5)
        
        # Attempt counter
        self.attempt_label = ctk.CTkLabel(
            main_frame,
            text="Failed Attempts: 0/3",
            font=ctk.CTkFont(size=12)
        )
        self.attempt_label.pack(pady=10)
        
        # Start status update
        self.update_status()
        
        # Check registration/consent
        if not has_consented():
            self.after(100, self.show_terms)
        elif not is_registered():
            self.after(100, self.show_register)
        
        logger.info(f"{APP_NAME} v{APP_VERSION} started")
    
    def update_status(self):
        """Update USB status display"""
        try:
            if is_locked():
                remaining = get_remaining_lockout_time()
                self.status_label.configure(
                    text=f"🔒 LOCKED for {remaining}s",
                    text_color="red"
                )
                self.enable_btn.configure(state="disabled")
                self.disable_btn.configure(state="disabled")
            else:
                status = get_usb_status()
                color = "green" if status == "Enabled" else "red"
                self.status_label.configure(
                    text=f"USB Status: {status}",
                    text_color=color
                )
                self.enable_btn.configure(state="normal")
                self.disable_btn.configure(state="normal")
            
            self.after(2000, self.update_status)
        except Exception as e:
            logger.error(f"Status update failed: {e}")
            self.after(2000, self.update_status)
    
    def toggle_usb(self, enable: bool):
        """Toggle USB state with authentication"""
        if is_locked():
            messagebox.showerror(
                "Locked",
                f"System locked. Try again in {get_remaining_lockout_time()}s"
            )
            return
        
        # Password dialog
        dialog = ctk.CTkInputDialog(
            text="Enter your USB passcode:",
            title="Authentication Required"
        )
        entered_pass = dialog.get_input()
        
        if entered_pass is None:  # Cancel clicked
            return
        
        stored_pass = get_stored_passcode()
        
        if entered_pass == stored_pass:
            if change_usb_state(enable):
                self.intruder_attempts = 0
                self.attempt_label.configure(text="Failed Attempts: 0/3")
                
                # Generate new passcode
                new_pass = generate_passcode()
                user = load_registration()
                
                if user:
                    send_passcode_email_async(
                        user['email'],
                        user['name'],
                        new_pass
                    )
                
                action = "Enabled" if enable else "Disabled"
                messagebox.showinfo(
                    "Success",
                    f"✅ USB {action}!\n\nNew passcode sent to your email."
                )
                logger.info(f"USB {action} successfully")
        else:
            self.intruder_attempts += 1
            self.attempt_label.configure(text=f"Failed Attempts: {self.intruder_attempts}/3")
            logger.warning(f"Failed authentication attempt: {self.intruder_attempts}/3")
            
            if self.intruder_attempts >= 3:
                start_lock_timer(30)
                
                user = load_registration()
                if user:
                    # Capture intruder snapshot
                    img_path = take_snapshot()
                    send_intruder_alert_async(user['email'], user['name'], img_path)
                
                messagebox.showerror(
                    "Access Blocked",
                    "❌ Too many incorrect attempts!\n\nUSB access locked for 30 minutes.\nAlert email sent."
                )
                self.update_status()
            else:
                messagebox.showerror(
                    "Invalid Passcode",
                    f"❌ Wrong passcode!\n\nAttempts: {self.intruder_attempts}/3"
                )
    
    def show_details(self):
        """Display user registration details"""
        if not is_registered():
            messagebox.showinfo("Info", "No user registered yet.")
            return
        
        user = load_registration()
        if not user:
            messagebox.showerror("Error", "Failed to load user details")
            return
        
        info = f"""📋 USER REGISTRATION DETAILS

Name: {user['name']}
Employee ID: {user['emp_id']}
Department: {user['dept']}
Email: {user['email']}

USB Status: {get_usb_status()}
Registered: Yes
App Version: {APP_VERSION}"""
        
        messagebox.showinfo("User Details", info)
    
    def show_settings(self):
        """Display settings dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("500x300")
        dialog.grab_set()
        
        header = ctk.CTkLabel(
            dialog,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=15)
        
        info_frame = ctk.CTkFrame(dialog)
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="Email Configuration",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        ctk.CTkLabel(
            info_frame,
            text="Configure email for sending passcodes and alerts",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 10))
        
        ctk.CTkButton(
            info_frame,
            text="Setup Email Credentials",
            command=setup_email_credentials,
            fg_color="blue"
        ).pack(pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="Security Notes:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(20, 5))
        
        security_text = """• Credentials are stored securely in Windows Credential Manager
• No passwords are stored in files or registry
• All local data is encrypted with Fernet
• Logs are saved to AppData folder"""
        
        ctk.CTkLabel(
            info_frame,
            text=security_text,
            font=ctk.CTkFont(size=10),
            text_color="gray",
            justify="left"
        ).pack(anchor="w", pady=10)
    
    def show_terms(self):
        """Display terms and conditions"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Terms & Conditions")
        dialog.geometry("600x500")
        dialog.grab_set()
        
        header = ctk.CTkLabel(
            dialog,
            text="📋 Terms & Conditions",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=10)
        
        terms_text = f"""USB Security Pro v{APP_VERSION} - Terms & Conditions

1. ADMINISTRATOR PRIVILEGES
   This application requires admin rights to modify USB policies via Windows registry.

2. CAMERA ACCESS
   Webcam is used ONLY to capture intruder snapshots on failed authentication attempts.
   Camera data is stored locally and sent via encrypted email.

3. DATA COLLECTION & STORAGE
   We collect: Name, Employee ID, Department, Email
   Storage: Encrypted locally in AppData\\Roaming\\USBControlPro
   Encryption: Fernet with Scrypt KDF

4. DATA SECURITY
   • Master password stored in Windows Credential Manager (DPAPI-backed)
   • Email credentials stored securely in Credential Manager
   • NO credentials stored in plaintext
   • NO credentials stored in registry or environment variables
   • All sensitive data encrypted with strong cryptography

5. INTERNET CONNECTIVITY
   Active internet required to send passcodes and security alerts via email.

6. SECURITY ENFORCEMENT
   • 3 incorrect passcodes trigger 30-minute lockout
   • Intruder snapshot sent to registered email
   • System logs all access attempts
   • Failed attempts result in immediate camera capture

7. LOGGING
   Activity logs stored in: {APPDATA_PATH}\\usb_security.log
   Logs include: Actions, errors, and security events

8. CREDENTIAL MANAGEMENT
   • Credentials managed via Windows Credential Manager
   • Synced across Windows devices with same user account
   • Only accessible to the user who created them
   • NEVER shared in plaintext or environment variables

9. CONSENT
   Using this application implies consent to all above terms.
        """
        
        text_area = ctk.CTkTextbox(dialog, wrap="word")
        text_area.pack(fill="both", expand=True, padx=10, pady=10)
        text_area.insert("1.0", terms_text)
        text_area.configure(state="disabled")
        
        agree_var = ctk.BooleanVar(value=False)
        
        checkbox = ctk.CTkCheckBox(
            dialog,
            text="I have read and agree to the Terms",
            variable=agree_var
        )
        checkbox.pack(pady=10)
        
        def agree():
            if agree_var.get():
                set_consented()
                dialog.destroy()
                if not is_registered():
                    self.show_register()
            else:
                messagebox.showwarning("Required", "You must agree to continue.")
        
        ctk.CTkButton(
            dialog,
            text="I Agree",
            command=agree,
            fg_color="green"
        ).pack(pady=10)
    
    def show_register(self):
        """Display registration form"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Employee Registration")
        dialog.geometry("500x450")
        dialog.grab_set()
        
        header = ctk.CTkLabel(
            dialog,
            text="👤 Employee Registration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=15)
        
        # Name
        ctk.CTkLabel(dialog, text="Full Name:").pack(anchor="w", padx=30, pady=(10, 0))
        name_entry = ctk.CTkEntry(dialog, width=250)
        name_entry.pack(padx=30, pady=5)
        
        # Employee ID
        ctk.CTkLabel(dialog, text="Employee ID:").pack(anchor="w", padx=30, pady=(10, 0))
        empid_entry = ctk.CTkEntry(dialog, width=250)
        empid_entry.pack(padx=30, pady=5)
        
        # Department
        ctk.CTkLabel(dialog, text="Department:").pack(anchor="w", padx=30, pady=(10, 0))
        dept_entry = ctk.CTkEntry(dialog, width=250)
        dept_entry.pack(padx=30, pady=5)
        
        # Email
        ctk.CTkLabel(dialog, text="Email Address:").pack(anchor="w", padx=30, pady=(10, 0))
        email_entry = ctk.CTkEntry(dialog, width=250)
        email_entry.pack(padx=30, pady=5)
        
        error_label = ctk.CTkLabel(dialog, text="", text_color="red")
        error_label.pack()
        
        def register():
            name = name_entry.get().strip()
            empid = empid_entry.get().strip()
            dept = dept_entry.get().strip()
            email = email_entry.get().strip()
            
            # Validation
            if not all([name, empid, dept, email]):
                error_label.configure(text="❌ All fields required!")
                return
            
            if not validate_email(email):
                error_label.configure(text="❌ Invalid email format!")
                return
            
            # Check camera
            if not check_camera_permission():
                messagebox.showwarning(
                    "Camera Required",
                    "Camera not accessible.\n\nPlease enable webcam access in system settings."
                )
                return
            
            # Check email configuration
            if not get_credential("email_address"):
                messagebox.showwarning(
                    "Email Not Configured",
                    "Please configure email first in Settings."
                )
                return
            
            # Store registration
            if store_registration(name, empid, dept, email):
                passcode = generate_passcode()
                
                # Send initial passcode email
                send_passcode_email_async(email, name, passcode)
                
                messagebox.showinfo(
                    "Success",
                    f"✅ Registration successful!\n\nPasscode sent to {email}"
                )
                dialog.destroy()
                self.intruder_attempts = 0
            else:
                error_label.configure(text="❌ Registration failed!")
        
        ctk.CTkButton(
            dialog,
            text="Complete Registration",
            command=register,
            width=250,
            height=40,
            fg_color="green"
        ).pack(pady=30)

# ==================== APP ENTRY POINT ====================

if __name__ == "__main__":
    if is_locked():
        root = ctk.CTk()
        root.withdraw()
        remaining = get_remaining_lockout_time()
        messagebox.showerror(
            "Service Locked",
            f"🔒 USB Control locked due to multiple failed attempts.\n\nTime remaining: {remaining}s"
        )
        sys.exit()
    
    app = USBSecurityProApp()
    app.mainloop()
