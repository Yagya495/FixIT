import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertOctagon, Bot, Clock, FastForward, FileDown, Mic, Phone, PhoneOff, Send, ShieldCheck, Users, Volume2, VolumeX } from "lucide-react";
import { get, imgUrl, post } from "../api";
import { CopyButton, DemoBadge, Disclaimer, ErrorBox, SeverityChip, Spinner, ViolationCard } from "../components/ui";
import { AlarmRules } from "../components/AlarmRules";

// Smoke/CO source prototype is shown only for cases that include an alarm issue.
const alarmTypes = (c: any): ("smoke" | "co")[] => {
  const t = new Set((c.violations ?? []).map((v: any) => v.violation_type));
  return [...(t.has("SMOKE_DETECTOR_MISSING") ? ["smoke" as const] : []), ...(t.has("CO_DETECTOR_MISSING") ? ["co" as const] : [])];
};

const TONES = ["friendly", "formal", "final"] as const;
// "Final request", not "Final notice": the City issues Official Notices; a tenant letter must not sound like one.
const TONE_LABEL = { friendly: "Friendly", formal: "Formal", final: "Final request" };

export default function Case() {
  const { id } = useParams();
  const [c, setC] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const reload = () => get(`/api/cases/${id}`).then(setC).catch((e) => setError(e.message));
  useEffect(() => { reload(); }, [id]);
  if (error) return <ErrorBox error={error} />;
  if (!c) return <Spinner label="Loading case…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-sm text-neutral-500 font-semibold">Case {c.request_id}</div>
          <h1 className="h1">{c.address}{c.unit ? `, Unit ${c.unit}` : ""}</h1>
          <div className="text-neutral-600">Landlord: {c.landlord} · {c.violations.length} issues · worst: <SeverityChip s={c.severity} /></div>
        </div>
        <a className="btn-ghost" href={`/api/cases/${c.request_id}/packet.pdf`}><FileDown className="w-4 h-4" /> Evidence packet PDF</a>
      </div>

      {c.emergency && (
        <div className="rounded-2xl bg-red-600 text-white p-5 flex gap-3">
          <AlertOctagon className="w-8 h-8 shrink-0" />
          <div>
            <div className="text-xl font-extrabold">This may be an emergency</div>
            <p>If anyone is in immediate danger (fire, gas smell, sparking wires), call <b>911</b>. Otherwise call City of Madison Building Inspection now: <b>608-266-4551</b>. You can still send the letter below.</p>
          </div>
        </div>
      )}

      <Collective c={c} />

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <section className="space-y-3">
            <h2 className="h2">Issues</h2>
            {c.violations.map((v: any) => <ViolationCard key={v.violation_id} v={v} />)}
          </section>
          {alarmTypes(c).length > 0 && <AlarmRules types={alarmTypes(c)} />}
          <Evidence c={c} />
        </div>
        <div className="space-y-6">
          <Letter c={c} onChange={reload} />
          <Call c={c} onDone={reload} />
          <Deadline c={c} onChange={setC} />
        </div>
      </div>
      <Disclaimer />
    </div>
  );
}

function Collective({ c }: { c: any }) {
  const col = c.collective;
  const [joint, setJoint] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  if (!col?.matched) return null;
  async function fileTogether() {
    setBusy(true); setErr(null);
    try { setJoint(await post(`/api/cases/${c.request_id}/joint`)); }
    catch (e: any) { setErr(e.message); }
    finally { setBusy(false); }
  }
  return (
    <section className="rounded-2xl bg-ink text-white p-5 space-y-3">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm font-bold uppercase tracking-wide text-red-300"><span className="flex items-center gap-2"><Users className="w-4 h-4" /> You're not alone</span> <DemoBadge label="Simulated neighbor reports" /></div>
      {col.headline && <div className="text-2xl md:text-3xl font-extrabold">{col.headline}</div>}
      {col.owner_line && <div className="text-lg text-neutral-300">{col.owner_line}</div>}
      <div className="flex flex-wrap gap-2">
        {col.neighbors.by_category.slice(0, 5).map((x: any) => (
          <span key={x.category} className="chip bg-white/10 text-white">{x.category.replace("_", " ")} · {x.households} households</span>
        ))}
      </div>
      {col.other_buildings.length > 0 && (
        <div className="text-sm text-neutral-300">Same owner: {col.other_buildings.map((b: any) => (
          <Link key={b.property_id} to={`/buildings/${b.property_id}`} className="underline mr-3">{b.address_norm} ({b.open_issues} open)</Link>))}
        </div>
      )}
      {!joint ? (
        <>
          <button className="btn-primary text-lg" disabled={busy} onClick={fileTogether}>
            <Users className="w-5 h-5" /> File together
          </button>
          <ErrorBox error={err} />
        </>
      ) : (
        <div className="bg-white text-ink rounded-xl p-4 space-y-2">
          <div className="font-bold">{joint.form}</div>
          <div className="text-sm text-neutral-500">{joint.units.length} households · {joint.privacy}</div>
          <pre className="whitespace-pre-wrap font-sans text-sm bg-neutral-50 p-3 rounded-lg max-h-64 overflow-auto">{joint.text}</pre>
          <div className="flex gap-2"><CopyButton text={joint.text} /><a className="btn-ghost" href={joint.official_url} target="_blank">Open city complaint page</a></div>
        </div>
      )}
    </section>
  );
}

