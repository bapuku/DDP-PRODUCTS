"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import PageAssistant from "@/components/PageAssistant";
import { api } from "@/services/api";

interface CalendarEntry {
  year: number;
  regulation: string;
  deadline: string;
  description: string;
}

const CURRENT_YEAR = new Date().getFullYear();

function deadlineStatus(deadline: string): "past" | "upcoming" | "future" {
  const d = new Date(deadline);
  const now = new Date();
  const sixMonths = new Date();
  sixMonths.setMonth(sixMonths.getMonth() + 6);
  if (d < now) return "past";
  if (d <= sixMonths) return "upcoming";
  return "future";
}

const STATUS_STYLES = {
  past: "bg-emerald-50 border-emerald-200 text-emerald-700",
  upcoming: "bg-amber-50 border-amber-200 text-amber-700",
  future: "bg-slate-50 border-slate-200 text-slate-500",
};

const STATUS_DOT = {
  past: "bg-emerald-400",
  upcoming: "bg-amber-400",
  future: "bg-slate-300",
};

const STATUS_LABELS = {
  past: "Completed",
  upcoming: "Upcoming",
  future: "Future",
};

export default function ComplianceCalendarPage() {
  const t = useTranslations("complianceCalendar");
  const tCommon = useTranslations("common");
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.complianceCalendar()
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, []);

  const years = Array.from(new Set(entries.map((e) => e.year))).sort();

  return (
    <div className="max-w-3xl space-y-6">
      <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
      <p className="text-slate-600 text-sm">{t("description")}</p>

      {/* --- Visual Timeline Indicator --- */}
      {years.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h4 className="text-sm font-semibold text-slate-800 mb-3">Timeline Overview</h4>
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {years.map((year) => (
              <div
                key={year}
                className={`flex-1 min-w-[56px] text-center py-2 rounded-lg text-sm font-medium transition ${
                  year === CURRENT_YEAR
                    ? "bg-sky-500 text-white shadow-sm"
                    : year < CURRENT_YEAR
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-slate-100 text-slate-500"
                }`}
              >
                {year}
              </div>
            ))}
          </div>
          <div className="flex items-center gap-4 mt-3">
            <span className="flex items-center gap-1.5 text-xs text-slate-500">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-400" /> Past
            </span>
            <span className="flex items-center gap-1.5 text-xs text-slate-500">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-sky-500" /> Current Year
            </span>
            <span className="flex items-center gap-1.5 text-xs text-slate-500">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-amber-400" /> Upcoming (≤ 6 months)
            </span>
            <span className="flex items-center gap-1.5 text-xs text-slate-500">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-slate-300" /> Future
            </span>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-slate-400">{tCommon("loading")}</p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-left text-slate-600">
                <th className="px-4 py-3 font-medium">{t("year")}</th>
                <th className="px-4 py-3 font-medium">{t("regulation")}</th>
                <th className="px-4 py-3 font-medium">{t("deadline")}</th>
                <th className="px-4 py-3 font-medium">{t("descriptionCol")}</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e, i) => {
                const status = deadlineStatus(e.deadline);
                return (
                  <tr key={i} className="border-t border-slate-200 hover:bg-slate-50 text-slate-800">
                    <td className={`px-4 py-3 font-medium ${e.year === CURRENT_YEAR ? "text-sky-600" : ""}`}>{e.year}</td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/compliance?query=${encodeURIComponent(e.regulation)}`}
                        className="text-sky-600 hover:underline"
                      >
                        {e.regulation}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{e.deadline}</td>
                    <td className="px-4 py-3 text-slate-500">{e.description}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}>
                        <span className={`inline-block h-1.5 w-1.5 rounded-full ${STATUS_DOT[status]}`} />
                        {STATUS_LABELS[status]}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/compliance?query=${encodeURIComponent(e.regulation)}`}
                        className="text-xs text-sky-500 hover:text-sky-600 hover:underline whitespace-nowrap"
                      >
                        Run compliance check →
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <PageAssistant agentId="regulatory_compliance" agentLabel="Regulatory Compliance" pageContext="compliance-calendar" />
    </div>
  );
}
