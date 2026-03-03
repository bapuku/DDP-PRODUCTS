"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Agent {
  id: string;
  name: string;
  description: string;
  category: string;
  phase: string;
  compliance_refs: string[];
  skills: string[];
  tools: string[];
  llm_model: string | null;
  status: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  orchestration: "bg-purple-900/50 text-purple-300 border-purple-700",
  compliance: "bg-blue-900/50 text-blue-300 border-blue-700",
  data: "bg-teal-900/50 text-teal-300 border-teal-700",
  generation: "bg-amber-900/50 text-amber-300 border-amber-700",
  quality: "bg-orange-900/50 text-orange-300 border-orange-700",
  traceability: "bg-cyan-900/50 text-cyan-300 border-cyan-700",
  knowledge: "bg-indigo-900/50 text-indigo-300 border-indigo-700",
  audit: "bg-slate-800/50 text-slate-300 border-slate-600",
  ml: "bg-emerald-900/50 text-emerald-300 border-emerald-700",
  lifecycle: "bg-rose-900/50 text-rose-300 border-rose-700",
  governance: "bg-sky-900/50 text-sky-300 border-sky-700",
};

const CATEGORY_ICONS: Record<string, string> = {
  orchestration: "🎯",
  compliance: "⚖️",
  data: "📊",
  generation: "🏭",
  quality: "✅",
  traceability: "🔗",
  knowledge: "🧠",
  audit: "📜",
  ml: "🤖",
  lifecycle: "♻️",
  governance: "👁️",
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
    fetch(`${API}/api/v1/agents/registry`, {
      headers: { "Accept-Language": getLocale() },
    })
      .then((r) => r.json())
      .then(setAgents)
      .catch(() => setAgents([]))
      .finally(() => setLoading(false));
  }, []);

  const categories = [...new Set(agents.map((a) => a.category))];
  const filtered = filter ? agents.filter((a) => a.category === filter) : agents;

  return (
    <div className="max-w-6xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">{t("title")}</h2>
          <p className="text-slate-400 text-sm mt-1">{t("description")}</p>
        </div>
        <div className="flex gap-2">
          <Link href="/agents/skills" className="px-3 py-1.5 text-sm rounded bg-slate-800 border border-slate-700 hover:border-sky-500 transition">
            {t("skillsRegistry")}
          </Link>
          <Link href="/agents/tools" className="px-3 py-1.5 text-sm rounded bg-slate-800 border border-slate-700 hover:border-sky-500 transition">
            {t("toolsRegistry")}
          </Link>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <span className="text-sm text-slate-400">{t("totalAgents", { count: agents.length })}</span>
        <div className="flex gap-1 flex-wrap">
          <button
            onClick={() => setFilter("")}
            className={`px-2 py-1 text-xs rounded transition ${!filter ? "bg-sky-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}
          >
            {t("all")}
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat === filter ? "" : cat)}
              className={`px-2 py-1 text-xs rounded transition ${filter === cat ? "bg-sky-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}
            >
              {CATEGORY_ICONS[cat] ?? "📦"} {cat}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="text-slate-500">{tCommon("loading")}</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((agent) => (
            <Link
              key={agent.id}
              href={`/agents/${agent.id}`}
              className={`rounded-lg border p-5 transition hover:ring-1 hover:ring-sky-500 ${CATEGORY_COLORS[agent.category] ?? "bg-slate-800 border-slate-700"}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{CATEGORY_ICONS[agent.category] ?? "📦"}</span>
                  <h3 className="font-semibold">{agent.name}</h3>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${agent.status === "active" ? "bg-emerald-900/60 text-emerald-300" : "bg-red-900/60 text-red-300"}`}>
                  {agent.status}
                </span>
              </div>
              <p className="text-sm opacity-80 mb-3 line-clamp-2">{agent.description}</p>
              <div className="flex flex-wrap gap-1 mb-2">
                {agent.compliance_refs.slice(0, 3).map((ref) => (
                  <span key={ref} className="text-xs px-1.5 py-0.5 rounded bg-black/20">{ref}</span>
                ))}
                {agent.compliance_refs.length > 3 && (
                  <span className="text-xs px-1.5 py-0.5 rounded bg-black/20">+{agent.compliance_refs.length - 3}</span>
                )}
              </div>
              <div className="flex items-center justify-between text-xs opacity-60">
                <span>{agent.skills.length} {t("skills")} · {agent.tools.length} {t("tools")}</span>
                <span>{agent.llm_model ?? "—"}</span>
              </div>
              <div className="text-xs opacity-50 mt-1">{t("phase")}: {agent.phase}</div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
