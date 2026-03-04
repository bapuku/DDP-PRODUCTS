"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

interface Connector { id: string; name: string; type: string; protocol: string; description: string; status: string; last_sync: string | null; records_ingested: number; auto_create_dpp: boolean; }
interface Template { type: string; name: string; protocol: string; description: string; fields: string[]; }

const TYPE_STYLE: Record<string, { icon: string; color: string }> = {
  erp: { icon: "🏢", color: "bg-blue-50 border-blue-200 text-blue-700" },
  mes: { icon: "🏭", color: "bg-amber-50 border-amber-200 text-amber-700" },
  plm: { icon: "📐", color: "bg-purple-50 border-purple-200 text-purple-700" },
  lims: { icon: "🔬", color: "bg-teal-50 border-teal-200 text-teal-700" },
  iot: { icon: "📡", color: "bg-emerald-50 border-emerald-200 text-emerald-700" },
  scada: { icon: "⚡", color: "bg-orange-50 border-orange-200 text-orange-700" },
  wms: { icon: "📦", color: "bg-cyan-50 border-cyan-200 text-cyan-700" },
  custom: { icon: "🔧", color: "bg-slate-50 border-slate-200 text-slate-700" },
};

export default function ConnectorsPage() {
  const t = useTranslations("connectors");
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("custom");
  const [newProtocol, setNewProtocol] = useState("rest");
  const [newAuto, setNewAuto] = useState(false);

  useEffect(() => {
    fetch("/api/v1/connectors").then(r => r.json()).then(setConnectors).catch(() => {});
    fetch("/api/v1/connectors/templates").then(r => r.json()).then(setTemplates).catch(() => {});
  }, []);

  async function addConnector() {
    if (!newName.trim()) return;
    const res = await fetch("/api/v1/connectors", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName, type: newType, protocol: newProtocol, auto_create_dpp: newAuto }),
    });
    if (res.ok) {
      const c = await res.json();
      setConnectors(prev => [...prev, c]);
      setShowNew(false);
      setNewName("");
    }
  }

  async function testConnector(id: string) {
    const res = await fetch(`/api/v1/connectors/${id}/test`, { method: "POST" });
    if (res.ok) {
      setConnectors(prev => prev.map(c => c.id === id ? { ...c, status: "active" } : c));
    }
  }

  return (
    <div className="max-w-6xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">{t("title")}</h2>
          <p className="text-sm text-slate-500 mt-1">{t("description")}</p>
        </div>
        <div className="flex gap-2">
          <Link href="/blockchain" className="px-4 py-2 text-sm rounded-lg bg-white border border-slate-200 text-slate-700 hover:border-sky-400 font-medium transition">
            {t("viewBlockchain")} →
          </Link>
          <button onClick={() => setShowNew(!showNew)} className="px-4 py-2 text-sm rounded-lg bg-sky-500 text-white font-medium hover:bg-sky-600 transition">
            {t("addConnector")}
          </button>
        </div>
      </div>

      {/* How it works */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <h3 className="font-semibold text-blue-800 mb-2">{t("howTitle")}</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-3">
          {[t("step1"), t("step2"), t("step3"), t("step4")].map((step, i) => (
            <div key={i} className="flex items-start gap-2">
              <span className="w-6 h-6 rounded-full bg-blue-200 text-blue-700 flex items-center justify-center text-xs font-bold flex-shrink-0">{i + 1}</span>
              <p className="text-sm text-blue-700">{step}</p>
            </div>
          ))}
        </div>
      </div>

      {/* New connector form */}
      {showNew && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
          <h3 className="font-semibold text-slate-800">{t("newConnector")}</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-slate-600 mb-1">{t("name")}</label>
              <input value={newName} onChange={e => setNewName(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" placeholder="SAP S/4HANA Production" />
            </div>
            <div>
              <label className="block text-sm text-slate-600 mb-1">{t("type")}</label>
              <select value={newType} onChange={e => setNewType(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm">
                <option value="erp">ERP</option><option value="mes">MES</option><option value="plm">PLM</option>
                <option value="lims">LIMS</option><option value="iot">IoT</option><option value="scada">SCADA</option>
                <option value="wms">WMS</option><option value="custom">Custom</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-600 mb-1">{t("protocol")}</label>
              <select value={newProtocol} onChange={e => setNewProtocol(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm">
                <option value="rest">REST API</option><option value="soap">SOAP</option><option value="opc-ua">OPC-UA</option>
                <option value="mqtt">MQTT</option><option value="kafka">Kafka</option><option value="webhook">Webhook</option>
                <option value="sftp">SFTP</option><option value="custom">Custom</option>
              </select>
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input type="checkbox" checked={newAuto} onChange={e => setNewAuto(e.target.checked)} className="rounded" />
                {t("autoDpp")}
              </label>
            </div>
          </div>
          <button onClick={addConnector} className="px-5 py-2 rounded-lg bg-sky-500 text-white font-medium hover:bg-sky-600 transition text-sm">
            {t("register")}
          </button>
        </div>
      )}

      {/* Active connectors */}
      {connectors.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-slate-800">{t("activeConnectors")} ({connectors.length})</h3>
          {connectors.map(c => {
            const style = TYPE_STYLE[c.type] ?? TYPE_STYLE.custom;
            return (
              <div key={c.id} className={`rounded-xl border p-4 ${style.color}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{style.icon}</span>
                    <div>
                      <p className="font-semibold">{c.name}</p>
                      <p className="text-xs opacity-70">{c.type.toUpperCase()} · {c.protocol.toUpperCase()} · {c.records_ingested} records</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${c.status === "active" ? "bg-emerald-100 text-emerald-700" : c.status === "error" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-600"}`}>
                      {c.status}
                    </span>
                    {c.auto_create_dpp && <span className="text-xs px-2 py-1 rounded-full bg-sky-100 text-sky-700 font-medium">Auto-DPP</span>}
                    <button onClick={() => testConnector(c.id)} className="text-xs px-3 py-1 rounded-lg bg-white border border-current opacity-70 hover:opacity-100 transition">
                      {t("test")}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Templates */}
      <div className="space-y-3">
        <h3 className="font-semibold text-slate-800">{t("templates")} ({templates.length})</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {templates.map((tpl, i) => {
            const style = TYPE_STYLE[tpl.type] ?? TYPE_STYLE.custom;
            return (
              <div key={i} className="rounded-xl border border-slate-200 bg-white p-4 card-hover">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">{style.icon}</span>
                  <h4 className="font-semibold text-sm text-slate-800">{tpl.name}</h4>
                </div>
                <p className="text-xs text-slate-500 mb-2">{tpl.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-500">{tpl.protocol.toUpperCase()}</span>
                  <button onClick={() => { setNewName(tpl.name); setNewType(tpl.type); setNewProtocol(tpl.protocol); setShowNew(true); }}
                    className="text-xs text-sky-500 font-medium hover:underline">{t("useTemplate")} →</button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
