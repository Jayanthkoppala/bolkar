# Dictation API — feedback from building Bolkar

Found while building a Hinglish voice-to-GitHub-issue tool on the beta endpoint (`dictation.assemblyai.com/transcribe`). Ordered by impact. The prompt-injection issue has its own writeup in `SECURITY.md`.

## 1. Unknown config fields are rejected, not forwarded

The docs say:

> Unknown fields are forwarded to the transcription engine as-is, so transcription parameters added in the future work without dictation-side changes.

In practice they are rejected:

```json
{ "config": {"llm_instruction": "Clean up.", "diarization": true, "foo": 1} }
-> HTTP 400
{"status":400,"title":"Bad Request",
 "detail":"invalid config part: foo: Extra inputs are not permitted; diarization: Extra inputs are not permitted"}
```

This is a real contradiction, not just a made-up field being refused: `diarization` is a genuine transcription parameter, exactly the kind the docs promise will pass through. Either the validator is stricter than intended or the docs describe behavior that no longer exists.

## 2. Undocumented minimum audio duration (80 ms)

The docs give a 120-second maximum but no minimum. A short clip returns:

```json
HTTP 400 {"status":400,"title":"Audio Too Short","detail":"audio duration 60 ms below minimum 80 ms"}
```

Worth documenting the 80 ms floor next to the 120 s ceiling. A client that records on a quick tap hits this immediately.

## 3. The rewrite fails with an undocumented "truncated" error on short structured requests

On a short clip, a structured `llm_instruction` (asking for a titled, multi-section bug report) reliably returns `llm_response: null` with `llm_error: "truncated"`. Two problems:

- `"truncated"` is not documented. The *Response* table lists only `"timeout"` and `"error"` for `llm_error`.
- It is deterministic, not flaky. The same short clip fails on every retry with the structured instruction, but succeeds immediately with a simple instruction like "translate to English and fix punctuation." So the structuring instruction on a short or sparse transcript is the trigger.

Longer, richer speech rewrites fine; short synthetic clips fail every time. We work around it by retrying and then falling back to a plain translation, but the underlying rewrite should not truncate on small inputs.

## 4. Smaller items

- The response includes an undocumented `auth_time_ms` field, not in the *Response* table (which lists `request_time_ms` and `sync_time_ms`).
- Language count: marketing says "18 languages"; the docs `language_codes` list has 19 (en, es, de, fr, it, pt, tr, nl, sv, no, da, fi, hi, vi, ar, he, ja, ur, zh).
- Code-switched input is script-normalized (Roman Hinglish audio returns a Devanagari `text`). Useful behavior, but undocumented, so a developer may not expect the script to switch.

## What worked well

- Verbatim plus rewrite in a single call is the standout. Building a "speak a mess, get a structured artifact" flow took no orchestration code.
- The rewrite recovers meaning even when the transcript is messy on real-mic code-switched speech.
- Latency was consistently 1.5–4 s end to end for short clips.
