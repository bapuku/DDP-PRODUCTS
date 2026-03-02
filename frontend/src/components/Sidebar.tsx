"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Dashboard", icon: "🏠" },
  { href: "/dpp", label: "DPP Explorer", icon: "📋" },
  { href: "/dpp/lifecycle/new", label: "New DPP (Lifecycle)", icon: "🆕" },
  { href: "/dpp/battery/new", label: "New Battery Passport", icon: "🔋" },
  { href: "/compliance", label: "Compliance Check", icon: "✅" },
  { href: "/compliance/calendar", label: "Compliance Calendar", icon: "📅" },
  { href: "/supply-chain", label: "Supply Chain", icon: "🔗" },
  { href: "/human-review", label: "Human Review (Art.14)", icon: "👁️" },
  { href: "/audit", label: "Audit Log (Art.12)", icon: "📜" },
  { href: "/ml/predictions", label: "ML Predictions", icon: "🤖" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 bg-slate-900 border-r border-slate-700 min-h-screen flex flex-col">
      <div className="px-4 py-5 border-b border-slate-700">
        <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">EU DPP Platform</p>
        <p className="text-xs text-slate-500 mt-1">v0.1.0</p>
      </div>
      <nav className="flex-1 py-4 space-y-0.5">
        {NAV.map(({ href, label, icon }) => {
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
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-slate-700 text-xs text-slate-500">
        EU AI Act Art. 12/13/14 compliant
      </div>
    </aside>
  );
}
