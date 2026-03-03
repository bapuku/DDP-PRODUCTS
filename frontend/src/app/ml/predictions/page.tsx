"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import PageAssistant from "@/components/PageAssistant";
import { api } from "@/services/api";

const MODELS = [
  { name: "ESPR Classifier", type: "Classification", target: "Ecodesign compliance class" },
  { name: "RoHS Classifier", type: "Classification", target: "Hazardous-substance compliance" },
  { name: "REACH Classifier", type: "Classification", target: "Chemical-registration status" },
  { name: "Carbon Regressor", type: "Regression", target: "Carbon footprint (kg CO₂e)" },
  { name: "Circularity Regressor", type: "Regression", target: "Circularity score (0–1)" },
];

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
      <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
      <p className="text-slate-600 text-sm">{t("description")}</p>

      {/* EU AI Act explainer */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5 space-y-3">
        <h3 className="text-sm font-semibold text-blue-900">
          ML Compliance Predictions &mdash; EU AI Act Art.&nbsp;9, 10, 15
        </h3>
        <p className="text-sm text-blue-800 leading-relaxed">
          Five GradientBoosting models predict regulatory compliance outcomes before the full
          verification pipeline runs. Art.&nbsp;9 (risk management), Art.&nbsp;10 (data governance),
          and Art.&nbsp;15 (accuracy &amp; robustness) govern how these models are trained,
          monitored, and audited.
        </p>
        <Link
          href="/agents/predictive"
          className="inline-block text-sm font-medium text-blue-700 hover:text-blue-900 hover:underline"
        >
          Powered by: Predictive Risk Scoring Agent &rarr;
        </Link>
      </div>

      {/* 5 models overview */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
        <h3 className="text-sm font-semibold text-slate-700">Model Ensemble (5 models)</h3>
        <div className="space-y-2">
          {MODELS.map((m) => (
            <div key={m.name} className="flex items-center gap-3 text-sm">
              <span className={`inline-block h-2 w-2 rounded-full ${m.type === "Classification" ? "bg-violet-500" : "bg-amber-500"}`} />
              <span className="font-medium text-slate-800 w-40">{m.name}</span>
              <span className="text-slate-500">{m.target}</span>
            </div>
          ))}
        </div>
        <div className="flex gap-3 mt-1">
          <span className="flex items-center gap-1.5 text-xs text-slate-500">
            <span className="inline-block h-2 w-2 rounded-full bg-violet-500" /> Classification
          </span>
          <span className="flex items-center gap-1.5 text-xs text-slate-500">
            <span className="inline-block h-2 w-2 rounded-full bg-amber-500" /> Regression
          </span>
        </div>
      </div>

      {/* Prediction form */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">{t("sector")}</label>
          <select
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800"
          >
            <option value="generic">{t("generic")}</option>
            <option value="battery">{t("battery")}</option>
            <option value="textile">{t("textile")}</option>
            <option value="electronics">{t("electronics")}</option>
            <option value="vehicles">{t("vehicles")}</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">{t("ddpCompleteness")}</label>
          <input
            type="number"
            min={0}
            max={1}
            step={0.1}
            value={completeness}
            onChange={(e) => setCompleteness(parseFloat(e.target.value) || 0)}
            className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800"
          />
        </div>
        <button
          onClick={handlePredict}
          disabled={loading}
          className="w-full rounded-lg bg-sky-500 hover:bg-sky-600 text-white py-2 text-sm font-medium disabled:opacity-50 transition"
        >
          {loading ? t("predicting") : t("predictCompliance")}
        </button>
        {result && !("error" in result) && (
          <div className="rounded-lg bg-slate-50 p-4 text-sm space-y-1 text-slate-600">
            <p>{t("espr")} {String(result.espr_class ?? "—")}</p>
            <p>{t("rohs")} {String(result.rohs_class ?? "—")}</p>
            <p>{t("reach")} {String(result.reach_class ?? "—")}</p>
            <p>{t("complianceScore")} {String(result.compliance_score ?? "—")}</p>
          </div>
        )}
        {result && "error" in result && (
          <p className="text-red-600 text-sm">{String(result.error)}</p>
        )}
      </div>

      {/* Context after results */}
      {result && !("error" in result) && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500 leading-relaxed">
          These predictions use GradientBoosting models trained on 80k products.
          Confidence scores above 85% are auto-approved; lower scores are routed
          to{" "}
          <Link href="/human-review" className="text-sky-600 hover:underline">
            human review
          </Link>
          .
        </div>
      )}
      <PageAssistant agentId="predictive" agentLabel="Predictive Scoring" pageContext="ml-predictions" />
    </div>
  );
}
