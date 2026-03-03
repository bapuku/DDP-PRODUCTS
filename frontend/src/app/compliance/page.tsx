"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
      <h2 className="text-2xl font-semibold">{t("title")}</h2>
      <p className="text-slate-400">{t("description")}</p>
      <div className="space-y-2">
        <label className="block text-sm font-medium">{t("query")}</label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={defaultQuery}
          className="w-full rounded bg-slate-800 border border-slate-600 p-2 text-sm"
          rows={3}
        />
      </div>
      <div className="space-y-2">
        <label className="block text-sm font-medium">{t("productGtinOptional")}</label>
        <input
          type="text"
          value={gtin}
          onChange={(e) => setGtin(e.target.value)}
          placeholder={t("placeholderGtin")}
          className="w-full rounded bg-slate-800 border border-slate-600 p-2"
        />
      </div>
      <button
        onClick={runCheck}
        disabled={loading}
        className="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-50"
      >
        {loading ? t("running") : t("runCheck")}
      </button>
      {result && (
        <pre className="rounded bg-slate-900 border border-slate-700 p-4 text-xs overflow-auto max-h-96">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
