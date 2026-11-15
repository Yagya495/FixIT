import { useEffect, useRef, useState } from "react";
import { Phone, PhoneOff, RefreshCw } from "lucide-react";
import { get } from "../api";
import { ErrorBox } from "./ui";

type CallRecord = { attempt_id: string; provider_call_id?: string; status: string; created_at: string;
  transcript: { speaker: string; text: string }[]; outcome_json: any; disconnection_reason?: string; resumable?: boolean };
// "rejected": Retell refused the create request, so no call exists.
const terminal = new Set(["ended", "error", "not_connected", "rejected"]);

export function RetellCall({ caseId }: { caseId: string }) {
  const [enabled, setEnabled] = useState(false);
  const [token, setToken] = useState("");
  const [unlocked, setUnlocked] = useState(false);
  const [records, setRecords] = useState<CallRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);
  const polls = useRef(0);
  const [attempt, setAttempt] = useState(() => crypto.randomUUID());
  const [number, setNumber] = useState("");
  const [tenant, setTenant] = useState("");
  const [manager, setManager] = useState("");
  const [previous, setPrevious] = useState("");
  const [timeline, setTimeline] = useState("");
  const [consent, setConsent] = useState([false, false, false, false]);
  const [reconcileId, setReconcileId] = useState("");
  useEffect(() => { get("/api/retell/config").then(r => setEnabled(r.enabled)).catch(e => setError(e.message)); }, []);

  async function api(path: string, body?: unknown) {
    const r = await fetch(`/api/retell${path}`, { method: body === undefined ? "GET" : "POST",
      headers: { "Content-Type": "application/json", "X-Fixit-Call-Token": token },
      body: body === undefined ? undefined : JSON.stringify(body) });
    // A sign-in redirect or proxy error can return HTML; never show it raw.
    const value = await r.json().catch(() => null);
    if (!r.ok || value === null) throw new Error(typeof value?.detail === "string" ? value.detail
      : r.ok ? "Unexpected response from the server. Reload the page and sign in again." : "Check the call details and required consent.");
    return value;
  }
  async function load() { setRecords(await api(`/cases/${caseId}/calls`)); }
  async function action(fn: () => Promise<void>) {
    if (inFlight.current) return;
    inFlight.current = true; setBusy(true); setError(null);
    try { await fn(); } catch (e: any) { setError(e.message); }
    finally { inFlight.current = false; setBusy(false); }
  }
  const latest = records[records.length - 1];
  async function refresh(record: CallRecord, id?: string) {
    const updated = await api(`/calls/${record.attempt_id}/refresh`, id ? { provider_call_id: id } : {});
    setRecords(old => old.map(r => r.attempt_id === updated.attempt_id ? updated : r));
  }
  // Bounded polling while the panel is open. Stop after errors; manual Refresh can resume.
  useEffect(() => {
    if (!unlocked || !latest?.provider_call_id || error || polls.current >= 60 ||
        (terminal.has(latest.status) && (latest.outcome_json?.analyzed || latest.status !== "ended"))) return;
    const timer = window.setTimeout(() => { polls.current += 1; void action(() => refresh(latest)); }, 10000);
    return () => window.clearTimeout(timer);
  }, [unlocked, latest, error]);

  async function start() {
    polls.current = 0;
    try {
      const record = await api(`/cases/${caseId}/calls`, {
        attempt_id: attempt, to_number: number, tenant_name: tenant, management_company: manager,
        previous_requests: previous, preferred_timeline: timeline, tenant_authorized: consent[0],
        recipient_consented: consent[1], recording_consented: consent[2], case_reviewed: consent[3], test_call: true,
      });
      setRecords(old => [...old.filter(r => r.attempt_id !== record.attempt_id), record]);
      setConsent([false, false, false, false]);
    } catch (e) {
      // Retrieve a persisted uncertain attempt without ever issuing a second create request.
      await load().catch(() => {});
      throw e;
    }
  }
  const pending = latest && (!terminal.has(latest.status) || (latest.status === "ended" && !latest.outcome_json?.analyzed));
  const blocked = records.some(r => r.outcome_json?.do_not_call);
  const usedAttempt = records.some(r => r.attempt_id === attempt);
  const outcome = latest?.outcome_json;

  return <section className="card p-5 space-y-3">
    <h2 className="h2 flex items-center gap-2"><Phone className="w-5 h-5 text-badger" /> Retell phone call</h2>
    <p className="text-sm text-neutral-600">Place a real phone call to a consenting teammate playing the landlord.
      The AI identifies this as a test. Calls are recorded and transcribed.</p>
    {!enabled && <p className="rounded-lg bg-amber-50 p-3 text-sm">Phone calling is disabled. An operator must finish Retell setup before calls can be placed. The simulated call above is available.</p>}
    <label className="block text-sm font-semibold">Operator access token
      <input className="input mt-1" type="password" autoComplete="off" value={token} disabled={unlocked}
        onChange={e => setToken(e.target.value)} placeholder="Provided by the app operator" />
    </label>
    {!unlocked ? <button className="btn-ghost" disabled={busy || !token} onClick={() => action(async () => {
      await load(); setUnlocked(true);
    })}>Open call records</button> : <>
      <button className="btn-ghost" disabled={busy} onClick={() => { setUnlocked(false); setToken(""); setRecords([]); }}>Lock call panel</button>
      <div className="grid sm:grid-cols-2 gap-3">
        <label className="text-sm">Tenant name (demo)<input className="input" maxLength={120} value={tenant} onChange={e => setTenant(e.target.value)} /></label>
        <label className="text-sm">Consenting recipient's phone<input className="input" type="tel" placeholder="+16085550123" value={number} onChange={e => setNumber(e.target.value)} /></label>
      </div>
      <label className="block text-sm">Management company (optional)<input className="input" maxLength={200} value={manager} onChange={e => setManager(e.target.value)} /></label>
      <label className="block text-sm">Previous requests actually made (optional)<textarea className="input" maxLength={2000} value={previous} onChange={e => setPrevious(e.target.value)} /></label>
      <label className="block text-sm">Preferred timeline (optional)<input className="input" maxLength={300} value={timeline} onChange={e => setTimeline(e.target.value)} /></label>
      <fieldset className="space-y-2 text-sm" disabled={busy}>
        <legend className="font-semibold mb-2">Confirm before each call</legend>
        {[
          "The tenant has explicitly authorized this call on their behalf.",
          "The recipient has given all required consent to receive this AI test call.",
          "All participants have authorized recording and transcription by Retell (retained there for 30 days); the transcript and outcome will also be saved in FixIt.",
          "I reviewed this demo case's issues and evidence. The recipient is a consenting teammate or judge role-playing the landlord.",
        ].map((label, i) => <label key={i} className="flex items-start gap-2"><input type="checkbox" className="mt-1" checked={consent[i]}
          onChange={e => setConsent(old => old.map((v, j) => j === i ? e.target.checked : v))} /><span>{label}</span></label>)}
      </fieldset>
      {blocked && <p className="text-red-700 text-sm">A recipient requested no more AI calls. Further calls to that number are blocked.</p>}
      {usedAttempt && !pending && <button className="btn-ghost" disabled={busy} onClick={() => { setAttempt(crypto.randomUUID()); setConsent([false, false, false, false]); }}>Prepare another authorized call</button>}
      <button className="btn-primary" disabled={!enabled || busy || !!pending || usedAttempt || !consent.every(Boolean) || !tenant.trim() || !/^\+[1-9][0-9]{7,14}$/.test(number)}
        onClick={() => action(start)}><Phone className="w-4 h-4" /> {busy ? "Working…" : "Place authorized test call"}</button>
      {latest && <div className="rounded-xl bg-neutral-50 p-3 space-y-3" aria-live="polite">
        <div className="font-semibold">Call status: {latest.status.replace(/_/g, " ")}</div>
        <p className="text-xs break-all">Attempt: {latest.attempt_id}</p>
        <div className="flex flex-wrap gap-2">
          <button className="btn-ghost" disabled={busy} onClick={() => action(() => refresh(latest))}><RefreshCw className="w-4 h-4" /> Refresh outcome</button>
          {latest.provider_call_id && !terminal.has(latest.status) && <button className="btn-ghost" disabled={busy} onClick={() => action(async () => {
            await api(`/calls/${latest.attempt_id}/stop`, {}); await refresh(latest);
          })}><PhoneOff className="w-4 h-4" /> End call</button>}
        </div>
        {latest.status === "rejected" && <p className="text-sm">Retell rejected this request, so no call was placed.
          {latest.outcome_json?.do_not_call ? " The number appears to be on Retell's do-not-call list; further calls are blocked." : " Check the Retell dashboard before preparing another call."}</p>}
        {!latest.provider_call_id && latest.status !== "rejected" && <div className="space-y-2 text-sm">
          <p>Do not redial. Creation of this call is uncertain.</p>
          {latest.resumable && <>
            <p>Retell deduplicates a repeated request with the same attempt ID for one hour, so resuming returns the existing call instead of placing a second one.</p>
            <button className="btn-ghost" disabled={busy} onClick={() => action(async () => {
              const updated = await api(`/calls/${latest.attempt_id}/resume`, {});
              setRecords(old => old.map(r => r.attempt_id === updated.attempt_id ? updated : r));
            })}>Resume this attempt (same ID)</button>
          </>}
          <p>Or find this attempt ID in Retell's call metadata and enter its call ID.</p>
          <label className="block">Retell call ID<input className="input" value={reconcileId} onChange={e => setReconcileId(e.target.value)} /></label>
          <button className="btn-ghost" disabled={busy || !reconcileId} onClick={() => action(() => refresh(latest, reconcileId))}>Reconcile existing call</button>
        </div>}
        {outcome?.analyzed ? <>
          <p className="text-xs text-neutral-500">AI summary from Retell. Review against the transcript; no repair deadline was set automatically.</p>
          <p>{outcome.summary}</p>
          <dl className="text-sm space-y-1">
            <div><dt className="font-semibold">Acknowledgement</dt><dd>{outcome.acknowledgement}</dd></div>
            <div><dt className="font-semibold">Appointment / commitment</dt><dd>{outcome.appointment_kind?.replace(/_/g, " ")} · {outcome.appointment_date || "No specific date"}</dd></div>
            {outcome.date_as_spoken && <div><dt className="font-semibold">Recipient's words</dt><dd>“{outcome.date_as_spoken}”</dd></div>}
            <div><dt className="font-semibold">Coordinator</dt><dd>{outcome.coordinator || "Not supplied"}</dd></div>
            <div><dt className="font-semibold">Information requested</dt><dd>{outcome.tenant_information_requested || "None captured"}</dd></div>
            <div><dt className="font-semibold">Next steps</dt><dd>{outcome.next_steps || "None captured"}</dd></div>
            <div><dt className="font-semibold">Follow-up needed</dt><dd>{outcome.follow_up_needed ? "Yes" : "No, according to the call analysis"}</dd></div>
          </dl>
        </> : <p className="text-sm">{terminal.has(latest.status) ? "No analyzed outcome yet. Refresh after Retell finishes processing." : "The transcript and outcome will appear when available."}</p>}
        {latest.disconnection_reason && <p className="text-xs">Call ended: {latest.disconnection_reason.replace(/_/g, " ")}</p>}
        <Transcript record={latest} />
      </div>}
      {records.length > 1 && <details className="text-sm"><summary>Earlier calls ({records.length - 1})</summary>
        {records.slice(0, -1).map(r => <div key={r.attempt_id} className="border-t py-2">
          <p>{r.created_at} · {r.status}</p><p>{r.outcome_json?.summary}</p><Transcript record={r} />
        </div>)}
      </details>}
    </>}
    <ErrorBox error={error} />
  </section>;
}

function Transcript({ record }: { record: CallRecord }) {
  return record.transcript?.length ? <details><summary className="cursor-pointer font-semibold">Transcript</summary>
    <div className="max-h-72 overflow-y-auto space-y-2 mt-2 text-sm">
      {record.transcript.map((t, i) => <p key={i}><b>{t.speaker === "ai" ? "FixIT AI" : "Recipient"}:</b> {t.text}</p>)}
    </div>
  </details> : null;
}
