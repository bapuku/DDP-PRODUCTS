"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { api } from "@/services/api";

const WORKFLOW_STEPS = [
  { step: 1, label: "Classify", desc: "Product sector & regulation mapping", agent: "data_collection", agentLabel: "Data Collection Agent" },
  { step: 2, label: "Collect Data", desc: "Gather mandatory fields from sources", agent: "data_collection", agentLabel: "Data Collection Agent" },
  { step: 3, label: "Generate DPP", desc: "Build ESPR-compliant passport", agent: "ddp_generation", agentLabel: "DPP Generation Agent" },
  { step: 4, label: "Validate", desc: "JSON-LD schema & completeness check", agent: "validation", agentLabel: "Validation Agent" },
  { step: 5, label: "Compliance", desc: "Regulatory verification (RoHS, REACH)", agent: "regulatory_compliance", agentLabel: "Regulatory Compliance Agent" },
  { step: 6, label: "Publish", desc: "Sign, hash & store on IPFS + registry", agent: "ddp_generation", agentLabel: "DPP Generation Agent" },
];

export default function NewLifecyclePage() {
  const t = useTranslations("lifecycleNew");
  const tCommon = useTranslations("common");
  const router = useRouter();
  const [gtin, setGtin] = useState("");
  const [serial, setSerial] = useState("");
  const [batch, setBatch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ ddp_uri?: string; validation_passed?: boolean; requires_human_review?: boolean } | null>(null);
  const [activeStep, setActiveStep] = useState<number | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    setActiveStep(1);
    try {
      const stepTimer = setInterval(() => {
        setActiveStep((prev) => (prev && prev < 6 ? prev + 1 : prev));
      }, 1200);
      const r = await api.lifecycle.create({
        product_gtin: gtin,
        serial_number: serial,
        batch_number: batch || undefined,
        query: "Create DPP",
      });
      clearInterval(stepTimer);
      setActiveStep(6);
      setResult(r);
      if (r.ddp_uri) setTimeout(() => router.push(`/dpp/${gtin}/${serial}`), 2000);
    } catch {
      setActiveStep(null);
      setError(tCommon("requestFailed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
      <p className="text-slate-600 text-sm">{t("description")}</p>

      {/* Workflow explainer */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5 space-y-4">
        <h3 className="text-sm font-semibold text-blue-900">DPP Creation Workflow</h3>
        <p className="text-sm text-blue-800 leading-relaxed">
          Submitting this form triggers a 6-step automated pipeline. Each step is handled
          by a specialized agent and logged to the audit trail.
        </p>
        <div className="space-y-2">
          {WORKFLOW_STEPS.map((ws) => {
            const isActive = activeStep === ws.step;
            const isComplete = activeStep !== null && activeStep > ws.step;
            return (
              <div
                key={ws.step}
                className={`flex items-start gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-sky-100 border border-sky-300"
                    : isComplete
                    ? "bg-emerald-50 border border-emerald-200"
                    : "bg-white/60 border border-transparent"
                }`}
              >
                <span
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                    isComplete
                      ? "bg-emerald-500 text-white"
                      : isActive
                      ? "bg-sky-500 text-white animate-pulse"
                      : "bg-blue-100 text-blue-700"
                  }`}
                >
                  {isComplete ? "✓" : ws.step}
                </span>
                <div className="min-w-0">
                  <p className="font-medium text-slate-800">
                    {ws.label}
                    <span className="ml-2 text-xs text-slate-500">{ws.desc}</span>
                  </p>
                  <Link
                    href={`/agents/${ws.agent}`}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    {ws.agentLabel} &rarr;
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">{t("gtin14")}</label>
          <input
            type="text"
            value={gtin}
            onChange={(e) => setGtin(e.target.value)}
            placeholder={t("placeholderGtin")}
            className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">{t("serialNumber")}</label>
          <input
            type="text"
            value={serial}
            onChange={(e) => setSerial(e.target.value)}
            placeholder={t("placeholderSerial")}
            className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">{t("batchOptional")}</label>
          <input
            type="text"
            value={batch}
            onChange={(e) => setBatch(e.target.value)}
            className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800"
          />
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        {result && (
          <div className="rounded-lg bg-slate-50 p-3 text-sm space-y-1">
            <p className="text-slate-600">{t("ddpUri")} {result.ddp_uri ?? "—"}</p>
            <p className="text-slate-600">{t("validationPassed")} {result.validation_passed ? tCommon("yes") : tCommon("no")}</p>
            <p className="text-slate-600">{t("humanReviewRequired")} {result.requires_human_review ? tCommon("yes") : tCommon("no")}</p>
            {result.ddp_uri && (
              <Link href={`/dpp/${gtin}/${serial}`} className="inline-block mt-2 text-sm text-sky-600 hover:underline">
                View created DPP &rarr;
              </Link>
            )}
          </div>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-sky-500 hover:bg-sky-600 text-white py-2 text-sm font-medium disabled:opacity-50 transition"
        >
          {loading ? t("creating") : t("createDpp")}
        </button>
      </form>
    </div>
  );
}
