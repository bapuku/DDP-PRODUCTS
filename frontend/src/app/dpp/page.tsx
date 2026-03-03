"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
/* ────────────────────────────── sector registry ────────────────────────────── */

interface SectorMeta {
  key: string;
  icon: string;
  name: string;
  regulation: string;
  fields: string;
  description: string;
  color: string;       // tailwind accent
  formHref: string;
  listHref: string;
  complianceHref: string;
}

const SECTORS: SectorMeta[] = [
  {
    key: "batteries",
    icon: "🔋",
    name: "Batteries & Accumulators",
    regulation: "EU 2023/1542",
    fields: "87 fields — Annex XIII",
    description:
      "Electrochemistry, carbon footprint, supply-chain due diligence, recycled content, performance & durability, and end-of-life collection targets.",
    color: "sky",
    formHref: "/dpp/battery/new",
    listHref: "/dpp?section=batteries",
    complianceHref: "/compliance?sector=batteries",
  },
  {
    key: "electronics",
    icon: "💻",
    name: "Electronics & ICT",
    regulation: "ESPR — Energy Labelling, RoHS, WEEE",
    fields: "Energy label + substance restrictions",
    description:
      "Energy efficiency rating, hazardous substance declarations (RoHS), WEEE collection & recycling obligations, repairability index, and spare-part availability.",
    color: "indigo",
    formHref: "/dpp/lifecycle/new?sector=electronics",
    listHref: "/dpp?section=electronics",
    complianceHref: "/compliance?sector=electronics",
  },
  {
    key: "textiles",
    icon: "🧵",
    name: "Textiles & Apparel",
    regulation: "ESPR — Sustainable Textiles Strategy",
    fields: "Composition, durability, recyclability",
    description:
      "Fibre composition, microplastic shedding, durability testing, recyclability assessment, chemical treatments, and supply-chain traceability.",
    color: "rose",
    formHref: "/dpp/lifecycle/new?sector=textiles",
    listHref: "/dpp?section=textiles",
    complianceHref: "/compliance?sector=textiles",
  },
  {
    key: "vehicles",
    icon: "🚗",
    name: "Vehicles & Automotive",
    regulation: "ELV Directive 2000/53/EC",
    fields: "End-of-life, recyclability rates",
    description:
      "Material composition, recycled-content targets, dismantling instructions, hazardous substance inventory, and end-of-life recyclability/recoverability rates.",
    color: "amber",
    formHref: "/dpp/lifecycle/new?sector=vehicles",
    listHref: "/dpp?section=vehicles",
    complianceHref: "/compliance?sector=vehicles",
  },
  {
    key: "construction",
    icon: "🏗️",
    name: "Construction Products",
    regulation: "CPR — Construction Products Regulation",
    fields: "Performance, safety, environmental",
    description:
      "Declaration of performance (DoP), essential characteristics, fire behaviour, environmental product declaration (EPD), and CE marking data.",
    color: "orange",
    formHref: "/dpp/lifecycle/new?sector=construction",
    listHref: "/dpp?section=construction",
    complianceHref: "/compliance?sector=construction",
  },
  {
    key: "furniture",
    icon: "🪑",
    name: "Furniture & Furnishings",
    regulation: "ESPR — Ecodesign Delegated Acts",
    fields: "Durability, repairability scores",
    description:
      "Material breakdown, durability test results, repairability score, disassembly instructions, recycled-content share, and chemical safety data.",
    color: "teal",
    formHref: "/dpp/lifecycle/new?sector=furniture",
    listHref: "/dpp?section=furniture",
    complianceHref: "/compliance?sector=furniture",
  },
  {
    key: "plastics",
    icon: "♻️",
    name: "Plastics & Packaging",
    regulation: "EU 2019/904 — Single-Use Plastics",
    fields: "Recycled content, single-use status",
    description:
      "Polymer type, recycled-content percentage, single-use classification, biodegradability data, collection & recycling targets, and extended producer responsibility.",
    color: "emerald",
    formHref: "/dpp/lifecycle/new?sector=plastics",
    listHref: "/dpp?section=plastics",
    complianceHref: "/compliance?sector=plastics",
  },
  {
    key: "chemicals",
    icon: "🧪",
    name: "Chemicals & Substances",
    regulation: "REACH / CLP",
    fields: "Substances of concern, safety data",
    description:
      "SVHC declarations, safety data sheets, classification & labelling (CLP), exposure scenarios, downstream-use restrictions, and SCIP notifications.",
    color: "red",
    formHref: "/dpp/lifecycle/new?sector=chemicals",
    listHref: "/dpp?section=chemicals",
    complianceHref: "/compliance?sector=chemicals",
  },
];

