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
      <h2 className="text-2xl font-semibold">{t("title")}</h2>
      <p className="text-slate-400">{t("description")}</p>
      <div className="flex gap-3">
        <input
          value={gtin}
          onChange={(e) => setGtin(e.target.value)}
          placeholder={t("placeholderGtin")}
          className="flex-1 rounded bg-slate-800 border border-slate-600 px-3 py-2"
        />
        <button
          onClick={trace}
          disabled={loading}
          className="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-50"
        >
          {loading ? t("tracing") : t("trace")}
        </button>
      </div>
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {result && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-slate-700 p-4">
              <p className="text-sm text-slate-400">{t("gtin")}</p>
              <p className="font-mono">{result.gtin}</p>
            </div>
            <div className="rounded-lg border border-slate-700 p-4">
              <p className="text-sm text-slate-400">{t("chainDepth")}</p>
              <p className="text-2xl font-semibold">{result.supply_chain_depth}</p>
            </div>
          </div>
          {result.upstream_nodes.length > 0 ? (
            <div>
              <h3 className="font-medium mb-2">{t("upstreamNodes")}</h3>
              <div className="space-y-2">
                {result.upstream_nodes.map((node, i) => (
                  <div key={i} className="rounded border border-slate-700 p-3 text-sm">
                    <pre className="text-xs overflow-auto">{JSON.stringify(node, null, 2)}</pre>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-slate-500 text-sm">{t("noUpstream")}</p>
          )}
          <div className="rounded border border-slate-700 p-4">
            <h3 className="font-medium mb-2">{t("productData")}</h3>
            <pre className="text-xs overflow-auto text-slate-300">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
