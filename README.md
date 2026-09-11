# Bolkar

**Speak the bug in Hinglish. Get a filed-ready GitHub issue.**

Live: https://bolkar-eta.vercel.app

Bolkar is a voice bug reporter built on [AssemblyAI's Dictation API](https://www.assemblyai.com/docs/dictation). Hold a key, describe a bug the way you'd actually say it out loud, in Hindi, English, or a mix, and let go. In one HTTP call you get back the verbatim transcript and a clean, structured GitHub issue in English (Summary, Steps to Reproduce, Expected, Actual, Environment), plus a one-click button that opens a prefilled GitHub issue with no token.

Built for the AssemblyAI Voice Hackathon Week (Sep 9–13, 2026).

## Why it's different

Every other dictation build re-skins the same call: audio in, cleaned text out. Bolkar leans on the one thing this API does that a generic Whisper/Deepgram pipeline can't do inline:

- **Verbatim + arbitrary LLM rewrite in a single call.** The rewrite turns rambling speech into a structured issue, not just filler-stripped text.
- **Code-switching.** You speak natural Hinglish; the transcript normalizes to Devanagari and the rewrite lands in clean English.
- **Verbatim shown alongside the rewrite** as a trust signal, so you always see exactly what was heard.

Three presets reshape the same clip via `llm_instruction`: **Bug issue**, **Message**, **Commit**.

## How it works

```
mic (browser Web Audio API) -> 16 kHz mono WAV encoded in-browser -> base64
  -> POST /api/report  (Vercel serverless function, holds the key)
      -> POST dictation.assemblyai.com/transcribe
           config: { language_codes: ["hi","en"], llm_instruction: <preset> }
      -> { text (verbatim), llm_response (structured issue) }
  -> render both; "Open GitHub issue" builds a prefilled issues/new URL
```

The browser encodes the WAV, so there is no server-side transcode and nothing to install. The key lives only in a Vercel environment variable, never in the client. No SDK; the Dictation API is called over plain HTTP.

## Run it locally

```bash
python3 -m venv venv && ./venv/bin/pip install flask requests
echo "ASSEMBLYAI_API_KEY=your_key_here" > .env
./venv/bin/python server.py
# open http://127.0.0.1:5055
```

`server.py` is the local dev twin of `api/report.js`; both take the same base64 WAV and forward it.

## Deploy

```bash
vercel link --project bolkar
vercel env add ASSEMBLYAI_API_KEY production   # paste your key
vercel deploy --prod
```

## Feedback and security

While building, I logged API feedback in [`FEEDBACK.md`](./FEEDBACK.md) and one reproducible prompt-injection finding in [`SECURITY.md`](./SECURITY.md).
