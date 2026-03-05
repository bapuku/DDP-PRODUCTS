"use client";

import { useState } from "react";
import Link from "next/link";

interface AnomalyDetail { type: string; field: string; value: unknown; severity: string; message: string; }
interface ComplianceCheck { applicable: boolean; status: string; ref: string; }
interface ProductResult {
  dpp_id: string; product_name: string; sector: string; manufacturer: string; country: string;
  dpp_uri: string; completeness: number;
  compliance: { overall: string; score: number; checks: Record<string, ComplianceCheck> };
  anomalies: { count: number; anomalies: AnomalyDetail[]; data_quality_score: number };
  impact: { gwp_total: number; carbon_class: string; water_litres: number; energy_mj: number; recyclability_pct: number; eol_recovery_pct: number; renewable_energy_pct: number };
  blockchain_hash: string; lifecycle_phase: string;
}
interface Stats {
  total: number; compliant: number; non_compliant: number; anomalies_total: number;
  anomaly_rate: number; avg_completeness: number; avg_data_quality: number;
  sectors: Record<string, number>; carbon_classes: Record<string, number>;
}

const SEVERITY_COLOR: Record<string, string> = { critical: "bg-red-600 text-white", high: "bg-red-100 text-red-700", medium: "bg-amber-100 text-amber-700", low: "bg-blue-100 text-blue-700" };
const CC_COLOR: Record<string, string> = { A: "bg-emerald-500", B: "bg-green-400", C: "bg-lime-400", D: "bg-yellow-400", E: "bg-amber-400", F: "bg-red-400", "N/A": "bg-slate-300" };

