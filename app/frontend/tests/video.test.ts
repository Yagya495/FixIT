// Run: npm test (Node >= 22.18 strips TypeScript types natively; no extra dependencies).
import { test } from "node:test";
import assert from "node:assert/strict";
import { batches, frameTimes, overallSource, resolveDuration, samplingSummary, seekTo } from "../src/video.ts";

test("1 frame per second for short videos", () => {
  assert.deepEqual(frameTimes(12), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]);
  assert.deepEqual(frameTimes(0.4), [0]);
  assert.deepEqual(frameTimes(1), [0]);
  assert.equal(frameTimes(30).length, 30);
});

test("long videos: max 30 frames spread over the whole video, not just the first 30 s", () => {
  const t = frameTimes(120);
  assert.equal(t.length, 30);
  assert.equal(t[0], 0);
  assert.equal(t[1], 4);
  assert.ok(t[29] >= 110 && t[29] < 120);
});

test("unknown duration (Infinity/NaN) gives one frame, never 30 seeks past the end", () => {
  assert.deepEqual(frameTimes(Infinity), [0]);
  assert.deepEqual(frameTimes(NaN), [0]);
  assert.deepEqual(frameTimes(0), [0]);
});

test("timestamps stay inside the video", () => {
  for (const d of [0.5, 1.02, 7.3, 29.99, 31, 600]) for (const t of frameTimes(d)) assert.ok(t >= 0 && t < d, `${t} in ${d}`);
});

test("batches", () => {
  assert.deepEqual(batches([1, 2, 3, 4, 5, 6, 7], 5), [[1, 2, 3, 4, 5], [6, 7]]);
  assert.deepEqual(batches([], 5), []);
});

test("overall source is the most cautious label", () => {
  assert.equal(overallSource({ live: 12 }), "live");
  assert.equal(overallSource({ live: 10, none: 2 }), "partial");
  assert.equal(overallSource({ none: 3, repeat: 2 }), "none");
  assert.equal(overallSource({ live: 3, cache: 1 }), "cache");
  assert.equal(overallSource({ repeat: 4 }), undefined);
});

test("sampling summary says what was sampled", () => {
  assert.match(samplingSummary(12, frameTimes(12)), /12 frames \(1 per second\) from a 12-second video/);
  assert.match(samplingSummary(120, frameTimes(120)), /30 frames spread across the 2:00 video \(about 1 every 4 s/);
  assert.match(samplingSummary(Infinity, [0]), /only its first frame/);
});

class FakeVideo {
  duration: number; currentTime = 0; readyState = 4; l: Record<string, (() => void)[]> = {};
  realDuration: number; fireSeeked: boolean;
  constructor(duration: number, realDuration = duration, fireSeeked = true) {
    this.duration = duration; this.realDuration = realDuration; this.fireSeeked = fireSeeked;
  }
  addEventListener(t: string, f: () => void) { (this.l[t] ??= []).push(f); }
  removeEventListener(t: string, f: () => void) { this.l[t] = (this.l[t] ?? []).filter((x) => x !== f); }
  emit(t: string) { [...(this.l[t] ?? [])].forEach((f) => f()); }
  seek(t: number) {
    this.currentTime = Math.min(t, this.realDuration);
    setTimeout(() => {
      if (!Number.isFinite(this.duration)) { this.duration = this.realDuration; this.emit("durationchange"); }
      if (this.fireSeeked) this.emit("seeked");
    }, 1);
  }
}
function proxy(v: FakeVideo) {
  return new Proxy(v, { set(o, k, val) { if (k === "currentTime") o.seek(val); else (o as any)[k] = val; return true; } });
}

test("resolveDuration finds the real length of a recording that reports Infinity", async () => {
  const v = proxy(new FakeVideo(Infinity, 12.4));
  assert.equal(await resolveDuration(v), 12.4);
  assert.equal(v.currentTime, 0);
});

test("resolveDuration keeps a normal duration without seeking", async () => {
  const v = proxy(new FakeVideo(8));
  assert.equal(await resolveDuration(v), 8);
});

test("seekTo times out instead of hanging when the browser never fires 'seeked'", async () => {
  const v = proxy(new FakeVideo(10, 10, false));
  await assert.rejects(seekTo(v, 3, 50), /timed out/);
  await seekTo(v, 3, 50);  // already there: returns immediately
});
