// Vercel serverless proxy for the AssemblyAI Dictation API.
// The browser sends a base64 16 kHz mono WAV; this adds the key (kept in an env
// var, never shipped to the client) and forwards to AssemblyAI in one call.
const URL = "https://dictation.assemblyai.com/transcribe";

const PRESETS = {
  bug: "Translate to clear professional English and rewrite as a GitHub bug report. "
     + "First line must be 'TITLE: ' followed by a concise title under 10 words. "
     + "Then markdown sections: ## Summary, ## Steps to Reproduce, ## Expected, "
     + "## Actual, ## Environment. Infer reasonable steps from what was said.",
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
  const config = { language_codes: ["hi", "en"], llm_instruction: PRESETS[preset] || PRESETS.bug };

  const form = new FormData();
  form.append("audio", new Blob([wav], { type: "audio/wav" }), "clip.wav");
  form.append("config", JSON.stringify(config));

  let r;
  try {
    r = await fetch(URL, { method: "POST", headers: { Authorization: key }, body: form });
  } catch (e) {
    return res.status(502).json({ error: "upstream unreachable" });
  }
  const text = await r.text();
  if (r.status !== 200) {
    let detail = text.slice(0, 300);
    try { detail = JSON.parse(text).title || JSON.parse(text).detail || detail; } catch {}
    return res.status(502).json({ error: `API ${r.status}: ${detail}` });
  }
  const j = JSON.parse(text);
  let rewrite = j.llm_response || j.text || "";
  let title = "";
  if (preset === "bug" && rewrite.startsWith("TITLE:")) {
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
