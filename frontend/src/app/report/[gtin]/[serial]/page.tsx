"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";

interface Phase { phase: number; id: string; label: string; status: string; }
interface Recommendation { priority?: string; priorite?: string; category?: string; categorie?: string; recommendation?: string; recommandation?: string; regulation?: string; reglementation?: string; }

function SectionHeader({ num, title }: { num: number; title: string }) {
  return (
    <div className="flex items-center gap-3 mb-3 print:mb-2">
      <span className="w-8 h-8 rounded-full bg-teal-600 text-white flex items-center justify-center text-sm font-bold print:bg-black">{num}</span>
      <h3 className="text-base font-bold text-slate-800 uppercase tracking-wide">{title}</h3>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | number | undefined | null }) {
  return (
    <div className="py-1.5 border-b border-slate-100 flex justify-between items-baseline">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs font-semibold text-slate-800 text-right ml-2">{value != null ? String(value) : "—"}</span>
    </div>
  );
}

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

  const product: Record<string, unknown> = (report.product as Record<string, unknown>) || {};
  const phases: Phase[] = Array.isArray(report.lifecycle_phases) ? report.lifecycle_phases as Phase[] : [];
  const insurance: Record<string, unknown> = (report.insurance_traceability as Record<string, unknown>) || {};
  const compliance: Record<string, Record<string, string>> = (report.compliance_summary as Record<string, Record<string, string>>) || {};
  const recommendations: Recommendation[] = Array.isArray(report.recommendations) ? report.recommendations as Recommendation[] : [];

  const priorityColor: Record<string, string> = { high: "bg-red-100 text-red-700", haute: "bg-red-100 text-red-700", medium: "bg-amber-100 text-amber-700", moyenne: "bg-amber-100 text-amber-700", normal: "bg-blue-100 text-blue-700", normale: "bg-blue-100 text-blue-700" };

  return (
    <div className="max-w-5xl space-y-6 print:space-y-3 print:text-[11px]">
      {/* ═══ REPORT COVER ═══ */}
      <div className="rounded-xl border-2 border-teal-600 bg-white p-6 text-center print:border print:p-4">
        <p className="text-xs text-teal-600 font-semibold tracking-widest uppercase">Union Europeenne — Digital Product Passport</p>
        <p className="text-[10px] text-slate-400 mt-1">Reglement (UE) 2024/1781 (ESPR) · Chapitre III, Articles 9-15</p>
        <h1 className="text-xl font-bold text-slate-800 mt-3">RAPPORT D&apos;EVALUATION DU CYCLE DE VIE</h1>
        <p className="text-sm text-slate-500 mt-1">Life Cycle Assessment Report — Modele reglementaire DPP</p>
        <div className="mt-4 inline-flex flex-col items-start text-left text-xs text-slate-600 bg-slate-50 rounded-lg p-3 border border-slate-200">
          <Field label="DPP-ID (GS1 Digital Link)" value={String(product.dpp_uri)} />
          <Field label="GTIN-14" value={String(product.gtin)} />
          <Field label="N° Serie" value={String(product.serial_number)} />
          <Field label="Score completude DPP" value={`${Math.round(Number(product.completeness || 0) * 100)}%`} />
          <Field label="Date d'emission" value={String(report.generated_at).slice(0, 10)} />
          <Field label="Statut DPP" value="Publie" />
        </div>
        <div className="mt-3 flex justify-center gap-2 print:hidden">
          <button onClick={() => window.print()} className="px-5 py-2 rounded-lg bg-teal-600 text-white text-sm font-medium hover:bg-teal-700 transition">Exporter PDF</button>
          <Link href={`/dpp/${gtin}/${serial}`} className="px-4 py-2 rounded-lg bg-white border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition">Voir DPP</Link>
        </div>
      </div>

      {/* ═══ SECTION 1 — CADRE REGLEMENTAIRE ═══ */}
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <SectionHeader num={1} title="Cadre reglementaire et obligations legales" />
        <div className="overflow-auto">
          <table className="w-full text-xs border-collapse">
            <thead><tr className="bg-slate-50"><th className="text-left p-2 border border-slate-200">Instrument</th><th className="text-left p-2 border border-slate-200">Articles</th><th className="text-left p-2 border border-slate-200">Domaine</th></tr></thead>
            <tbody>
              <tr><td className="p-2 border border-slate-100">Reglement (UE) 2024/1781 — ESPR</td><td className="p-2 border border-slate-100">Art. 9-15, Annexe III</td><td className="p-2 border border-slate-100">DPP, donnees cycle de vie</td></tr>
              <tr><td className="p-2 border border-slate-100">Reglement (UE) 2023/1542 — Batteries</td><td className="p-2 border border-slate-100">Art. 7, 11, 77-78, Annexe XIII</td><td className="p-2 border border-slate-100">Passeport batterie, empreinte carbone</td></tr>
              <tr><td className="p-2 border border-slate-100">Reglement (UE) 2024/1689 — AI Act</td><td className="p-2 border border-slate-100">Art. 12, 14, 18, 19</td><td className="p-2 border border-slate-100">Journalisation IA, supervision humaine</td></tr>
              <tr><td className="p-2 border border-slate-100">ISO 14040:2006 / 14044:2006</td><td className="p-2 border border-slate-100">Phases 1-4 ACV</td><td className="p-2 border border-slate-100">Methodologie evaluation cycle de vie</td></tr>
              <tr><td className="p-2 border border-slate-100">Methode EF 3.1 (Comm. 2021/2279)</td><td className="p-2 border border-slate-100">16 categories d&apos;impact</td><td className="p-2 border border-slate-100">Empreinte environnementale produit</td></tr>
              <tr><td className="p-2 border border-slate-100">GS1 Digital Link v1.6.0 / ISO 18975</td><td className="p-2 border border-slate-100">URI, GTIN-14, QR</td><td className="p-2 border border-slate-100">Identifiant unique, transporteur donnees</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* ═══ SECTION 2 — IDENTIFICATION PRODUIT ═══ */}
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <SectionHeader num={2} title="Identification du produit et DPP" />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6">
          <Field label="Denomination commerciale" value={String(product.product_name || product.gtin)} />
          <Field label="GTIN-14" value={String(product.gtin)} />
          <Field label="N° serie" value={String(product.serial_number)} />
          <Field label="Secteur ESPR" value={String(product.sector)} />
          <Field label="Pays fabrication" value={String(product.manufacturing_country || "EU-27")} />
          <Field label="Granularite DPP" value="Unite individuelle" />
          <Field label="DPP URI (GS1 Digital Link)" value={String(product.dpp_uri)} />
          <Field label="Completude DPP" value={`${Math.round(Number(product.completeness || 0) * 100)}% (objectif ≥85%)`} />
          <Field label="Poids (kg)" value={String(product.weight_kg || product.Product_Weight_kg || "—")} />
        </div>
      </section>

      {/* ═══ SECTION 3 — OPERATEUR ECONOMIQUE ═══ */}
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <SectionHeader num={3} title="Identification de l'operateur economique" />
        <div className="grid grid-cols-2 gap-x-6">
          <Field label="Denomination legale" value="SovereignPiAlpha France Ltd" />
          <Field label="Adresse" value="36 rue Scheffer, 75116 Paris" />
          <Field label="Contact DPP" value="sovereignpialphafrance-contact@startmail.com" />
          <Field label="Plateforme DPP" value="EU DPP Platform v0.1.0" />
        </div>
      </section>

      {/* ═══ SECTION 4 — OBJECTIF ET CHAMP (ISO 14040 Phase 1) ═══ */}
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <SectionHeader num={4} title="Objectif et champ de l'evaluation (ISO 14040 — Phase 1)" />
        <div className="grid grid-cols-2 gap-x-6">
          <Field label="Methode ACV" value="ISO 14040/44 + PEF/EF 3.1" />
          <Field label="Unite fonctionnelle" value="1 unite produit sur cycle de vie complet" />
          <Field label="Perimetre systeme" value="Berceau-a-tombeau (cradle-to-grave)" />
          <Field label="Application" value="Conformite DPP ESPR + Declaration EPD" />
        </div>
      </section>

      {/* ═══ SECTION 5 — PHASES DU CYCLE DE VIE ═══ */}
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <SectionHeader num={5} title="Phases du cycle de vie — Donnees et obligations DPP" />
        <div className="flex gap-0.5 mb-3">
          {phases.map((p, idx) => (
            <div key={idx} className={`flex-1 rounded-lg p-2 text-center text-[9px] ${p.status === "completed" ? "bg-emerald-100 text-emerald-700" : p.status === "current" ? "bg-teal-100 text-teal-800 ring-2 ring-teal-400" : "bg-slate-50 text-slate-400"}`}>
              <span className="font-bold block">{String(p.phase)}</span>
              <span className="leading-tight block">{String(p.label)}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-500">10 phases de cycle de vie conforme ESPR Art. 5-15. Chaque phase genere des donnees DPP obligatoires.</p>
      </section>

      {/* ═══ SECTION 6 — ESPR Annex III (ICV baseline) ═══ */}
      {report.espr_annex_iii ? (
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <SectionHeader num={6} title="Inventaire — ESPR Annexe III (Categories de donnees DPP)" />
          <p className="text-xs text-slate-400 mb-3">{String((report.espr_annex_iii as Record<string, unknown>).standard)}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {Object.entries((report.espr_annex_iii as Record<string, unknown>).categories as Record<string, Record<string, string>>).map(([key, cat]) => (
              <div key={key} className="flex items-start gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs">
                <span className="font-mono font-bold text-teal-600 w-5">{key}</span>
                <div className="min-w-0"><p className="font-medium text-slate-700">{cat.name}</p><p className="text-slate-500 truncate">{cat.value}</p></div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {/* ═══ SECTION 6b — Battery Annex XIII ═══ */}
      {report.battery_annex_xiii ? (
        <section className="rounded-xl border border-amber-200 bg-amber-50 p-5">
          <div className="flex items-center gap-3 mb-3">
            <span className="w-8 h-8 rounded-full bg-amber-600 text-white flex items-center justify-center text-sm font-bold">6b</span>
            <h3 className="text-base font-bold text-amber-800 uppercase tracking-wide">Battery Reg (EU) 2023/1542 — Annexe XIII</h3>
          </div>
          <p className="text-xs text-amber-600 mb-3">{String((report.battery_annex_xiii as Record<string, unknown>).total_mandatory_attributes)} attributs obligatoires</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {Object.entries((report.battery_annex_xiii as Record<string, unknown>).clusters as Record<string, Record<string, unknown>>).map(([key, cluster]) => (
              <div key={key} className="rounded-lg bg-white border border-amber-100 p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-amber-700">{String(cluster.name)}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-600">{String(cluster.fields)} champs</span>
                </div>
                <div className="flex flex-wrap gap-1">{(cluster.items as string[]).map((item: string, j: number) => (
                  <span key={j} className="text-[9px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-600 border border-amber-100">{item}</span>
                ))}</div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {/* ═══ SECTION 7 — EVALUATION DES IMPACTS EF 3.1 ═══ */}
      {report.lca_environmental_footprint ? (() => {
        const lca = report.lca_environmental_footprint as Record<string, unknown>;
        const cats = (lca.impact_categories as Array<Record<string, unknown>>) || [];
        return (
          <section className="rounded-xl border border-green-200 bg-green-50 p-5">
            <SectionHeader num={7} title="Evaluation des impacts — EF 3.1 (ISO 14044 — Phase 3)" />
            <p className="text-xs text-green-600 mb-1">{String(lca.methodology)} · {String(lca.system_boundary)}</p>
            <div className="flex gap-4 items-baseline mb-3">
              <span className="text-lg font-bold text-green-800">{String(lca.total_carbon_footprint_kg_co2eq)} kg CO₂-eq</span>
              <span className="text-sm font-bold px-2 py-0.5 rounded bg-green-200 text-green-800">Classe {String(lca.carbon_footprint_class)}</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-1.5">
              {cats.map((c: Record<string, unknown>, i: number) => (
                <div key={i} className="rounded-lg bg-white border border-green-100 p-2 text-center">
                  <p className="text-[9px] text-slate-400 leading-tight">{String(c.name)}</p>
                  <p className="text-xs font-bold text-green-700 mt-0.5">{String(c.value)}</p>
                  <p className="text-[8px] text-slate-400">{String(c.unit)}</p>
                </div>
              ))}
            </div>
          </section>
        );
      })() : null}

      {/* ═══ SECTION 8 — INTERPRETATION ET RESULTATS ═══ */}
      <section className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <SectionHeader num={8} title="Interpretation et resultats DPP (ISO 14044 — Phase 4)" />
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
      </section>

      {/* ═══ SECTION 9 — TRACABILITE ASSURANTIELLE ═══ */}
      <section className="rounded-xl border border-teal-200 bg-teal-50 p-5">
        <SectionHeader num={9} title="Tracabilite assurantielle et audit trail" />
        <p className="text-sm text-teal-700 mb-3">{String(insurance.description)}</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
          <div className="bg-white rounded-lg p-3 border border-teal-100">
            <span className="text-xs text-slate-400">Blockchain</span>
            <p className="font-semibold text-teal-700">{String(insurance.integrite_blockchain || insurance.blockchain_integrity)}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border border-teal-100">
            <span className="text-xs text-slate-400">Decisions IA</span>
            <p className="font-semibold text-teal-700">{String(insurance.nombre_decisions_ia || insurance.ai_decisions_count)}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border border-teal-100">
            <span className="text-xs text-slate-400">Score confiance</span>
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
      </section>

      {/* ═══ SECTION 10 — CONFORMITE CHECKLIST ═══ */}
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <SectionHeader num={10} title="Conformite reglementaire — Checklist executoire" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {Object.entries(compliance).map(([key, val]) => (
            <div key={key} className="flex items-center gap-3 p-3 rounded-lg bg-emerald-50 border border-emerald-100">
              <span className="text-emerald-600 text-lg">✓</span>
              <div className="flex-1 min-w-0">
                <span className="text-xs font-semibold text-emerald-700">{val.article}</span>
                <p className="text-xs text-slate-600 truncate">{val.detail}</p>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-medium">{val.statut || val.status}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ SECTION 11 — DECLARATION ═══ */}
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <SectionHeader num={11} title="Declaration et signatures" />
        <div className="bg-slate-50 rounded-lg p-4 text-xs text-slate-600 space-y-2">
          <p>L&apos;operateur economique ci-dessus declare que les informations contenues dans le present rapport sont exactes, completes et conformes aux exigences des reglements (UE) 2024/1781, (UE) 2023/1542, et (UE) 2024/1689.</p>
          <div className="grid grid-cols-2 gap-4 mt-3">
            <div className="border border-slate-200 rounded p-3 h-16"><p className="text-[10px] text-slate-400">Signature operateur economique</p></div>
            <div className="border border-slate-200 rounded p-3 h-16"><p className="text-[10px] text-slate-400">Validation verificateur independant (ISO 14044 §6)</p></div>
          </div>
        </div>
      </section>

      {/* ═══ SECTION 12 — BIBLIOGRAPHIE ═══ */}
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <SectionHeader num={12} title="Bibliographie — Sources reglementaires" />
        <ul className="text-xs text-slate-600 space-y-1 list-disc list-inside">
          {((report.regulation_basis as string[]) || [
            "ESPR (EU) 2024/1781 Art. 9 — DPP Requirements",
            "ESPR Annex III — Baseline DPP Data Categories",
            "Battery Reg (EU) 2023/1542 Annex XIII — 80 Mandatory Attributes",
            "EU AI Act (EU) 2024/1689 Art. 12 — Logging",
            "ISO 14040:2006 / ISO 14044:2006 — LCA Methodology",
            "EU Environmental Footprint EF 3.1 — 16 Impact Categories",
            "GS1 Digital Link (ISO/IEC 18975) — Data Carriers",
            "EPCIS 2.0 (ISO/IEC 19987) — Supply Chain",
          ]).map((r: string, i: number) => <li key={i}>{r}</li>)}
        </ul>
      </section>

      {/* Footer */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-center text-xs text-slate-400 print:border-0">
        <p>Genere le : {String(report.generated_at)}</p>
        <p>{String(report.generated_by)}</p>
        <p className="mt-1 text-[9px]">Ce rapport constitue un instrument de conformite reglementaire au titre du Reglement (UE) 2024/1781 (ESPR).</p>
      </div>
    </div>
  );
}
