import { useEffect, useState } from "react";
import { post } from "../api";

// Prototype (2026-11-14): tenant-entered building facts → which smoke/CO legal sources might be relevant.
// Nonpersistent: answers live only in this component's state (never saved, never sent anywhere but /api/alarm-rules).
// Never inferred from photos or the synthetic demo-building records. No legal deadline is shown (disabled server-side).

type Opt = [string, string];
const Q: { key: string; label: string; opts: Opt[]; for: ("smoke" | "co")[] }[] = [
  { key: "units", label: "Residential units in the building", opts: [["unknown", "Not sure"], ["1", "1"], ["2", "2"], ["3+", "3 or more"]], for: ["smoke", "co"] },
  { key: "built", label: "When was it built?", opts: [["unknown", "Not sure"], ["before_1980_06_01", "Before June 1, 1980"], ["1980_06_01_to_2008", "June 1, 1980 – 2008"], ["2009_or_later", "2009 or later"]], for: ["smoke", "co"] },
  { key: "owner_occupied", label: "Does the owner live in the building? (optional)", opts: [["unknown", "Not sure"], ["yes", "Yes"], ["no", "No"]], for: ["smoke"] },
  { key: "attached_garage", label: "Attached garage", opts: [["unknown", "Not sure"], ["yes", "Yes"], ["no", "No"]], for: ["co"] },
  { key: "fireplace", label: "Fireplace", opts: [["unknown", "Not sure"], ["yes", "Yes"], ["no", "No"]], for: ["co"] },
  { key: "fuel_burning_appliance", label: "Fuel-burning appliance (gas stove, gas water heater…)", opts: [["unknown", "Not sure"], ["yes", "Yes"], ["no", "No"]], for: ["co"] },
  { key: "fuel_forced_air_furnace", label: "Gas or oil forced-air furnace", opts: [["unknown", "Not sure"], ["yes", "Yes"], ["no", "No"]], for: ["co"] },
];
const CHIP: Record<string, string> = {
  conditions_met_unverified: "bg-amber-100 text-amber-900",
  may_apply: "bg-sky-100 text-sky-900",
  outside_stated_scope: "bg-neutral-200 text-neutral-700",
  not_evaluated: "bg-neutral-100 text-neutral-500",
};

export function AlarmRules({ types }: { types: ("smoke" | "co")[] }) {
  const [p, setP] = useState<Record<string, string>>({});
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState("");
  const key = JSON.stringify(p) + types.join(",");
  useEffect(() => {
    let live = true;
    post("/api/alarm-rules", { profile: p, alarm_types: types })
      .then((r) => live && (setRes(r), setErr("")))
      .catch((e) => live && setErr(String(e?.message ?? e)));
    return () => { live = false; };
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <section className="card p-4 space-y-3">
      <div>
        <h2 className="h2">Smoke and CO alarm rules: building details</h2>
        <p className="text-xs text-neutral-500">Optional, prototype. Your answers aren't saved and FixIt never guesses them from photos or demo data. Not legal advice; these sources aren't verified yet.</p>
      </div>
      <div className="grid sm:grid-cols-2 gap-2">
        {Q.filter((q) => q.for.some((t) => types.includes(t))).map((q) => (
          <label key={q.key} className="text-sm space-y-1 min-w-0">
            <span className="block text-neutral-600">{q.label}</span>
            <select className="w-full border rounded-lg px-2 py-1.5 bg-white" value={p[q.key] ?? "unknown"}
              onChange={(e) => setP({ ...p, [q.key]: e.target.value })}>
              {q.opts.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
            </select>
          </label>
        ))}
      </div>
      {err && <p className="text-sm text-red-700">Couldn't check the rules: {err}</p>}
      {res && types.map((t) => (
        <div key={t} className="space-y-2">
          <h3 className="font-bold">{t === "smoke" ? "Smoke alarms" : "Carbon monoxide alarms"}</h3>
          {res.alarms[t]?.map((s: any) => (
            <div key={s.source_id} className="border rounded-lg p-2 text-sm space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold">{s.source_id}</span>
                <span className="text-neutral-500">{s.kind}</span>
                <span className={`chip ${CHIP[s.status] ?? ""}`}>{s.status_text}</span>
              </div>
              {s.reasons.map((r: string) => <div key={r} className="text-neutral-700">{r}</div>)}
              {s.missing.length > 0 && <div className="text-neutral-600">Depends on: {s.missing.join(", ")}</div>}
              {s.unresolved.length > 0 && <div className="text-xs text-neutral-500">Unresolved: {s.unresolved.join(" ")}</div>}
            </div>
          ))}
        </div>
      ))}
      {res && (
        <div className="text-xs text-neutral-500 space-y-1">
          <p>{res.governing_rule_note}</p>
          <p>{res.deadline.reason}</p>
          <p>FixIt's own follow-up reminder (the Deadline card on this page) is separate and is not a legal deadline.</p>
        </div>
      )}
    </section>
  );
}
