import { NavLink, Route, Routes, Link } from "react-router-dom";
import { Wrench } from "lucide-react";
import Home from "./pages/Home";
import Listing from "./pages/Listing";
import Scan from "./pages/Scan";
import Case from "./pages/Case";
import Cases from "./pages/Cases";
import Landlords from "./pages/Landlords";
import Owner from "./pages/Owner";
import Building from "./pages/Building";
import City from "./pages/City";
import About from "./pages/About";
import { DISCLAIMER } from "./components/ui";

const NAV = [
  ["/listing", "Check a listing"],
  ["/scan", "Scan"],
  ["/cases", "My cases"],
  ["/landlords", "Landlords"],
  ["/city", "City view"],
  ["/about", "How it works"],
];

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-badger text-white sticky top-0 z-[1000]" style={{ paddingTop: "env(safe-area-inset-top)" }}>
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 font-extrabold text-lg tracking-tight shrink-0">
            <Wrench className="w-5 h-5" /> FixIt Madison
          </Link>
          <nav className="flex gap-1 overflow-x-auto text-sm font-semibold no-scrollbar">
            {NAV.map(([to, label]) => (
              <NavLink key={to} to={to}
                className={({ isActive }) => `px-3 py-1.5 rounded-lg whitespace-nowrap ${isActive ? "bg-white/20" : "hover:bg-white/10"}`}>
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/listing" element={<Listing />} />
          <Route path="/scan" element={<Scan />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/cases/:id" element={<Case />} />
          <Route path="/landlords" element={<Landlords />} />
          <Route path="/owners/:id" element={<Owner />} />
          <Route path="/buildings/:id" element={<Building />} />
          <Route path="/city" element={<City />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </main>
      <footer className="border-t border-neutral-200 bg-white" style={{ paddingBottom: "env(safe-area-inset-bottom)" }}>
        <div className="max-w-6xl mx-auto px-4 py-4 text-xs text-neutral-500 space-y-1">
          <p>{DISCLAIMER}</p>
          <p>Owner, building and neighbor data shown is synthetic demo data. Built on Databricks for MadHacks 2026.</p>
        </div>
      </footer>
    </div>
  );
}
