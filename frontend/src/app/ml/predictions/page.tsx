"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/services/api";

export default function MLPredictionsPage() {
  const t = useTranslations("ml");
  const tCommon = useTranslations("common");
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
      setResult({ error: tCommon("apiUnavailable") });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <h2 className="text-2xl font-semibold">{t("title")}</h2>
      <p className="text-slate-400 text-sm">{t("description")}</p>
      <div className="rounded-lg border border-slate-700 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">{t("sector")}</label>
          <select
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="w-full rounded bg-slate-800 border border-slate-600 px-3 py-2 text-sm"
          >
            <option value="generic">{t("generic")}</option>
            <option value="battery">{t("battery")}</option>
            <option value="textile">{t("textile")}</option>
            <option value="electronics">{t("electronics")}</option>
            <option value="vehicles">{t("vehicles")}</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">{t("ddpCompleteness")}</label>
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
          {loading ? t("predicting") : t("predictCompliance")}
        </button>
        {result && !("error" in result) && (
          <div className="rounded bg-slate-800 p-4 text-sm space-y-1">
            <p>{t("espr")} {String(result.espr_class ?? "—")}</p>
            <p>{t("rohs")} {String(result.rohs_class ?? "—")}</p>
            <p>{t("reach")} {String(result.reach_class ?? "—")}</p>
            <p>{t("complianceScore")} {String(result.compliance_score ?? "—")}</p>
          </div>
        )}
        {result && "error" in result && (
          <p className="text-red-400 text-sm">{String(result.error)}</p>
        )}
      </div>
    </div>
  );
}
