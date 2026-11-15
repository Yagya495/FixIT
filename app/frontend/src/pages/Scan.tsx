import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, CameraOff, Flame, Upload, Video } from "lucide-react";
import { post, postForm, sampleVideo, sha256Hex, toJpeg, type Violation } from "../api";
import { MAX_FRAMES, batches, overallSource } from "../video";
import { AiSource, Disclaimer, ErrorBox, Progress, ViolationCard } from "../components/ui";

export default function Scan() {
  const nav = useNavigate();
  const [address, setAddress] = useState("1234 Demo St");
  const [unit, setUnit] = useState("9");
  const [scanId, setScanId] = useState<string | null>(null);
  const [violations, setViolations] = useState<Violation[]>([]);
  const [busy, setBusy] = useState(false);
  const [frames, setFrames] = useState(0);
  const [analyzedFrames, setAnalyzedFrames] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
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

  /** Uploads in small batches (progress + no single long request); results are re-consolidated server-side after
   *  each batch, so the findings list always covers every frame uploaded so far. */
  async function upload(blobs: Blob[], origShas: string[] = []) {
    if (!blobs.length) return;
    setBusy(true); setError(null);
    const counts: Record<string, number> = {};
    let model: string | null = null, done = 0;
    try {
      const id = await ensureScan();
      for (const part of batches(blobs.map((b, i) => ({ b, o: origShas[i] ?? "" })))) {
        setProgress(blobs.length > 1 ? `Analyzing ${part.length > 1 ? `frames ${done + 1}–${done + part.length}` : `frame ${done + 1}`} of ${blobs.length}…` : null);
        const fd = new FormData();
        part.forEach(({ b, o }, i) => {
          fd.append("files", b, `frame-${done + i}.jpg`); fd.append("captured_at", new Date().toISOString());
          fd.append("orig_sha", o);
        });
        fd.append("frame_offset", String(done)); fd.append("frame_total", String(blobs.length));
        const r = await postForm(`/api/scans/${id}/frames`, fd);
        setViolations(r.violations);
        for (const f of r.frames) counts[f.repeat ? "repeat" : f.source] = (counts[f.repeat ? "repeat" : f.source] ?? 0) + 1;
        model = r.model ?? model;
        setFrames((n) => n + r.frames.filter((f: any) => !f.repeat).length);
        setAnalyzedFrames((n) => n + r.frames.filter((f: any) => !f.repeat && f.source !== "none").length);
        done += part.length;
      }
    } catch (e: any) {
      setError(done ? `Stopped after ${done} of ${blobs.length} frames: ${e.message}. The frames before that were saved and analyzed.` : e.message);
    } finally {
      const source = overallSource(counts);
      setAiSource({ source, model });
      const analyzed = Object.entries(counts).filter(([k]) => k !== "repeat").reduce((a, [, n]) => a + n, 0);
      // The vision model didn't answer and Demo Mode is off: say so, don't imply the room is clean.
      if (source === "none") setError("The vision model didn't respond, so these photos weren't analyzed (they're still saved as evidence). Try again, or add issues manually.");
      else if (source === "partial") setError(`${counts.none} of ${analyzed} frames weren't analyzed because the vision model didn't respond (they're still saved as evidence). Try uploading them again.`);
      if (counts.repeat) setNote((n) => [n, `${counts.repeat} repeated frame${counts.repeat > 1 ? "s were" : " was"} identical to one already analyzed and skipped.`].filter(Boolean).join(" "));
      setProgress(null); setBusy(false);
    }
  }

  async function onFiles(list: FileList | null) {
    const files = Array.from(list ?? []);
    const blobs: Blob[] = [];
    const origs: string[] = [];
    const notes: string[] = [];
    setError(null); setNote(null);
    if (files.some((f) => f.type.startsWith("video/"))) setProgress("Extracting frames from the video…");
    for (const f of files) {
      try {
        if (f.type.startsWith("video/")) {
          const s = await sampleVideo(f);
          blobs.push(...s.frames.map((x) => x.blob)); origs.push(...s.frames.map(() => ""));
          notes.push(s.summary);
        } else {
          blobs.push(await toJpeg(f)); origs.push(await sha256Hex(f).catch(() => ""));
        }
      } catch {
        setError(`Couldn't read ${f.name}. Try a JPG/PNG photo or an MP4 video.`);
      }
    }
    setProgress(null);
    if (blobs.length > MAX_FRAMES) notes.push(`Only the first ${MAX_FRAMES} of ${blobs.length} photos/frames were analyzed; upload the rest separately.`);
    setNote(notes.join(" ") || null);
    upload(blobs.slice(0, MAX_FRAMES), origs.slice(0, MAX_FRAMES));
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

  async function reportManual(type_id: string, note: string) {
    setError(null);
    try {
      const id = await ensureScan();
      const r = await post(`/api/scans/${id}/manual`, { type_id, note });
      setViolations(r.violations);
    } catch (e: any) { setError(e.message); }
  }
  const reportNoHeat = () => reportManual("NO_HEAT", "Tenant reports no heat");

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
                <input type="file" accept="image/*,video/*" multiple className="hidden" disabled={busy}
                  onChange={(e) => { onFiles(e.target.files); e.target.value = ""; }} />
              </label>
            </div>
          )}
          {!live && (
            <label className={`btn-ghost w-full cursor-pointer flex-col !gap-0 ${busy ? "opacity-50 pointer-events-none" : ""}`}>
              <span className="flex items-center gap-2"><Video className="w-5 h-5" /> Record a walkthrough video</span>
              <span className="text-xs text-neutral-500 font-normal">On a phone this opens the camera. Walk slowly; we check about 1 frame per second (max 30).</span>
              {/* capture= opens the camera's video mode on phones; desktop browsers ignore it and show a file picker. */}
              <input type="file" accept="video/*" capture="environment" className="hidden" disabled={busy}
                onChange={(e) => { onFiles(e.target.files); e.target.value = ""; }} />
            </label>
          )}
          <button className="btn-ghost w-full" onClick={reportNoHeat}><Flame className="w-5 h-5 text-badger" /> Report no heat (can't be photographed)</button>
          <div className="grid grid-cols-2 gap-2">
            <button className="btn-ghost text-sm" onClick={() => reportManual("SMOKE_DETECTOR_MISSING", "Tenant reports a missing or non-working smoke alarm")}>Report smoke alarm missing / not working</button>
            <button className="btn-ghost text-sm" onClick={() => reportManual("CO_DETECTOR_MISSING", "Tenant reports a missing or non-working CO alarm")}>Report CO alarm missing / not working</button>
          </div>
          {(busy || progress) && <div className="card p-4 space-y-2">
            {progress && <p className="text-sm font-semibold" role="status">{progress}</p>}
            {busy && <Progress steps={["Saving evidence + SHA-256 hash…", "Looking for possible issues…", "Matching to MGO Chapter 27…"]} done={false} intervalMs={700} />}
          </div>}
          <ErrorBox error={error} />
          {note && <p className="text-sm text-neutral-600">{note}</p>}
          {frames > 0 && <p className="text-sm text-neutral-500">{frames} frame{frames > 1 ? "s" : ""} saved to the evidence locker{analyzedFrames === frames ? " and analyzed" : `; ${analyzedFrames} analyzed`}.</p>}
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
