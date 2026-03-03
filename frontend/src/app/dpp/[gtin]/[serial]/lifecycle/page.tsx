"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";

const PHASE_KEYS = [
  "phase0", "phase1", "phase2", "phase3", "phase4",
  "phase5", "phase6", "phase7", "phase8", "phase9",
] as const;

export default function LifecycleTimelinePage() {
  const t = useTranslations("lifecycle");
  const params = useParams();
  const gtin = params?.gtin as string;
  const serial = params?.serial as string;

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/dpp/${gtin}/${serial}`} className="text-sky-400 text-sm hover:underline">
          {t("backToDpp")}
        </Link>
        <h2 className="text-2xl font-semibold">{t("timelineTitle")}</h2>
      </div>
      <p className="text-slate-400 text-sm">{t("description")}</p>
      <ul className="space-y-2">
        {PHASE_KEYS.map((key, i) => (
          <li
            key={key}
            className="flex items-center gap-3 rounded-lg border border-slate-700 p-4"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-700 text-sm font-medium text-slate-300">
              {i}
            </span>
            <span className="text-slate-200">{t(`phases.${key}`)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
