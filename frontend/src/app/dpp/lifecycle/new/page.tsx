"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { api } from "@/services/api";

export default function NewLifecyclePage() {
  const t = useTranslations("lifecycleNew");
  const tCommon = useTranslations("common");
  const router = useRouter();
  const [gtin, setGtin] = useState("");
  const [serial, setSerial] = useState("");
  const [batch, setBatch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ ddp_uri?: string; validation_passed?: boolean; requires_human_review?: boolean } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const r = await api.lifecycle.create({
        product_gtin: gtin,
        serial_number: serial,
        batch_number: batch || undefined,
        query: "Create DPP",
      });
      setResult(r);
      if (r.ddp_uri) setTimeout(() => router.push(`/dpp/${gtin}/${serial}`), 2000);
    } catch {
      setError(tCommon("requestFailed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <h2 className="text-2xl font-semibold text-slate-800">{t("title")}</h2>
      <p className="text-slate-600 text-sm">{t("description")}</p>
      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">{t("gtin14")}</label>
          <input
            type="text"
            value={gtin}
            onChange={(e) => setGtin(e.target.value)}
            placeholder={t("placeholderGtin")}
            className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">{t("serialNumber")}</label>
          <input
            type="text"
            value={serial}
            onChange={(e) => setSerial(e.target.value)}
            placeholder={t("placeholderSerial")}
            className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">{t("batchOptional")}</label>
          <input
            type="text"
            value={batch}
            onChange={(e) => setBatch(e.target.value)}
            className="w-full rounded-lg bg-white border border-slate-300 px-3 py-2 text-sm text-slate-800"
          />
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        {result && (
          <div className="rounded-lg bg-slate-50 p-3 text-sm">
            <p className="text-slate-600">{t("ddpUri")} {result.ddp_uri ?? "—"}</p>
            <p className="text-slate-600">{t("validationPassed")} {result.validation_passed ? tCommon("yes") : tCommon("no")}</p>
            <p className="text-slate-600">{t("humanReviewRequired")} {result.requires_human_review ? tCommon("yes") : tCommon("no")}</p>
          </div>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-sky-500 hover:bg-sky-600 text-white py-2 text-sm font-medium disabled:opacity-50 transition"
        >
          {loading ? t("creating") : t("createDpp")}
        </button>
      </form>
    </div>
  );
}
