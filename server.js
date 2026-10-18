const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.static('public')); // واجهة الويب للمستخدم

const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

let activeAgent = null;

io.on('connection', (socket) => {
    console.log('اتصال جديد:', socket.id);

    // تسجيل حاسوبك كـ "عيل طباعة محلي"
    socket.on('register_agent', (data) => {
        activeAgent = socket.id;
        console.log(`تم ربط حاسوبك بنجاح! الطابعات المتاحة:`, data.printers);
        io.emit('agent_status', { online: true, printers: data.printers });
    });

    // استقبال أمر الطباعة من الهاتف وإرساله لحاسوبك
    socket.on('print_job', (jobData) => {
        if (activeAgent) {
            io.to(activeAgent).emit('execute_print', jobData);
        }
    });

    socket.on('disconnect', () => {
        if (socket.id === activeAgent) {
            activeAgent = null;
            io.emit('agent_status', { online: false });
            console.log('انقطع اتصال الحاسوب المحلي بالسيرفر');
        }
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`السيرفر السحابي يعمل على المنفذ ${PORT}`));