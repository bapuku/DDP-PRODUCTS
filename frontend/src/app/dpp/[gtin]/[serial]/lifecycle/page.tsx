"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";

interface PhaseData {
  id: string;
  label: string;
  regulation: string;
  agent: string;
  agentId: string;
  status: "completed" | "current" | "pending";
  dataFields: string[];
  description: string;
  outputs: string[];
}

const PHASES_EN: PhaseData[] = [
  { id: "pre_conception", label: "Phase 0: Pre-conception", regulation: "ESPR Art. 5–7", agent: "Data Collection", agentId: "data_collection", status: "completed", description: "Ecodesign performance thresholds — durability, reusability, upgradability, reparability, recyclability, substance restrictions. ISO 14006:2020 ecodesign integration.", dataFields: ["Ecodesign requirements", "Substance restrictions (REACH)", "Recyclability targets", "Durability specifications", "Material composition forecast"], outputs: ["Ecodesign compliance checklist", "Material restriction report", "Design-stage LCA estimate"] },
  { id: "design", label: "Phase 1: Design", regulation: "ESPR Art. 5–7 + ISO 14006", agent: "Data Collection", agentId: "data_collection", status: "completed", description: "Material composition data, recyclability specifications, repairability scores, and design-stage LCA estimates that feed into DPP entries.", dataFields: ["Bill of Materials (BOM)", "Material composition (%)", "Recyclability score", "Repairability index", "Carbon footprint estimate (design)", "Substances of concern (SVHC)"], outputs: ["BOM register", "Design LCA report", "Repairability score card"] },
  { id: "prototype", label: "Phase 2: Prototyping", regulation: "Battery Reg Art. 48–52", agent: "Data Collection", agentId: "data_collection", status: "completed", description: "Conformity assessment test results, prototype-level carbon footprint verification, raw material origin traceability.", dataFields: ["Prototype test results", "Carbon footprint verification", "Conformity assessment", "Critical raw materials sourcing", "Due diligence documentation (OECD)"], outputs: ["Test certification", "Prototype carbon footprint", "OECD due diligence report"] },
  { id: "supplier_qual", label: "Phase 3: Suppliers", regulation: "Battery Reg Art. 48–52", agent: "Supply Chain", agentId: "supply_chain", status: "completed", description: "Supplier identification, raw material origin traceability, due diligence for cobalt, lithium, nickel, natural graphite. EPCIS 2.0 event capture.", dataFields: ["Supplier identification records", "Raw material origin", "Due diligence (Co, Li, Ni, graphite)", "EPCIS supply chain events", "Conflict minerals assessment", "Tier-1/2/3 supplier mapping"], outputs: ["Supply chain map (Neo4j)", "Due diligence report", "EPCIS event log"] },
  { id: "manufacturing", label: "Phase 4: Manufacturing", regulation: "ESPR Art. 9 + Battery Annex XIII", agent: "DDP Generation", agentId: "ddp_generation", status: "current", description: "Primary DPP creation event: batch/serial assignment, facility ID, carbon footprint per plant/batch, energy consumption, QC results, CE marking, Declaration of Conformity.", dataFields: ["GTIN-14 (ISO/IEC 15459)", "Serial number / Batch number", "Manufacturing facility (GLN)", "Production date", "Carbon footprint (site-specific, JRC method)", "Energy consumption data", "QC results", "CE marking", "Declaration of Conformity", "BMS calibration (batteries)"], outputs: ["Digital Product Passport (JSON-LD)", "GS1 Digital Link URI", "QR code (ISO/IEC 18004)", "NFC NDEF payload", "RFID SGTIN-96"] },
  { id: "distribution", label: "Phase 5: Distribution", regulation: "ESPR Art. 13 + EPCIS 2.0", agent: "Document Generation", agentId: "document_generation", status: "pending", description: "DPP registry registration (operational July 2026), data carrier affixation, logistics carbon footprint, customs (EORI), transport safety.", dataFields: ["DPP registry registration", "Data carrier verification", "Logistics carbon footprint", "Customs documentation (EORI)", "Transport safety compliance", "EPCIS ObjectEvent (shipping)"], outputs: ["Registry confirmation", "Shipping EPCIS event", "Customs declaration"] },
  { id: "active_use", label: "Phase 6: Active Use (BMS IoT)", regulation: "Battery Reg Art. 11 + Annex VII", agent: "Predictive Scoring", agentId: "predictive", status: "pending", description: "Consumer-facing sustainability info, maintenance guides, dynamic BMS reporting: State of Health, charge/discharge cycles, capacity degradation.", dataFields: ["State of Health (SoH)", "Charge/discharge cycle count", "Capacity degradation (%)", "Temperature history", "Energy throughput (kWh)", "Maintenance records", "Consumer sustainability info"], outputs: ["Dynamic performance report", "SoH certificate", "Maintenance log"] },
  { id: "eol", label: "Phase 7: Second Life", regulation: "Battery Reg Art. 14", agent: "Circular Economy", agentId: "circular_economy", status: "pending", description: "SoH assessment, repurposing documentation (new battery passport required), updated performance specs. Refurbishment, repurpose, or recycling pathway.", dataFields: ["SoH assessment (≥80% threshold)", "Repurposing documentation", "Updated performance specs", "New DPP (if repurposed)", "Refurbishment records", "Second-life operator ID"], outputs: ["Second-life assessment", "Repurpose decision", "Updated DPP"] },
  { id: "recycling", label: "Phase 8: Recycling", regulation: "Battery Reg Art. 8, 57 + WEEE", agent: "Recycling Agent", agentId: "recycling", status: "pending", description: "Dismantling instructions, material recovery rates, recycled content tracking. Targets 2031: 16% Co, 6% Li, 6% Ni, 85% Pb. Targets 2036: increased.", dataFields: ["Dismantling instructions", "Tools & safety precautions", "Material recovery rates", "Recycled content (% Co, Li, Ni, Pb)", "Collection target compliance (73% by 2030)", "WEEE reporting"], outputs: ["Dismantling guide", "Material recovery report", "Recycled content certificate"] },
  { id: "destruction", label: "Phase 9: Destruction", regulation: "WEEE + Waste Framework Dir.", agent: "Destruction Agent", agentId: "destruction", status: "pending", description: "Final disposition records, EPR reporting, collection target compliance. Battery passport ceases to exist after recycling is complete.", dataFields: ["Destruction authorization", "Final disposition record", "EPR reporting", "Environmental impact assessment", "Hazardous waste manifest", "Destruction certificate"], outputs: ["Destruction proof", "EPR compliance report", "DPP closure record"] },
];

