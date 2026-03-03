"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import Link from "next/link";
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

const LOGGED_ITEMS = [
  { icon: "🤖", label: "Agent decisions", detail: "Every approve / reject / escalate action" },
  { icon: "📊", label: "Confidence scores", detail: "ML model output probabilities" },
  { icon: "📜", label: "Regulatory citations", detail: "ESPR, RoHS, REACH article references" },
  { icon: "🔒", label: "Input / output hashes", detail: "SHA-256 integrity proof per decision" },
  { icon: "👤", label: "Human overrides", detail: "Reviewer identity and rationale" },
];

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

      {/* EU AI Act explainer */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5 space-y-3">
        <h3 className="text-sm font-semibold text-blue-900">EU AI Act Art.&nbsp;12 &mdash; Record-Keeping</h3>
        <p className="text-sm text-blue-800 leading-relaxed">
          High-risk AI systems must automatically log events throughout their lifetime.
          This audit trail records every agent decision, confidence score, regulatory citation,
          and human override so that supervisory authorities can reconstruct the decision chain.
        </p>
        <div className="flex items-center gap-4">
          <Link
            href="/agents/audit_trail"
            className="text-sm font-medium text-blue-700 hover:text-blue-900 hover:underline"
          >
            Managed by: Audit Trail Agent &rarr;
          </Link>
          <span className="text-xs text-blue-600 bg-blue-100 rounded-full px-2.5 py-0.5 font-medium">
            Retention: 10 years per EU AI Act
          </span>
        </div>
      </div>

      {/* Stats bar */}
      {!loading && (
        <div className="flex gap-4">
          <div className="flex-1 rounded-xl border border-slate-200 bg-white p-4 text-center">
            <p className="text-2xl font-bold text-slate-800">{entries.length}</p>
            <p className="text-xs text-slate-500 mt-1">Total entries loaded</p>
          </div>
          <div className="flex-1 rounded-xl border border-slate-200 bg-white p-4 text-center">
            <p className="text-2xl font-bold text-slate-800">
              {new Set(entries.map((e) => e.agent_id)).size}
            </p>
            <p className="text-xs text-slate-500 mt-1">Distinct agents</p>
          </div>
          <div className="flex-1 rounded-xl border border-slate-200 bg-white p-4 text-center">
            <p className="text-2xl font-bold text-slate-800">
              {entries.filter((e) => e.human_override).length}
            </p>
            <p className="text-xs text-slate-500 mt-1">Human overrides</p>
          </div>
        </div>
      )}

      {/* What is logged */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
        <h3 className="text-sm font-semibold text-slate-700">What Is Logged</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {LOGGED_ITEMS.map((item) => (
            <div key={item.label} className="flex items-start gap-2 text-sm">
              <span className="mt-0.5">{item.icon}</span>
              <div>
                <p className="font-medium text-slate-800">{item.label}</p>
                <p className="text-slate-500 text-xs">{item.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filter */}
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

      {/* Table */}
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