function Evidence({ c }: { c: any }) {
  return (
    <section className="space-y-3">
      <h2 className="h2 flex items-center gap-2"><ShieldCheck className="w-6 h-6 text-emerald-600" /> Evidence locker</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {c.evidence.map((e: any) => (
          <div key={e.evidence_id} className="card overflow-hidden">
            <img src={imgUrl(e.evidence_id)} className="w-full h-28 object-cover" />
            <div className="p-2 text-[10px] leading-tight text-neutral-500">
              <div>{new Date(e.captured_at).toLocaleString()}</div>
              <div className="font-mono truncate" title={e.sha256}>sha256 {e.sha256.slice(0, 16)}…</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Letter({ c, onChange }: { c: any; onChange: () => void }) {
  const [tone, setTone] = useState<string>(c.tone ?? "formal");
  const [text, setText] = useState<string>(c.letter_text);
  async function pick(t: string) { setTone(t); const r = await post(`/api/cases/${c.request_id}/letter`, { tone: t }); setText(r.letter_text); }
  return (
    <section className="card p-5 space-y-3">
      <h2 className="h2">Repair request letter</h2>
      <div>
        <input type="range" min={0} max={2} step={1} value={TONES.indexOf(tone as any)} onChange={(e) => pick(TONES[+e.target.value])} className="w-full accent-badger" />
        <div className="flex justify-between text-sm font-semibold">{TONES.map((t) => <span key={t} className={t === tone ? "text-badger" : "text-neutral-400"}>{TONE_LABEL[t]}</span>)}</div>
      </div>
      <pre className="whitespace-pre-wrap font-sans text-sm bg-neutral-50 rounded-xl p-3 max-h-80 overflow-auto">{text}</pre>
      <div className="flex flex-wrap gap-2">
        <CopyButton text={text} />
        <a className="btn-ghost" href={`/api/cases/${c.request_id}/letter.pdf`}>PDF</a>
        {c.sent_at ? <span className="btn bg-emerald-50 text-emerald-700">Sent {new Date(c.sent_at).toLocaleString()}</span> :
          <button className="btn-dark" onClick={async () => { await post(`/api/cases/${c.request_id}/send`); onChange(); }}><Send className="w-4 h-4" /> Mark as sent</button>}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- simulated AI call
function speak(text: string, on: boolean) {
  if (!on || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1.05;
  window.speechSynthesis.speak(u);
}

function Call({ c, onDone }: { c: any; onDone: () => void }) {
  const [callId, setCallId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<any[]>([]);
  const [result, setResult] = useState<any>(c.calls?.[c.calls.length - 1] ?? null);
  const [input, setInput] = useState("");
  const [voice, setVoice] = useState(true);
  const [listening, setListening] = useState(false);
  const [script, setScript] = useState<string[]>([]);
  const [scriptIdx, setScriptIdx] = useState(0);
  const [err, setErr] = useState<string | null>(null);
  const [sending, setSending] = useState(false);  // one landlord line at a time (double-clicks used to hit a closed call)
  const inFlight = useRef(false);  // synchronous guard: state updates land after the click handler returns
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { get("/api/calls/demo-script").then((r) => setScript(r.lines)).catch(() => setScript([])); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [transcript]);

  async function start() {
    setResult(null); setScriptIdx(0); setErr(null);
    try {
      const r = await post(`/api/cases/${c.request_id}/call/start`);
      setCallId(r.call_id); setTranscript(r.transcript);
      speak(r.transcript[0].text, voice);
    } catch (e: any) { setErr(`Couldn't start the call: ${e.message}`); }
  }
  async function say(text: string): Promise<boolean> {
    if (!callId || !text.trim() || inFlight.current) return false;
    inFlight.current = true;
    setSending(true); setInput(""); setErr(null);
    setTranscript((t) => [...t, { speaker: "landlord", text }]);
    try {
      const r = await post(`/api/calls/${callId}/say`, { text });
      setTranscript(r.transcript);
      if (r.reply) speak(r.reply, voice);
      if (r.done) { setResult(r.result); setCallId(null); onDone(); }
      return true;
    } catch (e: any) { setErr(`The AI didn't get that: ${e.message}`); return false; }
    finally { inFlight.current = false; setSending(false); }
  }
  async function hangUp() {
    if (!callId) return;
    try {
      const r = await post(`/api/calls/${callId}/end`);
      setTranscript(r.transcript); setResult(r.result); setCallId(null); onDone();
    } catch (e: any) { setErr(e.message); setCallId(null); }
  }
  function listen() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setErr("Speech recognition isn't supported in this browser. Type the landlord's words instead."); return; }
    const rec = new SR();
    rec.lang = "en-US"; rec.interimResults = false;
    rec.onresult = (e: any) => say(e.results[0][0].transcript);
    rec.onend = () => setListening(false);
    setListening(true); rec.start();
  }

  return (
    <section className="card p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="h2 flex items-center gap-2"><Bot className="w-6 h-6 text-badger" /> AI calls your landlord</h2>
        <button className="text-neutral-500" onClick={() => setVoice(!voice)} title="Toggle voice">{voice ? <Volume2 /> : <VolumeX />}</button>
      </div>
      <p className="text-sm text-neutral-500">Simulated call: a teammate plays the landlord. The AI says up front that it's an AI acting for you. It never threatens and never claims to be a lawyer or the city.</p>
      {!callId && <button className="btn-primary text-lg" onClick={start}><Phone className="w-5 h-5" /> {transcript.length ? "Call again" : "Call landlord"}</button>}
      {transcript.length > 0 && (
        <div className="bg-neutral-50 rounded-xl p-3 space-y-2 max-h-80 overflow-auto">
          {transcript.map((t, i) => (
            <div key={i} className={`flex ${t.speaker === "ai" ? "" : "justify-end"}`}>
              <div className={`rounded-2xl px-3 py-2 max-w-[85%] ${t.speaker === "ai" ? "bg-white border" : "bg-ink text-white"}`}>
                <div className="text-[10px] font-bold uppercase opacity-60">{t.speaker === "ai" ? "Tenant's AI" : "Landlord"}</div>
                {t.text}
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>
      )}
      {callId && (
        <div className="space-y-2">
          <div className="flex gap-2">
            <input className="input" value={input} placeholder={sending ? "AI is replying…" : "Landlord says…"} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && say(input)} />
            <button className={`btn-ghost ${listening ? "ring-2 ring-badger" : ""}`} onClick={listen} title="Speak"><Mic className="w-5 h-5" /></button>
            <button className="btn-dark" disabled={sending} onClick={() => say(input)}>Say</button>
          </div>
          <div className="flex gap-2">
            {script[scriptIdx] && (
              <button className="btn-ghost text-sm flex-1 justify-start truncate" disabled={sending}
                onClick={async () => { const line = script[scriptIdx]; if (await say(line)) setScriptIdx((i) => i + 1); }}>
                Demo line: “{script[scriptIdx]}”
              </button>
            )}
            <button className="btn-ghost text-red-700" onClick={hangUp}><PhoneOff className="w-4 h-4" /> Hang up</button>
          </div>
        </div>
      )}
      <ErrorBox error={err} />
      {result && !callId && (
        <div className={`rounded-xl p-3 ${result.commitment_date ? "bg-emerald-50 text-emerald-900" : "bg-amber-50 text-amber-900"}`}>
          {result.commitment_date ? (
            <><div className="font-bold">Commitment captured: {new Date(result.commitment_date).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}</div>
              <div className="text-sm">“{result.commitment_text}” · landlord tone: {result.landlord_tone}. The follow-up clock has started.</div>
              <div className="text-xs opacity-75 mt-1">
                Date taken from the landlord's words and read back on the call.
                {result.source === "live" ? " Tone and summary extracted live by the Databricks chat model." : " Tone estimated by FixIt's rules (no live model used)."}
              </div></>
          ) : <div className="font-bold">No repair date given. A FixIt default deadline was set. Follow up in writing.</div>}
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------- deadline + escalation
function Deadline({ c, onChange }: { c: any; onChange: (c: any) => void }) {
  const [err, setErr] = useState<string | null>(null);
  const act = (path: string, body?: unknown) => async () => {
    setErr(null);
    try { onChange(await post(`/api/cases/${c.request_id}/${path}`, body)); } catch (e: any) { setErr(e.message); }
  };
  const d = c.deadline;
  if (!d) return (
    <section className="card p-5"><h2 className="h2 flex items-center gap-2"><Clock className="w-6 h-6" /> Deadline</h2>
      <p className="text-neutral-500 mt-2">Starts when you send the letter or the landlord commits to a date on the call.</p></section>
  );
  const tl = d.time_left;
  const overdue = tl.overdue || d.status === "missed" || d.status === "escalated";
  return (
    <section className="card p-5 space-y-3">
      <h2 className="h2 flex items-center gap-2"><Clock className="w-6 h-6" /> Follow-up deadline</h2>
      <div className={`rounded-xl p-4 ${d.status === "met" ? "bg-emerald-600 text-white" : overdue ? "bg-red-600 text-white" : "bg-neutral-900 text-white"}`}>
        <div className="text-sm uppercase font-bold opacity-80">{d.status === "met" ? "Fixed" : overdue ? "Promised date passed" : "Time left"}</div>
        <div className="text-4xl font-extrabold tabular-nums">
          {d.status === "met" ? "✓" : `${overdue ? "−" : ""}${tl.days}d ${tl.hours}h ${tl.minutes}m`}
        </div>
        <div className="text-sm opacity-80">Due {new Date(d.due_date).toLocaleString(undefined, { weekday: "long", month: "short", day: "numeric", hour: "numeric" })}
          {d.sim_offset_days ? ` · simulated +${d.sim_offset_days} days` : ""}</div>
      </div>
      {d.status !== "met" && d.status !== "escalated" && (
        <div className="flex flex-wrap gap-2">
          <button className="btn-ghost" onClick={act("simulate", { days: 8 })}><FastForward className="w-4 h-4" /> Simulate +8 days</button>
          <button className="btn-ghost" onClick={act("fixed")}>Landlord fixed it</button>
          {overdue && <button className="btn-primary" onClick={act("escalate")}>Prepare city complaint draft →</button>}
        </div>
      )}
      <ErrorBox error={err} />
      <p className="text-xs text-neutral-500">A FixIt reminder, not a legal deadline: it's the landlord's promised date, or a FixIt default (7 days routine, 48h urgent, 24h emergency). Only the City sets official repair deadlines, in an Official Notice after an inspection.</p>
      {c.complaint && <Complaint p={c.complaint} />}
    </section>
  );
}

function Complaint({ p }: { p: any }) {
  const text = Object.entries(p.fields).map(([k, v]) => `${k}: ${v}`).join("\n");
  return (
    <div className="border-2 border-badger rounded-xl p-4 space-y-3">
      <div className="font-extrabold text-lg">{p.form}</div>
      <div className="rounded-lg bg-amber-50 text-amber-900 text-sm p-2">{p.submit_note}</div>
      <dl className="text-sm space-y-1.5">
        {Object.entries(p.fields).map(([k, v]) => (
          <div key={k} className="grid grid-cols-3 gap-2"><dt className="font-semibold text-neutral-500">{k}</dt><dd className="col-span-2 whitespace-pre-wrap">{String(v)}</dd></div>
        ))}
      </dl>
      <div className="flex flex-wrap gap-2"><CopyButton text={text} label="Copy fields" /><a className="btn-primary" href={p.official_url} target="_blank">Open official city page</a></div>
      <div>
        <div className="font-bold">Next steps</div>
        <ul className="list-disc pl-5 text-sm space-y-1">{p.next_steps.map((s: string) => <li key={s}>{s}</li>)}</ul>
        <div className="flex flex-wrap gap-3 text-sm mt-2">
          <a className="text-badger underline" href={p.links.rent_abatement} target="_blank">Rent abatement (city)</a>
          {p.links.retaliation && <a className="text-badger underline" href={p.links.retaliation} target="_blank">Retaliation (city)</a>}
          {p.links.complaint_process && <a className="text-badger underline" href={p.links.complaint_process} target="_blank">Complaint process (city)</a>}
          <a className="text-badger underline" href={p.links.tenant_resource_center} target="_blank">Tenant Resource Center</a>
        </div>
      </div>
    </div>
  );
}