/* ────────────────────────────── colour helpers ──────────────────────────────
   Tailwind needs full class names at build time so we map them explicitly.   */

const accentClasses: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  sky:     { bg: "bg-sky-50",     border: "border-sky-200",     text: "text-sky-700",     badge: "bg-sky-100 text-sky-700" },
  indigo:  { bg: "bg-indigo-50",  border: "border-indigo-200",  text: "text-indigo-700",  badge: "bg-indigo-100 text-indigo-700" },
  rose:    { bg: "bg-rose-50",    border: "border-rose-200",    text: "text-rose-700",    badge: "bg-rose-100 text-rose-700" },
  amber:   { bg: "bg-amber-50",   border: "border-amber-200",   text: "text-amber-700",   badge: "bg-amber-100 text-amber-700" },
  orange:  { bg: "bg-orange-50",  border: "border-orange-200",  text: "text-orange-700",  badge: "bg-orange-100 text-orange-700" },
  teal:    { bg: "bg-teal-50",    border: "border-teal-200",    text: "text-teal-700",    badge: "bg-teal-100 text-teal-700" },
  emerald: { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700", badge: "bg-emerald-100 text-emerald-700" },
  red:     { bg: "bg-red-50",     border: "border-red-200",     text: "text-red-700",     badge: "bg-red-100 text-red-700" },
};

/* ──────────────────────── workflow steps ─────────────────────────────────── */

const WORKFLOW_STEPS = [
  { step: 1, title: "Select sector",      detail: "Choose one of the 8 regulated product categories." },
  { step: 2, title: "Enter product data",  detail: "Fill in sector-specific fields or import from your ERP / PLM." },
  { step: 3, title: "AI generates DPP",    detail: "The data_collection and dpp_generation agents enrich & structure the data." },
  { step: 4, title: "Validate",            detail: "The validation agent checks completeness & regulatory conformance." },
  { step: 5, title: "Publish",             detail: "Publish to the decentralised registry and generate a scannable QR." },
];

/* ──────────────────────── sector card ────────────────────────────────────── */

function SectorCard({ sector }: { sector: SectorMeta }) {
  const a = accentClasses[sector.color] ?? accentClasses.sky;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col gap-3 hover:shadow-md hover:border-slate-300 transition">
      {/* header */}
      <div className="flex items-start gap-3">
        <span className={`flex h-10 w-10 items-center justify-center rounded-lg text-xl ${a.bg}`}>
          {sector.icon}
        </span>
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-slate-800 leading-tight">{sector.name}</h3>
          <p className={`text-xs font-medium mt-0.5 ${a.text}`}>{sector.regulation}</p>
        </div>
      </div>

      {/* fields badge */}
      <span className={`self-start text-[11px] font-medium px-2 py-0.5 rounded-full ${a.badge}`}>
        {sector.fields}
      </span>

      {/* description */}
      <p className="text-xs text-slate-500 leading-relaxed flex-1">{sector.description}</p>

      {/* actions */}
      <div className="flex flex-wrap gap-2 pt-1">
        <Link
          href={sector.formHref}
          className="inline-flex items-center gap-1 text-xs font-medium text-white bg-slate-800 hover:bg-slate-700 rounded-lg px-3 py-1.5 transition"
        >
          Create DPP <span aria-hidden="true">&rarr;</span>
        </Link>
        <Link
          href={sector.listHref}
          className="inline-flex items-center gap-1 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg px-3 py-1.5 transition"
        >
          View existing <span aria-hidden="true">&rarr;</span>
        </Link>
        <Link
          href={sector.complianceHref}
          className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-700 transition"
        >
          Run compliance <span aria-hidden="true">&rarr;</span>
        </Link>
      </div>
    </div>
  );
}

/* ──────────────────────── main page content ──────────────────────────────── */

