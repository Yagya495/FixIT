import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../api";
import { Spinner } from "../components/ui";

export default function Cases() {
  const [rows, setRows] = useState<any[] | null>(null);
  useEffect(() => { get("/api/cases").then(setRows); }, []);
  if (!rows) return <Spinner label="Loading…" />;
  return (
    <div className="space-y-4">
      <h1 className="h1">My cases</h1>
      {rows.length === 0 && (
        <div className="card p-8 text-center space-y-3">
          <p className="text-neutral-600 text-lg">No cases yet.</p>
          <Link to="/scan" className="btn-primary">Scan my apartment</Link>
        </div>
      )}
      {rows.map((r) => (
        <Link key={r.request_id} to={`/cases/${r.request_id}`} className="card p-4 flex items-center justify-between hover:border-badger">
          <div>
            <div className="font-bold text-lg">{r.address}{r.unit ? `, Unit ${r.unit}` : ""}</div>
            <div className="text-sm text-neutral-500">Opened {new Date(r.created_at).toLocaleString()} · {r.sent_at ? "letter sent" : "letter not sent"}</div>
          </div>
          <span className="chip bg-neutral-100">{r.status ?? "draft"}</span>
        </Link>
      ))}
    </div>
  );
}
