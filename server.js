const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// قراءة الملفات الثابتة من مجلد public
app.use(express.static(path.join(__dirname, 'public')));

// تخزين مؤقت لمهام الطباعة والحالة في الذاكرة
let currentJob = null;
let registeredPrinters = [];

// مسار تسجيل الطابعات من الوسيط المحلي
app.post('/api/register-agent', (req, res) => {
    const { printers } = req.body;
    if (printers) {
        registeredPrinters = printers;
        console.log('تم تسجيل الطابعات المتاحة:', printers);
    }
    res.json({ success: true });
});

// مسار لجلب الطابعات المسجلة لعرضها في الواجهة
app.get('/api/printers', (req, res) => {
    res.json({ printers: registeredPrinters });
});

// مسار لاستقبال طلب الطباعة من الواجهة
app.post('/api/print', (req, res) => {
    const { fileUrl, printerName, fileName } = req.body;
    
    currentJob = {
        id: Date.now(),
        fileUrl,
        printerName,
        fileName: fileName || "document.pdf"
    };

    console.log('تم إضافة مهمة طباعة جديدة:', currentJob);
    res.json({ success: true, message: 'تم إرسال المهمة بنجاح، بانتظار سحبها من الوسيط المحلي' });
});

// مسار لكي يقوم الوسيط المحلي (agent.py) بالسؤال عن مهام الطباعة الجديدة
app.get('/api/get-job', (req, res) => {
    if (currentJob) {
        const jobToSend = currentJob;
        currentJob = null; 
        res.json(jobToSend);
    } else {
        res.status(204).send(); 
    }
});

// مسار الجذر لعرض واجهة الويب (index.html) مباشرة
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// لتشغيل السيرفر محلياً
const PORT = process.env.PORT || 3000;
if (process.env.NODE_ENV !== 'production') {
    app.listen(PORT, () => console.log(`السيرفر يعمل محلياً على المنفذ ${PORT}`));
}

module.exports = app;