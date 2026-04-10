import os
import json
import httpx
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta

app = Flask(__name__)

def get_kw_and_dates():
    today = datetime.now()
    # Monday of last week
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)
    last_sunday = last_monday + timedelta(days=6)
    # ISO week number of current week
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
        return jsonify({"error": "ANTHROPIC_API_KEY nicht gesetzt. Bitte in Render als Environment Variable eintragen."}), 500

    kw, year, date_range = get_kw_and_dates()
    kw_label = f"KW {kw} / {year}"

    system_prompt = (
        "Supply Chain Analyst fuer Brugg Lifting AG "
        "(Aufzugsseile Stahldraht, Aufzugsriemen Polyurethan, Standorte: Schweiz und China). "
        "Schreibe auf Deutsch mit korrekten Umlauten (ae=ae, oe=oe, ue=ue, schreibe immer ae oe ue als ae oe ue NEIN - "
        "schreibe ä ö ü ß). Kein Markdown, kein **."
    )

    user_prompt = (
        f"Suche aktuelle Daten (Zeitraum: {date_range}) zu: "
        "Walzdrahtpreise Europa und China, Seefrachtraten (Drewry WCI), "
        "TTF-Gaspreise, EUR/CHF/USD/CNY Kurse, US-Zoelle Auswirkungen, "
        "Supply Chain Stoerungen, Aufzugsmarkt (Kone, Schindler, Otis, TK Elevator). "
        f"Dann schreibe den Newsletter exakt so:\n\n"
        f"SUPPLY CHAIN NEWSLETTER \u2014 {kw_label}\n"
        f"Brugg Lifting AG | Interner Marktueberlick\n"
        f"Zeitraum: {date_range}\n\n"
        "1. THEMA IN GROSSBUCHSTABEN\n"
        "Inhalt: 2-3 Saetze mit konkreten Zahlen.\n"
        "Auswirkungen fuer Brugg Lifting: Relevanz fuer CH und China-Standort.\n"
        "Einschaetzung: Kurze Handlungsempfehlung.\n\n"
        "[4-5 Themen total]\n\n"
        "Quellen: [Liste]\n\n"
        "WICHTIG: Verwende immer korrekte deutsche Umlaute: ae schreibe als ae, "
        "aber ä schreibe als ä, ö als ö, ü als ü, ß als ß."
    )

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 3000,
        "system": system_prompt,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "messages": [{"role": "user", "content": user_prompt}]
    }

    try:
        messages = [{"role": "user", "content": user_prompt}]
        final_text = ""
        iterations = 0

        while iterations < 8:
            iterations += 1
            resp = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json={**body, "messages": messages},
                timeout=120
            )
            resp.raise_for_status()
            data = resp.json()

            content = data.get("content", [])
            text_blocks = [b["text"] for b in content if b.get("type") == "text"]
            if text_blocks:
                final_text = "\n".join(text_blocks).strip()

            if data.get("stop_reason") == "end_turn" or not data.get("stop_reason"):
                break

            if data.get("stop_reason") == "tool_use":
                tool_blocks = [b for b in content if b.get("type") == "tool_use"]
                if not tool_blocks:
                    break
                messages.append({"role": "assistant", "content": content})
                tool_results = [
                    {"type": "tool_result", "tool_use_id": b["id"], "content": "(Suchergebnis verarbeitet)"}
                    for b in tool_blocks
                ]
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        if not final_text:
            return jsonify({"error": "Keine Antwort erhalten. Bitte erneut versuchen."}), 500

        return jsonify({"text": final_text, "kw_label": kw_label, "date_range": date_range})

    except httpx.HTTPStatusError as e:
        try:
            err = e.response.json().get("error", {}).get("message", str(e))
        except Exception:
            err = str(e)
        return jsonify({"error": f"API-Fehler: {err}"}), 500
    except Exception as e:
        return jsonify({"error": f"Fehler: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
