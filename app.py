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
        "Du bist ein Supply Chain Analyst fuer Brugg Lifting AG "
        "(Hersteller von Aufzugsseilen aus Stahldraht und Aufzugsriemen aus Polyurethan, "
        "Produktionsstandorte: Schweiz und China). "
        "Schreibe auf Deutsch mit korrekten Umlauten: ae=\u00e4, oe=\u00f6, ue=\u00fc, ss=\u00df. "
        "Kein Markdown, keine ** Sternchen, keine # Rauten."
    )

    user_prompt = (
        f"Erstelle den woechentlichen Supply Chain Newsletter fuer Brugg Lifting AG.\n"
        f"Berichtsperiode: {date_range}\n\n"
        f"Schreibe den Newsletter EXAKT in diesem Format:\n\n"
        f"SUPPLY CHAIN NEWSLETTER \u2014 {kw_label}\n"
        f"Brugg Lifting AG | Interner Marktueberlick\n"
        f"Zeitraum: {date_range}\n\n"
        f"1. THEMA IN GROSSBUCHSTABEN\n"
        f"Inhalt: 2-3 Saetze mit konkreten Zahlen zu: Walzdraht/Stahlpreise Europa+China, "
        f"Seefrachtraten (Drewry WCI), Energiepreise (TTF), Waehrungen EUR/CHF/USD/CNY, "
        f"US-Zoelle, Supply Chain Stoerungen, Aufzugsmarkt (Kone/Schindler/Otis/TK Elevator).\n"
        f"Auswirkungen fuer Brugg Lifting: Relevanz fuer CH-Standort und China-Standort.\n"
        f"Einschaetzung: Kurze Handlungsempfehlung.\n\n"
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
                "model": "claude-sonnet-4-6",
                "max_tokens": 3000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=25,
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
