import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { get } from "../api";
import { DemoBadge, GradeBadge, Spinner, Stat, SyntheticNote } from "../components/ui";

export default function Owner() {
  const { id } = useParams();
  const [o, setO] = useState<any>(null);
  useEffect(() => { get(`/api/owners/${id}`).then(setO); }, [id]);
  if (!o) return <Spinner label="Loading report card…" />;
  const s = o.scores;
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <GradeBadge g={s.grade} size="lg" />
        <div>
          <h1 className="h1">{o.name}</h1>
          <div className="text-neutral-600 flex items-center gap-2">{o.management_company} <DemoBadge />
            {o.repeat_offender && <span className="chip bg-red-100 text-red-800">repeat offender</span>}</div>
        </div>
      </div>
      <div>
        <SyntheticNote>Fictional owner. The grade and statistics are computed from simulated complaint records in FixIt's synthetic demo dataset.</SyntheticNote>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Open issues" value={s.open_issues} />
        <Stat label="Median days to fix" value={s.median_days_to_fix ?? "—"} />
        <Stat label="Fixed within 30 days" value={s.pct_fixed_within_30d != null ? `${Math.round(s.pct_fixed_within_30d * 100)}%` : "—"} />
        <Stat label="Issues per unit (12 mo)" value={s.issues_per_unit} sub={`${s.units} units · ${s.buildings} buildings`} />
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="card p-4">
          <h2 className="h2 mb-2">Issues by type</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={o.issues_by_type} layout="vertical" margin={{ left: 0, right: 12 }}>
              <XAxis type="number" allowDecimals={false} />
              <YAxis type="category" dataKey="violation_type" width={170} tick={{ fontSize: 11 }}
                tickFormatter={(t: string) => t.toLowerCase().replace(/_/g, " ").replace(/^\w/, (ch) => ch.toUpperCase())} />
              <Tooltip /><Bar dataKey="n" name="All reports" fill="#d4d4d4" /><Bar dataKey="open_n" name="Open" fill="#C5050C" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-4">
          <h2 className="h2 mb-2">Buildings</h2>
          <div className="divide-y">{o.buildings.map((b: any) => (
            <Link key={b.property_id} to={`/buildings/${b.property_id}`} className="py-2 flex justify-between hover:bg-neutral-50">
              <span><span className="font-semibold">{b.address_norm}</span> <span className="text-sm text-neutral-500">{b.neighborhood} · {b.units} units</span></span>
              <span className={`font-bold ${b.open_issues ? "text-badger" : "text-neutral-400"}`}>{b.open_issues} open</span>
            </Link>))}</div>
        </div>
      </div>
      <details className="card p-4"><summary className="font-bold cursor-pointer">How grades work</summary>
        <p className="mt-2 font-mono text-sm">{o.grade_explainer.formula}</p><p className="text-sm">{o.grade_explainer.cuts}</p>
        <p className="text-sm text-neutral-500">Score for this owner: {s.score}</p></details>
    </div>
  );
}
