"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Agent {
  id: string; name: string; description: string; category: string; phase: string;
  compliance_refs: string[]; skills: string[]; tools: string[]; llm_model: string | null; status: string;
}

const CAT_STYLE: Record<string, { bg: string; text: string; icon: string }> = {
  orchestration: { bg: "bg-purple-50 border-purple-200", text: "text-purple-700", icon: "🎯" },
  compliance: { bg: "bg-blue-50 border-blue-200", text: "text-blue-700", icon: "⚖️" },
  data: { bg: "bg-teal-50 border-teal-200", text: "text-teal-700", icon: "📊" },
  generation: { bg: "bg-amber-50 border-amber-200", text: "text-amber-700", icon: "🏭" },
  quality: { bg: "bg-orange-50 border-orange-200", text: "text-orange-700", icon: "✅" },
  traceability: { bg: "bg-cyan-50 border-cyan-200", text: "text-cyan-700", icon: "🔗" },
  knowledge: { bg: "bg-indigo-50 border-indigo-200", text: "text-indigo-700", icon: "🧠" },
  audit: { bg: "bg-slate-50 border-slate-200", text: "text-slate-700", icon: "📜" },
  ml: { bg: "bg-emerald-50 border-emerald-200", text: "text-emerald-700", icon: "🤖" },
  lifecycle: { bg: "bg-rose-50 border-rose-200", text: "text-rose-700", icon: "♻️" },
  governance: { bg: "bg-sky-50 border-sky-200", text: "text-sky-700", icon: "👁️" },
};

function getLocale(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  return m ? m[1].trim() : "en";
}

export default function AgentRegistryPage() {
  const t = useTranslations("agentRegistry");
  const tCommon = useTranslations("common");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    fetch(`${API}/api/v1/agents/registry`, { headers: { "Accept-Language": getLocale() } })
      .then((r) => r.json()).then(setAgents).catch(() => setAgents([])).finally(() => setLoading(false));
  }, []);

  const categories = [...new Set(agents.map((a) => a.category))];
  const filtered = filter ? agents.filter((a) => a.category === filter) : agents;

  return (
    <div className="max-w-6xl space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">{t("title")}</h2>
          <p className="text-sm text-slate-500 mt-1">{t("description")}</p>
        </div>
        <div className="flex gap-2">
          <Link href="/agents/skills" className="px-4 py-2 text-sm rounded-lg bg-white border border-slate-200 text-slate-700 hover:border-sky-400 hover:text-sky-600 font-medium transition card-hover">
            {t("skillsRegistry")} →
          </Link>
          <Link href="/agents/tools" className="px-4 py-2 text-sm rounded-lg bg-white border border-slate-200 text-slate-700 hover:border-sky-400 hover:text-sky-600 font-medium transition card-hover">
            {t("toolsRegistry")} →
          </Link>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-sm font-medium text-slate-500">{t("totalAgents", { count: agents.length })}</span>
        <div className="h-4 w-px bg-slate-200" />
        <div className="flex gap-1.5 flex-wrap">
          <button onClick={() => setFilter("")} className={`px-3 py-1.5 text-xs rounded-lg font-medium transition ${!filter ? "bg-sky-500 text-white shadow-sm" : "bg-white border border-slate-200 text-slate-600 hover:border-sky-300"}`}>
            {t("all")}
          </button>
          {categories.map((cat) => {
            const s = CAT_STYLE[cat] ?? CAT_STYLE.audit;
            return (
              <button key={cat} onClick={() => setFilter(cat === filter ? "" : cat)} className={`px-3 py-1.5 text-xs rounded-lg font-medium transition ${filter === cat ? "bg-sky-500 text-white shadow-sm" : `bg-white border border-slate-200 text-slate-600 hover:border-sky-300`}`}>
                {s.icon} {cat}
              </button>
            );
          })}
        </div>
      </div>

      {loading ? (
        <p className="text-slate-400 text-center py-12">{tCommon("loading")}</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((agent) => {
            const s = CAT_STYLE[agent.category] ?? CAT_STYLE.audit;
            return (
              <Link key={agent.id} href={`/agents/${agent.id}`} className={`rounded-xl border p-5 card-hover ${s.bg} group`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">{s.icon}</span>
                    <h3 className={`font-semibold ${s.text}`}>{agent.name}</h3>
                  </div>
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${agent.status === "active" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                    {agent.status}
                  </span>
                </div>
                <p className="text-sm text-slate-600 mb-3 line-clamp-2 leading-relaxed">{agent.description}</p>
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {agent.compliance_refs.slice(0, 3).map((ref) => (
                    <span key={ref} className="text-[10px] px-2 py-0.5 rounded-full bg-white/80 text-slate-600 border border-slate-200 font-medium">{ref}</span>
                  ))}
                  {agent.compliance_refs.length > 3 && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/80 text-slate-500 border border-slate-200">+{agent.compliance_refs.length - 3}</span>
                  )}
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>{agent.skills.length} {t("skills")} · {agent.tools.length} {t("tools")}</span>
                  <span className="text-sky-500 font-medium group-hover:underline">Open →</span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
