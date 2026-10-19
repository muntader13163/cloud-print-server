const express = require('express');
const path = require('path');
const app = express();

app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// متغيرات لتخزين الحالة مؤقتاً
let registeredPrinters = [];
let pendingJob = null;
let pendingDefaultPrinter = null;

// 1. استقبال تسجيل الطابعات من الوسيط المحلي (agent.py)
app.post('/api/register-agent', (req, res) => {
    const { printers } = req.body;
    if (printers) {
        registeredPrinters = printers;
    }
    res.json({ success: true });
});

// 2. إرسال قائمة الطابعات لواجهة الويب
app.get('/api/printers', (req, res) => {
    res.json({ printers: registeredPrinters });
});

// 3. استقبال طلب الطباعة من واجهة الويب
app.post('/api/print', (req, res) => {
    pendingJob = req.body;
    console.log(`[Server] تم استلام مهمة طباعة للطابعة: ${pendingJob.printerName}`);
    res.json({ success: true, message: 'تم إرسال المهمة للوسيط المحلي' });
});

// 4. سحب مهمة الطباعة بواسطة الوسيط المحلي (agent.py)
app.get('/api/get-job', (req, res) => {
    if (pendingJob) {
        const job = pendingJob;
        pendingJob = null; // مسح المهمة بعد سحبها
        return res.json(job);
    }
    res.json(null);
});

// 5. استقبال طلب تعيين الطابعة الافتراضية من واجهة الويب
app.post('/api/set-default-printer', (req, res) => {
    const { printerName } = req.body;
    if (!printerName) {
        return res.status(400).json({ success: false, message: 'اسم الطابعة مطلوب' });
    }
    pendingDefaultPrinter = printerName;
    console.log(`[Server] تم تسجيل طلب تعيين طابعة افتراضية: ${printerName}`);
    res.json({ success: true, message: 'تم حفظ الأمر بنجاح' });
});

// 6. سحب أمر تعيين الطابعة الافتراضية بواسطة الوسيط المحلي (agent.py)
app.get('/api/get-default-printer-job', (req, res) => {
    if (pendingDefaultPrinter) {
        const printer = pendingDefaultPrinter;
        pendingDefaultPrinter = null; // مسح الأمر بعد سحبه
        return res.json({ printerName: printer });
    }
    res.json({ printerName: null });
});

// توجيه صفحة السيرفر المستقلة
app.get('/server.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'server.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Cloud Print Server running on port ${PORT}`);
});