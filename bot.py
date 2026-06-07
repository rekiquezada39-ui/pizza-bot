import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# --- LLAVES (desde variables de entorno de Render) ---
TOKEN_TELEGRAM = os.environ.get("TELEGRAM_TOKEN")
TOKEN_GROQ = os.environ.get("GROQ_TOKEN")

client = Groq(api_key=TOKEN_GROQ)

# --- MENÚ DEL NEGOCIO ---
PERSONALIDAD_IA = """
Eres el asistente virtual de 'Pizza Express'.
Tu objetivo es ser amable y tomar pedidos.
MENÚ:
1. Pizza Pepperoni - $10
2. Pizza Hawaiana - $12
3. Pizza Vegetariana - $11
Si el cliente decide comprar, pídele su nombre y dirección.
Al final confirma diciendo: Tu pedido está en camino.
"""

# --- SERVIDOR WEB FALSO (Para que Render no apague el bot) ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo!")
    
    def log_message(self, format, *args):
        pass  # Esto evita que llene la terminal de logs innecesarios

def iniciar_servidor():
    puerto = int(os.environ.get("PORT", 8080))
    servidor = HTTPServer(('0.0.0.0', puerto), HealthCheck)
    print(f"Servidor web activo en puerto {puerto}")
    servidor.serve_forever()

# --- FUNCIONES DEL BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍕 ¡Hola! Bienvenido a Pizza Express.\n¿Qué te gustaría ordenar hoy?"
    )

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_usuario = update.message.text
    
    respuesta = client.chat.completions.create(
        messages=[
            {"role": "system", "content": PERSONALIDAD_IA},
            {"role": "user", "content": texto_usuario}
        ],
        model="llama-3.3-70b-versatile",
    ).choices[0].message.content

    await update.message.reply_text(respuesta)

# --- ARRANQUE ---
if __name__ == '__main__':
    # Iniciamos el servidor web en un hilo separado
    hilo = threading.Thread(target=iniciar_servidor, daemon=True)
    hilo.start()
    
    # Iniciamos el bot de Telegram
    app = Application.builder().token(TOKEN_TELEGRAM).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    
    print("🚀 Bot de Pizza Express activo...")
    app.run_polling()
