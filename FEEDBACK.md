# Dictation API — feedback from building Bolkar

Found while building a Hinglish voice-to-GitHub-issue tool on the beta endpoint (`dictation.assemblyai.com/transcribe`). Ordered by impact. The prompt-injection issue is written up separately in `SECURITY.md`.

## 1. Docs say unknown config fields are forwarded; the API rejects them (400)

The docs state:

> Unknown fields are forwarded to the transcription engine as-is, so transcription parameters added in the future work without dictation-side changes.

In practice, any unrecognized config field is rejected:

```json
{ "config": {"llm_instruction": "Clean up.", "diarization": true, "foo": 1} }
-> HTTP 400
{"status":400,"title":"Bad Request",
 "detail":"invalid config part: foo: Extra inputs are not permitted; diarization: Extra inputs are not permitted"}
```

Either the validation is stricter than intended, or the docs describe behavior that no longer exists. This bit me because I read the docs and assumed I could pass engine params through. Please make the docs and the validator agree.

## 2. Undocumented minimum audio duration (80 ms)

The docs give a 120-second maximum but no minimum. A short clip returns:

```json
HTTP 400 {"status":400,"title":"Audio Too Short","detail":"audio duration 60 ms below minimum 80 ms"}
```

Worth documenting the 80 ms floor next to the 120 s ceiling. A client that records on a quick tap hits this immediately.

## 3. Undocumented response field `auth_time_ms`

Responses include `auth_time_ms`, which is not in the *Response* table (which lists `request_time_ms` and `sync_time_ms`). Minor, but the docs claim to enumerate the response fields.

## 4. Language count: marketing says 18, docs list 19

Event and marketing copy say "18 languages"; the docs `language_codes` list has 19 (en, es, de, fr, it, pt, tr, nl, sv, no, da, fi, hi, vi, ar, he, ja, ur, zh). Pick one number.

## 5. Code-switched input is script-normalized (undocumented, but good)

Roman-script Hinglish audio ("Yaar ye login button ka bahut bada issue hai...") comes back as a Devanagari `text` transcript, and the rewrite translates it cleanly. This is useful behavior and a real strength for Indian-language dictation, but it is not documented. Worth a line so developers know the verbatim may switch script.

## What worked well

- Verbatim + rewrite in a single call is the standout. Building a "speak a mess, get a structured artifact" flow took no orchestration code.
- The rewrite recovers meaning even when the ASR transcript is messy on noisy real-mic code-switched speech. In one test the transcript was partly garbled but the issue it produced was still correct.
- Latency was consistently 2.4–4 s end to end for ~20 s clips.
