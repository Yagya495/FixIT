import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, ExternalLink, Loader2, Scale } from "lucide-react";
import type { Violation } from "../api";
import { imgUrl } from "../api";

export const DISCLAIMER =
  "FixIt is not a lawyer and this is not legal advice. For help, contact the Tenant Resource Center (608-257-0006) or City of Madison Building Inspection (608-266-4551).";

export function Disclaimer({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`flex gap-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 ${compact ? "p-2 text-xs" : "p-3 text-sm"}`}>
      <Scale className="w-4 h-4 shrink-0 mt-0.5" />
      <span>{DISCLAIMER}</span>
    </div>
  );
}

export function DemoBadge({ label = "Synthetic demo data" }: { label?: string }) {
  return <span className="chip bg-violet-100 text-violet-800" title="Synthetic demo data: fictional buildings, owners, neighbors and complaint histories. No real tenants, owners or City records.">{label}</span>;
}

/** One-line explanation of what on this screen is synthetic (shown next to demo data). */
export function SyntheticNote({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-violet-800 bg-violet-50 rounded-lg px-3 py-2">{children}</p>;
}

const SEV: Record<string, string> = {
  emergency: "bg-red-600 text-white",
  urgent: "bg-orange-100 text-orange-800",
  routine: "bg-sky-100 text-sky-800",
};
export function SeverityChip({ s }: { s: string }) {
  return <span className={`chip ${SEV[s] ?? "bg-neutral-100"}`}>{s}</span>;
}

const GRADE: Record<string, string> = {
  A: "bg-emerald-600", B: "bg-lime-600", C: "bg-amber-500", D: "bg-orange-600", F: "bg-red-700",
};
export function GradeBadge({ g, size = "md" }: { g?: string | null; size?: "sm" | "md" | "lg" }) {
  const dim = size === "lg" ? "w-20 h-20 text-5xl" : size === "sm" ? "w-7 h-7 text-sm" : "w-11 h-11 text-2xl";
  return (
    <div title="Fictional grade computed from synthetic demo data (not a real rating of a real landlord)"
      className={`${dim} ${GRADE[g ?? ""] ?? "bg-neutral-400"} rounded-xl text-white font-extrabold grid place-items-center shrink-0`}>
      {g ?? "?"}
    </div>
  );
}

/** Animated "AI is working" steps. `done` flips everything to complete. */
export function Progress({ steps, done, intervalMs = 900 }: { steps: string[]; done: boolean; intervalMs?: number }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (done) { setI(steps.length); return; }
    setI(0);
    const t = setInterval(() => setI((x) => Math.min(x + 1, steps.length - 1)), intervalMs);
    return () => clearInterval(t);
  }, [done, steps.length, intervalMs]);
  return (
    <ol className="space-y-2">
      {steps.map((s, k) => (
        <li key={s} className={`flex items-center gap-2 text-base ${k > i ? "text-neutral-400" : ""}`}>
          {k < i || done ? <CheckCircle2 className="w-5 h-5 text-emerald-600" /> :
            k === i ? <Loader2 className="w-5 h-5 animate-spin text-badger" /> : <span className="w-5 h-5 rounded-full border-2 border-neutral-300" />}
          {s}
        </li>
      ))}
    </ol>
  );
}

