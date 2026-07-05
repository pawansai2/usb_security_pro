# 🔐 USB Security Pro v1.0.0

**Enterprise USB Control System - SECURE PRODUCTION READY EDITION**

Unified Python application with Windows Credential Manager integration, zero hardcoded credentials, and single-process architecture.

## 🛡️ SECURITY FIXES APPLIED

- ✅ **Eliminated Open Door Vulnerability**: No TCP port 9999 exposure
- ✅ **Fixed Credential Handling**: Moved from plaintext registry to Credential Manager
- ✅ **Removed Hardcoded Credentials**: Zero secrets in code or batch files
- ✅ **Unified Architecture**: Eliminated unnecessary C++ backend complexity
- ✅ **Strong Cryptography**: Fernet + Scrypt KDF for all data
- ✅ **No Network Exposure**: Single-process local architecture
- ✅ **Comprehensive Logging**: Full audit trail

## ✨ Features

- **USB Control**: Enable/disable USB access with passcode authentication
- **Employee Registration**: Encrypted user data storage
- **Passcode Management**: Auto-generated passcodes sent via email
- **Lockout Mechanism**: 30-minute lockout after 3 failed attempts
- **Email Alerts**: Secure email notifications
- **Intruder Detection**: Webcam snapshots on suspicious activity
- **Credential Manager**: Windows DPAPI-backed secure storage
- **Encryption**: Fernet encryption with Scrypt KDF
- **Audit Logging**: Complete activity trail

## 🔧 Requirements

### System Requirements
- Windows 10/11 (64-bit)
- Administrator privileges required
- Internet connection (for email features)
- Python 3.8 or later

