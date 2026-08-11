"""
Bot Telegram per trascrivere messaggi vocali/audio.
Uso: inoltra o carica un vocale (anche scaricato da WhatsApp) al bot
e riceverai il testo trascritto in risposta.

Richiede due variabili d'ambiente:
- TELEGRAM_BOT_TOKEN : token ottenuto da @BotFather
- GROQ_API_KEY       : chiave API gratuita di Groq (https://console.groq.com/keys),
                        usata per la trascrizione con Whisper large-v3
"""

import logging
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from openai import OpenAI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

# Groq espone un'API compatibile con quella di OpenAI: basta puntare
# l'SDK OpenAI al loro endpoint per usare Whisper gratuitamente.
transcription_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# Dimensione massima file gestita dall'API Bot di Telegram (20 MB)
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Ciao! Inviami un messaggio vocale, una nota audio, oppure inoltrami "
        "un audio (ad esempio scaricato da WhatsApp) e te lo trascrivo in testo."
    )


async def transcribe_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message

    # Individua il file audio, qualunque sia il tipo di messaggio
    tg_file_obj = None
    file_name = "audio.ogg"
    if message.voice:
        tg_file_obj = message.voice
        file_name = "voice.ogg"
    elif message.audio:
        tg_file_obj = message.audio
        file_name = message.audio.file_name or "audio.mp3"
    elif message.document and (message.document.mime_type or "").startswith("audio"):
        tg_file_obj = message.document
        file_name = message.document.file_name or "audio.bin"

    if tg_file_obj is None:
        await message.reply_text(
            "Non ho trovato un audio in questo messaggio. Inviami un vocale "
            "o un file audio."
        )
        return

    if tg_file_obj.file_size and tg_file_obj.file_size > MAX_FILE_SIZE_BYTES:
        await message.reply_text(
            "Il file è troppo grande (limite Telegram: 20 MB). Prova a inviare "
            "un audio più corto."
        )
        return

    await message.chat.send_action(action="typing")
    status_msg = await message.reply_text("Trascrizione in corso…")

    try:
        tg_file = await tg_file_obj.get_file()

        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, file_name)
            await tg_file.download_to_drive(local_path)

            with open(local_path, "rb") as audio_file:
                transcript = transcription_client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=audio_file,
                    # language="it",  # scommenta per forzare l'italiano
                )

        text = transcript.text.strip() or "(nessun testo riconosciuto)"
        await status_msg.edit_text(text)

    except Exception:
        logger.exception("Errore durante la trascrizione")
        await status_msg.edit_text(
            "Si è verificato un errore durante la trascrizione. Riprova."
        )


class _HealthCheckHandler(BaseHTTPRequestHandler):
    """Server HTTP minimale: serve solo a far vedere a Render (e a un
    servizio di ping esterno tipo UptimeRobot) che il servizio è vivo."""

    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot attivo.")

  def do_HEAD(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
    def log_message(self, format, *args):  # silenzia i log delle richieste
        pass


def _start_health_server() -> None:
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), _HealthCheckHandler)
    server.serve_forever()


def main() -> None:
    # Avvia il server HTTP in un thread separato: necessario perché Render,
    # sul piano gratuito, supporta solo servizi di tipo "Web Service"
    # (deve rispondere su una porta HTTP).
    threading.Thread(target=_start_health_server, daemon=True).start()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.VOICE | filters.AUDIO | filters.Document.AUDIO,
            transcribe_audio,
        )
    )

    logger.info("Bot avviato, in ascolto...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
