"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

const DEMO_STEPS = [
  { id: "create", delay: 0 },
  { id: "collect", delay: 1200 },
  { id: "generate", delay: 2400 },
  { id: "validate", delay: 3600 },
  { id: "comply", delay: 4800 },
  { id: "publish", delay: 6000 },
];

function LiveDemo() {
  const t = useTranslations("landing");
  const [activeStep, setActiveStep] = useState(-1);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  function runDemo() {
    setRunning(true);
    setResult(null);
    setActiveStep(0);
    DEMO_STEPS.forEach((step, i) => {
      setTimeout(() => {
        setActiveStep(i);
        if (i === DEMO_STEPS.length - 1) {
          setTimeout(() => {
            setResult({
              dpp_uri: "https://id.gs1.org/01/06374692674377/21/SN-DEMO-001",
              compliance_score: 0.92,
              completeness: 0.87,
              sectors_checked: ["ESPR", "Battery Reg 2023/1542", "REACH", "RoHS"],
              agents_used: 6,
              audit_entries: 12,
            });
            setRunning(false);
          }, 1200);
        }
      }, step.delay);
    });
  }

  const stepLabels = [
    { icon: "📋", label: t("demoStep1"), agent: "Supervisor" },
    { icon: "📊", label: t("demoStep2"), agent: "Data Collection" },
    { icon: "🏭", label: t("demoStep3"), agent: "DDP Generation" },
    { icon: "✅", label: t("demoStep4"), agent: "Validation" },
    { icon: "⚖️", label: t("demoStep5"), agent: "Regulatory Compliance" },
    { icon: "🌐", label: t("demoStep6"), agent: "Document Generation" },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-slate-800">{t("demoTitle")}</h3>
          <p className="text-sm text-slate-500 mt-1">{t("demoSubtitle")}</p>
        </div>
        <button
          onClick={runDemo}
          disabled={running}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 text-white font-semibold shadow-md hover:shadow-lg transition disabled:opacity-50"
        >
          {running ? t("demoRunning") : t("demoLaunch")}
        </button>
      </div>

      <div className="grid grid-cols-6 gap-2 mb-6">
        {stepLabels.map((step, i) => (
          <div
            key={i}
            className={`rounded-xl p-3 text-center transition-all duration-500 border ${
              activeStep === i
                ? "bg-sky-50 border-sky-300 shadow-md scale-105"
                : activeStep > i
                ? "bg-emerald-50 border-emerald-200"
                : "bg-slate-50 border-slate-200"
            }`}
          >
            <span className="text-2xl block mb-1">
              {activeStep > i ? "✓" : activeStep === i && running ? "⚙️" : step.icon}
            </span>
            <p className="text-[10px] font-semibold text-slate-700 leading-tight">{step.label}</p>
            <p className="text-[9px] text-slate-400 mt-0.5">{step.agent}</p>
          </div>
        ))}
      </div>

      {result && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 animate-in">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xl">🎉</span>
            <p className="font-bold text-emerald-800">{t("demoSuccess")}</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <p className="text-[10px] uppercase tracking-wider text-slate-400">{t("demoUri")}</p>
              <p className="text-xs font-mono text-sky-600 mt-1 break-all">{String(result.dpp_uri)}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <p className="text-[10px] uppercase tracking-wider text-slate-400">{t("demoCompliance")}</p>
              <p className="text-2xl font-bold text-emerald-700">{Math.round((result.compliance_score as number) * 100)}%</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <p className="text-[10px] uppercase tracking-wider text-slate-400">{t("demoCompleteness")}</p>
              <p className="text-2xl font-bold text-sky-700">{Math.round((result.completeness as number) * 100)}%</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <p className="text-[10px] uppercase tracking-wider text-slate-400">{t("demoRegulations")}</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {(result.sectors_checked as string[]).map((s) => (
                  <span key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">{s}</span>
                ))}
              </div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <p className="text-[10px] uppercase tracking-wider text-slate-400">{t("demoAgents")}</p>
              <p className="text-2xl font-bold text-purple-700">{String(result.agents_used)}</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <p className="text-[10px] uppercase tracking-wider text-slate-400">{t("demoAudit")}</p>
              <p className="text-2xl font-bold text-slate-700">{String(result.audit_entries)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function LandingPage() {
  const t = useTranslations("landing");
  const [agentCount] = useState(16);
  const [skillCount] = useState(64);
  const [toolCount] = useState(15);

  return (
    <div className="min-h-screen bg-white">
      {/* Hero */}
      <header className="relative overflow-hidden">
        <div className="absolute inset-0">
          <img src="/images/hero-towers.jpg" alt="" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-br from-[#065f73]/90 via-[#00838f]/85 to-[#1a237e]/90" />
        </div>
        <nav className="relative z-10 max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-teal-400 to-cyan-300 rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-[#065f73] font-extrabold text-sm">EU</span>
            </div>
            <span className="text-white font-bold text-lg">DPP Platform</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="#demo" className="text-white/70 hover:text-white text-sm transition">Demo</a>
            <a href="#capabilities" className="text-white/70 hover:text-white text-sm transition">{t("navCapabilities")}</a>
            <a href="#agents" className="text-white/70 hover:text-white text-sm transition">Agents</a>
            <a href="#compliance" className="text-white/70 hover:text-white text-sm transition">{t("navCompliance")}</a>
            <Link href="/" className="px-4 py-2 bg-gradient-to-r from-teal-400 to-cyan-300 text-[#065f73] rounded-lg text-sm font-bold hover:from-teal-300 hover:to-cyan-200 transition shadow-md">
              {t("navPlatform")} →
            </Link>
          </div>
        </nav>

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-20 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur border border-white/20 text-white/80 text-xs font-medium mb-6">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            {t("heroBadge")}
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold text-white leading-tight max-w-4xl mx-auto">
            {t("heroTitle")}
          </h1>
          <p className="text-lg text-white/70 mt-6 max-w-2xl mx-auto leading-relaxed">
            {t("heroSubtitle")}
          </p>
          <div className="flex items-center justify-center gap-4 mt-10">
            <Link href="/" className="px-8 py-3.5 bg-gradient-to-r from-teal-400 to-cyan-300 text-[#065f73] rounded-xl font-bold shadow-lg hover:shadow-xl transition text-sm">
              {t("heroCtaPrimary")}
            </Link>
            <a href="#demo" className="px-8 py-3.5 bg-white/10 backdrop-blur border border-white/30 text-white rounded-xl font-medium hover:bg-white/20 transition text-sm">
              {t("heroCtaDemo")}
            </a>
          </div>

          <div className="grid grid-cols-3 gap-6 mt-16 max-w-lg mx-auto">
            <div className="text-center">
              <p className="text-3xl font-bold text-white">{agentCount}</p>
              <p className="text-xs text-white/60 mt-1">{t("statAgents")}</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-white">{skillCount}</p>
              <p className="text-xs text-white/60 mt-1">{t("statSkills")}</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-white">{toolCount}</p>
              <p className="text-xs text-white/60 mt-1">{t("statTools")}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Capabilities */}
      <section id="capabilities" className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-800">{t("capTitle")}</h2>
          <p className="text-slate-500 mt-3 max-w-2xl mx-auto">{t("capSubtitle")}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {[
            { icon: "📋", title: t("cap1Title"), desc: t("cap1Desc"), color: "sky" },
            { icon: "⚖️", title: t("cap2Title"), desc: t("cap2Desc"), color: "blue" },
            { icon: "🔗", title: t("cap3Title"), desc: t("cap3Desc"), color: "purple" },
            { icon: "🤖", title: t("cap4Title"), desc: t("cap4Desc"), color: "emerald" },
            { icon: "📈", title: t("cap5Title"), desc: t("cap5Desc"), color: "amber" },
            { icon: "♻️", title: t("cap6Title"), desc: t("cap6Desc"), color: "rose" },
            { icon: "📜", title: t("cap7Title"), desc: t("cap7Desc"), color: "slate" },
            { icon: "👁️", title: t("cap8Title"), desc: t("cap8Desc"), color: "cyan" },
          ].map((cap, i) => (
            <div key={i} className="rounded-xl border border-slate-200 p-6 hover:shadow-lg transition group card-hover bg-white">
              <span className="text-3xl block mb-3">{cap.icon}</span>
              <h3 className="font-bold text-slate-800 mb-2">{cap.title}</h3>
              <p className="text-sm text-slate-500 leading-relaxed">{cap.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Visual break — circular economy image */}
      <section className="relative h-64 overflow-hidden">
        <img src="/images/hero-circular.jpg" alt="Circular Economy" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#065f73]/70 to-transparent flex items-center">
          <div className="max-w-7xl mx-auto px-6">
            <p className="text-3xl font-bold text-white max-w-md">Circular Economy Meets Digital Innovation</p>
          </div>
        </div>
      </section>

      {/* Live Demo */}
      <section id="demo" className="bg-gradient-to-b from-slate-50 to-white py-20">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-slate-800">{t("demoSectionTitle")}</h2>
            <p className="text-slate-500 mt-3">{t("demoSectionSubtitle")}</p>
          </div>
          <LiveDemo />
        </div>
      </section>

      {/* Agents */}
      <section id="agents" className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-800">{t("agentsTitle")}</h2>
          <p className="text-slate-500 mt-3 max-w-2xl mx-auto">{t("agentsSubtitle")}</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { icon: "🎯", name: "Supervisor", phase: "All" },
            { icon: "⚖️", name: "Regulatory Compliance", phase: "All" },
            { icon: "📊", name: "Data Collection", phase: "0-3" },
            { icon: "🏭", name: "DDP Generation", phase: "4" },
            { icon: "✅", name: "Validation", phase: "4-5" },
            { icon: "🔗", name: "Supply Chain", phase: "3-6" },
            { icon: "🧠", name: "Knowledge Graph", phase: "All" },
            { icon: "📄", name: "Document Generation", phase: "4-5" },
            { icon: "📜", name: "Audit Trail", phase: "All" },
            { icon: "🔍", name: "Anomaly Detection", phase: "4-6" },
            { icon: "📈", name: "Predictive Scoring", phase: "4-6" },
            { icon: "♻️", name: "Circular Economy", phase: "7" },
            { icon: "🔄", name: "Recycling", phase: "8" },
            { icon: "🗑️", name: "Destruction", phase: "9" },
            { icon: "👁️", name: "Human Review", phase: "All" },
            { icon: "📝", name: "Synthesizer", phase: "All" },
          ].map((a, i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 bg-white">
              <span className="text-xl">{a.icon}</span>
              <div>
                <p className="text-sm font-medium text-slate-700">{a.name}</p>
                <p className="text-[10px] text-slate-400">Phase: {a.phase}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="text-center mt-8">
          <Link href="/agents" className="px-6 py-3 bg-gradient-to-r from-teal-600 to-cyan-500 text-white rounded-xl font-semibold hover:from-teal-500 hover:to-cyan-400 transition shadow-md">
            {t("agentsCta")} →
          </Link>
        </div>
      </section>

      {/* Industry images strip */}
      <section className="grid grid-cols-3 h-48">
        <div className="relative overflow-hidden">
          <img src="/images/industry-manufacturing.jpg" alt="Manufacturing" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-[#065f73]/50 flex items-center justify-center"><span className="text-white font-bold text-sm">Manufacturing</span></div>
        </div>
        <div className="relative overflow-hidden">
          <img src="/images/industry-supply-chain.jpg" alt="Supply Chain" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-[#00838f]/50 flex items-center justify-center"><span className="text-white font-bold text-sm">Supply Chain</span></div>
        </div>
        <div className="relative overflow-hidden">
          <img src="/images/industry-recycling.jpg" alt="Recycling" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-[#1a237e]/50 flex items-center justify-center"><span className="text-white font-bold text-sm">Recycling</span></div>
        </div>
      </section>

      {/* Compliance */}
      <section id="compliance" className="bg-gradient-to-b from-slate-50 to-white py-20">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-slate-800">{t("compTitle")}</h2>
            <p className="text-slate-500 mt-3">{t("compSubtitle")}</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {[
              { reg: "EU AI Act 2024/1689", articles: ["Art. 12 — Audit Trail", "Art. 13 — Transparency", "Art. 14 — Human Oversight"], color: "blue" },
              { reg: "ESPR", articles: ["Art. 9 — DPP Data", "Art. 9(3) — Validation", "Art. 9(4) — Public Access"], color: "emerald" },
              { reg: "Battery Reg 2023/1542", articles: ["Annex XIII — 87 Fields", "Art. 49 — Supply Chain", "Art. 14 — Second Life"], color: "amber" },
            ].map((r, i) => (
              <div key={i} className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                <h3 className="font-bold text-slate-800 mb-4">{r.reg}</h3>
                <ul className="space-y-2">
                  {r.articles.map((a, j) => (
                    <li key={j} className="flex items-center gap-2 text-sm text-slate-600">
                      <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-xs flex-shrink-0">✓</span>
                      {a}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
          <Link href="/reports" className="px-6 py-3 bg-gradient-to-r from-teal-600 to-cyan-500 text-white rounded-xl font-semibold hover:from-teal-500 hover:to-cyan-400 transition shadow-md">
            {t("compCta")} →
          </Link>
          </div>
        </div>
      </section>

      {/* Sectors */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-800">{t("sectorsTitle")}</h2>
          <p className="text-slate-500 mt-3">{t("sectorsSubtitle")}</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { icon: "🔋", name: t("sectorBatteries"), reg: "EU 2023/1542" },
            { icon: "💻", name: t("sectorElectronics"), reg: "ESPR" },
            { icon: "👕", name: t("sectorTextiles"), reg: "ESPR" },
            { icon: "🚗", name: t("sectorVehicles"), reg: "ELV Directive" },
            { icon: "🏗️", name: t("sectorConstruction"), reg: "CPR" },
            { icon: "🪑", name: t("sectorFurniture"), reg: "ESPR" },
            { icon: "🧴", name: t("sectorPlastics"), reg: "EU 2019/904" },
            { icon: "⚗️", name: t("sectorChemicals"), reg: "REACH / CLP" },
          ].map((s, i) => (
            <Link key={i} href={`/dpp?section=${s.name.toLowerCase()}`} className="flex flex-col items-center gap-2 p-5 rounded-xl border border-slate-200 bg-white card-hover text-center group">
              <span className="text-3xl">{s.icon}</span>
              <p className="font-semibold text-slate-700 group-hover:text-sky-600">{s.name}</p>
              <p className="text-xs text-slate-400">{s.reg}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative py-20 overflow-hidden">
        <img src="/images/cover-brand.jpg" alt="" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#065f73]/92 to-[#1a237e]/88" />
        <div className="relative max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-white">{t("ctaTitle")}</h2>
          <p className="text-white/80 mt-4 text-lg">{t("ctaSubtitle")}</p>
          <div className="flex items-center justify-center gap-4 mt-8">
            <Link href="/" className="px-8 py-3.5 bg-gradient-to-r from-teal-400 to-cyan-300 text-[#065f73] rounded-xl font-bold shadow-lg hover:shadow-xl transition">
              {t("ctaPrimary")}
            </Link>
            <a href="mailto:sovereignpialphafrance-contact@startmail.com" className="px-8 py-3.5 bg-white/10 border border-white/30 text-white rounded-xl font-medium hover:bg-white/20 transition">
              {t("ctaContact")}
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#0a2e3d] text-white py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-gradient-to-br from-teal-400 to-cyan-300 rounded-xl flex items-center justify-center">
                  <span className="text-[#065f73] font-extrabold text-sm">EU</span>
                </div>
                <span className="font-bold text-lg">DPP Platform</span>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed max-w-md">
                {t("footerDesc")}
              </p>
              <div className="mt-4 text-sm text-slate-400">
                <p className="font-semibold text-slate-300">SovereignPiAlpha France Ltd</p>
                <p>36 Rue Scheffer, 75116 Paris, France</p>
                <a href="mailto:sovereignpialphafrance-contact@startmail.com" className="text-cyan-400 hover:underline mt-1 inline-block">
                  sovereignpialphafrance-contact@startmail.com
                </a>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-3 text-slate-300">{t("footerRegulations")}</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>ESPR (Ecodesign for Sustainable Products)</li>
                <li>Battery Regulation 2023/1542</li>
                <li>EU AI Act 2024/1689</li>
                <li>REACH / RoHS / WEEE</li>
                <li>GS1 Digital Link (ISO/IEC 18004)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-3 text-slate-300">{t("footerTech")}</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>LangGraph Multi-Agent System</li>
                <li>Claude Sonnet / Opus 4</li>
                <li>Neo4j Knowledge Graph</li>
                <li>Qdrant Vector Search</li>
                <li>Kafka Event Streaming</li>
                <li>FastAPI + Next.js 14</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-[#1a3d4d] mt-10 pt-6 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs text-slate-500">
              © {new Date().getFullYear()} SovereignPiAlpha France Ltd. {t("footerRights")}
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span>{t("footerAiAct")}</span>
              <span>·</span>
              <span>{t("footerGdpr")}</span>
              <span>·</span>
              <span>{t("footerEspr")}</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
