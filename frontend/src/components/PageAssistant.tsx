"use client";

import { useState, useRef, useEffect } from "react";
import { useTranslations } from "next-intl";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface PageAssistantProps {
  agentId: string;
  agentLabel: string;
  pageContext: string;
}

function getLocale(): string {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/locale=([^;]+)/);
  return m ? m[1].trim() : "en";
}

export default function PageAssistant({ agentId, agentLabel, pageContext }: PageAssistantProps) {
  const t = useTranslations("assistant");
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setSending(true);
    try {
      const res = await fetch(`/api/v1/agents/${agentId}/assist`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept-Language": getLocale() },
        body: JSON.stringify({ message: userMsg, context: { page: pageContext } }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.response ?? data.detail ?? "No response" }]);
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
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-full bg-sky-500 text-white shadow-lg hover:bg-sky-600 transition hover:shadow-xl"
      >
        <span className="text-lg">💬</span>
        <span className="text-sm font-medium">{t("askAssistant")} — {agentLabel}</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-[420px] max-w-[calc(100vw-2rem)] rounded-2xl border border-slate-200 bg-white shadow-2xl flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white">
        <div className="flex items-center gap-2">
          <span className="text-lg">💬</span>
          <div>
            <p className="text-sm font-semibold">{t("title")} — {agentLabel}</p>
            <p className="text-[10px] opacity-80">{t("poweredBy")}</p>
          </div>
        </div>
        <button onClick={() => setOpen(false)} className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center hover:bg-white/30 transition text-sm">✕</button>
      </div>

      <div className="h-72 overflow-auto p-4 space-y-3 bg-slate-50">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <p className="text-3xl mb-3">🤖</p>
            <p className="text-sm text-slate-500">{t("placeholder")}</p>
            <div className="flex flex-wrap gap-1.5 justify-center mt-3">
              {[t("suggestion1"), t("suggestion2"), t("suggestion3")].map((s, i) => (
                <button key={i} onClick={() => { setInput(s); }} className="text-xs px-3 py-1.5 rounded-full bg-white border border-slate-200 text-slate-600 hover:border-sky-400 hover:text-sky-600 transition">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${msg.role === "user" ? "bg-sky-500 text-white rounded-br-md" : "bg-white border border-slate-200 text-slate-700 rounded-bl-md shadow-sm"}`}>
              <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-md px-4 py-2.5 text-sm text-slate-400 shadow-sm">
              <span className="animate-pulse">{t("thinking")}</span>
            </div>
          </div>
        )}
        <div ref={chatEnd} />
      </div>

      <form onSubmit={send} className="flex border-t border-slate-200">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("inputPlaceholder")}
          className="flex-1 px-4 py-3 text-sm focus:outline-none bg-white"
          disabled={sending}
        />
        <button type="submit" disabled={sending || !input.trim()} className="px-5 py-3 bg-sky-500 hover:bg-sky-600 text-white text-sm font-medium disabled:opacity-40 transition">
          ↑
        </button>
      </form>
    </div>
  );
}
