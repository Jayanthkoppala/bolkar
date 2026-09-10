# Bolkar

**Speak the bug in Hinglish. Get a filed-ready GitHub issue.**

Bolkar is a voice bug reporter built on [AssemblyAI's Dictation API](https://www.assemblyai.com/docs/dictation). Hold a key, describe a bug the way you'd actually say it out loud — in Hindi, English, or a mix — and let go. In one HTTP call you get back the verbatim transcript and a clean, structured GitHub issue in English (Summary, Steps to Reproduce, Expected, Actual, Environment), plus a one-click button that opens a prefilled GitHub issue — no token needed.

Built for the AssemblyAI Voice Hackathon Week (Sep 9–13, 2026).

## Why it's different

Every other dictation build re-skins the same call: audio in, cleaned text out. Bolkar leans on the one thing this API does that a generic Whisper/Deepgram pipeline can't do inline:

- **Verbatim + arbitrary LLM rewrite in a single call.** The rewrite turns rambling speech into a structured issue, not just filler-stripped text.
- **Code-switching.** You speak natural Hinglish; the transcript normalizes to Devanagari and the rewrite lands in clean English. Real Indian developers don't narrate bugs in tidy monolingual English.
- **Verbatim shown alongside the rewrite** as a trust signal — you always see exactly what was heard.

Three presets show the same clip reshaped different ways via `llm_instruction`: **Bug issue**, **Message**, **Commit**.

## Run it

```bash
python3 -m venv venv && ./venv/bin/pip install flask requests
echo "ASSEMBLYAI_API_KEY=your_key_here" > .env
./venv/bin/python server.py
# open http://127.0.0.1:5055
```

Requires `ffmpeg` on PATH (transcodes the browser's audio to 16 kHz WAV).

## How it works

```
mic (browser MediaRecorder)
  -> POST /api/report  (Flask)
      -> ffmpeg  webm/opus -> 16 kHz mono WAV
      -> POST dictation.assemblyai.com/transcribe
           config: { language_codes: ["hi","en"], llm_instruction: <preset> }
      -> { text (verbatim), llm_response (structured issue) }
  -> render both; "Open GitHub issue" builds a prefilled issues/new URL
```

About 90 lines of Python and one HTML file. No SDK — the Dictation API has none yet, so it's called over plain HTTP.

## Feedback and security

While building, I logged API feedback in [`FEEDBACK.md`](./FEEDBACK.md) and one reproducible prompt-injection finding in [`SECURITY.md`](./SECURITY.md).
