"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/services/api";

interface CalendarEntry {
  year: number;
  regulation: string;
  deadline: string;
  description: string;
}

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

  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
      <p className="text-slate-600 text-sm">{t("description")}</p>
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
              </tr>
            </thead>
            <tbody>
              {entries.map((e, i) => (
                <tr key={i} className="border-t border-slate-200 hover:bg-slate-50 text-slate-800">
                  <td className="px-4 py-3">{e.year}</td>
                  <td className="px-4 py-3">{e.regulation}</td>
                  <td className="px-4 py-3">{e.deadline}</td>
                  <td className="px-4 py-3 text-slate-500">{e.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
