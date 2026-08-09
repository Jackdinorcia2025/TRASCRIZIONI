# Bot Telegram per trascrivere audio WhatsApp

Un bot Telegram che trascrive in automatico i messaggi vocali. Poiché
WhatsApp non offre un modo ufficiale e sicuro per leggere i messaggi in
automatico su un account personale, il flusso di lavoro è:

1. Ricevi un vocale su WhatsApp.
2. Lo inoltri (funzione "Inoltra") al tuo bot Telegram — WhatsApp permette
   di inoltrare i messaggi vocali anche verso altre app, oppure lo salvi e
   lo carichi manualmente.
3. Il bot ti risponde con il testo trascritto, in pochi secondi.

Funziona anche per vocali di Telegram, Messenger o qualsiasi altra app: ti
basta far arrivare l'audio al bot.

## 1. Crea il bot Telegram

1. Apri Telegram e cerca **@BotFather**.
2. Manda `/newbot`, scegli un nome e uno username (deve finire in "bot").
3. BotFather ti darà un **token** (es. `123456:ABC-DEF...`). Copialo.

## 2. Ottieni una chiave Groq (gratuita)

1. Vai su https://console.groq.com/keys, registrati e crea una chiave API.
2. Nessuna carta di credito richiesta. Il piano gratuito include fino a
   8 ore di audio trascritto al giorno (Whisper large-v3), più che
   sufficiente per un uso personale.

## 3. Prova il bot in locale (opzionale ma consigliato)

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="il_tuo_token"
export GROQ_API_KEY="la_tua_chiave_groq"
python bot.py
```

Apri la chat col tuo bot su Telegram, manda `/start` e poi un vocale: dovresti
ricevere la trascrizione.

## 4. Metti il bot online 24/7 su Render (gratis)

Render non offre più Background Worker gratuiti: sul piano free è
disponibile solo il tipo **Web Service**. Il bot include già un piccolo
server HTTP finto che lo fa riconoscere come Web Service; questo però fa
"addormentare" il servizio dopo 15 minuti senza richieste, quindi serve
un ping periodico gratuito per tenerlo sveglio (vedi punto 5).

1. Crea un repository su GitHub e caricaci questi file (`bot.py`,
   `requirements.txt`, `render.yaml`).
2. Vai su https://render.com, registrati/accedi, clicca **New +** →
   **Blueprint** e collega il repository GitHub.
3. Render leggerà `render.yaml` e proporrà di creare un **Web Service**
   chiamato `whatsapp-audio-transcriber-bot` sul piano **Free**.
4. Quando richiesto, inserisci le variabili d'ambiente:
   - `TELEGRAM_BOT_TOKEN`
   - `GROQ_API_KEY`
5. Fai il deploy. Al termine, Render ti darà un URL pubblico tipo
   `https://whatsapp-audio-transcriber-bot.onrender.com`.

## 5. Tieni il bot sveglio (gratis, con UptimeRobot)

Il piano free di Render mette in "sleep" il servizio dopo 15 minuti di
inattività. Per evitarlo, usa un servizio di ping gratuito:

1. Vai su https://uptimerobot.com e crea un account gratuito.
2. Crea un nuovo monitor di tipo **HTTP(s)**, incolla l'URL del tuo
   servizio Render (es. `https://whatsapp-audio-transcriber-bot.onrender.com`).
3. Imposta l'intervallo di controllo a 5 minuti (il minimo del piano
   gratuito).

Da quel momento UptimeRobot "sveglierà" il bot ogni 5 minuti e resterà
attivo 24/7, senza costi.

## Limiti da tenere presenti

- Telegram limita a 20 MB la dimensione dei file scaricabili dai bot
  (più che sufficiente per un vocale normale).
- Non esiste un modo ufficiale per far leggere automaticamente i messaggi
  WhatsApp a un bot esterno su un account personale: il passaggio
  "inoltra il vocale al bot" resta un'azione manuale (ma richiede solo
  1-2 tocchi).
- In alternativa, se in futuro vorrai automatizzare anche il lato
  WhatsApp, servirebbe la WhatsApp Business API (a pagamento, con
  approvazione Meta) — molto più complessa da mettere in piedi.
