import time
import requests
import win32print
import win32api
import os
import base64

# رابط السيرفر السحابي الخاص بك على Vercel
CLOUD_SERVER = "https://cloud-print-server-iota.vercel.app"

def get_installed_printers():
    """جلب قائمة الطابعات المثبتة على الجهاز المحلي"""
    printers = []
    try:
        printer_info = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        for p in printer_info:
            printers.append(p[2])
    except Exception as e:
        print(f"خطأ في جلب الطابعات: {e}")
    return printers

def register_agent():
    """إرسال الطابعات المتاحة إلى السيرفر السحابي"""
    printers = get_installed_printers()
    try:
        requests.post(f"{CLOUD_SERVER}/api/register-agent", json={"printers": printers})
    except Exception as e:
        print(f"فشل الاتصال بالسيرفر لتسجيل الطابعات: {e}")

def check_for_jobs():
    """التحقق من وجود مهام طباعة جديدة من السيرفر"""
    try:
        response = requests.get(f"{CLOUD_SERVER}/api/get-job")
        if response.status_code == 200:
            job = response.json()
            print(f"تم استلام مهمة طباعة للطابعة: {job.get('printerName')}")
            execute_print_job(job)
        elif response.status_code == 204:
            pass
    except Exception as e:
        print(f"خطأ أثناء سحب المهام: {e}")

def execute_print_job(job):
    """تنفيذ الطباعة صامتاً في الخلفية بدون أي نوافذ منبثقة"""
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
                
            # الطريقة الأضمن للطباعة الصامتة المباشرة عبر البيانات الثنائية للطابعة
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                # بدء مهمة طباعة خام (RAW) صامتة بالكامل في الخلفية
                hJob = win32print.StartDocPrinter(hPrinter, 1, (file_name, None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                
                with open(temp_file_path, "rb") as f:
                    win32print.WritePrinter(hPrinter, f.read())
                    
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                print(f"تمت الطباعة بنجاح صامتاً في الخلفية على '{printer_name}'.")
            finally:
                win32print.ClosePrinter(hPrinter)
                
    except Exception as e:
        print(f"فشل الطباعة المباشرة، جاري محاولة الطريقة البديلة: {e}")
        try:
            win32api.ShellExecute(0, "open", temp_file_path, f'/p /h "{printer_name}"', ".", 0)
        except Exception as ex:
            print(f"فشل نهائي: {ex}")

if __name__ == "__main__":
    print("=== الوسيط المحلي يعمل في الخلفية للطباعة السحابية ===")
    while True:
        register_agent()      # تحديث وتسجيل الطابعات دورياً
        check_for_jobs()      # فحص مهام الطباعة الجديدة
        time.sleep(4)         # الانتظار لمدة 4 ثوانٍ قبل الطلب التالي