"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
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

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

function getLocale(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  return m ? m[1].trim() : "en";
}

export default function AgentDetailPage() {
  const t = useTranslations("agentRegistry");
  const tCommon = useTranslations("common");
  const params = useParams();
  const agentId = params?.agentId as string;
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API}/api/v1/agents/registry/${agentId}`, {
      headers: { "Accept-Language": getLocale() },
    })
      .then((r) => r.json())
      .then(setAgent)
      .catch(() => setAgent(null))
      .finally(() => setLoading(false));
  }, [agentId]);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setSending(true);
    try {
      const res = await fetch(`${API}/api/v1/agents/${agentId}/assist`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept-Language": getLocale() },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.response ?? data.detail ?? "No response" }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Error contacting assistant." }]);
    } finally {
      setSending(false);
    }
  }

  if (loading) return <p className="text-slate-500">{tCommon("loading")}</p>;
  if (!agent) return <p className="text-red-400">{t("agentNotFound")}</p>;

  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/agents" className="text-sky-400 text-sm hover:underline">{t("backToAgents")}</Link>
        <h2 className="text-2xl font-semibold">{agent.name}</h2>
        <span className={`text-xs px-2 py-0.5 rounded-full ${agent.status === "active" ? "bg-emerald-900/60 text-emerald-300" : "bg-red-900/60 text-red-300"}`}>
          {agent.status}
        </span>
      </div>

      <p className="text-slate-400">{agent.description}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-3">{t("skills")} ({agent.skills.length})</h3>
          <div className="flex flex-wrap gap-1.5">
            {agent.skills.map((s) => (
              <span key={s} className="text-xs px-2 py-1 rounded bg-sky-900/40 text-sky-300">{s.replace(/_/g, " ")}</span>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-3">{t("tools")} ({agent.tools.length})</h3>
          <div className="flex flex-wrap gap-1.5">
            {agent.tools.map((tool) => (
              <span key={tool} className="text-xs px-2 py-1 rounded bg-amber-900/40 text-amber-300">{tool.replace(/_/g, " ")}</span>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-3">{t("complianceRefs")}</h3>
          <div className="flex flex-wrap gap-1.5">
            {agent.compliance_refs.map((ref) => (
              <span key={ref} className="text-xs px-2 py-1 rounded bg-emerald-900/40 text-emerald-300">{ref}</span>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-3">{t("metadata")}</h3>
          <div className="text-sm space-y-1 text-slate-400">
            <p>{t("category")}: <span className="text-slate-200 capitalize">{agent.category}</span></p>
            <p>{t("phase")}: <span className="text-slate-200">{agent.phase}</span></p>
            <p>{t("llmModel")}: <span className="text-slate-200">{agent.llm_model ?? "—"}</span></p>
          </div>
        </div>
      </div>

      {/* Gen AI Assistant Chat */}
      <div className="rounded-lg border border-slate-700 overflow-hidden">
        <div className="bg-slate-800 px-4 py-3 border-b border-slate-700 flex items-center gap-2">
          <span className="text-lg">💬</span>
          <h3 className="font-medium">{t("assistantTitle")} — {agent.name}</h3>
        </div>
        <div className="h-80 overflow-auto p-4 space-y-3 bg-slate-950/50">
          {messages.length === 0 && (
            <p className="text-slate-500 text-sm text-center mt-12">{t("assistantPlaceholder")}</p>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${msg.role === "user" ? "bg-sky-600 text-white" : "bg-slate-800 text-slate-200"}`}>
                <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="bg-slate-800 rounded-lg px-4 py-2 text-sm text-slate-400 animate-pulse">{t("thinking")}</div>
            </div>
          )}
          <div ref={chatEnd} />
        </div>
        <form onSubmit={sendMessage} className="flex border-t border-slate-700">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t("askAgent")}
            className="flex-1 bg-slate-900 px-4 py-3 text-sm focus:outline-none"
            disabled={sending}
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="px-6 py-3 bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium disabled:opacity-50 transition"
          >
            {t("send")}
          </button>
        </form>
      </div>
    </div>
  );
}
