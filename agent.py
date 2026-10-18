import time
import os
import requests
import win32print
import win32api
import socketio

# ضع هنا رابط السيرفر المجاني الذي حصلت عليه من موقع Render
SERVER_URL = "https://your-app-name.onrender.com"

sio = socketio.Client()

def get_installed_printers():
    """جلب الطابعات المتصلة بحاسوبك"""
    printers = []
    printer_objs = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
    for p in printer_objs:
        printers.append(p[2])
    return printers

@sio.event
def connect():
    print("تم الاتصال بالسيرفر السحابي المجاني بنجاح!")
    printers = get_installed_printers()
    sio.emit('register_agent', {'printers': printers})

@sio.on('execute_print')
def on_execute_print(data):
    print(f"استلام مستند للطباعة: {data.get('fileName')}")
    file_url = data.get('fileUrl')
    printer_name = data.get('printerName')

    try:
        # تنزيل الملف مؤقتاً وطباعته
        local_filename = f"temp_print_{int(time.time())}.pdf"
        response = requests.get(file_url)
        with open(local_filename, 'wb') as f:
            f.write(response.content)

        win32api.ShellExecute(0, "printto", os.path.abspath(local_filename), f'"{printer_name}"', ".", 0)
        print(f"تم إرسال الملف إلى الطابعة: {printer_name}")

    except Exception as e:
        print(f"خطأ في الطباعة: {e}")

if __name__ == '__main__':
    while True:
        try:
            sio.connect(SERVER_URL)
            sio.wait()
        except Exception as err:
            print(f"جاري إعادة المحاولة للاتصال بالسيرفر... ({err})")
            time.sleep(5)