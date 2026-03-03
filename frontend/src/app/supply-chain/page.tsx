"use client";

import { useState } from "react";
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
        </div>
      )}
    </div>
  );
}
