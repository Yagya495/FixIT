export type CodeSection = { section_id: string; title: string; snippet: string; url: string; score: number; verified: boolean };
export type Violation = {
  violation_id: string; scan_id: string; property_id: string | null; violation_type: string; name: string;
  category: string; severity: "routine" | "urgent" | "emergency"; confidence: number; certain: boolean; label: string;
  explanation: string; remedy: string; code_sections: CodeSection[]; evidence_ids: string[]; notes: string[];
};
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

/** Downscale an image file/blob to a JPEG (max 1280px) before upload. */
export async function toJpeg(src: Blob, max = 1280): Promise<Blob> {
  const bmp = await createImageBitmap(src);
  const s = Math.min(1, max / Math.max(bmp.width, bmp.height));
  const c = document.createElement("canvas");
  c.width = Math.round(bmp.width * s); c.height = Math.round(bmp.height * s);
  c.getContext("2d")!.drawImage(bmp, 0, 0, c.width, c.height);
  return new Promise((res) => c.toBlob((b) => res(b!), "image/jpeg", 0.85));
}

/** Sample frames from a video file at `fps` (max `maxFrames`), client-side. */
export async function sampleVideo(file: File, fps = 1, maxFrames = 30): Promise<Blob[]> {
  const url = URL.createObjectURL(file);
  const v = document.createElement("video");
  v.src = url; v.muted = true; v.playsInline = true;
  await new Promise((r, j) => { v.onloadedmetadata = r; v.onerror = j; });
  const n = Math.min(maxFrames, Math.max(1, Math.floor(v.duration * fps)));
  const c = document.createElement("canvas");
  const s = Math.min(1, 1280 / Math.max(v.videoWidth, v.videoHeight));
  c.width = v.videoWidth * s; c.height = v.videoHeight * s;
  const out: Blob[] = [];
  for (let i = 0; i < n; i++) {
    v.currentTime = Math.min(v.duration - 0.05, i / fps);
    await new Promise((r) => (v.onseeked = r));
    c.getContext("2d")!.drawImage(v, 0, 0, c.width, c.height);
    out.push(await new Promise<Blob>((r) => c.toBlob((b) => r(b!), "image/jpeg", 0.85)));
  }
  URL.revokeObjectURL(url);
  return out;
}
