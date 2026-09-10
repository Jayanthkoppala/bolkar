import os, json, requests, sys
KEY = [l.split('=',1)[1].strip() for l in open('.env') if l.startswith('ASSEMBLYAI_API_KEY')][0]
URL = "https://dictation.assemblyai.com/transcribe"
def call(wav, config=None, label=""):
    files = {"audio": (wav, open(wav,"rb"), "audio/wav")}
    data = {}
    if config is not None:
        data["config"] = json.dumps(config)
    print(f"\n===== {label} ({wav}) config={config} =====")
    try:
        r = requests.post(URL, headers={"Authorization": KEY}, files=files, data=data, timeout=90)
    except Exception as e:
        print("REQUEST ERROR:", e); return
    print("HTTP", r.status_code)
    try:
        j = r.json()
    except Exception:
        print("non-JSON:", r.text[:500]); return
    for k in ("text","llm_response","llm_error","confidence","audio_duration_ms","request_time_ms","sync_time_ms","session_id"):
        if k in j: print(f"  {k}: {j[k]!r}")
    extra = {k:v for k,v in j.items() if k not in ('text','llm_response','llm_error','confidence','audio_duration_ms','request_time_ms','sync_time_ms','session_id','words')}
    if extra: print("  OTHER:", extra)

# 1) English, default rewrite (disfluency removal)
call("english.wav", None, "English / default rewrite")
# 2) Hinglish -> translate + format as GitHub issue
call("hinglish.wav",
     {"language_codes": ["hi","en"],
      "llm_instruction": "Translate to clear professional English and rewrite as a GitHub bug report with sections: Summary, Steps to Reproduce, Expected, Actual, Environment. Use markdown."},
     "Hinglish / translate+issue")
# 3) Hinglish verbatim baseline (what did ASR hear?)
call("hinglish.wav", {"language_codes": ["hi","en"]}, "Hinglish / default rewrite (see verbatim)")
