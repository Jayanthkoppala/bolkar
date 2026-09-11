"""Bolkar — speak a bug in Hinglish, get a filed-ready GitHub issue.
Local dev server. The browser encodes a 16 kHz mono WAV and sends it base64,
so there is no server-side transcode. Production runs the same logic as a Vercel
serverless function in api/report.js.
"""
import base64, json, pathlib, requests
from flask import Flask, request, jsonify, Response

ROOT = pathlib.Path(__file__).parent
KEY = next(l.split("=", 1)[1].strip() for l in (ROOT / ".env").read_text().splitlines()
           if l.startswith("ASSEMBLYAI_API_KEY"))
URL = "https://dictation.assemblyai.com/transcribe"

PRESETS = {
    "bug": ("Translate to clear professional English and rewrite as a GitHub bug report. "
            "First line must be 'TITLE: ' followed by a concise title under 10 words. "
            "Then markdown sections: ## Summary, ## Steps to Reproduce, ## Expected, "
            "## Actual, ## Environment. Infer reasonable steps from what was said."),
    "message": ("Translate to clear, professional English and rewrite as a concise, "
                "polite message ready to send. No greeting or signature."),
    "commit": ("Translate to English and rewrite as a single Conventional Commit line "
               "(type: subject, under 72 chars). Output only that line."),
}

app = Flask(__name__)


@app.post("/api/report")
def report():
    body = request.get_json(silent=True) or {}
    b64 = body.get("audio_b64")
    if not b64:
        return jsonify(error="no audio"), 400
    preset = body.get("preset", "bug")
    wav = base64.b64decode(b64)
    data = {}
    if preset != "default":  # "default" sends no config -> the API's default cleanup
        config = {"language_codes": ["hi", "en"], "llm_instruction": PRESETS.get(preset, PRESETS["bug"])}
        data["config"] = json.dumps(config)
    r = requests.post(URL, headers={"Authorization": KEY},
                      files={"audio": ("clip.wav", wav, "audio/wav")},
                      data=data, timeout=90)
    if r.status_code != 200:
        return jsonify(error=f"API {r.status_code}: {r.text[:300]}"), 502
    j = r.json()
    rewrite = j.get("llm_response") or j.get("text", "")
    title = ""
    if preset == "bug" and rewrite.startswith("TITLE:"):
        head, _, rest = rewrite.partition("\n")
        title = head[6:].strip()
        rewrite = rest.strip()
    return jsonify(verbatim=j.get("text", ""), rewrite=rewrite, title=title,
                   llm_error=j.get("llm_error"),
                   ms=round(j.get("request_time_ms", 0)),
                   confidence=round(j.get("confidence", 0), 3))


@app.get("/")
def index():
    return Response((ROOT / "index.html").read_text(), mimetype="text/html")


if __name__ == "__main__":
    app.run(port=5055, debug=False)
