"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { api, SupplyChainResult } from "@/services/api";

export default function SupplyChainPage() {
  const t = useTranslations("supplyChain");
  const [gtin, setGtin] = useState("06374692674370");
  const [result, setResult] = useState<SupplyChainResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trace = () => {
    setLoading(true);
    setError(null);
    api.dpp
      .supplyChain(gtin)
      .then(setResult)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
      <p className="text-slate-600">{t("description")}</p>

      {/* --- Explainer: Supply Chain Traceability --- */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <h3 className="text-base font-semibold text-blue-900 mb-2">Supply Chain Traceability &mdash; Battery Reg Art.&nbsp;49</h3>
        <p className="text-sm text-blue-800 leading-relaxed">
          Article 49 of the <span className="font-medium">EU Battery Regulation 2023/1542</span> requires economic operators to implement
          due-diligence policies for the raw-material supply chain. This tool traces a product&apos;s upstream suppliers across
          multiple tiers, providing full visibility from raw-material extraction to final assembly.
        </p>
      </div>

      {/* --- How It Works (3 Steps) --- */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h4 className="text-sm font-semibold text-slate-800 mb-3">How It Works</h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex flex-col items-center text-center">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-sky-100 text-sky-700 text-sm font-bold mb-2">1</span>
            <p className="text-sm font-medium text-slate-800">Enter GTIN</p>
            <p className="text-xs text-slate-500 mt-1">Provide the GS1 Global Trade Item Number of the product to trace.</p>
          </div>
          <div className="flex flex-col items-center text-center">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-sky-100 text-sky-700 text-sm font-bold mb-2">2</span>
            <p className="text-sm font-medium text-slate-800">Neo4j Graph Traversal</p>
            <p className="text-xs text-slate-500 mt-1">The supply-chain agent queries the knowledge graph for upstream relationships.</p>
          </div>
          <div className="flex flex-col items-center text-center">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-sky-100 text-sky-700 text-sm font-bold mb-2">3</span>
            <p className="text-sm font-medium text-slate-800">Multi-Tier Visibility</p>
            <p className="text-xs text-slate-500 mt-1">View every supplier tier, from raw materials to final product assembly.</p>
          </div>
        </div>
      </div>

      {/* --- Agents & Tools Involved --- */}
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h4 className="text-sm font-semibold text-slate-800 mb-2">Agents &amp; Tools Involved</h4>
        <div className="flex flex-wrap gap-2">
          <Link href="/agents/supply_chain" className="inline-flex items-center gap-1.5 rounded-lg border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-700 hover:bg-violet-100 transition">
            Supply Chain Agent
          </Link>
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">
            Neo4j Knowledge Graph
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">
            EPCIS 2.0
          </span>
        </div>
      </div>

      {/* --- GTIN Input + Trace Button --- */}
      <div className="flex gap-3">
        <input
          value={gtin}
          onChange={(e) => setGtin(e.target.value)}
          placeholder={t("placeholderGtin")}
          className="flex-1 rounded-lg bg-white border border-slate-300 px-3 py-2 text-slate-800"
        />
        <button
          onClick={trace}
          disabled={loading}
          className="px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white disabled:opacity-50 transition"
        >
          {loading ? t("tracing") : t("trace")}
        </button>
      </div>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {/* --- Results --- */}
      {result && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-sm text-slate-400">{t("gtin")}</p>
              <p className="font-mono text-slate-800">{result.gtin}</p>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-sm text-slate-400">{t("chainDepth")}</p>
              <p className="text-2xl font-semibold text-slate-800">{result.supply_chain_depth}</p>
            </div>
          </div>
          {result.upstream_nodes.length > 0 ? (
            <div>
              <h3 className="font-medium mb-2 text-slate-800">{t("upstreamNodes")}</h3>
              <div className="space-y-2">
                {result.upstream_nodes.map((node, i) => (
                  <div key={i} className="bg-white rounded-xl border border-slate-200 p-3 text-sm">
                    <pre className="text-xs overflow-auto text-slate-600">{JSON.stringify(node, null, 2)}</pre>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-slate-400 text-sm">{t("noUpstream")}</p>
          )}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="font-medium mb-2 text-slate-800">{t("productData")}</h3>
            <pre className="text-xs overflow-auto text-slate-600">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>

          {/* --- Post-Result Actions --- */}
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h4 className="text-sm font-semibold text-slate-800 mb-2">Further Actions</h4>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `epcis-export-${result.gtin}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-700 hover:bg-emerald-100 transition"
              >
                Export EPCIS 2.0 Event
              </button>
              <Link
                href="/knowledge-graph"
                className="inline-flex items-center gap-1.5 rounded-lg border border-violet-200 bg-violet-50 px-3 py-1.5 text-sm font-medium text-violet-700 hover:bg-violet-100 transition"
              >
                View in Knowledge Graph
              </Link>
              <Link
                href={`/compliance?gtin=${result.gtin}`}
                className="inline-flex items-center gap-1.5 rounded-lg border border-sky-200 bg-sky-50 px-3 py-1.5 text-sm font-medium text-sky-700 hover:bg-sky-100 transition"
              >
                Run Compliance Check
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
