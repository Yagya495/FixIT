import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { MapContainer, Marker, TileLayer } from "react-leaflet";
import L from "leaflet";
import { get } from "../api";
import { DemoBadge, GradeBadge, SeverityChip, Spinner, Stat, SyntheticNote } from "../components/ui";

const pin = L.divIcon({ className: "", html: '<div style="width:18px;height:18px;border-radius:9px;background:#C5050C;border:3px solid white;box-shadow:0 1px 4px #0006"></div>' });

export default function Building() {
  const { id } = useParams();
  const [b, setB] = useState<any>(null);
  useEffect(() => { get(`/api/buildings/${id}`).then(setB); }, [id]);
  if (!b) return <Spinner label="Loading building…" />;
  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 text-neutral-500 font-semibold">{b.neighborhood} · built {b.year_built} · {b.units} units <DemoBadge /></div>
        <h1 className="h1">{b.address_norm}</h1>
        <SyntheticNote>Synthetic building with a simulated complaint history and a fictional owner grade (demo data, not City records).</SyntheticNote>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        <Link to={`/owners/${b.owner.owner_id}`} className="card p-4 flex items-center gap-3 hover:border-badger">
          <GradeBadge g={b.owner.grade} /><div><div className="font-bold">{b.owner.name}</div><div className="text-sm text-neutral-500">Owner report card →</div></div>
        </Link>
        <Stat label="Open issues" value={b.open_issues} />
        <Stat label="Total reports" value={b.timeline.length} />
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="h-72"><MapContainer center={[b.lat, b.lon]} zoom={15} className="h-full w-full" scrollWheelZoom={false}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap" />
          <Marker position={[b.lat, b.lon]} icon={pin} /></MapContainer></div>
        <div className="card p-4"><h2 className="h2 mb-2">Violation mix</h2>
          {b.category_mix.map((m: any) => (
            <div key={m.category} className="flex items-center gap-2 text-sm my-1">
              <span className="w-32 shrink-0">{m.category.replace("_", " ")}</span>
              <div className="h-4 bg-badger rounded" style={{ width: `${(m.n / b.category_mix[0].n) * 100}%` }} /><span>{m.n}</span>
            </div>))}
        </div>
      </div>
      <div className="card p-4">
        <h2 className="h2 mb-3">Timeline</h2>
        <ol className="relative border-l-2 border-neutral-200 ml-2 space-y-3">
          {b.timeline.map((r: any) => (
            <li key={r.report_id} className="ml-4">
              <span className={`absolute -left-[7px] w-3 h-3 rounded-full ${r.status === "fixed" ? "bg-emerald-500" : "bg-badger"}`} />
              <div className="flex flex-wrap items-center gap-2"><span className="font-semibold">{r.violation_type.replaceAll("_", " ").toLowerCase()}</span><SeverityChip s={r.severity} />
                <span className={`chip ${r.status === "fixed" ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}`}>{r.status}</span></div>
              <div className="text-sm text-neutral-500">Reported {r.reported_at.slice(0, 10)}{r.fixed_at ? ` · fixed ${r.fixed_at.slice(0, 10)} (${Math.round((+new Date(r.fixed_at) - +new Date(r.reported_at)) / 864e5)} days)` : ""}</div>
            </li>))}
        </ol>
      </div>
    </div>
  );
}
