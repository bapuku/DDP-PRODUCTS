"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/services/api";

const SECTOR_IDS = ["batteries", "electronics", "textiles", "vehicles", "construction", "furniture", "plastics", "chemicals"] as const;
const SECTOR_ICONS: Record<string, string> = { batteries: "🔋", electronics: "💻", textiles: "👕", vehicles: "🚗", construction: "🏗️", furniture: "🪑", plastics: "🧴", chemicals: "⚗️" };
const REG_KEYS: Record<string, string> = { batteries: "eu2023", electronics: "espr", textiles: "espr", vehicles: "elv", construction: "cpr", furniture: "espr", plastics: "eu2019", chemicals: "reach" };

export default function HomePage() {
  const t = useTranslations("home");
  const tCommon = useTranslations("common");
  const [apiStatus, setApiStatus] = useState<string>("checking");
  const [checks, setChecks] = useState<Record<string, string>>({});

  useEffect(() => {
    api.ready()
      .then((r) => { setApiStatus(r.status); setChecks(r.checks ?? {}); })
      .catch(() => setApiStatus("offline"));
  }, []);

  const statusLabel = apiStatus === "ready" ? tCommon("ready") : apiStatus === "degraded" ? tCommon("degraded") : apiStatus === "offline" ? tCommon("offline") : tCommon("checking");
  const statusColor = apiStatus === "ready" ? "bg-emerald-100 text-emerald-700 border-emerald-200" : apiStatus === "degraded" ? "bg-amber-100 text-amber-700 border-amber-200" : "bg-red-100 text-red-700 border-red-200";

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Status + Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className={`rounded-xl border p-4 ${statusColor}`}>
          <p className="text-xs font-medium uppercase tracking-wide opacity-70">{tCommon("apiStatus")}</p>
          <p className="text-2xl font-bold mt-1">{statusLabel}</p>
          <div className="flex gap-2 mt-2 flex-wrap">
            {Object.entries(checks).map(([k, v]) => (
              <span key={k} className={`text-xs px-2 py-0.5 rounded-full font-medium ${v === "ok" ? "bg-emerald-200/60 text-emerald-800" : "bg-red-200/60 text-red-800"}`}>
                {k} {v === "ok" ? "✓" : "✗"}
              </span>
            ))}
          </div>
        </div>
        <Link href="/agents" className="rounded-xl border border-slate-200 bg-white p-4 card-hover cursor-pointer group">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">AI Agents</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">16</p>
          <p className="text-xs text-sky-500 mt-2 group-hover:underline">{t("quickActions")} →</p>
        </Link>
        <Link href="/reports" className="rounded-xl border border-slate-200 bg-white p-4 card-hover cursor-pointer group">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">EU Regulations</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">7</p>
          <p className="text-xs text-sky-500 mt-2 group-hover:underline">ESPR · Battery · AI Act →</p>
        </Link>
        <Link href="/compliance/calendar" className="rounded-xl border border-slate-200 bg-white p-4 card-hover cursor-pointer group">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Deadlines</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">2026</p>
          <p className="text-xs text-sky-500 mt-2 group-hover:underline">Battery passport Feb →</p>
        </Link>
      </div>

      {/* AI Disclosure */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
            <span className="text-blue-600 text-sm">⚖️</span>
          </div>
          <div>
            <p className="text-sm font-semibold text-blue-800">{t("aiDisclosureTitle")}</p>
            <p className="text-sm text-blue-700 mt-1 leading-relaxed">{t("aiDisclosureBody")}</p>
            <div className="flex gap-2 mt-3">
              <Link href="/audit" className="text-xs font-medium px-3 py-1.5 rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200 transition">Art. 12 Audit →</Link>
              <Link href="/agents" className="text-xs font-medium px-3 py-1.5 rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200 transition">Art. 13 Agents →</Link>
              <Link href="/human-review" className="text-xs font-medium px-3 py-1.5 rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200 transition">Art. 14 Review →</Link>
            </div>
          </div>
        </div>
      </div>

      {/* Sector grid */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-800">{t("dppBySector")}</h2>
          <Link href="/dpp" className="text-sm text-sky-600 hover:text-sky-700 font-medium">View all →</Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {SECTOR_IDS.map((id) => (
            <Link
              key={id}
              href={`/dpp?section=${id}`}
              className="group flex flex-col gap-2 p-4 rounded-xl border border-slate-200 bg-white card-hover"
            >
              <span className="text-2xl">{SECTOR_ICONS[id] ?? "📦"}</span>
              <span className="font-medium text-slate-700 group-hover:text-sky-600 transition">{t(`sectors.${id}`)}</span>
              <span className="text-xs text-slate-400">{t(`regs.${REG_KEYS[id] ?? "espr"}`)}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Quick actions */}
      <section>
        <h2 className="text-lg font-semibold text-slate-800 mb-3">{t("quickActions")}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Link href="/dpp/battery/new" className="p-5 rounded-xl border border-slate-200 bg-white card-hover group">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center"><span className="text-lg">🔋</span></div>
              <p className="font-semibold text-slate-800 group-hover:text-sky-600">{t("actionBattery")}</p>
            </div>
            <p className="text-sm text-slate-500">{t("actionBatteryDesc")}</p>
            <p className="text-xs text-sky-500 mt-3 font-medium group-hover:underline">Create now →</p>
          </Link>
          <Link href="/compliance" className="p-5 rounded-xl border border-slate-200 bg-white card-hover group">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center"><span className="text-lg">✅</span></div>
              <p className="font-semibold text-slate-800 group-hover:text-sky-600">{t("actionCompliance")}</p>
            </div>
            <p className="text-sm text-slate-500">{t("actionComplianceDesc")}</p>
            <p className="text-xs text-sky-500 mt-3 font-medium group-hover:underline">Run check →</p>
          </Link>
          <Link href="/supply-chain" className="p-5 rounded-xl border border-slate-200 bg-white card-hover group">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center"><span className="text-lg">🔗</span></div>
              <p className="font-semibold text-slate-800 group-hover:text-sky-600">{t("actionSupplyChain")}</p>
            </div>
            <p className="text-sm text-slate-500">{t("actionSupplyChainDesc")}</p>
            <p className="text-xs text-sky-500 mt-3 font-medium group-hover:underline">Trace now →</p>
          </Link>
        </div>
      </section>
    </div>
  );
}
