"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";

const NAV_KEYS = [
  { href: "/", key: "dashboard", icon: "🏠" },
  { href: "/agents", key: "agentRegistry", icon: "🤖" },
  { href: "/reports", key: "complianceReports", icon: "📊" },
  { href: "/dpp", key: "dppExplorer", icon: "📋" },
  { href: "/dpp/lifecycle/new", key: "newDpp", icon: "🆕" },
  { href: "/dpp/battery/new", key: "newBatteryPassport", icon: "🔋" },
  { href: "/compliance", key: "complianceCheck", icon: "✅" },
  { href: "/compliance/calendar", key: "complianceCalendar", icon: "📅" },
  { href: "/supply-chain", key: "supplyChain", icon: "🔗" },
  { href: "/human-review", key: "humanReview", icon: "👁️" },
  { href: "/audit", key: "auditLog", icon: "📜" },
  { href: "/ml/predictions", key: "mlPredictions", icon: "📈" },
] as const;

export default function Sidebar() {
  const pathname = usePathname();
  const t = useTranslations("sidebar");
  return (
    <aside className="w-56 bg-slate-900 border-r border-slate-700 min-h-screen flex flex-col">
      <div className="px-4 py-5 border-b border-slate-700">
        <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">{t("platformName")}</p>
        <p className="text-xs text-slate-500 mt-1">{t("version")}</p>
      </div>
      <nav className="flex-1 py-4 space-y-0.5">
        {NAV_KEYS.map(({ href, key, icon }) => {
          const active = pathname === href || (href !== "/" && pathname?.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2 px-4 py-2 text-sm transition ${
                active ? "bg-sky-900/60 text-sky-300 font-medium" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              <span>{icon}</span>
              <span>{t(key)}</span>
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-slate-700 text-xs text-slate-500">
        {t("footerCompliant")}
      </div>
    </aside>
  );
}
