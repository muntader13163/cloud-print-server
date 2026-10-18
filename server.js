const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));
app.use(express.static('public')); // هذا السطر يكفي لعرض ملف index.html تلقائياً عند فتح الرابط

// تخزين مؤقت لمهام الطباعة والحالة في الذاكرة (مؤقت على مستوى الـ Serverless)
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

// مسار لاستقبال طلب الطباعة من الواجهة (من هاتف أو جهاز آخر)
app.post('/api/print', (req, res) => {
    const { fileUrl, printerName, fileName } = req.body;
    
    // وضع المهمة في قائمة الانتظار لكي يسحبها الوسيط المحلي
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
        currentJob = null; // مسح المهمة بعد أن تم سحبها لكي لا تتكرر الطباعة
        res.json(jobToSend);
    } else {
        res.status(204).send(); // لا توجد مهام جديدة حالياً
    }
});

// لتشغيل السيرفر محلياً (إذا أردت اختباره على جهازك)
const PORT = process.env.PORT || 3000;
if (process.env.NODE_ENV !== 'production') {
    app.listen(PORT, () => console.log(`السيرفر يعمل محلياً على المنفذ ${PORT}`));
}

module.exports = app;