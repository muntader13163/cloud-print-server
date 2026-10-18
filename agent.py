import time
import os
import requests
import win32print
import win32api

# رابط السيرفر السحابي على Vercel
SERVER_URL = "https://cloud-print-server-iota.vercel.app"

def get_installed_printers():
    """جلب الطابعات المتصلة بحاسوبك"""
    printers = []
    try:
        printer_objs = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        for p in printer_objs:
            printers.append(p[2])
    except Exception as e:
        print(f"خطأ في جلب الطابعات: {e}")
    return printers

def listen_for_print_jobs():
    print("تم تشغيل الوسيط المحلي بنجاح، وهو يراقب السيرفر السحابي للطباعة...")
    
    # تسجيل الطابعات المتاحة لدى السيرفر عند البدء
    try:
        printers = get_installed_printers()
        requests.post(f"{SERVER_URL}/api/register-agent", json={"printers": printers}, timeout=10)
    except Exception as e:
        print(f"تعذر تسجيل الطابعات لدى السيرفر مبدئياً: {e}")

    while True:
        try:
            # طلب مهمة الطباعة الجديدة من السيرفر السحابي
            response = requests.get(f"{SERVER_URL}/api/get-job", timeout=10)
            
            if response.status_code == 200:
                job = response.json()
                if job and job.get("fileUrl"):
                    file_url = job.get("fileUrl")
                    printer_name = job.get("printerName")
                    file_name = job.get("fileName", "document.pdf")
                    
                    print(f"استلام مستند للطباعة: {file_name}")
                    
                    # تنزيل الملف مؤقتاً وطباعته
                    local_filename = f"temp_print_{int(time.time())}.pdf"
                    file_response = requests.get(file_url)
                    with open(local_filename, 'wb') as f:
                        f.write(file_response.content)

                    win32api.ShellExecute(0, "printto", os.path.abspath(local_filename), f'"{printer_name}"', ".", 0)
                    print(f"تم إرسال الملف بنجاح إلى الطابعة: {printer_name}")
                    
                    # إعلام السيرفر بأن المهام تمت بنجاح (اختياري حسب تصميم السيرفر)
                    requests.post(f"{SERVER_URL}/api/job-done", json={"jobId": job.get("id")}, timeout=5)
            
        except requests.exceptions.RequestException:
            # تجاهل أخطاء الاتصال المؤقتة وإعادة المحاولة بصمت
            pass
        except Exception as e:
            print(f"خطأ أثناء معالجة مهمة الطباعة: {e}")
        
        # الانتظار لمدة 5 ثوانٍ قبل السؤال عن مهمة جديدة لتجنب الضغط على السيرفر
        time.sleep(5)

if __name__ == '__main__':
    listen_for_print_jobs()