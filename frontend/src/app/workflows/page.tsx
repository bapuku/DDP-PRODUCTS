"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { AGENTS, TOOLS, buildSkills, type AgentInfo, type ToolInfo } from "@/data/registry";

interface WorkflowStep { agentId: string; action: string; }

const PRESET_WORKFLOWS = [
  {
    id: "dpp_creation",
    name: { en: "DPP Creation Pipeline", fr: "Pipeline Création DPP" },
    description: { en: "Full 6-step DPP creation: classify → collect → generate → validate → compliance → publish", fr: "Création DPP complète en 6 étapes : classifier → collecter → générer → valider → conformité → publier" },
    steps: [
      { agentId: "supervisor", action: "Classify product request and route to sector-specific collection" },
      { agentId: "data_collection", action: "Collect BOM, supplier declarations, LCA data, carbon footprint" },
      { agentId: "ddp_generation", action: "Generate DPP (JSON-LD, QR code, NFC payload, RFID EPC)" },
      { agentId: "validation", action: "Structural + regulatory validation, completeness check" },
      { agentId: "regulatory_compliance", action: "Verify ESPR, Battery Reg, REACH, RoHS compliance" },
      { agentId: "document_generation", action: "Publish DPP with data carriers and audit trail" },
    ],
    endpoint: "/api/v1/dpp/lifecycle/create",
    pageLink: "/command-center",
  },
  {
    id: "compliance_check",
    name: { en: "Compliance Verification", fr: "Vérification Conformité" },
    description: { en: "AI-powered regulatory compliance check with EUR-Lex citations", fr: "Contrôle de conformité réglementaire par IA avec citations EUR-Lex" },
    steps: [
      { agentId: "supervisor", action: "Route to regulatory compliance agent" },
      { agentId: "regulatory_compliance", action: "Analyze ESPR, Battery Reg, REACH, RoHS, WEEE" },
      { agentId: "knowledge_graph", action: "Retrieve regulatory context from knowledge graph" },
      { agentId: "synthesize", action: "Consolidate findings with citations and confidence scores" },
      { agentId: "audit_trail", action: "Log decision with hash chain (Art. 12)" },
    ],
    endpoint: "/api/v1/compliance/check",
    pageLink: "/compliance",
  },
  {
    id: "lifecycle_update",
    name: { en: "Lifecycle Update", fr: "Mise à Jour Cycle de Vie" },
    description: { en: "Update product phase: dynamic data, service event, ownership, recall, EOL", fr: "Mettre à jour la phase produit : données dynamiques, service, transfert, rappel, fin de vie" },
    steps: [
      { agentId: "supervisor", action: "Classify update type (dynamic/service/recall/EOL)" },
      { agentId: "anomaly_detection", action: "Check for data anomalies (Isolation Forest)" },
      { agentId: "circular_economy", action: "Assess second-life pathway (if EOL)" },
      { agentId: "recycling", action: "Process recycling operations (if phase 8)" },
      { agentId: "audit_trail", action: "Log lifecycle transition" },
    ],
    endpoint: "/api/v1/dpp/lifecycle/{gtin}/{serial}/update",
    pageLink: "/dpp",
  },
  {
    id: "supply_chain_trace",
    name: { en: "Supply Chain Traceability", fr: "Traçabilité Chaîne d'Approvisionnement" },
    description: { en: "Multi-tier supply chain trace from product to raw materials (Battery Reg Art. 49)", fr: "Traçage multi-niveaux du produit aux matières premières (Règlement Batteries Art. 49)" },
    steps: [
      { agentId: "supply_chain", action: "Neo4j graph traversal for upstream nodes" },
      { agentId: "knowledge_graph", action: "Enrich with supplier regulatory data" },
      { agentId: "anomaly_detection", action: "Flag supply chain anomalies" },
      { agentId: "audit_trail", action: "Log traceability query" },
    ],
    endpoint: "/api/v1/dpp/sector/supply-chain/{gtin}",
    pageLink: "/supply-chain",
  },
  {
    id: "dpp_audit",
    name: { en: "DPP Audit Workflow", fr: "Workflow Audit DPP" },
    description: { en: "Full audit: scope → evidence → checks → findings → report → corrective actions", fr: "Audit complet : périmètre → preuves → vérifications → constats → rapport → actions correctives" },
    steps: [
      { agentId: "supervisor", action: "Determine audit scope" },
      { agentId: "audit_trail", action: "Collect evidence from audit log" },
      { agentId: "validation", action: "Execute structural and regulatory checks" },
      { agentId: "regulatory_compliance", action: "Analyze findings against regulations" },
      { agentId: "synthesize", action: "Generate audit report with corrective actions" },
    ],
    endpoint: "/api/v1/dpp/audit/{gtin}/{serial}",
    pageLink: "/audit",
  },
  {
    id: "ml_prediction",
    name: { en: "ML Compliance Prediction", fr: "Prédiction Conformité ML" },
    description: { en: "GradientBoosting v2 models predict ESPR, RoHS, REACH, carbon, circularity", fr: "Modèles GradientBoosting v2 prédisent ESPR, RoHS, REACH, carbone, circularité" },
    steps: [
      { agentId: "predictive", action: "Run 5 ML models (ESPR, RoHS, REACH classifiers + carbon, circularity regressors)" },
      { agentId: "anomaly_detection", action: "Cross-check predictions with historical data" },
      { agentId: "audit_trail", action: "Log prediction with model version and confidence" },
    ],
    endpoint: "/api/v1/ml/predict/compliance",
    pageLink: "/ml/predictions",
  },
];

