import { Link } from "react-router-dom";
import { Camera, FileSearch, FolderOpen, Users } from "lucide-react";
import { Disclaimer } from "../components/ui";

const ACTIONS = [
  { to: "/listing", icon: FileSearch, title: "Check a listing", body: "Spot problems in the landlord's own photos and see the building's complaint history before you sign." },
  { to: "/scan", icon: Camera, title: "Scan my apartment", body: "Point your camera at problems. Each one is matched to Madison's housing code and saved as hashed evidence." },
  { to: "/cases", icon: FolderOpen, title: "My cases", body: "Repair letters, an AI call to your landlord, deadline tracking, and a pre-filled city complaint." },
];

export default function Home() {
  return (
    <div className="space-y-8">
      <section className="pt-4 md:pt-10">
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-[1.05]">
          Your building inspector<br className="hidden md:block" /> and tenant advocate,<br />
          <span className="text-badger">in your pocket.</span>
        </h1>
        <p className="mt-4 text-lg md:text-xl text-neutral-600 max-w-2xl">
          Catch it before you sign. Document it while you live there. Fight it when they ignore you.
        </p>
      </section>
      <section className="grid md:grid-cols-3 gap-4">
        {ACTIONS.map(({ to, icon: Icon, title, body }) => (
          <Link key={to} to={to} className="card p-6 hover:shadow-md hover:border-badger transition group">
            <div className="w-12 h-12 rounded-xl bg-badger-light text-badger grid place-items-center mb-4 group-hover:bg-badger group-hover:text-white transition">
              <Icon className="w-6 h-6" />
            </div>
            <div className="text-xl font-bold">{title}</div>
            <p className="text-neutral-600 mt-1">{body}</p>
          </Link>
        ))}
      </section>
      <Link to="/city" className="card p-5 flex items-center gap-4 hover:border-badger transition">
        <Users className="w-8 h-8 text-badger shrink-0" />
        <div>
          <div className="font-bold text-lg">You're not alone</div>
          <p className="text-neutral-600">Every report joins a city-wide lakehouse. See landlord report cards, hot spots, and ask the data in plain English.</p>
        </div>
      </Link>
      <Disclaimer />
    </div>
  );
}
