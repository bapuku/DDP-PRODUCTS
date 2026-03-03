"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { api } from "@/services/api";

function DPPContent() {
  const t = useTranslations("dpp");
  const tCommon = useTranslations("common");
  const searchParams = useSearchParams();
  const section = searchParams.get("section") || "batteries";
  const [sectors, setSectors] = useState<string[]>([]);

  useEffect(() => {
    api.dpp.sectors()
      .then((d) => setSectors(d.sectors || []))
      .catch(() => setSectors(["batteries", "electronics", "textiles", "vehicles"]));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold capitalize text-slate-800">{t("title", { section })}</h2>
      <p className="text-slate-600">{t("description")}</p>
      <div className="flex gap-4 flex-wrap">
        {sectors.map((s) => (
          <Link
            key={s}
            href={`/dpp?section=${s}`}
            className={`px-4 py-2 rounded-lg ${section === s ? "bg-sky-500 text-white" : "bg-white border border-slate-200 text-slate-700"} hover:bg-sky-600 hover:text-white transition`}
          >
            {s}
          </Link>
        ))}
      </div>
      <div className="bg-white border border-slate-200 rounded-xl p-4">
        <h3 className="font-medium mb-2 text-slate-800">{t("batteryPassportTitle")}</h3>
        <p className="text-sm text-slate-400 mb-2">{t("batteryPassportApi")}</p>
        <Link href="/dpp/battery/new" className="text-sky-500 hover:text-sky-600 hover:underline text-sm">
          {t("newBatteryFormLink")}
        </Link>
      </div>
    </div>
  );
}

export default function DPPSectionPage() {
  const tCommon = useTranslations("common");
  return (
    <Suspense fallback={<div className="text-slate-400">{tCommon("loading")}</div>}>
      <DPPContent />
    </Suspense>
  );
}
