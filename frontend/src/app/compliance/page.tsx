"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CompliancePage() {
  const [query, setQuery] = useState("Is this battery compliant with EU Battery Regulation?");
  const [gtin, setGtin] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const runCheck = () => {
    setLoading(true);
    setResult(null);
    fetch(`${API}/api/v1/compliance/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, product_gtin: gtin || undefined }),
    })
      .then((r) => r.json())
      .then(setResult)
      .catch((e) => setResult({ error: e.message }))
      .finally(() => setLoading(false));
  };

  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-2xl font-semibold">Compliance check</h2>
      <p className="text-slate-400">
        Run compliance verification via the agent workflow (regulatory + product data). EU AI Act Art. 12 audit trail.
      </p>
      <div className="space-y-2">
        <label className="block text-sm font-medium">Query</label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded bg-slate-800 border border-slate-600 p-2 text-sm"
          rows={3}
        />
      </div>
      <div className="space-y-2">
        <label className="block text-sm font-medium">Product GTIN (optional)</label>
        <input
          type="text"
          value={gtin}
          onChange={(e) => setGtin(e.target.value)}
          placeholder="14 digits"
          className="w-full rounded bg-slate-800 border border-slate-600 p-2"
        />
      </div>
      <button
        onClick={runCheck}
        disabled={loading}
        className="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-50"
      >
        {loading ? "Running…" : "Run compliance check"}
      </button>
      {result && (
        <pre className="rounded bg-slate-900 border border-slate-700 p-4 text-xs overflow-auto max-h-96">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
