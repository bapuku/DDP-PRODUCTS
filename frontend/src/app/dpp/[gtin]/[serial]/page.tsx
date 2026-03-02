"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/services/api";

export default function DPPDetailPage() {
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
      setError(p ? null : "DPP not found");
    }).finally(() => setLoading(false));
  }, [gtin, serial]);

  if (loading) return <div className="text-slate-400">Loading…</div>;
  if (error) return <div className="text-red-400">{error}</div>;

  const dppUri = (product?.dpp_uri as string) ?? `https://dpp.example.eu/product/${gtin}/${serial}`;
  const completeness = (product?.ddp_completeness as number) ?? 0;

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">DPP detail</h2>
        <Link href={`/dpp/${gtin}/${serial}/lifecycle`} className="text-sm text-sky-400 hover:underline">
          View lifecycle timeline →
        </Link>
      </div>
      <p className="text-slate-400 text-sm">
        GTIN: {gtin} · Serial: {serial}
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-2">Completeness score</h3>
          <div className="h-3 rounded-full bg-slate-700 overflow-hidden">
            <div className="h-full bg-sky-500 rounded-full" style={{ width: `${Math.round(completeness * 100)}%` }} />
          </div>
          <p className="text-sm text-slate-400 mt-1">{Math.round(completeness * 100)}%</p>
        </div>
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-2">DPP URI</h3>
          <a href={dppUri} target="_blank" rel="noopener noreferrer" className="text-sky-400 text-sm break-all hover:underline">
            {dppUri}
          </a>
        </div>
      </div>
      {product && (
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-2">Product data (7 clusters / Annex XIII)</h3>
          <pre className="text-xs text-slate-400 overflow-auto max-h-64">{JSON.stringify(product, null, 2)}</pre>
        </div>
      )}
      {carrier && (
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-2">Data carriers</h3>
          <p className="text-sm text-slate-400">QR / GS1 Digital Link: {carrier.qr_data}</p>
          <p className="text-sm text-slate-400 mt-1">NFC NDEF: {carrier.nfc_ndef_uri}</p>
          <p className="text-sm text-slate-400 mt-1">RFID EPC SGTIN-96: {carrier.rfid_epc_sgtin96}</p>
          <img src={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/dpp/${gtin}/${serial}/carrier/qr.png`} alt="QR" className="mt-3 h-24 w-24" />
        </div>
      )}
    </div>
  );
}
