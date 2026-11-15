import { MAX_FRAMES, SAMPLE_FPS, frameTimes, resolveDuration, samplingSummary, seekTo, waitFor } from "./video";

export type CodeSection ={ section_id: string; title: string; snippet: string; url: string; score: number; verified: boolean;
  official_text?: boolean; page?: number | null };
export type Violation = {
  violation_id: string; scan_id: string; property_id: string | null; violation_type: string; name: string;
  category: string; severity: "routine" | "urgent" | "emergency"; confidence: number; certain: boolean; label: string;
  explanation: string; remedy: string; code_sections: CodeSection[]; evidence_ids: string[]; notes: string[];
  /** One per supporting photo or tenant report, each tied to its own evidence (null = tenant report, no photo). */
  observations?: Observation[]; bases?: string[]; verify_in_person?: boolean; tenant_reported?: boolean;
};
export type Observation = { evidence_id: string | null; note: string; basis: string; basis_text: string; confidence: number };
export type Frame = { evidence_id: string; sha256: string; scene: string; detections: any[]; source: string };

async function handle(r: Response) {
  if (!r.ok) {
    let msg = r.statusText;
    try { msg = (await r.json()).detail ?? msg; } catch {}
    throw new Error(msg);
  }
  return r.json();
}
export const get = (url: string) => fetch(url).then(handle);
export const post = (url: string, body?: unknown) =>
  fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined }).then(handle);
export const postForm = (url: string, form: FormData) => fetch(url, { method: "POST", body: form }).then(handle);

export const imgUrl = (evidenceId: string) => `/api/evidence/${evidenceId}/image`;

/** SHA-256 of the ORIGINAL file, sent with uploads so Demo Mode's cache (keyed by the file on disk) still matches
 *  after toJpeg() re-encodes the image. Evidence hashes are still computed server-side on the uploaded bytes. */
export async function sha256Hex(b: Blob): Promise<string> {
  const d = await crypto.subtle.digest("SHA-256", await b.arrayBuffer());
  return Array.from(new Uint8Array(d)).map((x) => x.toString(16).padStart(2, "0")).join("");
}

/** Downscale an image file/blob to a JPEG (max 1280px) before upload. */
export async function toJpeg(src: Blob, max = 1280): Promise<Blob> {
  const bmp = await createImageBitmap(src);
  const s = Math.min(1, max / Math.max(bmp.width, bmp.height));
  const c = document.createElement("canvas");
  c.width = Math.round(bmp.width * s); c.height = Math.round(bmp.height * s);
  c.getContext("2d")!.drawImage(bmp, 0, 0, c.width, c.height);
  return new Promise((res) => c.toBlob((b) => res(b!), "image/jpeg", 0.85));
}

export type VideoSample = { frames: { blob: Blob; t: number }[]; duration: number; summary: string };

/** Sample frames from a video file client-side: 1 per second, max 30 (spread evenly over longer videos).
 *  Handles browser recordings whose duration is reported as Infinity, and never waits forever on a seek. */
export async function sampleVideo(file: File, fps = SAMPLE_FPS, maxFrames = MAX_FRAMES): Promise<VideoSample> {
  const url = URL.createObjectURL(file);
  const v = document.createElement("video");
  v.muted = true; v.playsInline = true; v.preload = "auto";
  v.setAttribute("playsinline", ""); v.setAttribute("muted", "");  // iOS Safari
  try {
    const ready = waitFor(v, ["loadedmetadata", "error"], 15000);
    v.src = url; v.load();
    if ((await ready) === "error") throw new Error("unsupported video");
    const duration = await resolveDuration(v);
    const times = frameTimes(duration, fps, maxFrames);
    const c = document.createElement("canvas");
    const s = Math.min(1, 1280 / Math.max(v.videoWidth, v.videoHeight));
    c.width = Math.round(v.videoWidth * s); c.height = Math.round(v.videoHeight * s);
    if (!c.width || !c.height) throw new Error("video has no picture");
    const frames: { blob: Blob; t: number }[] = [];
    for (const t of times) {
      try { await seekTo(v, t); } catch { continue; }  // one stuck seek skips that frame, not the whole video
      c.getContext("2d")!.drawImage(v, 0, 0, c.width, c.height);
      frames.push({ blob: await new Promise<Blob>((r) => c.toBlob((b) => r(b!), "image/jpeg", 0.85)), t });
    }
    if (!frames.length) throw new Error("no frames could be read");
    return { frames, duration, summary: samplingSummary(duration, times) };
  } finally {
    v.removeAttribute("src"); v.load();
    URL.revokeObjectURL(url);
  }
}
