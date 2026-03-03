"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { REPORTS } from "@/data/registry";

const STATUS_BADGES: Record<string, string> = {
  implemented: "bg-emerald-100 text-emerald-700",
  partial: "bg-amber-100 text-amber-700",
  planned: "bg-slate-100 text-slate-600",
};

const grouped = REPORTS.reduce<Record<string, typeof REPORTS>>((acc, r) => {
  (acc[r.regulation] ??= []).push(r);
  return acc;
}, {});

export default function ReportsPage() {
  const t = useTranslations("reports");

  return (
    <div className="max-w-4xl space-y-6">
      <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
      <p className="text-slate-600 text-sm">{t("description")}</p>

      {Object.entries(grouped).map(([regulation, items]) => (
        <div key={regulation} className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-800 border-b border-slate-200 pb-2">{regulation}</h3>
          {items.map((report) => (
            <div key={report.id} className="bg-white rounded-xl border border-slate-200 p-5 card-hover hover:shadow-md transition">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2 py-1 rounded">{report.article}</span>
                  <h4 className="font-medium text-slate-800">{report.title}</h4>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_BADGES[report.status] ?? STATUS_BADGES.planned}`}>
                  {report.status}
                </span>
              </div>
              <p className="text-sm text-slate-500 mb-3">{report.description}</p>
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span>{t("agent")}: <Link href={`/agents/${report.agent}`} className="text-sky-500 hover:text-sky-600 hover:underline">{report.agent}</Link></span>
                <span>{t("endpoint")}: <code className="bg-slate-100 px-1.5 py-0.5 rounded text-sky-600">{report.endpoint}</code></span>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
