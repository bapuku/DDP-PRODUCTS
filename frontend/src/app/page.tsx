"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/services/api";

const SECTORS = [
  { id: "batteries", icon: "🔋", label: "Batteries", reg: "EU 2023/1542" },
  { id: "electronics", icon: "💻", label: "Electronics", reg: "ESPR" },
  { id: "textiles", icon: "👕", label: "Textiles", reg: "ESPR" },
  { id: "vehicles", icon: "🚗", label: "Vehicles", reg: "ELV Directive" },
  { id: "construction", icon: "🏗️", label: "Construction", reg: "CPR" },
  { id: "furniture", icon: "🪑", label: "Furniture", reg: "ESPR" },
  { id: "plastics", icon: "🧴", label: "Plastics", reg: "EU 2019/904" },
  { id: "chemicals", icon: "⚗️", label: "Chemicals", reg: "REACH / CLP" },
];

export default function HomePage() {
  const [apiStatus, setApiStatus] = useState<string>("checking...");
  const [checks, setChecks] = useState<Record<string, string>>({});

  useEffect(() => {
    api.ready()
      .then((r) => {
        setApiStatus(r.status);
        setChecks(r.checks ?? {});
      })
      .catch(() => setApiStatus("offline"));
  }, []);

  return (
    <div className="space-y-8">
      {/* Status bar */}
      <div className="flex items-center gap-3">
        <span className={`w-2 h-2 rounded-full ${apiStatus === "ready" ? "bg-emerald-400" : apiStatus === "degraded" ? "bg-amber-400" : "bg-red-400"}`} />
        <span className="text-sm text-slate-400">
          API: <span className="font-medium text-slate-200">{apiStatus}</span>
        </span>
        {Object.entries(checks).map(([k, v]) => (
          <span key={k} className={`text-xs px-2 py-0.5 rounded ${v === "ok" ? "bg-emerald-900/50 text-emerald-300" : "bg-red-900/50 text-red-300"}`}>
            {k}: {v}
          </span>
        ))}
      </div>

      {/* AI Act disclosure (Art. 13) */}
      <div className="rounded-lg border border-amber-800/50 bg-amber-950/30 p-4">
        <p className="text-xs text-amber-300">
          <strong>EU AI Act Art. 13 — AI Disclosure:</strong> This platform uses AI agents (Claude Sonnet/Opus 4)
          to interpret EU regulations. All decisions are logged (Art. 12). Human review required when confidence &lt; 85% (Art. 14).
        </p>
      </div>

      {/* Sector grid */}
      <section>
        <h2 className="text-xl font-semibold mb-4">DPP by Sector</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {SECTORS.map(({ id, icon, label, reg }) => (
            <Link
              key={id}
              href={`/dpp?section=${id}`}
              className="group flex flex-col gap-2 p-4 rounded-lg border border-slate-700 hover:border-sky-500 transition"
            >
              <span className="text-2xl">{icon}</span>
              <span className="font-medium group-hover:text-sky-300">{label}</span>
              <span className="text-xs text-slate-500">{reg}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Quick actions */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Quick actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Link href="/dpp/battery/new" className="p-4 rounded-lg border border-slate-700 hover:border-sky-500 transition">
            <p className="font-medium">New Battery Passport</p>
            <p className="text-sm text-slate-500 mt-1">EU Reg. 2023/1542 Annex XIII · 87 fields</p>
          </Link>
          <Link href="/compliance" className="p-4 rounded-lg border border-slate-700 hover:border-sky-500 transition">
            <p className="font-medium">Run compliance check</p>
            <p className="text-sm text-slate-500 mt-1">AI-assisted · EUR-Lex citations</p>
          </Link>
          <Link href="/supply-chain" className="p-4 rounded-lg border border-slate-700 hover:border-sky-500 transition">
            <p className="font-medium">Trace supply chain</p>
            <p className="text-sm text-slate-500 mt-1">Battery Reg. Art. 49 · Neo4j graph</p>
          </Link>
        </div>
      </section>
    </div>
  );
}
