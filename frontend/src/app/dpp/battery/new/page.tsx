"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

  return (
    <div className="max-w-xl space-y-4">
      <h2 className="text-xl font-semibold">{t("title")}</h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-slate-400">{t("gtin14")}</label>
          <input value={gtin} onChange={(e) => setGtin(e.target.value)} className="w-full rounded bg-slate-800 border border-slate-600 p-2" />
        </div>
        <div>
          <label className="block text-sm text-slate-400">{t("serialNumber")}</label>
          <input value={serial} onChange={(e) => setSerial(e.target.value)} className="w-full rounded bg-slate-800 border border-slate-600 p-2" />
        </div>
        <div>
          <label className="block text-sm text-slate-400">{t("batchNumber")}</label>
          <input value={batch} onChange={(e) => setBatch(e.target.value)} className="w-full rounded bg-slate-800 border border-slate-600 p-2" />
        </div>
      </div>
      <button onClick={submit} disabled={loading} className="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-50">
        {loading ? t("creating") : t("createPassport")}
      </button>
      {result && (
        <pre className="rounded bg-slate-900 border border-slate-700 p-4 text-xs overflow-auto">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
