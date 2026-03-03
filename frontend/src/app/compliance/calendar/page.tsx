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
      <h2 className="text-2xl font-semibold">{t("title")}</h2>
      <p className="text-slate-400 text-sm">{t("description")}</p>
      {loading ? (
        <p className="text-slate-500">{tCommon("loading")}</p>
      ) : (
        <div className="rounded-lg border border-slate-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-800 text-left text-slate-300">
                <th className="px-4 py-3">{t("year")}</th>
                <th className="px-4 py-3">{t("regulation")}</th>
                <th className="px-4 py-3">{t("deadline")}</th>
                <th className="px-4 py-3">{t("descriptionCol")}</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e, i) => (
                <tr key={i} className="border-t border-slate-700 hover:bg-slate-800/50">
                  <td className="px-4 py-3">{e.year}</td>
                  <td className="px-4 py-3">{e.regulation}</td>
                  <td className="px-4 py-3">{e.deadline}</td>
                  <td className="px-4 py-3 text-slate-400">{e.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
