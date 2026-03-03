"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "";

const BATTERY_CLUSTERS = [
  { id: 1, name: "General Information", fields: 14, example: "Manufacturer, chemistry, mass, category" },
  { id: 2, name: "Carbon Footprint", fields: 8, example: "CO₂e/kWh, footprint class, share per stage" },
  { id: 3, name: "Supply Chain Due Diligence", fields: 11, example: "Third-party certifications, OECD compliance" },
  { id: 4, name: "Circularity & Resource Efficiency", fields: 15, example: "Recycled content, dismantling info, spare parts" },
  { id: 5, name: "Performance & Durability", fields: 18, example: "Rated capacity, cycle life, SOCE, round-trip efficiency" },
  { id: 6, name: "Durability (Additional)", fields: 12, example: "Calendar aging, temperature ranges, warranty" },
  { id: 7, name: "Labelling & Marking", fields: 9, example: "CE marking, QR code, hazard symbols" },
];

export default function NewBatteryPassportPage() {
  const t = useTranslations("battery");
  const [serial, setSerial] = useState("SN-DEMO-001");
  const [batch, setBatch] = useState("BATCH-001");
  const [gtin, setGtin] = useState("06374692674377");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = () => {
    setLoading(true);
    setResult(null);
    fetch(`${API}/api/v1/dpp/battery`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        gtin,
        serial_number: serial,
        batch_number: batch,
        manufacturer_eoid: "EU1234567890123",
        manufacturer_identification: "Demo Manufacturer",
        manufacturing_date: "2024-01-15",
        battery_category: "EV",
        battery_mass_kg: 50,
        carbon_footprint_class: "B",
        carbon_footprint_kg_co2e_kwh: 55,
        chemistry: "NMC",
      }),
    })
      .then((r) => r.json())
      .then(setResult)
      .catch((e) => setResult({ error: e.message }))
      .finally(() => setLoading(false));
  };

  const totalFields = BATTERY_CLUSTERS.reduce((sum, c) => sum + c.fields, 0);

  return (
    <div className="max-w-xl space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">{t("title")}</h2>

      {/* Regulation explainer */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5 space-y-3">
        <h3 className="text-sm font-semibold text-blue-900">
          Battery Passport &mdash; EU Regulation 2023/1542 Annex&nbsp;XIII
        </h3>
        <p className="text-sm text-blue-800 leading-relaxed">
          From February 2027 every EV and industrial battery placed on the EU market must carry
          a digital battery passport. This form creates a passport containing{" "}
          <span className="font-semibold">{totalFields} mandatory fields</span> across 7 data
          clusters defined in Annex&nbsp;XIII.
        </p>
      </div>

      {/* 7 data clusters */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
        <h3 className="text-sm font-semibold text-slate-700">
          7 Data Clusters &middot; {totalFields} Mandatory Fields
        </h3>
        <div className="space-y-2">
          {BATTERY_CLUSTERS.map((c) => (
            <div key={c.id} className="flex items-start gap-3 text-sm">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xs font-bold text-sky-700">
                {c.id}
              </span>
              <div className="min-w-0">
                <p className="text-slate-800">
                  <span className="font-medium">{c.name}</span>
                  <span className="ml-2 text-xs text-slate-400">{c.fields} fields</span>
                </p>
                <p className="text-xs text-slate-500">{c.example}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Form */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400">{t("gtin14")}</label>
            <input value={gtin} onChange={(e) => setGtin(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 p-2 text-slate-800" />
          </div>
          <div>
            <label className="block text-sm text-slate-400">{t("serialNumber")}</label>
            <input value={serial} onChange={(e) => setSerial(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 p-2 text-slate-800" />
          </div>
          <div>
            <label className="block text-sm text-slate-400">{t("batchNumber")}</label>
            <input value={batch} onChange={(e) => setBatch(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 p-2 text-slate-800" />
          </div>
        </div>
        <button onClick={submit} disabled={loading} className="px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white disabled:opacity-50 transition">
          {loading ? t("creating") : t("createPassport")}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="space-y-3">
          <pre className="rounded-xl bg-white border border-slate-200 p-4 text-xs overflow-auto text-slate-600">
            {JSON.stringify(result, null, 2)}
          </pre>
          {!("error" in result) && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 flex items-center justify-between">
              <p className="text-sm text-emerald-800">Battery passport created successfully.</p>
              <Link
                href={`/dpp/${gtin}/${serial}`}
                className="text-sm font-medium text-emerald-700 hover:text-emerald-900 hover:underline"
              >
                Run compliance check &rarr;
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
