"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
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
  if (error) return <div className="text-red-400">{t("dppNotFound")}</div>;

  const dppUri = (product?.dpp_uri as string) ?? `https://dpp.example.eu/product/${gtin}/${serial}`;
  const completeness = (product?.ddp_completeness as number) ?? 0;

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">{t("title")}</h2>
        <Link href={`/dpp/${gtin}/${serial}/lifecycle`} className="text-sm text-sky-400 hover:underline">
          {t("viewLifecycle")}
        </Link>
      </div>
      <p className="text-slate-400 text-sm">
        {t("gtinSerial", { gtin, serial })}
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-2">{t("completenessScore")}</h3>
          <div className="h-3 rounded-full bg-slate-700 overflow-hidden">
            <div className="h-full bg-sky-500 rounded-full" style={{ width: `${Math.round(completeness * 100)}%` }} />
          </div>
          <p className="text-sm text-slate-400 mt-1">{Math.round(completeness * 100)}%</p>
        </div>
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-2">{t("dppUri")}</h3>
          <a href={dppUri} target="_blank" rel="noopener noreferrer" className="text-sky-400 text-sm break-all hover:underline">
            {dppUri}
          </a>
        </div>
      </div>
      {product && (
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-2">{t("productDataTitle")}</h3>
          <pre className="text-xs text-slate-400 overflow-auto max-h-64">{JSON.stringify(product, null, 2)}</pre>
        </div>
      )}
      {carrier && (
        <div className="rounded-lg border border-slate-700 p-5">
          <h3 className="font-medium mb-2">{t("dataCarriers")}</h3>
          <p className="text-sm text-slate-400">{t("qrGs1")} {carrier.qr_data}</p>
          <p className="text-sm text-slate-400 mt-1">{t("nfcNdef")} {carrier.nfc_ndef_uri}</p>
          <p className="text-sm text-slate-400 mt-1">{t("rfidEpc")} {carrier.rfid_epc_sgtin96}</p>
          <img src={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/dpp/${gtin}/${serial}/carrier/qr.png`} alt="QR" className="mt-3 h-24 w-24" />
        </div>
      )}
    </div>
  );
}
