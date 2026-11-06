// Worker de transcrição: roda o Whisper (transformers.js) fora da tela principal.
import { pipeline, env } from "./vendor/transformers.min.js";

env.allowLocalModels = false;                       // modelos vêm do Hugging Face (1ª vez) e ficam no cache do navegador
env.backends.onnx.wasm.wasmPaths = new URL("./vendor/", import.meta.url).href;

let asr = null, current = "";

async function load(model) {
  const key = model;
  if (asr && current === key) return asr.device;
  if (asr) { try { await asr.dispose(); } catch (_) {} asr = null; }

  const progress_callback = (p) => {
    if (p.status === "progress") self.postMessage({ type: "dl", file: p.file, loaded: p.loaded, total: p.total });
  };
  const hasGPU = !!(self.navigator && navigator.gpu && await navigator.gpu.requestAdapter().catch(() => null));
  if (hasGPU) {
    try {
      asr = await pipeline("automatic-speech-recognition", model, {
        device: "webgpu", dtype: { encoder_model: "fp32", decoder_model_merged: "q4" }, progress_callback });
      asr.device = "GPU (WebGPU)";
    } catch (e) { asr = null; }
  }
  if (!asr) {
    asr = await pipeline("automatic-speech-recognition", model, { device: "wasm", dtype: "q8", progress_callback });
    asr.device = "CPU (WASM)";
  }
  current = key;
  return asr.device;
}

self.onmessage = async (ev) => {
  const m = ev.data;
  try {
    if (m.type === "load") {
      const device = await load(m.model);
      self.postMessage({ type: "ready", device });
    } else if (m.type === "chunk") {
      const opts = { task: "transcribe", return_timestamps: true };
      if (m.language) opts.language = m.language;
      const out = await asr(m.audio, opts);
      self.postMessage({ type: "chunk", id: m.id, text: out.text || "", chunks: out.chunks || [] });
    }
  } catch (e) {
    self.postMessage({ type: "error", id: m.id, message: String(e && e.message || e) });
  }
};
