"use client";

import { useParams } from "next/navigation";
import Link from "next/link";

const PHASES = [
  { id: "pre_conception", label: "Phase 0: Pre-conception" },
  { id: "design", label: "Phase 1: Design" },
  { id: "prototype", label: "Phase 2: Prototypage" },
  { id: "supplier_qual", label: "Phase 3: Fournisseurs" },
  { id: "manufacturing", label: "Phase 4: Fabrication et Génération" },
  { id: "distribution", label: "Phase 5: Distribution EPCIS" },
  { id: "active_use", label: "Phase 6: Utilisation (BMS IoT)" },
  { id: "eol", label: "Phase 7: Seconde vie" },
  { id: "recycling", label: "Phase 8: Recyclage" },
  { id: "destruction", label: "Phase 9: Destruction" },
];

export default function LifecycleTimelinePage() {
  const params = useParams();
  const gtin = params?.gtin as string;
  const serial = params?.serial as string;

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/dpp/${gtin}/${serial}`} className="text-sky-400 text-sm hover:underline">
          ← DPP detail
        </Link>
        <h2 className="text-2xl font-semibold">Lifecycle timeline</h2>
      </div>
      <p className="text-slate-400 text-sm">
        Product lifecycle phases (0–9) per EU DPP Orchestration v3.0. Use the Lifecycle Update API to transition phases.
      </p>
      <ul className="space-y-2">
        {PHASES.map((phase, i) => (
          <li
            key={phase.id}
            className="flex items-center gap-3 rounded-lg border border-slate-700 p-4"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-700 text-sm font-medium text-slate-300">
              {i}
            </span>
            <span className="text-slate-200">{phase.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
