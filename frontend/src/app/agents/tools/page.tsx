"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

const API = process.env.NEXT_PUBLIC_API_URL || "";

interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
  used_by: string[];
}

function getLocale(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  return m ? m[1].trim() : "en";
}

export default function ToolsRegistryPage() {
  const t = useTranslations("agentRegistry");
  const tCommon = useTranslations("common");
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/v1/agents/tools`, {
      headers: { "Accept-Language": getLocale() },
    })
      .then((r) => r.json())
      .then(setTools)
      .catch(() => setTools([]))
      .finally(() => setLoading(false));
  }, []);

  const grouped = tools.reduce<Record<string, Tool[]>>((acc, t) => {
    (acc[t.category] ??= []).push(t);
    return acc;
  }, {});

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/agents" className="text-sky-500 text-sm hover:text-sky-600 hover:underline">{t("backToAgents")}</Link>
        <h2 className="text-2xl font-semibold text-slate-800">{t("toolsTitle")}</h2>
      </div>
      <p className="text-slate-600 text-sm">{t("toolsDescription")}</p>

      {loading ? (
        <p className="text-slate-400">{tCommon("loading")}</p>
      ) : (
        Object.entries(grouped).map(([category, items]) => (
          <div key={category} className="space-y-2">
            <h3 className="text-lg font-medium capitalize text-slate-600">{category}</h3>
            <div className="space-y-2">
              {items.map((tool) => (
                <div key={tool.id} className="bg-white rounded-xl border border-slate-200 p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="font-medium text-sm text-slate-800">{tool.name}</h4>
                      <p className="text-xs text-slate-500 mt-1">{tool.description}</p>
                    </div>
                    <span className="text-xs text-slate-400 whitespace-nowrap ml-4">{tool.used_by.length} {t("agents")}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {tool.used_by.map((agentId) => (
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
