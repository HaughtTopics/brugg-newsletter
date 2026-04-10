import os
import httpx
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta

app = Flask(__name__)


def get_kw_and_dates():
    today = datetime.now()
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)
    last_sunday = last_monday + timedelta(days=6)
    kw = today.isocalendar()[1]
    year = today.year
    date_range = f"{last_monday.strftime('%d.%m.%Y')} \u2013 {last_sunday.strftime('%d.%m.%Y')}"
    return kw, year, date_range


@app.route("/")
def index():
    kw, year, date_range = get_kw_and_dates()
    return render_template("index.html", kw=kw, year=year, date_range=date_range)


@app.route("/generate", methods=["POST"])
def generate():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return jsonify({
            "error": "ANTHROPIC_API_KEY fehlt. Bitte in Render unter Environment Variables eintragen."
        }), 500

    kw, year, date_range = get_kw_and_dates()
    kw_label = f"KW {kw} / {year}"

    system_prompt = (
        "Du bist ein Supply Chain Analyst f\u00fcr Brugg Lifting AG "
        "(Hersteller von Aufzugsseilen aus Stahldraht und Aufzugsriemen aus Polyurethan, "
        "Produktionsstandorte: Schweiz und China). "
        "Schreibe ausschliesslich auf Deutsch. "
        "WICHTIG: Verwende IMMER korrekte deutsche Sonderzeichen: "
        "\u00e4 (nicht ae), \u00f6 (nicht oe), \u00fc (nicht ue), "
        "\u00c4 (nicht Ae), \u00d6 (nicht Oe), \u00dc (nicht Ue), "
        "\u00df (nicht ss). "
        "Beispiele: f\u00fcr (nicht fuer), M\u00e4rkte (nicht Maerkte), "
        "\u00dcberblick (nicht Ueberblick), Sch\u00e4tzung (nicht Schaetzung), "
        "Auswirkungen f\u00fcr (nicht fuer), Einsch\u00e4tzung (nicht Einschaetzung). "
        "Kein Markdown, keine ** Sternchen, keine # Rauten."
    )

    user_prompt = (
        f"Erstelle den w\u00f6chentlichen Supply Chain Newsletter f\u00fcr Brugg Lifting AG.\n"
        f"Berichtsperiode: {date_range}\n\n"
        f"Schreibe den Newsletter EXAKT in diesem Format "
        f"(alle W\u00f6rter mit korrekten Umlauten \u00e4/\u00f6/\u00fc/\u00df):\n\n"
        f"SUPPLY CHAIN NEWSLETTER \u2014 {kw_label}\n"
        f"Brugg Lifting AG | Interner Markt\u00fcberblick\n"
        f"Zeitraum: {date_range}\n\n"
        f"1. THEMA IN GROSSBUCHSTABEN\n"
        f"Inhalt: 2-3 S\u00e4tze mit konkreten Zahlen zu: Walzdraht/Stahlpreise Europa+China, "
        f"Seefrachtraten (Drewry WCI), Energiepreise (TTF), W\u00e4hrungen EUR/CHF/USD/CNY, "
        f"US-Z\u00f6lle, Supply Chain St\u00f6rungen, Aufzugsmarkt (Kone/Schindler/Otis/TK Elevator).\n"
        f"Auswirkungen f\u00fcr Brugg Lifting: Relevanz f\u00fcr CH-Standort und China-Standort.\n"
        f"Einsch\u00e4tzung: Kurze Handlungsempfehlung.\n\n"
        f"[4-5 Themen insgesamt]\n\n"
        f"Quellen: [Quellenangabe]\n"
    )

    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 2000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=28,
        )
        response.raise_for_status()
        data = response.json()

        content = data.get("content", [])
        text = " ".join(
            block["text"] for block in content if block.get("type") == "text"
        ).strip()

        if not text:
            return jsonify({"error": "Leere Antwort. Bitte erneut versuchen."}), 500

        return jsonify({"text": text, "kw_label": kw_label, "date_range": date_range})

    except httpx.TimeoutException:
        return jsonify({"error": "Zeitueberschreitung. Bitte erneut versuchen."}), 504
    except httpx.HTTPStatusError as e:
        try:
            msg = e.response.json().get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        return jsonify({"error": f"API-Fehler {e.response.status_code}: {msg}"}), 500
    except Exception as e:
        return jsonify({"error": f"Serverfehler: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