export function ViolationCard({ v, open: initOpen = false }: { v: Violation; open?: boolean }) {
  const [open, setOpen] = useState(initOpen);
  const [allObs, setAllObs] = useState(false);
  // A video can show the same problem in many consecutive frames: one finding, every frame kept, first few shown.
  const OBS_SHOWN = 4;
  const obs = v.observations ?? [];
  const shownObs = allObs ? obs : obs.slice(0, OBS_SHOWN);
  return (
    <div className={`card overflow-hidden ${v.certain ? "" : "border-dashed"}`}>
      <button onClick={() => setOpen(!open)} className="w-full text-left p-4 flex gap-3 items-start">
        {v.evidence_ids?.[0] ? (
          <img src={imgUrl(v.evidence_ids[0])} alt="" className="w-16 h-16 rounded-lg object-cover shrink-0 bg-neutral-100" />
        ) : (
          <div className="w-16 h-16 rounded-lg bg-neutral-100 grid place-items-center shrink-0">
            <AlertTriangle className="w-6 h-6 text-neutral-400" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-bold text-lg leading-tight">{v.certain ? v.name : v.name}</span>
            <SeverityChip s={v.severity} />
          </div>
          {!v.certain && <div className="text-sm text-amber-700 font-semibold">Possible issue — verify in person</div>}
          <div className="text-sm text-neutral-500 mt-0.5">
            {v.tenant_reported && !v.evidence_ids?.length ? "Reported by you" : `Confidence ${(v.confidence * 100).toFixed(0)}%`}
            {" · "}{v.code_sections[0]?.title ?? "MGO Ch. 27"}
          </div>
        </div>
        <span className="text-neutral-400 text-sm">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-neutral-100 pt-3">
          {obs.length ? (
            <ul className="space-y-2">
              {obs.length > 1 && <li className="text-xs text-neutral-500">Seen or reported {obs.length} times in this scan:</li>}
              {shownObs.map((o, k) => (
                <li key={k} className="flex gap-2 items-start text-sm">
                  {o.evidence_id ? <img src={imgUrl(o.evidence_id)} alt="" className="w-10 h-10 rounded object-cover shrink-0 bg-neutral-100" />
                    : <div className="w-10 h-10 rounded bg-neutral-100 shrink-0" />}
                  <div className="min-w-0">
                    <span className="text-xs font-semibold uppercase text-neutral-500">{o.basis_text}{o.evidence_id ? ` · ${o.evidence_id}` : ""}</span>
                    {o.note && <p className="italic text-neutral-600 break-words">“{o.note}”</p>}
                  </div>
                </li>
              ))}
              {obs.length > OBS_SHOWN && (
                <li><button className="text-sm text-badger font-semibold" onClick={() => setAllObs(!allObs)}>
                  {allObs ? "Show fewer" : `Show ${obs.length - OBS_SHOWN} more`}</button></li>
              )}
            </ul>
          ) : v.notes?.length > 0 && <p className="text-sm italic text-neutral-600">“{v.notes[0]}”</p>}
          {v.category === "SMOKE_CO" && (
            <p className="text-xs text-neutral-500">A photo can't show that an alarm is missing from the unit or whether it works. Test alarms in person.</p>
          )}
          {v.code_sections.map((s) => (
            <blockquote key={s.section_id} className="border-l-4 border-badger bg-badger-light/50 rounded-r-lg p-3">
              <div className="text-xs font-bold uppercase text-badger">
                {s.verified ? `Possibly relevant: MGO § ${s.section_id}`
                  : s.section_id.startsWith("PENDING-") ? "Legal source not yet verified"
                  : "MGO Chapter 27 · section number pending verification"}
              </div>
              <div className="font-semibold">{s.title}</div>
              {s.verified ? (
                <div className="text-sm text-neutral-700">
                  “{s.snippet}”
                  <div className="text-xs text-neutral-500 mt-1">Official ordinance text, human-reviewed. Whether this condition violates it is for a City of Madison inspector to decide.</div>
                </div>
              ) : s.official_text ? (
                <div className="text-sm text-neutral-700">
                  <span className="text-xs font-semibold text-neutral-500">Text from the official Ch. 27 document{s.page ? ` (p. ${s.page})` : ""}; this match hasn't been human-reviewed: </span>“{s.snippet}”
                </div>
              ) : (
                <div className="text-sm text-neutral-700">
                  <span className="text-xs font-semibold text-neutral-500">Plain-language summary, not official text: </span>{s.snippet}
                </div>
              )}
              <a href={s.url} target="_blank" className="text-xs text-badger inline-flex items-center gap-1 mt-1">
                Official text <ExternalLink className="w-3 h-3" />
              </a>
            </blockquote>
          ))}
          <div><span className="label">What it means</span><p>{v.explanation}</p></div>
          <div><span className="label">What to ask for</span><p>{v.remedy}</p></div>
        </div>
      )}
    </div>
  );
}

/** Says truthfully where an AI result came from (API `source`). Never implies a live model when it wasn't one. */
export function AiSource({ source, model }: { source?: string; model?: string | null }) {
  const text: Record<string, string> = {
    live: `Analyzed live just now by ${model ? model.replace(/^databricks-/, "") : "the vision model"} on Databricks Model Serving.`,
    cache: "Saved result from an earlier live analysis of this exact photo (Demo Mode).",
    fallback: "Demo script: scripted example detections, shown because the live model wasn't used (Demo Mode).",
    partial: `Partly analyzed live by ${model ? model.replace(/^databricks-/, "") : "the vision model"}: some frames weren't analyzed because the model didn't respond.`,
  };
  if (!source || !text[source]) return null;
  return (
    <div className={`text-xs rounded-lg px-2 py-1 inline-block ${source === "fallback" ? "bg-violet-50 text-violet-800" : "bg-neutral-100 text-neutral-600"}`}>
      {text[source]}
    </div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return <div className="flex items-center gap-2 text-neutral-500"><Loader2 className="w-5 h-5 animate-spin" />{label}</div>;
}

export function ErrorBox({ error }: { error: string | null }) {
  if (!error) return null;
  return <div className="rounded-xl bg-red-50 border border-red-200 text-red-800 p-3 text-sm">{error}</div>;
}

export function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="card p-4">
      <div className="text-sm text-neutral-500 font-semibold">{label}</div>
      <div className="text-3xl font-extrabold">{value}</div>
      {sub && <div className="text-xs text-neutral-500">{sub}</div>}
    </div>
  );
}

export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [ok, setOk] = useState(false);
  return (
    <button className="btn-ghost" onClick={() => { navigator.clipboard?.writeText(text); setOk(true); setTimeout(() => setOk(false), 1500); }}>
      {ok ? "Copied!" : label}
    </button>
  );
}
