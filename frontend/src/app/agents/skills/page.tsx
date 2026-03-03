"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Skill {
  id: string;
  name: string;
  agents: string[];
  category: string;
}

function getLocale(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  return m ? m[1].trim() : "en";
}

export default function SkillsRegistryPage() {
  const t = useTranslations("agentRegistry");
  const tCommon = useTranslations("common");
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/v1/agents/skills`, {
      headers: { "Accept-Language": getLocale() },
    })
      .then((r) => r.json())
      .then(setSkills)
      .catch(() => setSkills([]))
      .finally(() => setLoading(false));
  }, []);

  const grouped = skills.reduce<Record<string, Skill[]>>((acc, s) => {
    (acc[s.category] ??= []).push(s);
    return acc;
  }, {});

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/agents" className="text-sky-500 text-sm hover:text-sky-600 hover:underline">{t("backToAgents")}</Link>
        <h2 className="text-2xl font-semibold text-slate-800">{t("skillsTitle")}</h2>
      </div>
      <p className="text-slate-600 text-sm">{t("skillsDescription")}</p>

      {loading ? (
        <p className="text-slate-400">{tCommon("loading")}</p>
      ) : (
        Object.entries(grouped).map(([category, items]) => (
          <div key={category} className="space-y-2">
            <h3 className="text-lg font-medium capitalize text-slate-600">{category}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {items.map((skill) => (
                <div key={skill.id} className="bg-white rounded-xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm text-slate-800">{skill.name}</span>
                    <span className="text-xs text-slate-400">{skill.agents.length} {t("agents")}</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {skill.agents.map((agentId) => (
                      <Link key={agentId} href={`/agents/${agentId}`} className="text-xs px-2 py-0.5 rounded bg-sky-50 text-sky-700 hover:bg-sky-100 transition">
                        {agentId}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
