"use client";

import { useState } from "react";
import { api } from "@/services/api";

export default function MLPredictionsPage() {
  const [sector, setSector] = useState("generic");
  const [completeness, setCompleteness] = useState<number>(0.5);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  async function handlePredict() {
    setLoading(true);
    setResult(null);
    try {
      const r = await api.ml.predictComplianceGet(sector, completeness);
      setResult(r);
    } catch {
      setResult({ error: "API unavailable" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <h2 className="text-2xl font-semibold">ML compliance predictions</h2>
      <p className="text-slate-400 text-sm">
        Real-time predictions via v2 GradientBoosting models (ESPR, RoHS, REACH, carbon, circularity). EU AI Act Art. 9, 10, 15.
      </p>
      <div className="rounded-lg border border-slate-700 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">Sector</label>
          <select
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="w-full rounded bg-slate-800 border border-slate-600 px-3 py-2 text-sm"
          >
            <option value="generic">Generic</option>
            <option value="battery">Battery</option>
            <option value="textile">Textile</option>
            <option value="electronics">Electronics</option>
            <option value="vehicles">Vehicles</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">DDP completeness (0–1)</label>
          <input
            type="number"
            min={0}
            max={1}
            step={0.1}
            value={completeness}
            onChange={(e) => setCompleteness(parseFloat(e.target.value) || 0)}
            className="w-full rounded bg-slate-800 border border-slate-600 px-3 py-2 text-sm"
          />
        </div>
        <button
          onClick={handlePredict}
          disabled={loading}
          className="w-full rounded bg-sky-600 hover:bg-sky-500 text-white py-2 text-sm font-medium disabled:opacity-50"
        >
          {loading ? "Predicting…" : "Predict compliance"}
        </button>
        {result && !("error" in result) && (
          <div className="rounded bg-slate-800 p-4 text-sm space-y-1">
            <p>ESPR: {String(result.espr_class ?? "—")}</p>
            <p>RoHS: {String(result.rohs_class ?? "—")}</p>
            <p>REACH: {String(result.reach_class ?? "—")}</p>
            <p>Compliance score: {String(result.compliance_score ?? "—")}</p>
          </div>
        )}
        {result && "error" in result && (
          <p className="text-red-400 text-sm">{String(result.error)}</p>
        )}
      </div>
    </div>
  );
}
