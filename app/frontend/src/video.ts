// Client-side video frame sampling for walkthrough uploads. No imports: also unit-tested directly with Node
// (`npm test`, tests/video.test.ts).

export const SAMPLE_FPS = 1;
export const MAX_FRAMES = 30;
/** Frames per upload request: keeps each request well under proxy timeouts and lets the UI show progress. */
export const UPLOAD_BATCH = 5;

/**
 * Timestamps (seconds) to sample: 1 per second for short videos; for videos longer than maxFrames seconds, maxFrames
 * frames spread evenly over the whole video (so the end of a long walkthrough isn't silently ignored).
 * An unknown/invalid duration gives a single frame at 0.
 */
export function frameTimes(duration: number, fps = SAMPLE_FPS, maxFrames = MAX_FRAMES): number[] {
  if (!Number.isFinite(duration) || duration <= 0) return [0];
  const step = Math.max(1 / fps, duration / maxFrames);
  const n = Math.max(1, Math.min(maxFrames, Math.floor(duration / step + 1e-9)));
  const last = Math.max(0, duration - 0.05);
  return Array.from({ length: n }, (_, i) => Math.min(Math.round(i * step * 1000) / 1000, last));
}

/** Split into consecutive batches of `size`. */
export function batches<T>(items: T[], size = UPLOAD_BATCH): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < items.length; i += size) out.push(items.slice(i, i + size));
  return out;
}

/** "0:07" style label for a frame's position in the video. */
export function clock(t: number): string {
  const s = Math.max(0, Math.round(t));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/** One line describing what was sampled, for the Scan page. */
export function samplingSummary(duration: number, times: number[]): string {
  if (!Number.isFinite(duration) || duration <= 0) return "Couldn't read this video's length, so only its first frame was used.";
  const secs = Math.round(duration);
  if (times.length < 2 || times[1] - times[0] <= 1 / SAMPLE_FPS + 1e-6)
    return `Sampled ${times.length} frame${times.length === 1 ? "" : "s"} (1 per second) from a ${secs}-second video.`;
  const every = Math.round((times[1] - times[0]) * 10) / 10;
  return `Sampled ${times.length} frames spread across the ${clock(duration)} video (about 1 every ${every} s; max ${MAX_FRAMES}).`;
}

type Vid = {
  duration: number; currentTime: number; readyState: number;
  addEventListener(t: string, f: () => void, o?: { once?: boolean }): void;
  removeEventListener(t: string, f: () => void): void;
};

/** Wait for one of `events` on `el`, or reject after `ms`. */
export function waitFor(el: Vid, events: string[], ms: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const fns: [string, () => void][] = events.map((e) => [e, () => { done(); resolve(e); }]);
    const timer = setTimeout(() => { done(); reject(new Error(`timed out waiting for ${events.join("/")}`)); }, ms);
    function done() { clearTimeout(timer); fns.forEach(([e, f]) => el.removeEventListener(e, f)); }
    fns.forEach(([e, f]) => el.addEventListener(e, f));
  });
}

/** Seek and wait until the frame is ready. Seeking to the current position may not fire "seeked", so skip it. */
export async function seekTo(v: Vid, t: number, ms = 5000): Promise<void> {
  if (Math.abs(v.currentTime - t) < 0.001 && v.readyState >= 2) return;
  const p = waitFor(v, ["seeked"], ms);
  v.currentTime = t;
  await p;
}

/**
 * Browser recordings (MediaRecorder WebM from Chrome/Android) often report duration = Infinity until the end is
 * reached. Seeking far past the end makes the browser compute the real duration.
 */
export async function resolveDuration(v: Vid): Promise<number> {
  if (Number.isFinite(v.duration) && v.duration > 0) return v.duration;
  try {
    const p = waitFor(v, ["durationchange", "seeked"], 4000);
    v.currentTime = 1e7;
    await p;
    if (!(Number.isFinite(v.duration) && v.duration > 0)) await waitFor(v, ["durationchange"], 2000).catch(() => "");
  } catch { /* fall through: unknown duration */ }
  await seekTo(v, 0).catch(() => undefined);
  return Number.isFinite(v.duration) && v.duration > 0 ? v.duration : NaN;
}

/** Where a multi-batch upload's results came from, counted per frame (repeats excluded). Most cautious label wins:
 *  any unanswered frame -> "partial" (or "none" if no frame was analyzed); then scripted, then cached, then live. */
export function overallSource(counts: Record<string, number>): string | undefined {
  const analyzed = Object.entries(counts).filter(([k]) => k !== "repeat").reduce((a, [, n]) => a + n, 0);
  if (!analyzed) return undefined;
  if ((counts.none ?? 0) >= analyzed) return "none";
  if (counts.none) return "partial";
  if (counts.fallback) return "fallback";
  if (counts.cache) return "cache";
  return counts.live ? "live" : undefined;
}
