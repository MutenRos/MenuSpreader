const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const cors = require('cors');
const fs = require('fs');

const app = express();
app.use(express.json());
app.use(cors());

console.log("Inicializando cliente de WhatsApp...");

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', (qr) => {
    console.log('ESCANEA ESTE CÓDIGO QR CON TU WHATSAPP:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('✅ Cliente de WhatsApp listo y conectado!');
});

client.on('auth_failure', msg => {
    console.error('AUTHENTICATION FAILURE', msg);
});

client.initialize();

app.post('/send-menu', async (req, res) => {
    const { phone, caption, imagePath } = req.body;
    
    if (!phone) {
        return res.status(400).json({ error: 'Phone number missing' });
    }

    // Limpieza básica del número (eliminar caracteres no numéricos)
    const cleanPhone = phone.replace(/\D/g, ''); 
    // Añadir sufijo para contactos personales
    const chatId = cleanPhone + '@c.us'; 

    console.log(`Intentando enviar a ${chatId}...`);

    try {
        let media = null;
        if (imagePath && fs.existsSync(imagePath)) {
            // Cargar imagen desde ruta local absoluta
            media = MessageMedia.fromFilePath(imagePath);
        } else {
            console.warn(`Imagen no encontrada en ruta: ${imagePath}`);
        }

        if (media) {
             await client.sendMessage(chatId, media, { caption: caption });
             console.log(` -> Imagen enviada a ${cleanPhone}`);
        } else {
             await client.sendMessage(chatId, caption);
             console.log(` -> Texto enviado a ${cleanPhone}`);
        }
        res.json({ success: true });
    } catch (err) {
        console.error('Error al enviar mensaje:', err);
        res.status(500).json({ error: err.message });
    }
});

const PORT = 3001;
app.listen(PORT, () => {
    console.log(`🤖 Servidor del Bot escuchando en http://localhost:${PORT}`);
});
