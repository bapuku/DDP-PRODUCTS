"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/services/api";

function DPPContent() {
  const searchParams = useSearchParams();
  const section = searchParams.get("section") || "batteries";
  const [sectors, setSectors] = useState<string[]>([]);

  useEffect(() => {
    api.dpp.sectors()
      .then((d) => setSectors(d.sectors || []))
      .catch(() => setSectors(["batteries", "electronics", "textiles", "vehicles"]));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold capitalize">DPP – {section}</h2>
      <p className="text-slate-400">
        List and detail views for Battery Passport and multi-sector DPPs. Use the API to create and fetch passports.
      </p>
      <div className="flex gap-4 flex-wrap">
        {sectors.map((s) => (
          <Link
            key={s}
            href={`/dpp?section=${s}`}
            className={`px-4 py-2 rounded ${section === s ? "bg-sky-600" : "bg-slate-800"} hover:bg-slate-700`}
          >
            {s}
          </Link>
        ))}
      </div>
      <div className="border border-slate-700 rounded-lg p-4">
        <h3 className="font-medium mb-2">Battery Passport (EU 2023/1542 Annex XIII)</h3>
        <p className="text-sm text-slate-500 mb-2">Create: POST /api/v1/dpp/battery · Get: GET /api/v1/dpp/battery/&#123;gtin&#125;/&#123;serial&#125;</p>
        <Link href="/dpp/battery/new" className="text-sky-400 hover:underline text-sm">
          New Battery Passport form →
        </Link>
      </div>
    </div>
  );
}

export default function DPPSectionPage() {
  return (
    <Suspense fallback={<div className="text-slate-400">Loading...</div>}>
      <DPPContent />
    </Suspense>
  );
}
