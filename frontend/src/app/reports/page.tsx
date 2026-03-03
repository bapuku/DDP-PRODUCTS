"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ComplianceReport {
  id: string;
  regulation: string;
  article: string;
  title: string;
  description: string;
  status: string;
  agent: string;
  endpoint: string;
}

function getLocale(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  return m ? m[1].trim() : "en";
}

const STATUS_BADGES: Record<string, string> = {
  implemented: "bg-emerald-900/60 text-emerald-300",
  partial: "bg-amber-900/60 text-amber-300",
  planned: "bg-slate-700 text-slate-300",
};

export default function ReportsPage() {
  const t = useTranslations("reports");
  const tCommon = useTranslations("common");
  const [reports, setReports] = useState<ComplianceReport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/v1/agents/reports`, {
      headers: { "Accept-Language": getLocale() },
    })
      .then((r) => r.json())
      .then(setReports)
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  }, []);

  const grouped = reports.reduce<Record<string, ComplianceReport[]>>((acc, r) => {
    (acc[r.regulation] ??= []).push(r);
    return acc;
  }, {});

  return (
    <div className="max-w-4xl space-y-6">
      <h2 className="text-2xl font-semibold">{t("title")}</h2>
      <p className="text-slate-400 text-sm">{t("description")}</p>

      {loading ? (
        <p className="text-slate-500">{tCommon("loading")}</p>
      ) : (
        Object.entries(grouped).map(([regulation, items]) => (
          <div key={regulation} className="space-y-3">
            <h3 className="text-lg font-semibold text-slate-200 border-b border-slate-700 pb-2">{regulation}</h3>
            {items.map((report) => (
              <div key={report.id} className="rounded-lg border border-slate-700 p-5 bg-slate-800/30 hover:bg-slate-800/50 transition">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono bg-slate-700 px-2 py-1 rounded">{report.article}</span>
                    <h4 className="font-medium">{report.title}</h4>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_BADGES[report.status] ?? STATUS_BADGES.planned}`}>
                    {report.status}
                  </span>
                </div>
                <p className="text-sm text-slate-400 mb-3">{report.description}</p>
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span>{t("agent")}: <Link href={`/agents/${report.agent}`} className="text-sky-400 hover:underline">{report.agent}</Link></span>
                  <span>{t("endpoint")}: <code className="bg-slate-800 px-1.5 py-0.5 rounded text-sky-300">{report.endpoint}</code></span>
                </div>
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  );
}
