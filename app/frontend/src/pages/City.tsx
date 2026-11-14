import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import { MessageSquareText, Sparkles } from "lucide-react";
import { get, post } from "../api";
import { DemoBadge, ErrorBox, Spinner } from "../components/ui";

const color = (n: number) => (n >= 6 ? "#9B0000" : n >= 3 ? "#C5050C" : n >= 1 ? "#F59E0B" : "#10B981");

export default function City() {
  const [pts, setPts] = useState<any[] | null>(null);
  const [onlyOpen, setOnlyOpen] = useState(true);
  useEffect(() => { get("/api/city/map").then(setPts); }, []);
  const shown = useMemo(() => (pts ?? []).filter((p) => !onlyOpen || p.open_issues > 0), [pts, onlyOpen]);
  const worst = useMemo(() => [...(pts ?? [])].sort((a, b) => b.open_issues - a.open_issues).slice(0, 8), [pts]);
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><h1 className="h1">City view</h1><DemoBadge /></div>
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-2">
          <div className="h-[460px]">
            {!pts ? <Spinner label="Loading map…" /> : (
              <MapContainer center={[43.074, -89.395]} zoom={13} className="h-full w-full">
                {/* CARTO basemaps now need an API key (tiles render "API KEY REQUIRED"); use OSM like the building page. */}
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap" />
                {shown.map((p) => (
                  <CircleMarker key={p.property_id} center={[p.lat, p.lon]} radius={3 + Math.min(10, p.open_issues * 1.5)}
                    pathOptions={{ color: color(p.open_issues), fillColor: color(p.open_issues), fillOpacity: 0.55, weight: 1 }}>
                    <Popup><b>{p.address_norm}</b><br />{p.neighborhood} · owner grade {p.grade ?? "?"}<br />{p.open_issues} open issues<br />
                      <a href={`/buildings/${p.property_id}`}>Building page →</a></Popup>
                  </CircleMarker>))}
              </MapContainer>
            )}
          </div>
          <label className="text-sm flex items-center gap-2"><input type="checkbox" checked={onlyOpen} onChange={(e) => setOnlyOpen(e.target.checked)} /> Only buildings with open issues</label>
        </div>
        <div className="card p-4">
          <h2 className="h2 mb-2">Where to inspect next</h2>
          <p className="text-xs text-neutral-500 mb-2">Ranked by open issues for now. The P1 risk model (MLflow) will add predicted winter risk.</p>
          <ol className="space-y-2">{worst.map((p, i) => (
            <li key={p.property_id}><Link to={`/buildings/${p.property_id}`} className="flex justify-between hover:bg-neutral-50 rounded p-1">
              <span><b>{i + 1}.</b> {p.address_norm} <span className="text-xs text-neutral-500">{p.neighborhood}</span></span>
              <span className="font-bold text-badger">{p.open_issues}</span></Link></li>))}</ol>
        </div>
      </div>
      <AskData />
    </div>
  );
}

// Say truthfully what produced each answer: never imply live Genie when it was a saved or prepared answer.
const SOURCE_NOTE: Record<string, string> = {
  genie: "Answered live by Databricks Genie.",
  cache: "Saved Databricks Genie answer (Genie didn't respond just now).",
  local: "Answered by FixIt's prepared SQL for this sample question (Genie not connected).",
};

function AskData() {
  const [qs, setQs] = useState<string[]>([]);
  const [q, setQ] = useState("");
  const [ans, setAns] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSql, setShowSql] = useState(false);
  useEffect(() => { get("/api/meta").then((m) => setQs(m.sample_questions)); }, []);
  async function ask(question: string) {
    setQ(question); setBusy(true); setError(null); setAns(null);
    try { setAns(await post("/api/genie/ask", { question })); } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  }
  return (
    <section className="card p-5 space-y-4">
      <h2 className="h2 flex items-center gap-2"><Sparkles className="w-6 h-6 text-badger" /> Ask the data <span className="text-sm font-normal text-neutral-500">· plain-English questions over the gold tables</span></h2>
      <div className="flex gap-2">
        <input className="input text-lg" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask(q)} placeholder="Which owners have the most open heat issues this month?" />
        <button className="btn-primary" onClick={() => ask(q)} disabled={!q || busy}><MessageSquareText className="w-5 h-5" /> Ask</button>
      </div>
      <div className="flex flex-wrap gap-2">{qs.map((s) => <button key={s} className="chip bg-neutral-100 hover:bg-badger-light normal-case text-sm font-medium tracking-normal py-1" onClick={() => ask(s)}>{s}</button>)}</div>
      {busy && <Spinner label="Writing SQL over the gold tables…" />}
      <ErrorBox error={error} />
      {ans && (
        <div className="space-y-2">
          <p className="text-lg">{ans.text}</p>
          {ans.rows.length > 0 && (
            <div className="overflow-x-auto border rounded-xl">
              <table className="w-full text-sm"><thead className="bg-neutral-50"><tr>{ans.columns.map((c: string) => <th key={c} className="p-2 text-left">{c}</th>)}</tr></thead>
                <tbody>{ans.rows.map((r: any, i: number) => <tr key={i} className="border-t">{ans.columns.map((c: string) => <td key={c} className="p-2">{String(r[c] ?? "")}</td>)}</tr>)}</tbody></table>
            </div>
          )}
          {SOURCE_NOTE[ans.source] && <p className="text-xs text-neutral-500">{SOURCE_NOTE[ans.source]}</p>}
          {ans.sql && <button className="text-sm text-badger" onClick={() => setShowSql(!showSql)}>{showSql ? "Hide" : "Show"} SQL</button>}
          {showSql && <pre className="text-xs bg-neutral-900 text-green-300 rounded-xl p-3 overflow-x-auto">{ans.sql}</pre>}
        </div>
      )}
    </section>
  );
}
