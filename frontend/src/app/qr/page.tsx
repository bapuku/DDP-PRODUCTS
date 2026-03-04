"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

interface QRResult {
  gtin: string;
  serial_number: string;
  product_name: string | null;
  gs1_digital_link: string;
  qr_png_base64: string;
  qr_svg: string;
  nfc_ndef_uri: string;
  rfid_epc_sgtin96: string;
  blockchain?: { anchored: boolean; dpp_hash: string; block_number: number; block_hash: string; merkle_root: string };
}

export default function QRGeneratorPage() {
  const t = useTranslations("qr");
  const [gtin, setGtin] = useState("06374692674377");
  const [serial, setSerial] = useState("SN-001");
  const [productName, setProductName] = useState("");
  const [sector, setSector] = useState("batteries");
  const [manufacturer, setManufacturer] = useState("");
  const [anchorBlockchain, setAnchorBlockchain] = useState(false);
  const [result, setResult] = useState<QRResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function generate() {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("/api/v1/qr/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          gtin, serial_number: serial,
          product_name: productName || undefined,
          sector: sector || undefined,
          manufacturer: manufacturer || undefined,
          anchor_blockchain: anchorBlockchain,
        }),
      });
      setResult(await res.json());
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function downloadPng() {
    window.open(`/api/v1/qr/png?gtin=${gtin}&serial=${serial}&size=15`, "_blank");
  }

  function downloadSvg() {
    window.open(`/api/v1/qr/svg?gtin=${gtin}&serial=${serial}`, "_blank");
  }

  return (
    <div className="max-w-4xl space-y-6">
      <h2 className="text-xl font-bold text-slate-800">{t("title")}</h2>
      <p className="text-sm text-slate-500">{t("description")}</p>

      {/* Explainer */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <h3 className="font-semibold text-blue-800 mb-2">{t("howTitle")}</h3>
        <p className="text-sm text-blue-700 mb-3">{t("howDesc")}</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
          {[
            { icon: "📱", label: t("formatQR") },
            { icon: "📡", label: t("formatNFC") },
            { icon: "🏷️", label: t("formatRFID") },
            { icon: "🔐", label: t("formatBlockchain") },
          ].map((f, i) => (
            <div key={i} className="flex items-center gap-2 bg-white/80 rounded-lg p-2 border border-blue-100">
              <span className="text-lg">{f.icon}</span>
              <span className="text-xs font-medium text-blue-700">{f.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Form */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{t("gtin14")}</label>
            <input value={gtin} onChange={e => setGtin(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" placeholder="06374692674377" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{t("serial")}</label>
            <input value={serial} onChange={e => setSerial(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" placeholder="SN-001" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{t("productName")}</label>
            <input value={productName} onChange={e => setProductName(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" placeholder={t("productNamePlaceholder")} />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{t("sector")}</label>
            <select value={sector} onChange={e => setSector(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm">
              <option value="batteries">{t("sectorBatteries")}</option>
              <option value="electronics">{t("sectorElectronics")}</option>
              <option value="textiles">{t("sectorTextiles")}</option>
              <option value="vehicles">{t("sectorVehicles")}</option>
              <option value="construction">{t("sectorConstruction")}</option>
              <option value="furniture">{t("sectorFurniture")}</option>
              <option value="plastics">{t("sectorPlastics")}</option>
              <option value="chemicals">{t("sectorChemicals")}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{t("manufacturer")}</label>
            <input value={manufacturer} onChange={e => setManufacturer(e.target.value)} className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm" placeholder="EU1234567890123" />
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
              <input type="checkbox" checked={anchorBlockchain} onChange={e => setAnchorBlockchain(e.target.checked)} className="rounded" />
              {t("anchorBlockchain")}
            </label>
          </div>
        </div>
        <button onClick={generate} disabled={loading || !gtin || !serial} className="px-6 py-2.5 rounded-lg bg-sky-500 text-white font-semibold hover:bg-sky-600 transition disabled:opacity-50 text-sm">
          {loading ? t("generating") : t("generate")}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="space-y-4">
          {/* QR Code display */}
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <div className="flex flex-col md:flex-row gap-6">
              {/* QR Image */}
              <div className="flex-shrink-0 flex flex-col items-center gap-3">
                {result.qr_png_base64 && (
                  <img src={`data:image/png;base64,${result.qr_png_base64}`} alt="QR Code" className="w-48 h-48 rounded-lg border border-slate-200" />
                )}
                <div className="flex gap-2">
                  <button onClick={downloadPng} className="px-4 py-1.5 rounded-lg bg-emerald-500 text-white text-xs font-medium hover:bg-emerald-600 transition">
                    {t("downloadPNG")}
                  </button>
                  <button onClick={downloadSvg} className="px-4 py-1.5 rounded-lg bg-purple-500 text-white text-xs font-medium hover:bg-purple-600 transition">
                    {t("downloadSVG")}
                  </button>
                </div>
              </div>

              {/* Data carriers */}
              <div className="flex-1 space-y-3">
                <h3 className="font-semibold text-slate-800">{t("dataCarriers")}</h3>
                <div className="space-y-2">
                  <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">{t("gs1Link")}</p>
                    <p className="text-sm font-mono text-sky-600 break-all">{result.gs1_digital_link}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">{t("nfc")}</p>
                    <p className="text-sm font-mono text-slate-700 break-all">{result.nfc_ndef_uri}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">{t("rfid")}</p>
                    <p className="text-sm font-mono text-slate-700">{result.rfid_epc_sgtin96}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">GTIN / Serial</p>
                    <p className="text-sm font-mono text-slate-700">{result.gtin} / {result.serial_number}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Blockchain anchor result */}
          {result.blockchain && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">🔐</span>
                <h3 className="font-semibold text-emerald-800">{t("blockchainAnchored")}</h3>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white rounded-lg p-3 border border-emerald-100">
                  <p className="text-[10px] uppercase tracking-wider text-slate-400">DPP Hash</p>
                  <p className="text-xs font-mono text-slate-600 mt-1 break-all">{result.blockchain.dpp_hash}</p>
                </div>
                <div className="bg-white rounded-lg p-3 border border-emerald-100">
                  <p className="text-[10px] uppercase tracking-wider text-slate-400">Block #{result.blockchain.block_number}</p>
                  <p className="text-xs font-mono text-slate-600 mt-1 break-all">{result.blockchain.block_hash.slice(0, 32)}…</p>
                </div>
                <div className="bg-white rounded-lg p-3 border border-emerald-100 col-span-2">
                  <p className="text-[10px] uppercase tracking-wider text-slate-400">Merkle Root</p>
                  <p className="text-xs font-mono text-slate-600 mt-1 break-all">{result.blockchain.merkle_root}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
