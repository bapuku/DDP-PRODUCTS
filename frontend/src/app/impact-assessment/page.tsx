"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

interface ImpactCategory { id: string; name: string; value: number; unit: string; method: string; }
interface LifecycleStage { share_pct: number; label: string; }
interface Recommendation { priority?: string; priorite?: string; category?: string; categorie?: string; recommendation?: string; recommandation?: string; regulation?: string; reglementation?: string; }

function getLocale(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  return m ? m[1].trim() : "en";
}

export default function ImpactAssessmentPage() {
  const t = useTranslations("impact");
  const [gtin, setGtin] = useState("06374692674377");
  const [productName, setProductName] = useState("EV Battery Module");
  const [sector, setSector] = useState("batteries");
  const [weight, setWeight] = useState(50);
  const [energy, setEnergy] = useState(75);
  const [recycled, setRecycled] = useState(8);
  const [country, setCountry] = useState("EU-27");
  const [transport, setTransport] = useState(500);
  const [lifetime, setLifetime] = useState(10);
  const [boundary, setBoundary] = useState("cradle-to-grave");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  async function runAssessment() {
    setLoading(true); setResult(null);
    try {
      const res = await fetch("/api/v1/impact/run", {
        method: "POST", headers: { "Content-Type": "application/json", "Accept-Language": getLocale() },
        body: JSON.stringify({ gtin, product_name: productName, sector, weight_kg: weight, energy_kwh: energy, recycled_content_pct: recycled, manufacturing_country: country, transport_km: transport, lifetime_years: lifetime, system_boundary: boundary }),
      });
      setResult(await res.json());
    } catch { setResult(null); }
    finally { setLoading(false); }
  }

  const carbon = result?.carbon_footprint as Record<string, unknown> | undefined;
  const lcia = result?.lcia_results as Record<string, unknown> | undefined;
  const categories: ImpactCategory[] = lcia ? (lcia.categories as ImpactCategory[]) || [] : [];
  const stages = result?.lifecycle_stages as Record<string, LifecycleStage> | undefined;
  const recommendations: Recommendation[] = Array.isArray(result?.recommendations) ? result.recommendations as Recommendation[] : [];
  const dq = result?.data_quality as Record<string, string> | undefined;
  const regulatory = result?.regulatory_compliance as Record<string, Record<string, string>> | undefined;
  const priorityColor: Record<string, string> = { high: "bg-red-100 text-red-700", haute: "bg-red-100 text-red-700", medium: "bg-amber-100 text-amber-700", moyenne: "bg-amber-100 text-amber-700", normal: "bg-blue-100 text-blue-700", normale: "bg-blue-100 text-blue-700" };

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">{t("title")}</h2>
          <p className="text-sm text-slate-500 mt-1">{t("description")}</p>
        </div>
        <Link href="/agents/impact_assessment" className="px-4 py-2 text-sm rounded-lg bg-white border border-slate-200 text-teal-700 font-medium hover:border-teal-400 transition">{t("viewAgent")} →</Link>
      </div>

      {/* Explainer */}
      <div className="rounded-xl border border-green-200 bg-green-50 p-5">
        <h3 className="font-semibold text-green-800 mb-2">{t("regulation")}</h3>
        <p className="text-sm text-green-700 mb-3">{t("regulationDesc")}</p>
        <div className="flex flex-wrap gap-1.5">
          {["ESPR Art. 9", "Battery Reg Art. 7", "ISO 14040/14044", "ISO 14067", "EF 3.1 (16 cat.)", "PEF 2021/2279", "EN ISO 14025"].map(r => (
            <span key={r} className="text-[10px] px-2 py-1 rounded-full bg-white border border-green-200 text-green-700 font-medium">{r}</span>
          ))}
        </div>
      </div>

      {/* Form */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
        <h3 className="font-semibold text-slate-800">{t("productData")}</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div><label className="block text-xs font-medium text-slate-500 mb-1">{t("productName")}</label><input value={productName} onChange={e => setProductName(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" /></div>
          <div><label className="block text-xs font-medium text-slate-500 mb-1">{t("sector")}</label>
            <select value={sector} onChange={e => setSector(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm">
              {["batteries","electronics","textiles","vehicles","construction","furniture","plastics","chemicals"].map(s => <option key={s} value={s}>{s}</option>)}
            </select></div>
          <div><label className="block text-xs font-medium text-slate-500 mb-1">{t("weight")}</label><input type="number" value={weight} onChange={e => setWeight(+e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" /></div>
          <div><label className="block text-xs font-medium text-slate-500 mb-1">{t("energy")}</label><input type="number" value={energy} onChange={e => setEnergy(+e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" /></div>
          <div><label className="block text-xs font-medium text-slate-500 mb-1">{t("recycled")}</label><input type="number" value={recycled} onChange={e => setRecycled(+e.target.value)} min={0} max={100} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" /></div>
          <div><label className="block text-xs font-medium text-slate-500 mb-1">{t("transport")}</label><input type="number" value={transport} onChange={e => setTransport(+e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" /></div>
          <div><label className="block text-xs font-medium text-slate-500 mb-1">{t("boundary")}</label>
            <select value={boundary} onChange={e => setBoundary(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm">
              <option value="cradle-to-grave">Cradle-to-grave</option><option value="cradle-to-gate">Cradle-to-gate</option><option value="gate-to-gate">Gate-to-gate</option><option value="cradle-to-cradle">Cradle-to-cradle</option>
            </select></div>
          <div><label className="block text-xs font-medium text-slate-500 mb-1">{t("country")}</label><input value={country} onChange={e => setCountry(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" /></div>
          <div><label className="block text-xs font-medium text-slate-500 mb-1">{t("lifetime")}</label><input type="number" value={lifetime} onChange={e => setLifetime(+e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" /></div>
        </div>
        <button onClick={runAssessment} disabled={loading} className="w-full py-3 rounded-xl bg-gradient-to-r from-green-600 to-teal-500 text-white font-bold text-sm shadow-md hover:shadow-lg transition disabled:opacity-50">
          {loading ? t("running") : t("runAssessment")}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Carbon footprint headline */}
          {carbon && (
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-xl border border-slate-200 bg-white p-5 text-center">
                <p className="text-xs text-slate-400 uppercase">{t("totalCO2")}</p>
                <p className="text-3xl font-bold text-slate-800 mt-1">{String(carbon.total_kg_co2eq)}</p>
                <p className="text-xs text-slate-500">kg CO₂-eq</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-5 text-center">
                <p className="text-xs text-slate-400 uppercase">{t("perKwh")}</p>
                <p className="text-3xl font-bold text-slate-800 mt-1">{String(carbon.per_kwh_kg_co2eq)}</p>
                <p className="text-xs text-slate-500">kg CO₂-eq/kWh</p>
              </div>
              <div className={`rounded-xl border-2 p-5 text-center ${String(carbon.carbon_class) <= "C" ? "border-green-400 bg-green-50" : String(carbon.carbon_class) <= "E" ? "border-amber-400 bg-amber-50" : "border-red-400 bg-red-50"}`}>
                <p className="text-xs text-slate-400 uppercase">{t("carbonClass")}</p>
                <p className="text-5xl font-black mt-1">{String(carbon.carbon_class)}</p>
                <p className="text-xs text-slate-500">A (best) → G (worst)</p>
              </div>
            </div>
          )}

          {/* 16 Impact Categories */}
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-800 mb-1">{t("impactCategories")}</h3>
            <p className="text-xs text-slate-400 mb-3">{String(lcia?.method)} — {categories.length} {t("categories")}</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {categories.map((c, i) => (
                <div key={i} className="rounded-lg bg-green-50 border border-green-100 p-3 text-center">
                  <p className="text-[9px] text-slate-500 leading-tight mb-1">{c.name}</p>
                  <p className="text-sm font-bold text-green-800">{c.value < 0.001 ? c.value.toExponential(2) : c.value}</p>
                  <p className="text-[8px] text-slate-400">{c.unit}</p>
                  <p className="text-[7px] text-slate-300 mt-0.5">{c.method}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Lifecycle stages breakdown */}
          {stages && (
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-800 mb-3">{t("lifecycleBreakdown")}</h3>
              <div className="flex gap-0.5 h-8 rounded-full overflow-hidden mb-3">
                {Object.entries(stages).map(([k, v]) => (
                  <div key={k} className="bg-teal-400 flex items-center justify-center text-[9px] text-white font-bold" style={{ width: `${v.share_pct}%` }}>{v.share_pct}%</div>
                ))}
              </div>
              <div className="flex flex-wrap gap-3">
                {Object.entries(stages).map(([k, v]) => (
                  <span key={k} className="text-xs text-slate-600"><span className="inline-block w-3 h-3 bg-teal-400 rounded mr-1" />{v.label} ({v.share_pct}%)</span>
                ))}
              </div>
            </div>
          )}

          {/* Regulatory compliance */}
          {regulatory && (
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-800 mb-3">{t("regulatoryCompliance")}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {Object.entries(regulatory).map(([k, v]) => (
                  <div key={k} className="flex items-center gap-2 p-2 rounded-lg bg-emerald-50 border border-emerald-100 text-xs">
                    <span className="text-emerald-600">✓</span>
                    <div><p className="font-semibold text-emerald-700">{v.standard}</p><p className="text-slate-500">{v.article}</p></div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
              <h3 className="font-semibold text-blue-800 mb-3">💡 {t("recommendations")}</h3>
              <div className="space-y-2">
                {recommendations.map((r, i) => {
                  const prio = r.priority || r.priorite || "normal";
                  return (
                    <div key={i} className="flex items-start gap-3 bg-white rounded-lg p-3 border border-blue-100">
                      <span className={`text-[10px] px-2 py-1 rounded-full font-medium flex-shrink-0 ${priorityColor[prio] || "bg-slate-100"}`}>{prio}</span>
                      <div><p className="text-sm text-slate-700">{r.recommendation || r.recommandation}</p><p className="text-[10px] text-slate-400 mt-0.5">{r.regulation || r.reglementation}</p></div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Print */}
          <div className="text-center">
            <button onClick={() => window.print()} className="px-6 py-2.5 rounded-xl bg-teal-600 text-white font-medium hover:bg-teal-700 transition text-sm">{t("print")}</button>
          </div>
        </div>
      )}
    </div>
  );
}
