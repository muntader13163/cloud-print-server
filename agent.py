import time
import requests
import win32print
import win32con
import os
import base64

CLOUD_SERVER = "https://cloud-print-server-iota.vercel.app"

def get_installed_printers():
    printers = []
    try:
        printer_info = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        for p in printer_info:
            printers.append(p[2])
    except Exception as e:
        print(f"Error fetching printers: {e}")
    return printers

def register_agent():
    printers = get_installed_printers()
    try:
        requests.post(f"{CLOUD_SERVER}/api/register-agent", json={"printers": printers})
    except Exception as e:
        print(f"Failed to register agent: {e}")

def check_for_default_printer_request():
    try:
        response = requests.get(f"{CLOUD_SERVER}/api/get-default-printer-job")
        if response.status_code == 200:
            data = response.json()
            printer_name = data.get('printerName')
            if printer_name:
                print(f"Setting persistent default printer to: {printer_name}")
                # تعيين الطابعة افتراضياً بشكل دائم وقوي في نظام ويندوز
                win32print.SetDefaultPrinter(printer_name)
                # تحديث الـ Registry لضمان عدم عودتها للحالة القديمة
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows NT\\CurrentVersion\\Windows", 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "Device", 0, winreg.REG_SZ, f"{printer_name},winspool,Ne00")
                    winreg.CloseKey(key)
                except Exception as reg_err:
                    print(f"Registry note: {reg_err}")
                print(f"Default printer permanently set to '{printer_name}'.")
    except Exception as e:
        print(f"Error checking default printer: {e}")

def check_for_jobs():
    try:
        response = requests.get(f"{CLOUD_SERVER}/api/get-job")
        if response.status_code == 200:
            job = response.json()
            if job and job.get('printerName'):
                print(f"Received print job for printer: {job.get('printerName')}")
                execute_print_job(job)
    except Exception as e:
        print(f"Error checking jobs: {e}")

def execute_print_job(job):
    file_url = job.get('fileUrl')
    printer_name = job.get('printerName')
    file_name = job.get('fileName', 'print_doc.pdf')
    
    try:
        if "base64," in file_url:
            header, encoded = file_url.split(",", 1)
            file_data = base64.b64decode(encoded)
            
            temp_file_path = os.path.join(os.environ.get('TEMP', '.'), file_name)
            with open(temp_file_path, "wb") as f:
                f.write(file_data)

            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, (file_name, None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                with open(temp_file_path, "rb") as f:
                    win32print.WritePrinter(hPrinter, f.read())
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                print(f"Successfully printed silently on '{printer_name}'.")
            finally:
                win32print.ClosePrinter(hPrinter)
                
    except Exception as e:
        print(f"Failed to print: {e}")

if __name__ == "__main__":
    print("=== Local Cloud Print Agent Started (v2.5) ===")
    while True:
        register_agent()
        check_for_default_printer_request()
        check_for_jobs()
        time.sleep(3)