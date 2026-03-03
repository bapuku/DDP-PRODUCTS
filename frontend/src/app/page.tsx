"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/services/api";

const SECTOR_IDS = [
  "batteries",
  "electronics",
  "textiles",
  "vehicles",
  "construction",
  "furniture",
  "plastics",
  "chemicals",
] as const;
const SECTOR_ICONS: Record<string, string> = {
  batteries: "🔋",
  electronics: "💻",
  textiles: "👕",
  vehicles: "🚗",
  construction: "🏗️",
  furniture: "🪑",
  plastics: "🧴",
  chemicals: "⚗️",
};
const REG_KEYS: Record<string, string> = {
  batteries: "eu2023",
  electronics: "espr",
  textiles: "espr",
  vehicles: "elv",
  construction: "cpr",
  furniture: "espr",
  plastics: "eu2019",
  chemicals: "reach",
};

export default function HomePage() {
  const t = useTranslations("home");
  const tCommon = useTranslations("common");
  const [apiStatus, setApiStatus] = useState<string>("checking");
  const [checks, setChecks] = useState<Record<string, string>>({});

  useEffect(() => {
    api.ready()
      .then((r) => {
        setApiStatus(r.status);
        setChecks(r.checks ?? {});
      })
      .catch(() => setApiStatus("offline"));
  }, []);

  const statusLabel = apiStatus === "ready" ? tCommon("ready") : apiStatus === "degraded" ? tCommon("degraded") : apiStatus === "offline" ? tCommon("offline") : tCommon("checking");

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <span className={`w-2 h-2 rounded-full ${apiStatus === "ready" ? "bg-emerald-400" : apiStatus === "degraded" ? "bg-amber-400" : "bg-red-400"}`} />
        <span className="text-sm text-slate-400">
          {tCommon("apiStatus")}: <span className="font-medium text-slate-200">{statusLabel}</span>
        </span>
        {Object.entries(checks).map(([k, v]) => (
          <span key={k} className={`text-xs px-2 py-0.5 rounded ${v === "ok" ? "bg-emerald-900/50 text-emerald-300" : "bg-red-900/50 text-red-300"}`}>
            {k}: {v}
          </span>
        ))}
      </div>

      <div className="rounded-lg border border-amber-800/50 bg-amber-950/30 p-4">
        <p className="text-xs text-amber-300">
          <strong>{t("aiDisclosureTitle")}</strong> {t("aiDisclosureBody")}
        </p>
      </div>

      <section>
        <h2 className="text-xl font-semibold mb-4">{t("dppBySector")}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {SECTOR_IDS.map((id) => (
            <Link
              key={id}
              href={`/dpp?section=${id}`}
              className="group flex flex-col gap-2 p-4 rounded-lg border border-slate-700 hover:border-sky-500 transition"
            >
              <span className="text-2xl">{SECTOR_ICONS[id] ?? "📦"}</span>
              <span className="font-medium group-hover:text-sky-300">{t(`sectors.${id}`)}</span>
              <span className="text-xs text-slate-500">{t(`regs.${REG_KEYS[id] ?? "espr"}`)}</span>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">{t("quickActions")}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Link href="/dpp/battery/new" className="p-4 rounded-lg border border-slate-700 hover:border-sky-500 transition">
            <p className="font-medium">{t("actionBattery")}</p>
            <p className="text-sm text-slate-500 mt-1">{t("actionBatteryDesc")}</p>
          </Link>
          <Link href="/compliance" className="p-4 rounded-lg border border-slate-700 hover:border-sky-500 transition">
            <p className="font-medium">{t("actionCompliance")}</p>
            <p className="text-sm text-slate-500 mt-1">{t("actionComplianceDesc")}</p>
          </Link>
          <Link href="/supply-chain" className="p-4 rounded-lg border border-slate-700 hover:border-sky-500 transition">
            <p className="font-medium">{t("actionSupplyChain")}</p>
            <p className="text-sm text-slate-500 mt-1">{t("actionSupplyChainDesc")}</p>
          </Link>
        </div>
      </section>
    </div>
  );
}
