import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, CameraOff, Flame, Upload, Video } from "lucide-react";
import { post, postForm, sampleVideo, sha256Hex, toJpeg, type Violation } from "../api";
import { AiSource, Disclaimer, ErrorBox, Progress, ViolationCard } from "../components/ui";

export default function Scan() {
  const nav = useNavigate();
  const [address, setAddress] = useState("1234 Demo St");
  const [unit, setUnit] = useState("9");
  const [scanId, setScanId] = useState<string | null>(null);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [busy, setBusy] = useState(false);
  const [frames, setFrames] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [live, setLive] = useState(false);
  const [aiSource, setAiSource] = useState<{ source?: string; model?: string | null }>({});
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  async function ensureScan(): Promise<string> {
    if (scanId) return scanId;
    const fd = new FormData();
    fd.append("mode", "walkthrough"); fd.append("address", address); fd.append("unit", unit);
    const s = await postForm("/api/scans", fd);
    setScanId(s.scan_id);
    return s.scan_id;
  }

  async function upload(blobs: Blob[], origShas: string[] = []) {
    if (!blobs.length) return;
    setBusy(true); setError(null);
    try {
      const id = await ensureScan();
      const fd = new FormData();
      blobs.forEach((b, i) => {
        fd.append("files", b, `frame-${i}.jpg`); fd.append("captured_at", new Date().toISOString());
        fd.append("orig_sha", origShas[i] ?? "");
      });
      const r = await postForm(`/api/scans/${id}/frames`, fd);
      setViolations(r.violations);
      setFrames((n) => n + blobs.length);
      setAiSource({ source: r.source, model: r.model });
      // "none" = the vision model didn't respond and Demo Mode is off: say so, don't imply the room is clean.
      if (r.source === "none") setError("The vision model didn't respond, so these photos weren't analyzed (they're still saved as evidence). Try again, or add issues manually.");
    } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  }

  async function onFiles(list: FileList | null) {
    const files = Array.from(list ?? []);
    const blobs: Blob[] = [];
    const origs: string[] = [];
    setError(null);
    for (const f of files) {
      try {
        if (f.type.startsWith("video/")) {
          const frames = await sampleVideo(f, 1, 30);
          blobs.push(...frames); origs.push(...frames.map(() => ""));
        } else {
          blobs.push(await toJpeg(f)); origs.push(await sha256Hex(f).catch(() => ""));
        }
      } catch {
        setError(`Couldn't read ${f.name}. Try a JPG/PNG photo or an MP4 video.`);
      }
    }
    upload(blobs.slice(0, 30), origs.slice(0, 30));
  }

  async function startCamera() {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment", width: 1280 }, audio: false });
      streamRef.current = s;
      setLive(true);
      setTimeout(() => { if (videoRef.current) { videoRef.current.srcObject = s; videoRef.current.play(); } }, 50);
    } catch (e: any) { setError("Camera unavailable: " + e.message + ". Upload photos instead."); }
  }
  function stopCamera() { streamRef.current?.getTracks().forEach((t) => t.stop()); streamRef.current = null; setLive(false); }
  useEffect(() => stopCamera, []);

  async function capture() {
    const v = videoRef.current;
    if (!v) return;
    const c = document.createElement("canvas");
    c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext("2d")!.drawImage(v, 0, 0);
    const b = await new Promise<Blob>((r) => c.toBlob((x) => r(x!), "image/jpeg", 0.85));
    upload([b]);
  }

  async function reportNoHeat() {
    setError(null);
    try {
      const id = await ensureScan();
      const r = await post(`/api/scans/${id}/manual`, { type_id: "NO_HEAT", note: "Tenant reports no heat" });
      setViolations(r.violations);
    } catch (e: any) { setError(e.message); }
  }

  async function createCase() {
    setBusy(true);
    try {
      stopCamera();
      const c = await post("/api/cases", { scan_id: scanId, tone: "formal" });
      nav(`/cases/${c.request_id}`);
    } catch (e: any) { setError(e.message); setBusy(false); }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="h1">Walkthrough scan</h1>
        <p className="text-neutral-600 text-lg">Point your camera at problems. Each one is matched to Madison's housing code and saved as timestamped, hashed evidence.</p>
      </div>
      <div className="card p-4 grid grid-cols-3 gap-3">
        <label className="col-span-2 space-y-1"><span className="label">Address</span>
          <input className="input" value={address} disabled={!!scanId} onChange={(e) => setAddress(e.target.value)} /></label>
        <label className="space-y-1"><span className="label">Unit</span>
          <input className="input" value={unit} disabled={!!scanId} onChange={(e) => setUnit(e.target.value)} /></label>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-3">
          {live ? (
            <div className="relative">
              <video ref={videoRef} playsInline muted className="w-full rounded-2xl bg-black aspect-[3/4] md:aspect-video object-cover" />
              <div className="absolute bottom-3 inset-x-3 flex gap-2">
                <button className="btn-primary flex-1 text-lg" onClick={capture} disabled={busy}><Camera className="w-5 h-5" />{busy ? "Analyzing…" : "Capture"}</button>
                <button className="btn-ghost" onClick={stopCamera}><CameraOff className="w-5 h-5" /></button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <button className="btn-primary h-28 text-lg flex-col" onClick={startCamera}><Camera className="w-7 h-7" />Live camera</button>
              <label className="btn-ghost h-28 text-lg flex-col cursor-pointer">
                <span className="flex gap-1"><Upload className="w-6 h-6" /><Video className="w-6 h-6" /></span>Photos / video
                <input type="file" accept="image/*,video/*" multiple className="hidden" onChange={(e) => onFiles(e.target.files)} />
              </label>
            </div>
          )}
          <button className="btn-ghost w-full" onClick={reportNoHeat}><Flame className="w-5 h-5 text-badger" /> Report no heat (can't be photographed)</button>
          {busy && <div className="card p-4"><Progress steps={["Saving evidence + SHA-256 hash…", "Looking for violations…", "Matching to MGO Chapter 27…"]} done={false} intervalMs={700} /></div>}
          <ErrorBox error={error} />
          {frames > 0 && <p className="text-sm text-neutral-500">{frames} frame{frames > 1 ? "s" : ""} analyzed and saved to the evidence locker.</p>}
        </div>

        <div className="space-y-3">
          <h2 className="h2">Possible issues {violations.length > 0 && <span className="text-badger">({violations.length})</span>}</h2>
          {violations.length > 0 && (
            <div className="space-y-1">
              <AiSource {...aiSource} />
              <p className="text-xs text-neutral-500">Spotted by AI or reported by you. This is not an inspection: only a City of Madison building inspector can determine a code violation.</p>
            </div>
          )}
          {violations.length === 0 && (frames === 0 ? (
            <div className="card p-6 text-neutral-500 text-center">Nothing yet. Capture or upload a photo.</div>
          ) : aiSource.source !== "none" && (
            <div className="card p-6 text-neutral-600 text-center space-y-2">
              <div>No possible issues spotted in {frames} photo{frames > 1 ? "s" : ""}. Try a closer shot or another angle, or report an issue yourself (e.g. no heat).</div>
              <AiSource {...aiSource} />
            </div>
          ))}
          {violations.map((v, i) => <ViolationCard key={v.violation_id} v={v} open={i === 0} />)}
          {violations.length > 0 && (
            <button className="btn-dark w-full text-lg" onClick={createCase} disabled={busy}>Create repair request →</button>
          )}
        </div>
      </div>
      <Disclaimer compact />
    </div>
  );
}
