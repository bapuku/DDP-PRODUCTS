"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import PageAssistant from "@/components/PageAssistant";
import { api } from "@/services/api";

export default function DPPDetailPage() {
  const t = useTranslations("dppDetail");
  const tCommon = useTranslations("common");
  const params = useParams();
  const gtin = params?.gtin as string;
  const serial = params?.serial as string;
  const [product, setProduct] = useState<Record<string, unknown> | null>(null);
  const [carrier, setCarrier] = useState<{ qr_data: string; nfc_ndef_uri: string; rfid_epc_sgtin96: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!gtin || !serial) return;
    Promise.all([
      api.dpp.get("batteries", gtin, serial).catch(() => null),
      api.lifecycle.carrier(gtin, serial).catch(() => null),
    ]).then(([p, c]) => {
      setProduct(p ?? null);
      setCarrier(c ?? null);
      setError(p ? null : "not_found");
    }).finally(() => setLoading(false));
  }, [gtin, serial]);

  if (loading) return <div className="text-slate-400">{tCommon("loading")}</div>;
  if (error) return <div className="text-red-600">{t("dppNotFound")}</div>;

  const dppUri = (product?.dpp_uri as string) ?? `https://dpp.example.eu/product/${gtin}/${serial}`;
  const completeness = (product?.ddp_completeness as number) ?? 0;

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
        <Link href={`/dpp/${gtin}/${serial}/lifecycle`} className="text-sm text-sky-500 hover:text-sky-600 hover:underline">
          {t("viewLifecycle")}
        </Link>
      </div>
      <p className="text-slate-600 text-sm">
        {t("gtinSerial", { gtin, serial })}
      </p>

      {/* --- Quick-Action Bar --- */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 flex flex-wrap items-center gap-3">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400 mr-1">Quick Actions</span>
        <Link
          href={`/compliance?gtin=${gtin}`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-sky-200 bg-sky-50 px-3 py-1.5 text-sm font-medium text-sky-700 hover:bg-sky-100 transition"
        >
          <span>✓</span> Run Compliance Check
        </Link>
        <Link
          href={`/supply-chain?gtin=${gtin}`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-700 hover:bg-emerald-100 transition"
        >
          <span>⛓</span> View Supply Chain
        </Link>
        <a
          href={`/api/v1/dpp/${gtin}/${serial}/carrier/qr.png`}
          download
          className="inline-flex items-center gap-1.5 rounded-lg border border-violet-200 bg-violet-50 px-3 py-1.5 text-sm font-medium text-violet-700 hover:bg-violet-100 transition"
        >
          <span>↓</span> Download QR
        </a>
        <Link
          href={`/dpp/${gtin}/${serial}/lifecycle`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-3 py-1.5 text-sm font-medium text-amber-700 hover:bg-amber-100 transition"
        >
          <span>⏱</span> Lifecycle Timeline
        </Link>
      </div>

      {/* --- Completeness Score --- */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-slate-800">{t("completenessScore")}</h3>
            <Link href="/agents/dpp_generation" className="text-xs text-sky-500 hover:underline">DPP Agent →</Link>
          </div>
          <div className="h-3 rounded-full bg-slate-200 overflow-hidden">
            <div className="h-full bg-sky-500 rounded-full" style={{ width: `${Math.round(completeness * 100)}%` }} />
          </div>
          <p className="text-sm text-slate-400 mt-1">{Math.round(completeness * 100)}%</p>
          <p className="text-xs text-slate-400 mt-2">
            Measures how many required ESPR data fields are populated for this passport.
          </p>
        </div>

        {/* --- DPP URI --- */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h3 className="font-medium mb-2 text-slate-800">{t("dppUri")}</h3>
          <a href={dppUri} target="_blank" rel="noopener noreferrer" className="text-sky-500 text-sm break-all hover:underline hover:text-sky-600">
            {dppUri}
          </a>
        </div>
      </div>

      {/* --- Product Data --- */}
      {product && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-slate-800">{t("productDataTitle")}</h3>
            <Link href="/agents/dpp_generation" className="text-xs text-sky-500 hover:underline">Managed by DPP Generation Agent →</Link>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Raw product data stored in the DPP registry. Includes composition, carbon footprint, and material declarations.
          </p>
          <pre className="text-xs text-slate-600 overflow-auto max-h-64">{JSON.stringify(product, null, 2)}</pre>
        </div>
      )}

      {/* --- Data Carriers --- */}
      {carrier && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-slate-800">{t("dataCarriers")}</h3>
            <Link href="/agents/lifecycle_manager" className="text-xs text-sky-500 hover:underline">Lifecycle Agent →</Link>
          </div>
          <p className="text-xs text-slate-400 mb-3">
            Machine-readable identifiers linking the physical product to its digital passport via QR, NFC, and RFID.
          </p>
          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <span className="text-xs font-mono bg-slate-100 text-slate-500 rounded px-1.5 py-0.5 shrink-0">QR</span>
              <p className="text-sm text-slate-600 break-all">{carrier.qr_data}</p>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-xs font-mono bg-slate-100 text-slate-500 rounded px-1.5 py-0.5 shrink-0">NFC</span>
              <p className="text-sm text-slate-600 break-all">{carrier.nfc_ndef_uri}</p>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-xs font-mono bg-slate-100 text-slate-500 rounded px-1.5 py-0.5 shrink-0">RFID</span>
              <p className="text-sm text-slate-600 break-all">{carrier.rfid_epc_sgtin96}</p>
            </div>
          </div>
          <img src={`/api/v1/dpp/${gtin}/${serial}/carrier/qr.png`} alt="QR" className="mt-3 h-24 w-24" />
        </div>
      )}
      <PageAssistant agentId="ddp_generation" agentLabel="DPP Generation" pageContext="dpp-detail" />
    </div>
  );
}