export default function DemoWorkflowPage() {
  const [data, setData] = useState<{ stats: Stats; results: ProductResult[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "anomalies" | "non_compliant">("all");

  async function runWorkflow() {
    setLoading(true); setData(null);
    try {
      const res = await fetch("/api/v1/demo/run", { method: "POST" });
      if (res.ok) setData(await res.json());
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }

  const filtered = data?.results.filter(r => {
    if (filter === "anomalies") return r.anomalies.count > 0;
    if (filter === "non_compliant") return r.compliance.overall !== "COMPLIANT";
    return true;
  }) ?? [];

  return (
    <div className="max-w-6xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Workflow Complet — 50 Produits Demo</h2>
          <p className="text-sm text-slate-500 mt-1">Pipeline DPP complet : creation, conformite, detection d&apos;anomalies, evaluation d&apos;impact, ancrage blockchain</p>
        </div>
        <button onClick={runWorkflow} disabled={loading} className="px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-600 text-white font-bold text-sm shadow-md hover:shadow-lg transition disabled:opacity-50">
          {loading ? "Execution en cours..." : "Lancer le workflow complet"}
        </button>
      </div>

      {loading && (
        <div className="rounded-xl border border-teal-200 bg-teal-50 p-8 text-center">
          <div className="animate-spin inline-block w-10 h-10 border-4 border-teal-400 border-t-transparent rounded-full mb-3" />
          <p className="text-teal-700 font-medium">Traitement de 50 produits : DPP + Conformite + Anomalies + Impact + Blockchain...</p>
        </div>
      )}

      {data && (
        <>
          {/* Stats dashboard */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
              <p className="text-3xl font-bold text-slate-800">{data.stats.total}</p>
              <p className="text-xs text-slate-500 mt-1">Produits traites</p>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-center">
              <p className="text-3xl font-bold text-emerald-700">{data.stats.compliant}</p>
              <p className="text-xs text-emerald-600 mt-1">Conformes</p>
            </div>
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-center">
              <p className="text-3xl font-bold text-red-700">{data.stats.non_compliant}</p>
              <p className="text-xs text-red-600 mt-1">Non conformes</p>
            </div>
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-center">
              <p className="text-3xl font-bold text-amber-700">{data.stats.anomalies_total}</p>
              <p className="text-xs text-amber-600 mt-1">Anomalies detectees</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
              <p className="text-3xl font-bold text-teal-700">{data.stats.avg_completeness}%</p>
              <p className="text-xs text-slate-500 mt-1">Completude moy.</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
              <p className="text-3xl font-bold text-sky-700">{data.stats.avg_data_quality}%</p>
              <p className="text-xs text-slate-500 mt-1">Qualite donnees moy.</p>
            </div>
          </div>

          {/* Sector + carbon class breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-800 mb-3">Repartition par secteur</h3>
              <div className="space-y-2">
                {Object.entries(data.stats.sectors).sort((a, b) => b[1] - a[1]).map(([sector, count]) => (
                  <div key={sector} className="flex items-center gap-2">
                    <span className="text-xs text-slate-500 w-24 capitalize">{sector}</span>
                    <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-teal-400 rounded-full" style={{ width: `${count / data.stats.total * 100}%` }} />
                    </div>
                    <span className="text-xs font-bold text-slate-700 w-8 text-right">{count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h3 className="font-semibold text-slate-800 mb-3">Classes carbone (EF 3.1)</h3>
              <div className="flex gap-2 flex-wrap">
                {["A", "B", "C", "D", "E", "F", "N/A"].map(cls => {
                  const count = data.stats.carbon_classes[cls] || 0;
                  if (count === 0) return null;
                  return (
                    <div key={cls} className="text-center">
                      <div className={`w-12 h-12 rounded-xl ${CC_COLOR[cls]} flex items-center justify-center text-white font-black text-lg`}>{cls}</div>
                      <p className="text-xs text-slate-600 mt-1 font-semibold">{count}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="flex gap-2">
            {([["all", `Tous (${data.results.length})`], ["anomalies", `Anomalies (${data.results.filter(r => r.anomalies.count > 0).length})`], ["non_compliant", `Non conformes (${data.stats.non_compliant})`]] as const).map(([f, label]) => (
              <button key={f} onClick={() => setFilter(f)} className={`px-4 py-2 rounded-lg text-sm font-medium transition ${filter === f ? "bg-teal-600 text-white" : "bg-white border border-slate-200 text-slate-600 hover:border-teal-400"}`}>
                {label}
              </button>
            ))}
          </div>

          {/* Product results list */}
          <div className="space-y-2">
            {filtered.map(r => {
              const isExpanded = expanded === r.dpp_id;
              const hasAnomaly = r.anomalies.count > 0;
              const isCompliant = r.compliance.overall === "COMPLIANT";
              return (
                <div key={r.dpp_id} className={`rounded-xl border transition-all ${hasAnomaly ? "border-amber-300 bg-amber-50/50" : isCompliant ? "border-slate-200 bg-white" : "border-red-200 bg-red-50/30"} ${isExpanded ? "shadow-lg" : ""}`}>
                  <button onClick={() => setExpanded(isExpanded ? null : r.dpp_id)} className="w-full p-4 flex items-center gap-3 text-left">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 ${CC_COLOR[r.impact.carbon_class] || "bg-slate-400"}`}>
                      {r.impact.carbon_class}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm text-slate-800 truncate">{r.product_name}</p>
                      <p className="text-xs text-slate-500">{r.dpp_id} · {r.sector} · {r.manufacturer}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {hasAnomaly && <span className="text-[10px] px-2 py-1 rounded-full bg-amber-200 text-amber-800 font-medium">{r.anomalies.count} anomalie{r.anomalies.count > 1 ? "s" : ""}</span>}
                      <span className={`text-[10px] px-2 py-1 rounded-full font-medium ${isCompliant ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>{isCompliant ? "Conforme" : "Non conforme"}</span>
                      <span className="text-[10px] px-2 py-1 rounded-full bg-slate-100 text-slate-600">{Math.round(r.completeness * 100)}%</span>
                      <span className="text-slate-400 text-sm">{isExpanded ? "▲" : "▼"}</span>
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="px-4 pb-4 space-y-3 border-t border-current/10">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                        <div className="rounded-lg bg-white border border-slate-100 p-3 text-center">
                          <p className="text-[10px] text-slate-400">CO2 total</p>
                          <p className="text-sm font-bold text-slate-800">{r.impact.gwp_total.toLocaleString()} kg</p>
                        </div>
                        <div className="rounded-lg bg-white border border-slate-100 p-3 text-center">
                          <p className="text-[10px] text-slate-400">Eau</p>
                          <p className="text-sm font-bold text-slate-800">{r.impact.water_litres.toLocaleString()} L</p>
                        </div>
                        <div className="rounded-lg bg-white border border-slate-100 p-3 text-center">
                          <p className="text-[10px] text-slate-400">Recyclabilite</p>
                          <p className="text-sm font-bold text-slate-800">{r.impact.recyclability_pct}%</p>
                        </div>
                        <div className="rounded-lg bg-white border border-slate-100 p-3 text-center">
                          <p className="text-[10px] text-slate-400">Energie renouvelable</p>
                          <p className="text-sm font-bold text-slate-800">{r.impact.renewable_energy_pct}%</p>
                        </div>
                      </div>

                      {/* Compliance checks */}
                      <div className="rounded-lg bg-white border border-slate-100 p-3">
                        <p className="text-xs font-semibold text-slate-500 uppercase mb-2">Conformite reglementaire</p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(r.compliance.checks).map(([k, c]) => (
                            <span key={k} className={`text-[10px] px-2 py-1 rounded-full ${c.status === "Compliant" ? "bg-emerald-100 text-emerald-700" : c.status === "NON-COMPLIANT" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-500"}`}>
                              {k}: {c.status}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Anomalies */}
                      {r.anomalies.anomalies.length > 0 && (
                        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
                          <p className="text-xs font-semibold text-amber-700 uppercase mb-2">Anomalies detectees ({r.anomalies.count})</p>
                          <div className="space-y-1">
                            {r.anomalies.anomalies.map((a, i) => (
                              <div key={i} className="flex items-start gap-2">
                                <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium flex-shrink-0 ${SEVERITY_COLOR[a.severity] || "bg-slate-100"}`}>{a.severity}</span>
                                <p className="text-xs text-slate-700">{a.message}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="flex gap-2">
                        <span className="text-[10px] text-slate-400 font-mono">{r.blockchain_hash}</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
