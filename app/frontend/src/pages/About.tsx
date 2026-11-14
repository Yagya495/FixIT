import { Disclaimer } from "../components/ui";

const FLOW = [
  ["Ingest", "MGO Ch. 27 PDF → ai_parse_document → silver.code_sections → chunks (CDF)"],
  ["Retrieve", "Vector Search Delta Sync index → match_code() top-3 sections"],
  ["See", "Photos/frames → vision model (serving endpoint) → silver.detections → gold.violations"],
  ["Store", "UC Volumes (SHA-256-named evidence) · Delta bronze → silver → gold"],
  ["Act", "Letters · simulated AI call → silver.calls → silver.deadlines → complaint drafts"],
  ["Connect", "gold.reports × gold.properties → neighbor + same-owner matches, landlord_scores"],
  ["Ask", "Genie space over gold tables · AI/BI dashboard · MLflow traces + risk model"],
  ["Serve", "FastAPI + React as a Databricks App, SQL warehouse via service principal"],
];

export default function About() {
  return (
    <div className="space-y-6 max-w-4xl">
      <h1 className="h1">How FixIt works</h1>
      <div className="card p-5">
        <h2 className="h2 mb-3">Under the hood: Databricks lakehouse</h2>
        <ol className="space-y-2">{FLOW.map(([k, v], i) => (
          <li key={k} className="flex gap-3"><span className="w-7 h-7 rounded-full bg-badger text-white grid place-items-center font-bold shrink-0">{i + 1}</span>
            <div><b>{k}.</b> <span className="text-neutral-700">{v}</span></div></li>))}</ol>
      </div>
      <div className="card p-5 space-y-2">
        <h2 className="h2">Accuracy</h2>
        <p className="text-neutral-600">An evaluation panel (detection precision/recall per violation type and code-matching top-3 accuracy, logged to MLflow) arrives with P1-6. Until then, every low-confidence finding is labeled "possible issue — verify in person".</p>
      </div>
      <div className="card p-5 space-y-2">
        <h2 className="h2">Privacy, safety and AI calls</h2>
        <ul className="list-disc pl-5 space-y-1 text-neutral-700">
          <li>Every owner, building history and neighbor report in this demo is synthetic and labeled "Demo data".</li>
          <li>Unit numbers are hashed in the reports table. Joint complaints call units "Unit A, B…".</li>
          <li>The AI caller says it's an AI acting for the tenant in its first sentence. It never threatens and never claims to be a lawyer or the city.</li>
          <li>Real phone calls (P1) only go to an allowlist of consenting numbers, behind a kill switch. FixIt never calls real landlords during the hackathon.</li>
          <li>FixIt never submits complaints for you. It pre-fills them and links to the official city page.</li>
          <li>Evidence files are named by their SHA-256 hash with capture and upload timestamps, so you can show they haven't been changed.</li>
        </ul>
      </div>
      <Disclaimer />
    </div>
  );
}
