"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/services/api";

interface AuditRow {
  id: string;
  timestamp: string;
  agent_id: string;
  decision_type: string;
  confidence_score: number | null;
  entity_id: string | null;
  input_hash?: string;
  output_hash?: string;
  regulatory_citations?: unknown;
  human_override?: string;
}

export default function AuditPage() {
  const t = useTranslations("audit");
  const tCommon = useTranslations("common");
  const [entries, setEntries] = useState<AuditRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [entityFilter, setEntityFilter] = useState("");

  function fetchLog() {
    api.lifecycle.auditLog({ limit: 100, entity_id: entityFilter || undefined })
      .then((r) => setEntries(Array.isArray(r) ? r : []))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchLog();
    const interval = setInterval(fetchLog, 10000);
    return () => clearInterval(interval);
  }, [entityFilter]);

  return (
    <div className="max-w-4xl space-y-6">
      <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
      <p className="text-slate-600">{t("description")}</p>
      <div className="flex gap-2 items-center">
        <label className="text-sm text-slate-400">{t("filterByEntity")}</label>
        <input
          type="text"
          value={entityFilter}
          onChange={(e) => setEntityFilter(e.target.value)}
          placeholder={tCommon("optional")}
          className="rounded-lg bg-white border border-slate-300 px-2 py-1 text-sm w-48 text-slate-800"
        />
      </div>
      {loading && entries.length === 0 ? (
        <p className="text-slate-400">{tCommon("loading")}</p>
      ) : entries.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-6 text-center text-slate-400">
          {t("noEntries")}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-left text-slate-600">
                <th className="px-4 py-2 font-medium">{t("time")}</th>
                <th className="px-4 py-2 font-medium">{t("agent")}</th>
                <th className="px-4 py-2 font-medium">{t("decision")}</th>
                <th className="px-4 py-2 font-medium">{t("confidence")}</th>
                <th className="px-4 py-2 font-medium">{t("entityId")}</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-t border-slate-200 hover:bg-slate-50 text-slate-800">
                  <td className="px-4 py-2 text-slate-500">{e.timestamp}</td>
                  <td className="px-4 py-2">{e.agent_id}</td>
                  <td className="px-4 py-2">{e.decision_type}</td>
                  <td className="px-4 py-2">{e.confidence_score != null ? String(e.confidence_score) : "—"}</td>
                  <td className="px-4 py-2 text-slate-500">{e.entity_id ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
