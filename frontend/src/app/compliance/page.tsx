"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import PageAssistant from "@/components/PageAssistant";

const API = "";

const FRAMEWORKS = [
  { abbr: "ESPR", name: "Ecodesign for Sustainable Products Regulation" },
  { abbr: "Battery Reg", name: "EU Battery Regulation 2023/1542" },
  { abbr: "REACH", name: "Registration, Evaluation, Authorisation of Chemicals" },
  { abbr: "RoHS", name: "Restriction of Hazardous Substances Directive" },
  { abbr: "WEEE", name: "Waste Electrical and Electronic Equipment Directive" },
];

export default function CompliancePage() {
  const t = useTranslations("compliance");
  const [query, setQuery] = useState("");
  const [gtin, setGtin] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const defaultQuery = t("defaultQuery");
  const queryValue = query || defaultQuery;

  const runCheck = () => {
    setLoading(true);
    setResult(null);
    fetch(`${API}/api/v1/compliance/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryValue, product_gtin: gtin || undefined }),
    })
      .then((r) => r.json())
      .then(setResult)
      .catch((e) => setResult({ error: e.message }))
      .finally(() => setLoading(false));
  };

  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
      <p className="text-slate-600">{t("description")}</p>

      {/* --- How It Works --- */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <h3 className="text-base font-semibold text-blue-900 mb-3">How It Works</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex flex-col items-center text-center">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-200 text-blue-800 text-sm font-bold mb-2">1</span>
            <p className="text-sm font-medium text-blue-800">Enter your query</p>
            <p className="text-xs text-blue-600 mt-1">Describe the product or regulation question you need checked.</p>
          </div>
          <div className="flex flex-col items-center text-center">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-200 text-blue-800 text-sm font-bold mb-2">2</span>
            <p className="text-sm font-medium text-blue-800">AI agents analyze</p>
            <p className="text-xs text-blue-600 mt-1">The regulatory compliance agent cross-references EU frameworks automatically.</p>
          </div>
          <div className="flex flex-col items-center text-center">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-200 text-blue-800 text-sm font-bold mb-2">3</span>
            <p className="text-sm font-medium text-blue-800">Get compliance report</p>
            <p className="text-xs text-blue-600 mt-1">Receive a structured report with findings, risk level, and recommended actions.</p>
          </div>
        </div>
      </div>

      {/* --- Agents Involved --- */}
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h4 className="text-sm font-semibold text-slate-800 mb-2">Agents &amp; Tools Involved</h4>
        <div className="flex flex-wrap gap-2">
          <Link href="/agents/regulatory_compliance" className="inline-flex items-center gap-1.5 rounded-lg border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-700 hover:bg-violet-100 transition">
            Regulatory Compliance Agent
          </Link>
          <Link href="/agents/supervisor" className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 transition">
            Supervisor Agent
          </Link>
        </div>
      </div>

      {/* --- Frameworks Checked --- */}
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h4 className="text-sm font-semibold text-slate-800 mb-2">Regulatory Frameworks Checked</h4>
        <div className="flex flex-wrap gap-2">
          {FRAMEWORKS.map((fw) => (
            <span
              key={fw.abbr}
              title={fw.name}
              className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600"
            >
              {fw.abbr}
            </span>
          ))}
        </div>
      </div>

      {/* --- Query Input --- */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-400">{t("query")}</label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={defaultQuery}
          className="w-full rounded-lg bg-white border border-slate-300 p-2 text-sm text-slate-800"
          rows={3}
        />
      </div>
      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-400">{t("productGtinOptional")}</label>
        <input
          type="text"
          value={gtin}
          onChange={(e) => setGtin(e.target.value)}
          placeholder={t("placeholderGtin")}
          className="w-full rounded-lg bg-white border border-slate-300 p-2 text-slate-800"
        />
      </div>
      <button
        onClick={runCheck}
        disabled={loading}
        className="px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white disabled:opacity-50 transition"
      >
        {loading ? t("running") : t("runCheck")}
      </button>

      {/* --- Results + Follow-up Actions --- */}
      {result && (
        <div className="space-y-4">
          <pre className="rounded-xl bg-white border border-slate-200 p-4 text-xs overflow-auto max-h-96 text-slate-600">
            {JSON.stringify(result, null, 2)}
          </pre>
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-slate-800 mb-2">Next Steps</h4>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/audit-log"
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 transition"
              >
                View in Audit Log
              </Link>
              <Link
                href="/human-review"
                className="inline-flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-3 py-1.5 text-sm font-medium text-amber-700 hover:bg-amber-100 transition"
              >
                Request Human Review
              </Link>
              <Link
                href="/compliance/calendar"
                className="inline-flex items-center gap-1.5 rounded-lg border border-sky-200 bg-sky-50 px-3 py-1.5 text-sm font-medium text-sky-700 hover:bg-sky-100 transition"
              >
                View Compliance Calendar
              </Link>
            </div>
          </div>
        </div>
      )}
      <PageAssistant agentId="regulatory_compliance" agentLabel="Regulatory Compliance" pageContext="compliance-check" />
    </div>
  );
}