const PHASES_FR: PhaseData[] = [
  { id: "pre_conception", label: "Phase 0 : Pré-conception", regulation: "ESPR Art. 5–7", agent: "Collecte de Données", agentId: "data_collection", status: "completed", description: "Seuils de performance écoconception — durabilité, réutilisabilité, évolutivité, réparabilité, recyclabilité, restrictions de substances. Intégration ISO 14006:2020.", dataFields: ["Exigences écoconception", "Restrictions substances (REACH)", "Objectifs recyclabilité", "Spécifications durabilité", "Prévision composition matériaux"], outputs: ["Checklist conformité écoconception", "Rapport restrictions matériaux", "Estimation ACV conception"] },
  { id: "design", label: "Phase 1 : Conception", regulation: "ESPR Art. 5–7 + ISO 14006", agent: "Collecte de Données", agentId: "data_collection", status: "completed", description: "Données de composition, spécifications de recyclabilité, scores de réparabilité et estimations ACV qui alimentent le DPP.", dataFields: ["Nomenclature (BOM)", "Composition matériaux (%)", "Score recyclabilité", "Indice réparabilité", "Empreinte carbone (conception)", "Substances préoccupantes (SVHC)"], outputs: ["Registre BOM", "Rapport ACV conception", "Fiche score réparabilité"] },
  { id: "prototype", label: "Phase 2 : Prototypage", regulation: "Règlement Batteries Art. 48–52", agent: "Collecte de Données", agentId: "data_collection", status: "completed", description: "Résultats d'évaluation de conformité, vérification empreinte carbone prototype, traçabilité origines matières premières.", dataFields: ["Résultats tests prototype", "Vérification empreinte carbone", "Évaluation conformité", "Approvisionnement matières critiques", "Documentation diligence raisonnable (OCDE)"], outputs: ["Certification tests", "Empreinte carbone prototype", "Rapport diligence OCDE"] },
  { id: "supplier_qual", label: "Phase 3 : Fournisseurs", regulation: "Règlement Batteries Art. 48–52", agent: "Chaîne d'Approvisionnement", agentId: "supply_chain", status: "completed", description: "Identification fournisseurs, traçabilité origines, diligence raisonnable Co, Li, Ni, graphite. Capture événements EPCIS 2.0.", dataFields: ["Identification fournisseurs", "Origine matières premières", "Diligence raisonnable (Co, Li, Ni, graphite)", "Événements EPCIS", "Évaluation minerais de conflit", "Cartographie fournisseurs Tier 1/2/3"], outputs: ["Cartographie chaîne (Neo4j)", "Rapport diligence", "Journal EPCIS"] },
  { id: "manufacturing", label: "Phase 4 : Fabrication", regulation: "ESPR Art. 9 + Batteries Annexe XIII", agent: "Génération DDP", agentId: "ddp_generation", status: "current", description: "Événement principal de création DPP : attribution lot/série, ID usine, empreinte carbone par site/lot, données énergie, contrôle qualité, marquage CE.", dataFields: ["GTIN-14 (ISO/IEC 15459)", "Numéro série / lot", "Usine fabrication (GLN)", "Date production", "Empreinte carbone (site, méthode JRC)", "Consommation énergie", "Résultats CQ", "Marquage CE", "Déclaration de Conformité", "Calibration BMS (batteries)"], outputs: ["Passeport Numérique Produit (JSON-LD)", "URI GS1 Digital Link", "Code QR (ISO/IEC 18004)", "Payload NFC NDEF", "RFID SGTIN-96"] },
  { id: "distribution", label: "Phase 5 : Distribution", regulation: "ESPR Art. 13 + EPCIS 2.0", agent: "Génération Documents", agentId: "document_generation", status: "pending", description: "Enregistrement registre DPP (opérationnel juillet 2026), vérification support données, empreinte carbone logistique, douanes (EORI).", dataFields: ["Enregistrement registre DPP", "Vérification support données", "Empreinte carbone logistique", "Documentation douanière (EORI)", "Conformité transport", "EPCIS ObjectEvent (expédition)"], outputs: ["Confirmation registre", "Événement EPCIS expédition", "Déclaration douanière"] },
  { id: "active_use", label: "Phase 6 : Utilisation (BMS IoT)", regulation: "Règlement Batteries Art. 11 + Annexe VII", agent: "Scoring Prédictif", agentId: "predictive", status: "pending", description: "Info durabilité consommateur, guides maintenance, reporting BMS dynamique : état de santé, cycles charge/décharge, dégradation capacité.", dataFields: ["État de santé (SdS)", "Compteur cycles charge/décharge", "Dégradation capacité (%)", "Historique température", "Énergie cumulée (kWh)", "Registre maintenance", "Info durabilité consommateur"], outputs: ["Rapport performance dynamique", "Certificat SdS", "Journal maintenance"] },
  { id: "eol", label: "Phase 7 : Seconde Vie", regulation: "Règlement Batteries Art. 14", agent: "Économie Circulaire", agentId: "circular_economy", status: "pending", description: "Évaluation SdS, documentation réemploi (nouveau passeport requis), specs performance mises à jour. Reconditionnement ou recyclage.", dataFields: ["Évaluation SdS (seuil ≥80%)", "Documentation réemploi", "Specs performance mises à jour", "Nouveau DPP (si réemploi)", "Registre reconditionnement", "ID opérateur seconde vie"], outputs: ["Évaluation seconde vie", "Décision réemploi", "DPP mis à jour"] },
  { id: "recycling", label: "Phase 8 : Recyclage", regulation: "Règlement Batteries Art. 8, 57 + DEEE", agent: "Agent Recyclage", agentId: "recycling", status: "pending", description: "Instructions démontage, taux récupération matériaux, suivi contenu recyclé. Objectifs 2031 : 16% Co, 6% Li, 6% Ni, 85% Pb.", dataFields: ["Instructions démontage", "Outils & précautions sécurité", "Taux récupération matériaux", "Contenu recyclé (% Co, Li, Ni, Pb)", "Conformité objectif collecte (73% d'ici 2030)", "Reporting DEEE"], outputs: ["Guide démontage", "Rapport récupération matériaux", "Certificat contenu recyclé"] },
  { id: "destruction", label: "Phase 9 : Destruction", regulation: "DEEE + Directive Cadre Déchets", agent: "Agent Destruction", agentId: "destruction", status: "pending", description: "Dossiers disposition finale, reporting REP, conformité objectifs collecte. Le passeport batterie cesse d'exister après recyclage.", dataFields: ["Autorisation destruction", "Dossier disposition finale", "Reporting REP", "Évaluation impact environnemental", "Manifeste déchets dangereux", "Certificat destruction"], outputs: ["Preuve destruction", "Rapport conformité REP", "Dossier clôture DPP"] },
];

