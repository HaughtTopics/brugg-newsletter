# Supply Chain Newsletter Agent — Brugg Lifting AG

## Deployment auf Render.com (Schritt für Schritt)

### Schritt 1: GitHub-Konto erstellen
1. Gehe auf https://github.com und erstelle ein kostenloses Konto (falls noch keins vorhanden)

### Schritt 2: Neues Repository erstellen
1. Klicke auf GitHub oben rechts auf «+» → «New repository»
2. Name: `brugg-newsletter` (oder beliebig)
3. Sichtbarkeit: **Private**
4. Klicke «Create repository»

### Schritt 3: Dateien hochladen
1. Klicke im neuen Repository auf «uploading an existing file»
2. Lade ALLE Dateien aus diesem ZIP hoch:
   - app.py
   - requirements.txt
   - Procfile
   - templates/index.html
   - static/banner.jpg
3. Klicke «Commit changes»

### Schritt 4: Render-Konto erstellen
1. Gehe auf https://render.com
2. Klicke «Get Started for Free»
3. Melde dich mit deinem GitHub-Konto an (empfohlen)

### Schritt 5: Web Service auf Render erstellen
1. Klicke auf Render Dashboard auf «+ New» → «Web Service»
2. Wähle «Build and deploy from a Git repository»
3. Verbinde GitHub und wähle dein Repository `brugg-newsletter`
4. Einstellungen:
   - **Name**: brugg-newsletter (oder beliebig)
   - **Region**: Frankfurt (EU Central) — wählen für Schweiz
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free

### Schritt 6: API-Key als Environment Variable eintragen
1. Scrolle auf der Render-Seite runter zu «Environment Variables»
2. Klicke «Add Environment Variable»
3. Key: `ANTHROPIC_API_KEY`
4. Value: dein API-Key (sk-ant-api03-...)
5. Klicke «Save»

### Schritt 7: Deploy starten
1. Klicke «Create Web Service»
2. Render baut und deployt die App (dauert 2-3 Minuten)
3. Du erhältst eine URL wie: `https://brugg-newsletter.onrender.com`

### Nutzung (jeden Montag)
1. URL im Browser öffnen
2. «Newsletter generieren» klicken
3. Warten (ca. 30-60 Sekunden — Server sucht live im Web)
4. Newsletter erscheint mit Banner und Formatierung
5. «.eml» klicken → Datei öffnet sich in Outlook → Empfänger eintragen → Senden

### Wichtige Hinweise
- **Free Plan auf Render**: Die App «schläft» nach 15 Minuten Inaktivität.
  Beim nächsten Aufruf dauert der Start ca. 30-60 Sekunden (einmalig).
- **Kosten**: Render Free = kostenlos. Anthropic API ca. CHF 0.10-0.20 pro Newsletter.
- **Sicherheit**: Der API-Key ist nur auf dem Server gespeichert, nicht im Code.
