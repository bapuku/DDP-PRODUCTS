"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";

interface Phase { phase: number; id: string; label: string; status: string; }
interface Recommendation { priority?: string; priorite?: string; category?: string; categorie?: string; recommendation?: string; recommandation?: string; regulation?: string; reglementation?: string; }

export default function ProductReportPage() {
  const t = useTranslations("productReport");
  const tCommon = useTranslations("common");
  const params = useParams();
  const gtin = params?.gtin as string;
  const serial = params?.serial as string;
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!gtin || !serial) return;
    fetch(`/api/v1/report/${gtin}/${serial}`)
      .then(r => r.json()).then(setReport).catch(() => setReport(null)).finally(() => setLoading(false));
  }, [gtin, serial]);

  if (loading) return <p className="text-slate-400 py-12 text-center">{tCommon("loading")}</p>;
  if (!report) return <p className="text-red-600 py-12 text-center">{t("notFound")}</p>;

  const product = (report.product as Record<string, unknown>) || {};
  const phases = (report.lifecycle_phases as Phase[]) || [];
  const insurance = (report.insurance_traceability as Record<string, unknown>) || {};
  const compliance = (report.compliance_summary as Record<string, Record<string, string>>) || {};
  const recommendations = (report.recommendations as Recommendation[]) || [];
  const blockchain = (report.blockchain as Record<string, unknown>) || {};
  const audit = (report.audit_trail as Record<string, unknown>) || {};

  const priorityColor: Record<string, string> = { high: "bg-red-100 text-red-700", haute: "bg-red-100 text-red-700", medium: "bg-amber-100 text-amber-700", moyenne: "bg-amber-100 text-amber-700", normal: "bg-blue-100 text-blue-700", normale: "bg-blue-100 text-blue-700" };

  return (
    <div className="max-w-5xl space-y-6 print:space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">{t("title")}</h2>
          <p className="text-sm text-slate-500">{t("subtitle")}</p>
        </div>
        <button onClick={() => window.print()} className="px-4 py-2 rounded-lg bg-teal-600 text-white text-sm font-medium hover:bg-teal-700 transition print:hidden">{t("print")}</button>
      </div>

      {/* Product card */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold text-slate-800 mb-3">{t("productInfo")}</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div><span className="text-slate-400 text-xs">GTIN</span><p className="font-mono font-semibold">{String(product.gtin)}</p></div>
          <div><span className="text-slate-400 text-xs">{t("serial")}</span><p className="font-mono font-semibold">{String(product.serial_number)}</p></div>
          <div><span className="text-slate-400 text-xs">DPP URI</span><p className="font-mono text-xs text-teal-600 break-all">{String(product.dpp_uri)}</p></div>
          <div><span className="text-slate-400 text-xs">{t("completeness")}</span><p className="font-bold text-lg text-teal-700">{Math.round(Number(product.completeness || 0) * 100)}%</p></div>
        </div>
      </div>

      {/* Lifecycle phases */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold text-slate-800 mb-3">{t("lifecycle")}</h3>
        <div className="flex gap-1">
          {phases.map(p => (
            <div key={p.phase} className={`flex-1 rounded-lg p-2 text-center text-[10px] ${p.status === "completed" ? "bg-emerald-100 text-emerald-700" : p.status === "current" ? "bg-teal-100 text-teal-800 ring-2 ring-teal-400" : "bg-slate-50 text-slate-400"}`}>
              <span className="font-bold block">{p.phase}</span>
              <span className="leading-tight block">{p.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Insurance traceability */}
      <div className="rounded-xl border border-teal-200 bg-teal-50 p-5">
        <h3 className="font-semibold text-teal-800 mb-3">🛡️ {String(insurance.titre || insurance.title)}</h3>
        <p className="text-sm text-teal-700 mb-4">{String(insurance.description)}</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
          <div className="bg-white rounded-lg p-3 border border-teal-100">
            <span className="text-xs text-slate-400">Blockchain</span>
            <p className="font-semibold text-teal-700">{String(insurance.integrite_blockchain || insurance.blockchain_integrity)}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border border-teal-100">
            <span className="text-xs text-slate-400">{t("aiDecisions")}</span>
            <p className="font-semibold text-teal-700">{String(insurance.nombre_decisions_ia || insurance.ai_decisions_count)}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border border-teal-100">
            <span className="text-xs text-slate-400">{t("confidence")}</span>
            <p className="font-semibold text-teal-700">{String(insurance.score_confiance_global || insurance.overall_confidence_score)}</p>
          </div>
        </div>
        {Array.isArray(insurance.certificats || insurance.certificates) && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {((insurance.certificats || insurance.certificates) as string[]).map((c: string, i: number) => (
              <span key={i} className="text-[10px] px-2 py-1 rounded-full bg-white border border-teal-200 text-teal-700">{c}</span>
            ))}
          </div>
        )}
      </div>

      {/* Compliance summary */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold text-slate-800 mb-3">{t("complianceSummary")}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {Object.entries(compliance).map(([key, val]) => (
            <div key={key} className="flex items-center gap-3 p-3 rounded-lg bg-emerald-50 border border-emerald-100">
              <span className="text-emerald-600">✓</span>
              <div>
                <span className="text-xs font-semibold text-emerald-700">{val.article}</span>
                <p className="text-xs text-slate-600">{val.detail || val.detail}</p>
              </div>
              <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-medium`}>{val.statut || val.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <h3 className="font-semibold text-blue-800 mb-3">💡 {t("recommendations")}</h3>
        <div className="space-y-2">
          {recommendations.map((r, i) => {
            const prio = r.priority || r.priorite || "normal";
            return (
              <div key={i} className="flex items-start gap-3 bg-white rounded-lg p-3 border border-blue-100">
                <span className={`text-[10px] px-2 py-1 rounded-full font-medium flex-shrink-0 ${priorityColor[prio] || "bg-slate-100 text-slate-600"}`}>{prio}</span>
                <div>
                  <p className="text-sm font-medium text-slate-700">{r.recommendation || r.recommandation}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">{r.regulation || r.reglementation} · {r.category || r.categorie}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-center text-xs text-slate-400 print:border-0">
        <p>{t("generated")} {String(report.generated_at)}</p>
        <p>{String(report.generated_by)}</p>
        <p className="mt-1">{((report.regulation_basis as string[]) || []).join(" · ")}</p>
      </div>
    </div>
  );
}
