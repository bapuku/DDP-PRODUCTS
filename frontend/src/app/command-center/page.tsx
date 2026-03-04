"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

type Step = "idle" | "creating" | "created" | "checking" | "checked" | "generating_qr" | "qr_done" | "anchoring" | "anchored" | "error";

interface DppResult { ddp_uri?: string; ddp_completeness?: number; validation_passed?: boolean; requires_human_review?: boolean; }
interface ComplianceResult { compliance_status?: string; confidence_scores?: Record<string, number>; regulation_references?: string[]; requires_human_review?: boolean; }
interface QrResult { gs1_digital_link: string; qr_png_base64: string; nfc_ndef_uri: string; rfid_epc_sgtin96: string; }
interface BlockchainResult { dpp_hash: string; block_number: number; block_hash: string; merkle_root: string; }

export default function CommandCenterPage() {
  const t = useTranslations("commandCenter");

  const [gtin, setGtin] = useState("06374692674377");
  const [serial, setSerial] = useState("SN-001");
  const [batch, setBatch] = useState("BATCH-001");
  const [sector, setSector] = useState("batteries");
  const [query, setQuery] = useState("");

  const [step, setStep] = useState<Step>("idle");
  const [dpp, setDpp] = useState<DppResult | null>(null);
  const [compliance, setCompliance] = useState<ComplianceResult | null>(null);
  const [qr, setQr] = useState<QrResult | null>(null);
  const [blockchain, setBlockchain] = useState<BlockchainResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const steps: { id: Step; label: string; icon: string; agent: string }[] = [
    { id: "creating", label: t("step1"), icon: "📋", agent: "data_collection → ddp_generation → validation" },
    { id: "checking", label: t("step2"), icon: "⚖️", agent: "regulatory_compliance" },
    { id: "generating_qr", label: t("step3"), icon: "📱", agent: "document_generation" },
    { id: "anchoring", label: t("step4"), icon: "🔐", agent: "audit_trail" },
  ];

  const doneSteps: Record<string, Step> = { creating: "created", checking: "checked", generating_qr: "qr_done", anchoring: "anchored" };

  function stepIndex(s: Step): number {
    const order: Step[] = ["idle", "creating", "created", "checking", "checked", "generating_qr", "qr_done", "anchoring", "anchored"];
    return order.indexOf(s);
  }

  async function runFullPipeline() {
    setError(null); setDpp(null); setCompliance(null); setQr(null); setBlockchain(null);
    let localDppUri = "";

    // Step 1: Create DPP
    setStep("creating");
    try {
      const r1 = await fetch("/api/v1/dpp/lifecycle/create", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_gtin: gtin, serial_number: serial, batch_number: batch || undefined, query: "Create DPP" }),
      });
      if (!r1.ok) throw new Error(`HTTP ${r1.status}`);
      const d1 = await r1.json();
      localDppUri = d1.ddp_uri || `https://id.gs1.org/01/${gtin}/21/${serial}`;
      setDpp(d1);
      setStep("created");
    } catch (e: unknown) { setError(`Step 1 — DPP creation: ${e instanceof Error ? e.message : String(e)}`); setStep("error"); return; }

    // Step 2: Compliance Check
    setStep("checking");
    try {
      const r2 = await fetch("/api/v1/compliance/check", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query || `Compliance check for ${sector} product GTIN ${gtin}`, product_gtin: gtin }),
      });
      if (!r2.ok) throw new Error(`HTTP ${r2.status}`);
      const d2 = await r2.json();
      setCompliance(d2);
      setStep("checked");
    } catch (e: unknown) { setError(`Step 2 — Compliance: ${e instanceof Error ? e.message : String(e)}`); setStep("error"); return; }

    // Step 3: Generate QR + Data Carriers
    setStep("generating_qr");
    try {
      const r3 = await fetch("/api/v1/qr/generate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gtin, serial_number: serial, sector }),
      });
      if (!r3.ok) throw new Error(`HTTP ${r3.status}`);
      const d3 = await r3.json();
      setQr(d3);
      setStep("qr_done");
    } catch (e: unknown) { setError(`Step 3 — QR: ${e instanceof Error ? e.message : String(e)}`); setStep("error"); return; }

    // Step 4: Blockchain Anchor
    setStep("anchoring");
    try {
      const r4 = await fetch("/api/v1/blockchain/anchor", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dpp_uri: localDppUri, gtin, serial_number: serial, dpp_data: { gtin, serial_number: serial, sector, batch } }),
      });
      if (!r4.ok) throw new Error(`HTTP ${r4.status}`);
      const d4 = await r4.json();
      setBlockchain(d4);
      setStep("anchored");
    } catch (e: unknown) { setError(`Step 4 — Blockchain: ${e instanceof Error ? e.message : String(e)}`); setStep("error"); return; }
  }

  const isRunning = ["creating", "checking", "generating_qr", "anchoring"].includes(step);

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-800">{t("title")}</h2>
        <p className="text-sm text-slate-500 mt-1">{t("description")}</p>
      </div>

      {/* Pipeline steps visual */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <div className="grid grid-cols-4 gap-3">
          {steps.map((s, i) => {
            const si = stepIndex(s.id);
            const current = step === s.id;
            const done = stepIndex(step) > si + 1 || step === doneSteps[s.id] || stepIndex(step) > stepIndex(doneSteps[s.id]);
            return (
              <div key={s.id} className={`rounded-xl border p-4 text-center transition-all ${current ? "border-sky-400 bg-sky-50 shadow-md scale-105" : done ? "border-emerald-300 bg-emerald-50" : "border-slate-200 bg-slate-50"}`}>
                <span className="text-2xl block mb-1">{done ? "✅" : current ? "⚙️" : s.icon}</span>
                <p className="text-xs font-semibold text-slate-700">{s.label}</p>
                <p className="text-[9px] text-slate-400 mt-1">{s.agent}</p>
                {current && <div className="mt-2 h-1 bg-sky-200 rounded-full overflow-hidden"><div className="h-full bg-sky-500 rounded-full animate-pulse w-2/3" /></div>}
              </div>
            );
          })}
        </div>
      </div>

      {/* Input form */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
        <h3 className="font-semibold text-slate-800">{t("productInfo")}</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">GTIN-14</label>
            <input value={gtin} onChange={e => setGtin(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" disabled={isRunning} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">{t("serial")}</label>
            <input value={serial} onChange={e => setSerial(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" disabled={isRunning} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">{t("batch")}</label>
            <input value={batch} onChange={e => setBatch(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" disabled={isRunning} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">{t("sector")}</label>
            <select value={sector} onChange={e => setSector(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" disabled={isRunning}>
              <option value="batteries">Batteries</option><option value="electronics">Electronics</option>
              <option value="textiles">Textiles</option><option value="vehicles">Vehicles</option>
              <option value="construction">Construction</option><option value="furniture">Furniture</option>
              <option value="plastics">Plastics</option><option value="chemicals">Chemicals</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">{t("complianceQuery")}</label>
          <input value={query} onChange={e => setQuery(e.target.value)} placeholder={t("queryPlaceholder")} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" disabled={isRunning} />
        </div>
        <button onClick={runFullPipeline} disabled={isRunning || !gtin || !serial} className="w-full py-3 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold text-sm shadow-md hover:shadow-lg transition disabled:opacity-50">
          {isRunning ? t("running") : t("launch")}
        </button>
      </div>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      {/* Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* DPP Result */}
        {dpp && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
            <h3 className="font-semibold text-emerald-800 flex items-center gap-2 mb-3"><span>📋</span> {t("resultDpp")}</h3>
            <div className="space-y-2 text-sm">
              <p className="text-slate-600">{t("dppUri")}: <span className="font-mono text-sky-600 text-xs break-all">{dpp.ddp_uri ?? "—"}</span></p>
              <p className="text-slate-600">{t("completeness")}: <span className="font-bold text-emerald-700">{dpp.ddp_completeness != null ? Math.round(dpp.ddp_completeness * 100) + "%" : "—"}</span></p>
              <p className="text-slate-600">{t("validation")}: <span className={`font-bold ${dpp.validation_passed ? "text-emerald-700" : "text-amber-600"}`}>{dpp.validation_passed ? "✓ Passed" : "⚠ Review"}</span></p>
              {dpp.requires_human_review && <Link href="/human-review" className="text-xs text-amber-600 font-medium hover:underline">→ {t("humanReview")}</Link>}
            </div>
          </div>
        )}

        {/* Compliance Result */}
        {compliance && (
          <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
            <h3 className="font-semibold text-blue-800 flex items-center gap-2 mb-3"><span>⚖️</span> {t("resultCompliance")}</h3>
            <div className="space-y-2 text-sm">
              <p className="text-slate-600">{t("status")}: <span className="font-bold text-blue-700">{compliance.compliance_status ?? "—"}</span></p>
              {compliance.confidence_scores && Object.entries(compliance.confidence_scores).map(([k, v]) => (
                <div key={k} className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 w-24">{k}</span>
                  <div className="flex-1 h-2 bg-blue-100 rounded-full"><div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.round(v * 100)}%` }} /></div>
                  <span className="text-xs font-mono text-slate-600">{Math.round(v * 100)}%</span>
                </div>
              ))}
              {compliance.regulation_references && compliance.regulation_references.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {compliance.regulation_references.map((r, i) => <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">{r}</span>)}
                </div>
              )}
            </div>
          </div>
        )}

        {/* QR Result */}
        {qr && (
          <div className="rounded-xl border border-purple-200 bg-purple-50 p-5">
            <h3 className="font-semibold text-purple-800 flex items-center gap-2 mb-3"><span>📱</span> {t("resultQr")}</h3>
            <div className="flex gap-4">
              {qr.qr_png_base64 && <img src={`data:image/png;base64,${qr.qr_png_base64}`} alt="QR" className="w-28 h-28 rounded-lg border border-purple-200" />}
              <div className="flex-1 space-y-2 text-xs">
                <div><span className="text-slate-400">GS1</span><p className="font-mono text-sky-600 break-all">{qr.gs1_digital_link}</p></div>
                <div><span className="text-slate-400">NFC</span><p className="font-mono text-slate-600 break-all">{qr.nfc_ndef_uri}</p></div>
                <div><span className="text-slate-400">RFID</span><p className="font-mono text-slate-600">{qr.rfid_epc_sgtin96}</p></div>
                <div className="flex gap-2 mt-1">
                  <a href={`/api/v1/qr/png?gtin=${gtin}&serial=${serial}&size=15`} target="_blank" className="px-3 py-1 rounded-lg bg-purple-200 text-purple-700 font-medium hover:bg-purple-300 transition">PNG ↓</a>
                  <a href={`/api/v1/qr/svg?gtin=${gtin}&serial=${serial}`} target="_blank" className="px-3 py-1 rounded-lg bg-purple-200 text-purple-700 font-medium hover:bg-purple-300 transition">SVG ↓</a>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Blockchain Result */}
        {blockchain && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
            <h3 className="font-semibold text-amber-800 flex items-center gap-2 mb-3"><span>🔐</span> {t("resultBlockchain")}</h3>
            <div className="space-y-2 text-xs">
              <div><span className="text-slate-400">{t("block")}</span><p className="font-bold text-amber-700 text-lg">#{blockchain.block_number}</p></div>
              <div><span className="text-slate-400">{t("hash")}</span><p className="font-mono text-slate-600 break-all">{blockchain.dpp_hash}</p></div>
              <div><span className="text-slate-400">Merkle Root</span><p className="font-mono text-slate-600 break-all">{blockchain.merkle_root}</p></div>
              <Link href="/blockchain" className="text-xs text-amber-700 font-medium hover:underline">→ {t("viewChain")}</Link>
            </div>
          </div>
        )}
      </div>

      {step === "anchored" && (
        <div className="rounded-xl border border-emerald-300 bg-emerald-100 p-5 text-center">
          <p className="text-lg font-bold text-emerald-800">✅ {t("pipelineComplete")}</p>
          <p className="text-sm text-emerald-600 mt-1">{t("pipelineSummary")}</p>
          <div className="flex justify-center gap-3 mt-4">
            <Link href={`/dpp/${gtin}/${serial}`} className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition">{t("viewDpp")}</Link>
            <Link href="/audit" className="px-4 py-2 rounded-lg bg-white border border-emerald-300 text-emerald-700 text-sm font-medium hover:bg-emerald-50 transition">{t("viewAudit")}</Link>
            <button onClick={() => { setStep("idle"); setDpp(null); setCompliance(null); setQr(null); setBlockchain(null); }} className="px-4 py-2 rounded-lg bg-white border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50 transition">{t("createAnother")}</button>
          </div>
        </div>
      )}
    </div>
  );
}