function getLocale(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  return m ? m[1].trim() : "en";
}

export default function LifecycleTimelinePage() {
  const t = useTranslations("lifecycle");
  const params = useParams();
  const gtin = params?.gtin as string;
  const serial = params?.serial as string;
  const locale = getLocale();
  const phases = locale === "fr" ? PHASES_FR : PHASES_EN;
  const [expanded, setExpanded] = useState<string | null>("manufacturing");

  const statusColor = { completed: "bg-emerald-100 border-emerald-300 text-emerald-800", current: "bg-teal-100 border-teal-400 text-teal-800 ring-2 ring-teal-300", pending: "bg-slate-50 border-slate-200 text-slate-500" };
  const statusBadge = { completed: { label: locale === "fr" ? "Terminé" : "Completed", color: "bg-emerald-500 text-white" }, current: { label: locale === "fr" ? "En cours" : "In progress", color: "bg-teal-500 text-white" }, pending: { label: locale === "fr" ? "À venir" : "Pending", color: "bg-slate-300 text-slate-600" } };

  return (
    <div className="max-w-4xl space-y-4">
      <div className="flex items-center gap-4">
        <Link href={`/dpp/${gtin}/${serial}`} className="text-teal-600 text-sm hover:underline">{t("backToDpp")}</Link>
        <h2 className="text-xl font-bold text-slate-800">{t("timelineTitle")}</h2>
      </div>
      <p className="text-sm text-slate-500">{t("description")}</p>

      {/* Progress bar */}
      <div className="flex gap-0.5 h-3 rounded-full overflow-hidden">
        {phases.map(p => (
          <div key={p.id} className={`flex-1 transition-all ${p.status === "completed" ? "bg-emerald-400" : p.status === "current" ? "bg-teal-400 animate-pulse" : "bg-slate-200"}`} />
        ))}
      </div>

      {/* Phases */}
      <div className="space-y-2">
        {phases.map((phase, i) => {
          const isExpanded = expanded === phase.id;
          const badge = statusBadge[phase.status];
          return (
            <div key={phase.id} className={`rounded-xl border transition-all ${statusColor[phase.status]} ${isExpanded ? "shadow-md" : ""}`}>
              <button onClick={() => setExpanded(isExpanded ? null : phase.id)} className="w-full flex items-center gap-3 p-4 text-left">
                <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${phase.status === "completed" ? "bg-emerald-500 text-white" : phase.status === "current" ? "bg-teal-500 text-white" : "bg-slate-200 text-slate-500"}`}>
                  {phase.status === "completed" ? "✓" : i}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm">{phase.label}</p>
                  <p className="text-xs opacity-70">{phase.regulation} · {phase.agent}</p>
                </div>
                <span className={`text-[10px] px-2 py-1 rounded-full font-medium ${badge.color}`}>{badge.label}</span>
                <span className="text-slate-400 text-sm">{isExpanded ? "▲" : "▼"}</span>
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 space-y-3 border-t border-current/10">
                  <p className="text-sm text-slate-600 mt-3">{phase.description}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="rounded-lg bg-white/80 border border-current/10 p-3">
                      <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{locale === "fr" ? "Données collectées" : "Data Collected"}</h4>
                      <ul className="space-y-1">
                        {phase.dataFields.map((f, j) => (
                          <li key={j} className="text-xs text-slate-600 flex items-start gap-1.5">
                            <span className="text-teal-500 mt-0.5">•</span>{f}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="rounded-lg bg-white/80 border border-current/10 p-3">
                      <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{locale === "fr" ? "Livrables générés" : "Outputs Generated"}</h4>
                      <ul className="space-y-1">
                        {phase.outputs.map((o, j) => (
                          <li key={j} className="text-xs text-slate-600 flex items-start gap-1.5">
                            <span className="text-emerald-500 mt-0.5">→</span>{o}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="flex gap-2 flex-wrap">
                    <Link href={`/agents/${phase.agentId}`} className="text-xs px-3 py-1.5 rounded-lg bg-teal-100 text-teal-700 font-medium hover:bg-teal-200 transition">
                      {locale === "fr" ? "Agent" : "Agent"}: {phase.agent} →
                    </Link>
                    <Link href={`/report/${gtin}/${serial}`} className="text-xs px-3 py-1.5 rounded-lg bg-blue-100 text-blue-700 font-medium hover:bg-blue-200 transition">
                      {locale === "fr" ? "Voir rapport produit" : "View product report"} →
                    </Link>
                    {phase.status !== "completed" && (
                      <Link href={`/command-center`} className="text-xs px-3 py-1.5 rounded-lg bg-amber-100 text-amber-700 font-medium hover:bg-amber-200 transition">
                        {locale === "fr" ? "Déclencher cette phase" : "Trigger this phase"} →
                      </Link>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
