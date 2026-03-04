"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";

const NAV_SECTIONS = [
  {
    section: "main",
    items: [
      { href: "/", key: "dashboard", icon: "📊" },
      { href: "/agents", key: "agentRegistry", icon: "🤖" },
      { href: "/reports", key: "complianceReports", icon: "📋" },
    ],
  },
  {
    section: "dpp",
    items: [
      { href: "/dpp", key: "dppExplorer", icon: "🔍" },
      { href: "/dpp/lifecycle/new", key: "newDpp", icon: "➕" },
      { href: "/dpp/battery/new", key: "newBatteryPassport", icon: "🔋" },
      { href: "/qr", key: "qrGenerator", icon: "📱" },
    ],
  },
  {
    section: "compliance",
    items: [
      { href: "/compliance", key: "complianceCheck", icon: "✅" },
      { href: "/compliance/calendar", key: "complianceCalendar", icon: "📅" },
      { href: "/supply-chain", key: "supplyChain", icon: "🔗" },
    ],
  },
  {
    section: "integration",
    items: [
      { href: "/connectors", key: "connectors", icon: "🔌" },
      { href: "/blockchain", key: "blockchain", icon: "🔐" },
    ],
  },
  {
    section: "monitoring",
    items: [
      { href: "/human-review", key: "humanReview", icon: "👁️" },
      { href: "/audit", key: "auditLog", icon: "📜" },
      { href: "/ml/predictions", key: "mlPredictions", icon: "📈" },
    ],
  },
] as const;

const SECTION_LABELS: Record<string, { en: string; fr: string }> = {
  main: { en: "Overview", fr: "Vue d'ensemble" },
  dpp: { en: "Product Passports", fr: "Passeports Produit" },
  compliance: { en: "Compliance", fr: "Conformité" },
  integration: { en: "Integration", fr: "Intégration" },
  monitoring: { en: "Monitoring", fr: "Suivi" },
};

export default function Sidebar() {
  const pathname = usePathname();
  const t = useTranslations("sidebar");

  return (
    <aside className="w-60 bg-white border-r border-slate-200 min-h-screen flex flex-col shadow-sm">
      <div className="px-5 py-5 border-b border-slate-100">
        <p className="text-xs text-sky-600 font-semibold uppercase tracking-wider">{t("platformName")}</p>
        <p className="text-xs text-slate-400 mt-0.5">{t("version")}</p>
      </div>
      <nav className="flex-1 py-3 overflow-auto">
        {NAV_SECTIONS.map(({ section, items }) => (
          <div key={section} className="mb-2">
            <p className="px-5 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              {SECTION_LABELS[section]?.en ?? section}
            </p>
            {items.map(({ href, key, icon }) => {
              const active = pathname === href || (href !== "/" && pathname?.startsWith(href));
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-3 mx-2 px-3 py-2 text-sm rounded-lg transition ${
                    active
                      ? "nav-active bg-sky-50 text-sky-700 font-medium"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  <span className="text-base">{icon}</span>
                  <span>{t(key)}</span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
      <div className="px-5 py-3 border-t border-slate-100">
        <p className="text-[10px] text-slate-400 leading-relaxed">{t("footerCompliant")}</p>
      </div>
    </aside>
  );
}
