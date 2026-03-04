"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

interface ChainStatus { chain: string; algorithm: string; total_blocks: number; total_anchored_dpps: number; integrity: string; latest_block: { block_number: number; block_hash: string; merkle_root: string; timestamp: string } | null; }
interface AnchoredDpp { dpp_uri: string; dpp_hash: string; gtin: string; serial_number: string; block_number: number; block_hash: string; merkle_root: string; timestamp: string; }

export default function BlockchainPage() {
  const t = useTranslations("blockchain");
  const [status, setStatus] = useState<ChainStatus | null>(null);
  const [anchored, setAnchored] = useState<AnchoredDpp[]>([]);
  const [verifyHash, setVerifyHash] = useState("");
  const [verifyResult, setVerifyResult] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    fetch("/api/v1/blockchain/status").then(r => r.json()).then(setStatus).catch(() => {});
    fetch("/api/v1/blockchain/anchored").then(r => r.json()).then(setAnchored).catch(() => {});
  }, []);

  async function verify() {
    if (!verifyHash.trim()) return;
    const res = await fetch(`/api/v1/blockchain/verify/${verifyHash.trim()}`);
    setVerifyResult(await res.json());
  }

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">{t("title")}</h2>
          <p className="text-sm text-slate-500 mt-1">{t("description")}</p>
        </div>
        <Link href="/connectors" className="px-4 py-2 text-sm rounded-lg bg-white border border-slate-200 text-slate-700 hover:border-sky-400 font-medium transition">
          {t("viewConnectors")} →
        </Link>
      </div>

      {/* Explainer */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <h3 className="font-semibold text-blue-800 mb-2">{t("howTitle")}</h3>
        <p className="text-sm text-blue-700 mb-3">{t("howDesc")}</p>
        <div className="grid grid-cols-3 gap-3">
          {[t("howStep1"), t("howStep2"), t("howStep3")].map((step, i) => (
            <div key={i} className="flex items-start gap-2">
              <span className="w-6 h-6 rounded-full bg-blue-200 text-blue-700 flex items-center justify-center text-xs font-bold flex-shrink-0">{i + 1}</span>
              <p className="text-sm text-blue-700">{step}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Chain Status */}
      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
            <p className="text-[10px] uppercase tracking-wider text-slate-400">{t("totalBlocks")}</p>
            <p className="text-2xl font-bold text-slate-800">{status.total_blocks}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
            <p className="text-[10px] uppercase tracking-wider text-slate-400">{t("anchoredDpps")}</p>
            <p className="text-2xl font-bold text-sky-600">{status.total_anchored_dpps}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
            <p className="text-[10px] uppercase tracking-wider text-slate-400">{t("algorithm")}</p>
            <p className="text-sm font-semibold text-slate-700">{status.algorithm}</p>
          </div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-center">
            <p className="text-[10px] uppercase tracking-wider text-emerald-500">{t("integrity")}</p>
            <p className="text-2xl font-bold text-emerald-700">✓ {status.integrity}</p>
          </div>
        </div>
      )}

      {/* Verify */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold text-slate-800 mb-3">{t("verifyTitle")}</h3>
        <div className="flex gap-3">
          <input value={verifyHash} onChange={e => setVerifyHash(e.target.value)} placeholder={t("verifyPlaceholder")} className="flex-1 rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm font-mono" />
          <button onClick={verify} className="px-5 py-2 rounded-lg bg-sky-500 text-white font-medium hover:bg-sky-600 transition text-sm">{t("verify")}</button>
        </div>
        {verifyResult && (
          <div className={`mt-3 rounded-lg p-3 text-sm ${verifyResult.verified ? "bg-emerald-50 border border-emerald-200 text-emerald-700" : "bg-red-50 border border-red-200 text-red-700"}`}>
            <p className="font-semibold">{verifyResult.verified ? t("verifiedOk") : t("verifiedFail")}</p>
            {verifyResult.block_number != null && <p className="text-xs mt-1">Block #{String(verifyResult.block_number)} · {String(verifyResult.anchored_at)}</p>}
            {verifyResult.reason != null && <p className="text-xs mt-1">{String(verifyResult.reason)}</p>}
          </div>
        )}
      </div>

      {/* Anchored DPPs */}
      {anchored.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-slate-800">{t("anchoredList")} ({anchored.length})</h3>
          <div className="rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead><tr className="bg-slate-50 text-left text-slate-600">
                <th className="px-4 py-2">{t("block")}</th><th className="px-4 py-2">GTIN</th><th className="px-4 py-2">{t("hash")}</th><th className="px-4 py-2">{t("time")}</th>
              </tr></thead>
              <tbody>
                {anchored.map((a, i) => (
                  <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-2 font-mono">#{a.block_number}</td>
                    <td className="px-4 py-2">{a.gtin}</td>
                    <td className="px-4 py-2 font-mono text-xs text-slate-500">{a.dpp_hash.slice(0, 16)}…</td>
                    <td className="px-4 py-2 text-slate-500">{a.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