function getLocale(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  return m ? m[1].trim() : "en";
}

export default function WorkflowsPage() {
  const t = useTranslations("workflows");
  const locale = getLocale();
  const [selected, setSelected] = useState<string | null>(null);
  const [customSteps, setCustomSteps] = useState<WorkflowStep[]>([]);
  const [showBuilder, setShowBuilder] = useState(false);
  const skills = buildSkills();

  const agentMap = Object.fromEntries(AGENTS.map(a => [a.id, a]));

  function addCustomStep(agentId: string) {
    setCustomSteps(prev => [...prev, { agentId, action: "" }]);
  }

  function removeCustomStep(i: number) {
    setCustomSteps(prev => prev.filter((_, j) => j !== i));
  }

  function updateCustomAction(i: number, action: string) {
    setCustomSteps(prev => prev.map((s, j) => j === i ? { ...s, action } : s));
  }

  return (
    <div className="max-w-6xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">{t("title")}</h2>
          <p className="text-sm text-slate-500 mt-1">{t("description")}</p>
        </div>
        <div className="flex gap-2">
          <Link href="/command-center" className="px-4 py-2 text-sm rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 text-white font-medium shadow-md hover:shadow-lg transition">
            {t("commandCenter")} →
          </Link>
          <button onClick={() => setShowBuilder(!showBuilder)} className="px-4 py-2 text-sm rounded-lg bg-white border border-slate-200 text-slate-700 font-medium hover:border-sky-400 transition">
            {showBuilder ? t("hideBuilder") : t("showBuilder")}
          </button>
        </div>
      </div>

      {/* Preset Workflows */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PRESET_WORKFLOWS.map(wf => {
          const isSelected = selected === wf.id;
          const name = locale === "fr" ? wf.name.fr : wf.name.en;
          const desc = locale === "fr" ? wf.description.fr : wf.description.en;
          return (
            <div key={wf.id} className={`rounded-xl border bg-white p-5 transition cursor-pointer ${isSelected ? "border-sky-400 shadow-lg ring-1 ring-sky-200" : "border-slate-200 hover:border-sky-300 hover:shadow-md"}`} onClick={() => setSelected(isSelected ? null : wf.id)}>
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-slate-800">{name}</h3>
                <span className="text-xs px-2 py-1 rounded-full bg-sky-100 text-sky-700 font-medium">{wf.steps.length} {t("steps")}</span>
              </div>
              <p className="text-sm text-slate-500 mb-3">{desc}</p>

              {isSelected && (
                <div className="space-y-2 mt-4 pt-4 border-t border-slate-100">
                  {wf.steps.map((s, i) => {
                    const agent = agentMap[s.agentId];
                    return (
                      <div key={i} className="flex items-start gap-3">
                        <span className="w-6 h-6 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-xs font-bold flex-shrink-0">{i + 1}</span>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Link href={`/agents/${s.agentId}`} className="text-sm font-medium text-sky-600 hover:underline">{agent?.name ?? s.agentId}</Link>
                          </div>
                          <p className="text-xs text-slate-500">{s.action}</p>
                          {agent && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {agent.tools.slice(0, 3).map(tool => (
                                <span key={tool} className="text-[9px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-600 border border-amber-200">{tool.replace(/_/g, " ")}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  <div className="flex gap-2 mt-3">
                    <Link href={wf.pageLink} className="px-4 py-2 rounded-lg bg-sky-500 text-white text-xs font-medium hover:bg-sky-600 transition">{t("execute")} →</Link>
                    <span className="px-3 py-2 rounded-lg bg-slate-50 text-[10px] font-mono text-slate-400">{wf.endpoint}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Custom Workflow Builder */}
      {showBuilder && (
        <div className="rounded-xl border border-sky-200 bg-sky-50 p-6 space-y-4">
          <h3 className="font-bold text-sky-800">{t("builderTitle")}</h3>
          <p className="text-sm text-sky-600">{t("builderDesc")}</p>

          {/* Current steps */}
          {customSteps.length > 0 && (
            <div className="space-y-2">
              {customSteps.map((s, i) => {
                const agent = agentMap[s.agentId];
                return (
                  <div key={i} className="flex items-center gap-3 bg-white rounded-lg border border-sky-200 p-3">
                    <span className="w-6 h-6 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-xs font-bold">{i + 1}</span>
                    <span className="text-sm font-medium text-slate-700 w-40">{agent?.name ?? s.agentId}</span>
                    <input value={s.action} onChange={e => updateCustomAction(i, e.target.value)} placeholder={t("actionPlaceholder")} className="flex-1 rounded-lg bg-white border border-slate-300 px-3 py-1.5 text-sm" />
                    <button onClick={() => removeCustomStep(i)} className="text-red-400 hover:text-red-600 text-sm">✕</button>
                  </div>
                );
              })}
            </div>
          )}

          {/* Add agent */}
          <div>
            <p className="text-xs font-semibold text-sky-700 mb-2">{t("addAgent")}</p>
            <div className="grid grid-cols-4 md:grid-cols-8 gap-1.5">
              {AGENTS.map(a => (
                <button key={a.id} onClick={() => addCustomStep(a.id)} className="text-[10px] px-2 py-1.5 rounded-lg bg-white border border-sky-200 text-slate-600 hover:border-sky-400 hover:text-sky-600 transition truncate" title={a.name}>
                  {a.name.split(/[/(]/)[0].trim()}
                </button>
              ))}
            </div>
          </div>

          {customSteps.length > 0 && (
            <div className="flex gap-2 pt-2">
              <Link href="/command-center" className="px-4 py-2 rounded-lg bg-sky-500 text-white text-sm font-medium hover:bg-sky-600 transition">{t("executeCustom")} →</Link>
              <button onClick={() => setCustomSteps([])} className="px-4 py-2 rounded-lg bg-white border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition">{t("clear")}</button>
            </div>
          )}
        </div>
      )}

      {/* Resources */}
      <div className="grid grid-cols-3 gap-3">
        <Link href="/agents" className="rounded-xl border border-slate-200 bg-white p-4 text-center card-hover group">
          <p className="text-2xl mb-1">🤖</p>
          <p className="text-sm font-semibold text-slate-700 group-hover:text-sky-600">{AGENTS.length} Agents</p>
          <p className="text-xs text-slate-400">{t("viewRegistry")} →</p>
        </Link>
        <Link href="/agents/skills" className="rounded-xl border border-slate-200 bg-white p-4 text-center card-hover group">
          <p className="text-2xl mb-1">⚡</p>
          <p className="text-sm font-semibold text-slate-700 group-hover:text-sky-600">{skills.length} Skills</p>
          <p className="text-xs text-slate-400">{t("viewSkills")} →</p>
        </Link>
        <Link href="/agents/tools" className="rounded-xl border border-slate-200 bg-white p-4 text-center card-hover group">
          <p className="text-2xl mb-1">🔧</p>
          <p className="text-sm font-semibold text-slate-700 group-hover:text-sky-600">{TOOLS.length} Tools</p>
          <p className="text-xs text-slate-400">{t("viewTools")} →</p>
        </Link>
      </div>
    </div>
  );
}
