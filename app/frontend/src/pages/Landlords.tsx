import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { get } from "../api";
import { DemoBadge, GradeBadge, Spinner } from "../components/ui";

export default function Landlords() {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<any[] | null>(null);
  const [addr, setAddr] = useState<any[]>([]);
  const [meta, setMeta] = useState<any>(null);
  useEffect(() => { get("/api/meta").then(setMeta); }, []);
  useEffect(() => {
    const t = setTimeout(() => {
      get(`/api/owners?q=${encodeURIComponent(q)}&limit=30`).then(setRows);
      if (/^\d+\s+\w/.test(q)) get(`/api/properties/search?q=${encodeURIComponent(q)}`).then(setAddr); else setAddr([]);
    }, 200);
    return () => clearTimeout(t);
  }, [q]);
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3"><h1 className="h1">Landlord report cards</h1><DemoBadge /></div>
      <div className="relative">
        <Search className="absolute left-3 top-3 w-5 h-5 text-neutral-400" />
        <input className="input pl-10 text-lg" placeholder="Search owner, management company, or address (e.g. 1234 Demo St)" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {addr.length > 0 && (
        <div className="card divide-y">{addr.map((a) => (
          <Link key={a.property_id} to={`/buildings/${a.property_id}`} className="p-3 flex justify-between hover:bg-neutral-50">
            <span className="font-semibold">{a.address_norm}</span><span className="text-sm text-neutral-500">{a.neighborhood} · {a.owner_name}</span>
          </Link>))}
        </div>
      )}
      {meta && (
        <details className="card p-4">
          <summary className="font-bold cursor-pointer">How grades work</summary>
          <p className="mt-2 font-mono text-sm">{meta.grade_explainer.formula}</p>
          <p className="text-sm mt-1">{meta.grade_explainer.cuts}</p>
          <p className="text-sm text-neutral-500 mt-1">{meta.grade_explainer.notes}</p>
        </details>
      )}
      {!rows ? <Spinner /> : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-left text-neutral-500"><tr>
              <th className="p-3">Grade</th><th className="p-3">Owner</th><th className="p-3">Buildings</th><th className="p-3">Open issues</th>
              <th className="p-3">Issues (12 mo)</th><th className="p-3">Median days to fix</th><th className="p-3">Fixed ≤30d</th></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.owner_id} className="border-t hover:bg-neutral-50">
                <td className="p-3"><GradeBadge g={r.grade} size="sm" /></td>
                <td className="p-3"><Link to={`/owners/${r.owner_id}`} className="font-semibold hover:underline">{r.name}</Link>
                  {r.repeat_offender && <span className="chip bg-red-100 text-red-800 ml-2">repeat offender</span>}</td>
                <td className="p-3">{r.buildings}</td><td className="p-3 font-bold">{r.open_issues}</td><td className="p-3">{r.issues_last_12mo}</td>
                <td className="p-3">{r.median_days_to_fix ?? "—"}</td><td className="p-3">{r.pct_fixed_within_30d != null ? `${Math.round(r.pct_fixed_within_30d * 100)}%` : "—"}</td>
              </tr>))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}
