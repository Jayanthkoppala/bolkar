// Vercel serverless proxy for the AssemblyAI Dictation API.
// The browser sends a base64 16 kHz mono WAV; this adds the key (kept in an env
// var, never shipped to the client) and forwards to AssemblyAI in one call.
const URL = "https://dictation.assemblyai.com/transcribe";

const PRESETS = {
  bug: "Translate to clear professional English and rewrite as a GitHub bug report. "
     + "First line must be 'TITLE: ' followed by a concise title under 10 words. "
     + "Then markdown sections: ## Summary, ## Steps to Reproduce, ## Expected, "
     + "## Actual, ## Environment. Infer reasonable steps from what was said. "
     + "Keep every section to one or two short lines so the whole issue stays compact.",
  message: "Translate to clear, professional English and rewrite as a concise, "
         + "polite message ready to send. No greeting or signature.",
  commit: "Translate to English and rewrite as a single Conventional Commit line "
        + "(type: subject, under 72 chars). Output only that line.",
};

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const key = process.env.ASSEMBLYAI_API_KEY;
  if (!key) return res.status(500).json({ error: "server missing ASSEMBLYAI_API_KEY" });

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : (req.body || {});
  const { audio_b64, preset = "bug" } = body;
  if (!audio_b64) return res.status(400).json({ error: "no audio" });

  const wav = Buffer.from(audio_b64, "base64");
  const makeForm = () => {
    const f = new FormData();
    f.append("audio", new Blob([wav], { type: "audio/wav" }), "clip.wav");
    // "default" sends no config, so the API runs its documented default cleanup.
    if (preset !== "default") {
      f.append("config", JSON.stringify({ language_codes: ["hi", "en"], llm_instruction: PRESETS[preset] || PRESETS.bug }));
    }
    return f;
  };

  // The rewrite intermittently returns llm_error "truncated" with a null llm_response,
  // so retry a few times before giving up.
  let j = null, softErr = null;
  for (let i = 0; i < 3; i++) {
    let r;
    try { r = await fetch(URL, { method: "POST", headers: { Authorization: key }, body: makeForm() }); }
    catch (e) { softErr = "upstream unreachable"; continue; }
    const text = await r.text();
    if (r.status !== 200) {
      let detail = text.slice(0, 300);
      try { const b = JSON.parse(text); detail = b.title || b.detail || detail; } catch {}
      return res.status(502).json({ error: `API ${r.status}: ${detail}` });
    }
    j = JSON.parse(text);
    if (preset === "default" || j.llm_response) break;  // success, or default needs no rewrite
  }
  if (!j) return res.status(502).json({ error: softErr || "no response" });

  // If the structured rewrite truncated upstream, fall back to a plain English
  // translation so the user still gets usable text instead of an error.
  if (!j.llm_response && preset !== "default") {
    try {
      const f = new FormData();
      f.append("audio", new Blob([wav], { type: "audio/wav" }), "clip.wav");
      f.append("config", JSON.stringify({ language_codes: ["hi", "en"], llm_instruction: "Translate to clear professional English and fix punctuation. Do not restructure." }));
      const rr = await fetch(URL, { method: "POST", headers: { Authorization: key }, body: f });
      if (rr.status === 200) { const jj = JSON.parse(await rr.text()); if (jj.llm_response) j = jj; }
    } catch (e) {}
  }
  let rewrite = j.llm_response || "";  // "" when even the fallback failed; do NOT fall back to the transcript
  let title = "";
  if (rewrite && preset === "bug" && rewrite.startsWith("TITLE:")) {
    const nl = rewrite.indexOf("\n");
    title = rewrite.slice(6, nl < 0 ? undefined : nl).trim();
    rewrite = nl < 0 ? "" : rewrite.slice(nl + 1).trim();
  }
  return res.status(200).json({
    verbatim: j.text || "",
    rewrite,
    title,
    llm_error: j.llm_error || null,
    ms: Math.round(j.request_time_ms || 0),
    confidence: Math.round((j.confidence || 0) * 1000) / 1000,
  });
}
