"use client";

import { useState, useRef, useEffect } from "react";
import { useTranslations } from "next-intl";
import { usePathname } from "next/navigation";
import Link from "next/link";

interface Message {
  role: "user" | "assistant";
  content: string;
  action?: ActionResult | null;
}

interface ActionResult {
  type: string;
  agent?: string;
  params?: Record<string, string>;
  endpoint?: string;
}

function getLocale(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  return m ? m[1].trim() : "en";
}

const ACTION_LABELS: Record<string, { icon: string; label: string }> = {
  COMPLIANCE_CHECK: { icon: "✅", label: "Compliance Check" },
  CREATE_DPP: { icon: "📋", label: "DPP Creation" },
  CREATE_BATTERY: { icon: "🔋", label: "Battery Passport" },
  TRACE_SUPPLY_CHAIN: { icon: "🔗", label: "Supply Chain Trace" },
  ML_PREDICT: { icon: "📈", label: "ML Prediction" },
  VIEW_AUDIT: { icon: "📜", label: "Audit Log" },
  VIEW_CALENDAR: { icon: "📅", label: "Compliance Calendar" },
  VIEW_AGENTS: { icon: "🤖", label: "Agent Registry" },
  LIFECYCLE_UPDATE: { icon: "♻️", label: "Lifecycle Update" },
};

const PAGE_ACTIONS: Record<string, string[]> = {
  "/": ["What can I do on this platform?", "Show me the agent registry", "Run a compliance check"],
  "/agents": ["Which agent handles compliance?", "How do quality gates work?", "Explain the workflow"],
  "/dpp": ["Create a new DPP", "What sectors are supported?", "Explain the creation workflow"],
  "/compliance": ["Check battery regulation compliance", "What frameworks are checked?", "Show the compliance calendar"],
  "/supply-chain": ["Trace supply chain for a product", "How does Neo4j traceability work?", "What is EPCIS 2.0?"],
  "/audit": ["Show recent audit entries", "How long is data retained?", "What is logged per EU AI Act?"],
  "/ml/predictions": ["Predict compliance for a battery", "Which ML models are used?", "Explain the scoring"],
  "/reports": ["Show compliance status per regulation", "Which articles are implemented?", "Generate an Art. 12 report"],
  "/human-review": ["Why are items escalated?", "What are the confidence thresholds?", "How does Art. 14 work?"],
};

export default function SystemAssistant() {
  const t = useTranslations("assistant");
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const suggestions = PAGE_ACTIONS[pathname] || PAGE_ACTIONS["/"] || [];

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setSending(true);
    try {
      const history = messages.slice(-8).map((m) => ({ role: m.role, content: m.content }));
      const res = await fetch("/api/v1/assistant/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept-Language": getLocale() },
        body: JSON.stringify({ message: userMsg, history, context: { page: pathname } }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response ?? "No response",
          action: data.action ?? null,
        },
      ]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: t("error") }]);
    } finally {
      setSending(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-5 py-3.5 rounded-full bg-gradient-to-r from-teal-600 to-cyan-500 text-white shadow-lg hover:shadow-xl transition-all hover:scale-105"
      >
        <span className="text-xl">🤖</span>
        <span className="text-sm font-semibold">{t("systemAssistant")}</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-[480px] max-w-[calc(100vw-2rem)] h-[560px] max-h-[calc(100vh-3rem)] rounded-2xl border border-slate-200 bg-white shadow-2xl flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-teal-600 to-cyan-500 text-white flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <span className="text-xl">🤖</span>
          <div>
            <p className="text-sm font-bold">{t("systemTitle")}</p>
            <p className="text-[10px] opacity-80">{t("systemSubtitle")}</p>
          </div>
        </div>
        <button onClick={() => setOpen(false)} className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center hover:bg-white/30 transition text-sm font-bold">✕</button>
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-auto p-4 space-y-3 bg-slate-50">
        {messages.length === 0 && (
          <div className="space-y-4 py-4">
            <div className="text-center">
              <p className="text-3xl mb-2">🤖</p>
              <p className="text-sm font-semibold text-slate-700">{t("welcomeTitle")}</p>
              <p className="text-xs text-slate-500 mt-1">{t("welcomeSubtitle")}</p>
            </div>
            <div className="space-y-2">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 px-1">{t("trySaying")}</p>
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => setInput(s)}
                  className="w-full text-left text-sm px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:border-sky-400 hover:text-sky-600 transition"
                >
                  {s}
                </button>
              ))}
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-3 mt-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2">{t("capabilities")}</p>
              <div className="grid grid-cols-2 gap-1.5 text-xs text-slate-600">
                <span>✅ {t("capCompliance")}</span>
                <span>📋 {t("capCreateDPP")}</span>
                <span>🔗 {t("capSupplyChain")}</span>
                <span>📈 {t("capMLPredict")}</span>
                <span>📜 {t("capAudit")}</span>
                <span>⚖️ {t("capRegulations")}</span>
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className="max-w-[90%] space-y-2">
              <div className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-sky-500 text-white rounded-br-md"
                  : "bg-white border border-slate-200 text-slate-700 rounded-bl-md shadow-sm"
              }`}>
                <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
              </div>
              {msg.action && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-3 py-2 text-xs">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{ACTION_LABELS[msg.action.type]?.icon ?? "⚡"}</span>
                    <span className="font-semibold text-emerald-700">{t("actionExecuted")}: {ACTION_LABELS[msg.action.type]?.label ?? msg.action.type}</span>
                  </div>
                  {msg.action.agent && (
                    <p className="text-emerald-600">
                      Agent: <Link href={`/agents/${msg.action.agent}`} className="underline hover:text-emerald-800">{msg.action.agent}</Link>
                    </p>
                  )}
                  {msg.action.endpoint && (
                    <p className="text-emerald-500 font-mono">{msg.action.endpoint}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-md px-4 py-2.5 text-sm text-slate-400 shadow-sm flex items-center gap-2">
              <span className="animate-spin text-sky-500">⚙️</span>
              <span>{t("processing")}</span>
            </div>
          </div>
        )}
        <div ref={chatEnd} />
      </div>

      {/* Input */}
      <form onSubmit={send} className="flex border-t border-slate-200 flex-shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("systemPlaceholder")}
          className="flex-1 px-4 py-3.5 text-sm focus:outline-none bg-white"
          disabled={sending}
        />
        <button type="submit" disabled={sending || !input.trim()} className="px-5 py-3.5 bg-sky-500 hover:bg-sky-600 text-white font-bold disabled:opacity-40 transition">
          ↑
        </button>
      </form>
    </div>
  );
}
