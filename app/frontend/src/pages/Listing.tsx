import { useState } from "react";
import { Link } from "react-router-dom";
import { Ban, CircleHelp, ThumbsUp, Upload } from "lucide-react";
import { postForm, sha256Hex, toJpeg, imgUrl, type Violation } from "../api";
import { AiSource, CopyButton, DemoBadge, Disclaimer, ErrorBox, GradeBadge, Progress, SyntheticNote, ViolationCard } from "../components/ui";

const STEPS = ["Uploading listing photos…", "Scanning photos for possible code issues…", "Matching to MGO Chapter 27…",
  "Looking up the building's complaint history…", "Checking the owner's report card…", "Writing tour questions and lease addendum…"];

const VERDICT: Record<string, { cls: string; Icon: any }> = {
  dont_sign: { cls: "bg-red-600 text-white", Icon: Ban },
  ask_first: { cls: "bg-amber-400 text-ink", Icon: CircleHelp },
  sign: { cls: "bg-emerald-600 text-white", Icon: ThumbsUp },
};

export default function Listing() {
  const [address, setAddress] = useState("1234 Demo St");
  const [url, setUrl] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setBusy(true); setError(null); setRes(null);
    try {
      const fd = new FormData();
      fd.append("address", address);
      for (const f of files) {
        fd.append("files", await toJpeg(f), f.name.replace(/\.\w+$/, ".jpg"));
        fd.append("orig_sha", await sha256Hex(f).catch(() => ""));
      }
      const [r] = await Promise.all([postForm("/api/listing/xray", fd), new Promise((ok) => setTimeout(ok, 3500))]);
      setRes(r);
    } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="h1">Listing X-Ray</h1>
        <p className="text-neutral-600 text-lg">Upload the listing photos. We look for problems in the landlord's own pictures and pull the building's history.</p>
      </div>

      {!res && (
        <div className="card p-5 space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <label className="space-y-1 block"><span className="label">Address</span>
              <input className="input" value={address} onChange={(e) => setAddress(e.target.value)} placeholder="123 W Mifflin St" /></label>
            <label className="space-y-1 block"><span className="label">Listing URL (optional)</span>
              <input className="input" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" />
              {url && <span className="text-xs text-neutral-500">We don't scrape listing sites from the app. Please upload the listing photos instead.</span>}
            </label>
          </div>
          <label className="block border-2 border-dashed border-neutral-300 rounded-2xl p-8 text-center cursor-pointer hover:border-badger">
            <Upload className="w-8 h-8 mx-auto text-neutral-400" />
            <div className="font-semibold mt-2">{files.length ? `${files.length} photo${files.length > 1 ? "s" : ""} selected` : "Choose listing photos"}</div>
            <div className="text-sm text-neutral-500">JPG or PNG · up to 30</div>
            <input type="file" accept="image/*" multiple className="hidden" onChange={(e) => setFiles(Array.from(e.target.files ?? []).slice(0, 30))} />
          </label>
          {files.length > 0 && (
            <div className="flex gap-2 overflow-x-auto">{files.map((f, i) => <img key={i} src={URL.createObjectURL(f)} className="h-20 rounded-lg" />)}</div>
          )}
          <button className="btn-primary text-lg w-full md:w-auto" disabled={!files.length || !address || busy} onClick={run}>X-Ray this listing</button>
          {busy && <Progress steps={STEPS} done={false} intervalMs={600} />}
          <ErrorBox error={error} />
        </div>
      )}

      {res && <Result res={res} onReset={() => { setRes(null); setFiles([]); }} />}
    </div>
  );
}

