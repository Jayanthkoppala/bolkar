"""Bolkar — speak a bug in Hinglish, get a filed-ready GitHub issue.
Single-file Flask app over AssemblyAI's Dictation API.
ponytail: ffmpeg transcodes the browser blob to 16k WAV, so the host needs ffmpeg
on PATH. Swap for in-browser WAV encoding if you deploy somewhere without it.
"""
import json, subprocess, pathlib, requests
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


def to_wav(blob: bytes) -> bytes:
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0",
                        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-f", "wav", "pipe:1"],
                       input=blob, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode()[:300])
    return p.stdout


@app.post("/api/report")
def report():
    audio = request.files.get("audio")
    if not audio:
        return jsonify(error="no audio"), 400
    preset = request.form.get("preset", "bug")
    try:
        wav = to_wav(audio.read())
    except RuntimeError as e:
        return jsonify(error=f"transcode failed: {e}"), 400
    config = {"language_codes": ["hi", "en"], "llm_instruction": PRESETS.get(preset, PRESETS["bug"])}
    r = requests.post(URL, headers={"Authorization": KEY},
                      files={"audio": ("clip.wav", wav, "audio/wav")},
                      data={"config": json.dumps(config)}, timeout=90)
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