### Software Requirements
- Python 3.8+ (https://www.python.org/downloads/)
- pip (included with Python)

**NO C++ COMPILER REQUIRED** ✅
- Removed C++ backend completely
- Pure Python implementation
- Simplified deployment process

## 📦 Installation

### Step 1: Download/Clone Project

```bash
cd USB_Security_Pro
```

### Step 2: Run Setup Script (Administrator Required)

```bash
# Right-click setup_secure.bat and select "Run as Administrator"
setup_secure.bat
```

This automatically:
- ✅ Verifies Administrator privileges
- ✅ Checks Python installation
- ✅ Creates secure AppData directory
- ✅ Installs all dependencies
- ✅ Optionally configures email (recommended)

### Step 3: Launch Application

```bash
# Right-click run.bat and select "Run as Administrator"
run.bat
```

Or manually:
```bash
python usb_security_pro.py
```

## 🚀 Quick Start

### First Time Use

1. **Right-click setup_secure.bat** and select "Run as Administrator"
   - Installs Python dependencies
   - Creates encrypted storage directory
   - Optionally configures email

2. **Right-click run.bat** and select "Run as Administrator"

3. **Accept Terms & Conditions**
   - Review security model
   - Acknowledge data collection

4. **Register as Employee**
   - Full Name
   - Employee ID
   - Department
   - Email Address
   - Initial passcode will be sent to your email

5. **Control USB**
   - Use passcode to enable/disable USB
   - New passcode sent after each action

### Subsequent Uses

1. Right-click **run.bat** → "Run as Administrator"
2. Enter your passcode to control USB
3. New passcode automatically sent to email after each operation

---

## ⚙️ Email Configuration

To enable email features (for sending passcodes and alerts):

1. Launch the application: `python usb_security_pro.py`
2. Click Settings (⚙️) button
3. Click "Setup Email Credentials"
4. For **Gmail**:
   - Enable 2-Factor Authentication
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Enter the generated app password (NOT your regular Gmail password)
5. Test connection and save

**Important:** Credentials are stored SECURELY in Windows Credential Manager (DPAPI-encrypted), NOT in plaintext.
## 🔒 Security Model

### Credential Storage

**BEFORE (VULNERABLE):**
```batch
REM DO NOT USE - This is INSECURE
setx USB_MASTER_PASSWORD "SecurePass2026"
setx USB_SENDER_PASS "password_here"
REM Stored PLAINTEXT in: HKCU\Environment
```

**AFTER (SECURE):**
```python
# Stored in Windows Credential Manager (DPAPI-encrypted)
import keyring
keyring.set_password("USBSecurityPro", "master_password", password)
```

**Benefits:**
- DPAPI encryption (Windows system-level)
- Only accessible to authenticated user
- Synced across Windows devices automatically
- Can be managed via Windows Credential Manager UI
- Never exposed as plaintext

### Data Encryption

All local user data encrypted with:
- **Algorithm:** Fernet (AES-128 CBC + HMAC-SHA256)
- **KDF:** Scrypt (n=2^14, r=8, p=1)
- **Files encrypted:**
  - User registration data
  - Generated passcodes
  - Lockout information

### Single-Process Architecture

```
OLD (VULNERABLE):
  Python GUI ──→ TCP Port 9999 (NO AUTHENTICATION) ──→ C++ Backend
  
NEW (SECURE):
  USB Security Pro (Single Process)
  │
  ├─ GUI Layer
  ├─ Credential Manager (Secrets)
  ├─ Encryption/Decryption
  └─ Windows Registry (USB Control)
  
NO NETWORK EXPOSURE - NO ATTACK SURFACE
```

### Admin Privilege Enforcement

Application requires Administrator to run:
- Verified on startup
- Error message if not admin
- Prevents accidental unprivileged execution

---

## 📁 Project Structure

```
USB_Security_Pro/
├── usb_security_pro.py          ✅ NEW - Unified secure app
├── setup_secure.bat             ✅ NEW - Secure setup
├── run.bat                       ✅ NEW - Simple launcher
├── requirements.txt             ✅ UPDATED - With keyring
├── README.md                    ✅ UPDATED - This file
├── ARCHITECTURE.md              ✅ UPDATED - Security details
│
└── [DEPRECATED - To Remove]:
    ├── USB_SECURITY_PRO_FINAL.py
    ├── backend.cpp
    ├── frontend.py
    ├── build_and_run.bat
    ├── setup_environment.bat
    └── JSONCPP_SETUP.md
```

## 🐛 Troubleshooting

### Application won't start

**"Administrator privileges required"**
- Solution: Right-click run.bat and select "Run as Administrator"

**"Python not found"**
- Solution: Install Python 3.8+ from python.org
- Add to PATH during installation
- Verify: `python --version` in Command Prompt

### Email not working

**"Email not configured"**
- Solution: Click Settings (⚙️) → "Setup Email Credentials"

**"Invalid email/password"**
- Solution: For Gmail, use App Password, not regular password
- Generate: https://myaccount.google.com/apppasswords
- Verify: Internet connection is active

**"Connection refused"**
- Solution: Check firewall allows port 587 outbound
- Verify: SMTP server is accessible

### USB operations fail

**"Failed to modify USB"**
- Solution: Verify running as Administrator
- Check Registry: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\USBSTOR`

### Lockout issues

**"System locked" message**
- Normal: Wait 30 minutes
- Immediate: Delete `%APPDATA%\USBControlPro\lockout.bin`
- Note: Be careful - 3 more wrong attempts will lock again

### Check logs

View activity logs:
```bash
# Command Prompt
type %APPDATA%\USBControlPro\usb_security.log

# PowerShell
Get-Content $env:APPDATA\USBControlPro\usb_security.log -Tail 50
```

## 📁 Project Structure

```
USB_Security_Pro/
├── frontend.py              # Python GUI (CustomTkinter)
├── backend.cpp              # C++ System Service
├── backend.exe              # Compiled backend (after build)
├── requirements.txt         # Python dependencies
├── setup_environment.bat    # Environment variable setup
├── build_and_run.bat       # Quick build script
├── ARCHITECTURE.md          # Detailed architecture
├── README.md               # This file
└── .gitignore              # Git ignore rules
```

## 🔒 Security Notes

- **Never hardcode credentials** - Use Windows Credential Manager
- **Run as Administrator** - Required for registry access
- **Use app-specific passwords** - For Gmail/email providers
- **Keep passcodes private** - Treat like passwords
- **Enable 2FA** - On email accounts
- **Review logs regularly** - Check activity log

## 📞 Support

Check logs:
```bash
Get-Content $env:APPDATA\USBControlPro\usb_security.log -Tail 50
```

## 📝 License

Internal Use Only - 2025-2026

**Version**: 1.0.0 - Production Ready ✅

## 🔄 Workflow Diagram

```
User → Frontend (Python)
         ↓ (JSON over TCP)
      Backend (C++)
         ↓
    Windows Registry
         ↓
    USB State Control
```

## 📞 Support

For issues or questions, check:
1. [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed technical docs
2. Troubleshooting section above
3. Backend console output for errors

## 📝 License

Internal Use Only - 2025-2026

---

**Developer**: M. Harsha Vardhan  
**Version**: 1.0  
**Last Updated**: February 2026
