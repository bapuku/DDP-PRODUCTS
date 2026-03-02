"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";

interface CalendarEntry {
  year: number;
  regulation: string;
  deadline: string;
  description: string;
}

export default function ComplianceCalendarPage() {
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
      <h2 className="text-2xl font-semibold">Compliance calendar</h2>
      <p className="text-slate-400 text-sm">
        Regulatory deadlines 2025–2036 (ESPR, Battery Regulation). Plan DPP rollout and reporting.
      </p>
      {loading ? (
        <p className="text-slate-500">Loading…</p>
      ) : (
        <div className="rounded-lg border border-slate-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-800 text-left text-slate-300">
                <th className="px-4 py-3">Year</th>
                <th className="px-4 py-3">Regulation</th>
                <th className="px-4 py-3">Deadline</th>
                <th className="px-4 py-3">Description</th>
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
