"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { api } from "@/services/api";

const SECTOR_REGULATIONS: Record<string, { label: string; regulation: string }> = {
  batteries: { label: "Batteries & Accumulators", regulation: "EU Battery Regulation 2023/1542" },
  electronics: { label: "Electronics & ICT", regulation: "ESPR Delegated Acts — Ecodesign for Electronics" },
  textiles: { label: "Textiles & Apparel", regulation: "EU Strategy for Sustainable Textiles (2022)" },
  vehicles: { label: "Vehicles & Automotive", regulation: "End-of-Life Vehicles Directive 2000/53/EC" },
};

function DPPContent() {
  const t = useTranslations("dpp");
  const tCommon = useTranslations("common");
  const searchParams = useSearchParams();
  const section = searchParams.get("section") || "batteries";
  const [sectors, setSectors] = useState<string[]>([]);

  useEffect(() => {
    api.dpp.sectors()
      .then((d) => setSectors(d.sectors || []))
      .catch(() => setSectors(["batteries", "electronics", "textiles", "vehicles"]));
  }, []);

  const activeSector = SECTOR_REGULATIONS[section];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold capitalize text-slate-800">{t("title", { section })}</h2>
      <p className="text-slate-600">{t("description")}</p>

      {/* --- What is a DPP? Explainer --- */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <h3 className="text-base font-semibold text-blue-900 mb-2">What is a Digital Product Passport?</h3>
        <p className="text-sm text-blue-800 leading-relaxed">
          Under <span className="font-medium">ESPR Art.&nbsp;9</span> (Ecodesign for Sustainable Products Regulation), every product placed on the EU market
          will carry a <span className="font-medium">Digital Product Passport (DPP)</span> — a structured data record covering composition, carbon footprint,
          repairability, recyclability, and supply-chain provenance. DPPs enable regulators, recyclers, and consumers to access
          verified sustainability data throughout a product&apos;s lifecycle.
        </p>
      </div>

      {/* --- Sector Tabs --- */}
      <div className="flex gap-4 flex-wrap">
        {sectors.map((s) => (
          <Link
            key={s}
            href={`/dpp?section=${s}`}
            className={`px-4 py-2 rounded-lg ${section === s ? "bg-sky-500 text-white" : "bg-white border border-slate-200 text-slate-700"} hover:bg-sky-600 hover:text-white transition`}
          >
            {s}
          </Link>
        ))}
      </div>

      {/* --- Active Sector Regulation Info --- */}
      {activeSector && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg bg-sky-100 text-sky-600 text-sm font-bold shrink-0">§</span>
            <div>
              <h4 className="text-sm font-semibold text-slate-800">{activeSector.label}</h4>
              <p className="text-sm text-slate-500 mt-0.5">Applicable regulation: <span className="font-medium text-slate-700">{activeSector.regulation}</span></p>
            </div>
          </div>
        </div>
      )}

      {/* --- Quick Actions --- */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link
          href="/dpp/battery/new"
          className="rounded-xl border border-slate-200 bg-white p-4 hover:border-sky-300 hover:shadow-sm transition group"
        >
          <div className="text-sky-500 text-lg mb-1 group-hover:text-sky-600">+</div>
          <h4 className="text-sm font-semibold text-slate-800">Create New Passport</h4>
          <p className="text-xs text-slate-500 mt-1">Generate a DPP for a new product using the battery passport form.</p>
        </Link>
        <Link
          href="/compliance"
          className="rounded-xl border border-slate-200 bg-white p-4 hover:border-sky-300 hover:shadow-sm transition group"
        >
          <div className="text-amber-500 text-lg mb-1 group-hover:text-amber-600">✓</div>
          <h4 className="text-sm font-semibold text-slate-800">Run Compliance Check</h4>
          <p className="text-xs text-slate-500 mt-1">Verify a product against ESPR, Battery Regulation, REACH &amp; RoHS.</p>
        </Link>
        <Link
          href="/agents/dpp_generation"
          className="rounded-xl border border-slate-200 bg-white p-4 hover:border-sky-300 hover:shadow-sm transition group"
        >
          <div className="text-violet-500 text-lg mb-1 group-hover:text-violet-600">⚙</div>
          <h4 className="text-sm font-semibold text-slate-800">DPP Generation Agent</h4>
          <p className="text-xs text-slate-500 mt-1">View the AI agent that automates passport creation and data enrichment.</p>
        </Link>
      </div>

      {/* --- Battery Passport Card (original) --- */}
      <div className="bg-white border border-slate-200 rounded-xl p-4">
        <h3 className="font-medium mb-2 text-slate-800">{t("batteryPassportTitle")}</h3>
        <p className="text-sm text-slate-400 mb-2">{t("batteryPassportApi")}</p>
        <Link href="/dpp/battery/new" className="text-sky-500 hover:text-sky-600 hover:underline text-sm">
          {t("newBatteryFormLink")}
        </Link>
      </div>
    </div>
  );
}

export default function DPPSectionPage() {
  const tCommon = useTranslations("common");
  return (
    <Suspense fallback={<div className="text-slate-400">{tCommon("loading")}</div>}>
      <DPPContent />
    </Suspense>
  );
}