function Result({ res, onReset }: { res: any; onReset: () => void }) {
  const v = VERDICT[res.verdict.level];
  const h = res.history;
  const flagged = res.frames.filter((f: any) => f.detections.length);
  return (
    <div className="space-y-6">
      <div className={`rounded-2xl p-6 ${v.cls}`}>
        <div className="flex items-center gap-3"><v.Icon className="w-10 h-10" /><div className="text-4xl md:text-5xl font-extrabold">{res.verdict.label}</div></div>
        <div className="mt-1 opacity-90 text-lg">{res.address}</div>
        <ul className="mt-4 space-y-1 text-lg list-disc pl-6">{res.verdict.reasons.map((r: string) => <li key={r}>{r}</li>)}</ul>
      </div>
      <p className="text-sm text-neutral-600">{res.caveat}</p>
      <AiSource source={res.source} model={res.model} />
      {res.source === "none" && (
        <ErrorBox error="The vision model didn't respond, so the photos weren't analyzed. This verdict is based on the building's history only." />
      )}

      <div className="grid md:grid-cols-3 gap-4">
        <div className="md:col-span-2 space-y-3">
          <h2 className="h2">Found in their own listing photos</h2>
          {flagged.length > 0 && (
            <div className="flex gap-3 overflow-x-auto pb-2">
              {flagged.map((f: any, i: number) => (
                <figure key={f.evidence_id} className="shrink-0 w-64">
                  <img src={imgUrl(f.evidence_id)} className="w-64 h-44 object-cover rounded-xl ring-4 ring-badger" />
                  <figcaption className="text-sm mt-1"><b>Photo {res.frames.indexOf(f) + 1}:</b> {f.detections.map((d: any) => d.label).join(", ")}</figcaption>
                </figure>
              ))}
            </div>
          )}
          {res.violations.length === 0 && <p className="text-neutral-600">No possible issues spotted in these photos.</p>}
          {res.violations.map((x: Violation) => <ViolationCard key={x.violation_id} v={x} />)}
        </div>
        <div className="space-y-3">
          <h2 className="h2 flex items-center gap-2">Building history <DemoBadge /></h2>
          <SyntheticNote>Simulated complaint history and a fictional landlord grade from FixIt's synthetic demo dataset, not real City of Madison records.</SyntheticNote>
          {h ? (
            <div className="card p-4 space-y-3">
              <div className="flex items-center gap-3">
                <GradeBadge g={h.owner?.grade} />
                <div>
                  <Link to={`/owners/${h.owner?.owner_id}`} className="font-bold hover:underline">{h.owner?.name}</Link>
                  <div className="text-sm text-neutral-500">Owner report card</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-center">
                <div className="bg-neutral-50 rounded-lg p-2"><div className="text-2xl font-extrabold text-badger">{h.heat_reports_recent}</div><div className="text-xs">heat reports, 30 days</div></div>
                <div className="bg-neutral-50 rounded-lg p-2"><div className="text-2xl font-extrabold">{h.open_issues}</div><div className="text-xs">open issues</div></div>
                <div className="bg-neutral-50 rounded-lg p-2"><div className="text-2xl font-extrabold">{h.reports_last_12mo}</div><div className="text-xs">reports, 12 months</div></div>
                <div className="bg-neutral-50 rounded-lg p-2"><div className="text-2xl font-extrabold">{h.owner?.median_days_to_fix ?? "—"}</div><div className="text-xs">owner's median days to fix</div></div>
              </div>
              {res.property_id && <Link className="text-badger text-sm font-semibold" to={`/buildings/${res.property_id}`}>Full building timeline →</Link>}
            </div>
          ) : <div className="card p-4 text-neutral-600">This address isn't in FixIt's data yet.</div>}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="card p-5">
          <h2 className="h2 mb-3">Ask these on the tour</h2>
          <ol className="list-decimal pl-5 space-y-2">{res.tour_questions.map((q: string) => <li key={q}>{q}</li>)}</ol>
        </div>
        <div className="card p-5 space-y-3">
          <h2 className="h2">Lease addendum</h2>
          <pre className="whitespace-pre-wrap text-sm bg-neutral-50 rounded-xl p-3 max-h-72 overflow-auto font-sans">{res.addendum}</pre>
          <div className="flex gap-2">
            <CopyButton text={res.addendum} />
            <a className="btn-ghost" href={`/api/listing/${res.scan_id}/addendum.pdf`}>Download PDF</a>
          </div>
        </div>
      </div>
      <Disclaimer />
      <button className="btn-ghost" onClick={onReset}>Check another listing</button>
    </div>
  );
}