function DPPContent() {
  const t = useTranslations("dpp");
  const tCommon = useTranslations("common");
  const searchParams = useSearchParams();
  const _section = searchParams.get("section");

  return (
    <div className="space-y-10">
      {/* ── page header ── */}
      <div>
        <h2 className="text-2xl font-bold text-slate-800">Digital Product Passport Explorer</h2>
        <p className="text-slate-500 mt-1 max-w-2xl">
          Create, manage, and validate DPPs across <span className="font-medium text-slate-700">8 regulated EU sectors</span>.
          Each passport is structured to its sector-specific regulation and powered by AI agents.
        </p>
      </div>

      {/* ── What is a DPP? ── */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <h3 className="text-base font-semibold text-blue-900 mb-2">What is a Digital Product Passport?</h3>
        <p className="text-sm text-blue-800 leading-relaxed">
          Under <span className="font-medium">ESPR Art.&nbsp;9</span> (Ecodesign for Sustainable Products Regulation), every product placed
          on the EU market will carry a <span className="font-medium">Digital Product Passport (DPP)</span> — a structured data record
          covering composition, carbon footprint, repairability, recyclability, and supply-chain provenance. DPPs enable regulators,
          recyclers, and consumers to access verified sustainability data throughout a product&apos;s lifecycle.
        </p>
      </div>

      {/* ── Quick Actions ── */}
      <section>
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link
            href="/dpp/battery/new"
            className="rounded-xl border border-slate-200 bg-white p-4 hover:border-sky-300 hover:shadow-sm transition group"
          >
            <div className="text-sky-500 text-lg mb-1 group-hover:text-sky-600">🔋</div>
            <h4 className="text-sm font-semibold text-slate-800">Create Battery Passport</h4>
            <p className="text-xs text-slate-500 mt-1">Annex XIII — 87 mandatory fields for batteries &amp; accumulators.</p>
          </Link>
          <Link
            href="/dpp/lifecycle/new"
            className="rounded-xl border border-slate-200 bg-white p-4 hover:border-sky-300 hover:shadow-sm transition group"
          >
            <div className="text-violet-500 text-lg mb-1 group-hover:text-violet-600">🌐</div>
            <h4 className="text-sm font-semibold text-slate-800">Create Multi-Sector DPP</h4>
            <p className="text-xs text-slate-500 mt-1">Unified form for electronics, textiles, vehicles, and more.</p>
          </Link>
          <Link
            href="/compliance"
            className="rounded-xl border border-slate-200 bg-white p-4 hover:border-sky-300 hover:shadow-sm transition group"
          >
            <div className="text-amber-500 text-lg mb-1 group-hover:text-amber-600">✓</div>
            <h4 className="text-sm font-semibold text-slate-800">Run Compliance Check</h4>
            <p className="text-xs text-slate-500 mt-1">Validate against ESPR, Battery Regulation, REACH &amp; RoHS.</p>
          </Link>
        </div>
      </section>

      {/* ── All 8 Sectors ── */}
      <section>
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Sectors &amp; Regulations</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {SECTORS.map((s) => (
            <SectorCard key={s.key} sector={s} />
          ))}
        </div>
      </section>

      {/* ── DPP Creation Workflow ── */}
      <section>
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">DPP Creation Workflow</h3>
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
            {WORKFLOW_STEPS.map((ws, idx) => (
              <div key={ws.step} className="relative flex flex-col items-center text-center">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-800 text-white text-sm font-bold">
                  {ws.step}
                </span>
                {idx < WORKFLOW_STEPS.length - 1 && (
                  <span className="hidden sm:block absolute top-4 left-[calc(50%+22px)] w-[calc(100%-44px)] border-t border-dashed border-slate-300" />
                )}
                <h4 className="text-sm font-semibold text-slate-700 mt-2">{ws.title}</h4>
                <p className="text-[11px] text-slate-400 mt-1 leading-snug">{ws.detail}</p>
              </div>
            ))}
          </div>

          <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap gap-3 text-xs">
            <span className="text-slate-400 font-medium">Powered by agents:</span>
            {[
              { name: "data_collection", href: "/agents/data_collection" },
              { name: "dpp_generation", href: "/agents/dpp_generation" },
              { name: "validation", href: "/agents/validation" },
            ].map((agent) => (
              <Link
                key={agent.name}
                href={agent.href}
                className="inline-flex items-center gap-1 rounded-md bg-violet-50 px-2 py-0.5 text-violet-700 hover:bg-violet-100 transition font-mono"
              >
                {agent.name}
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

/* ──────────────────────── page wrapper ───────────────────────────────────── */

export default function DPPSectionPage() {
  const tCommon = useTranslations("common");
  return (
    <Suspense fallback={<div className="text-slate-400">{tCommon("loading")}</div>}>
      <DPPContent />
    </Suspense>
  );
}
