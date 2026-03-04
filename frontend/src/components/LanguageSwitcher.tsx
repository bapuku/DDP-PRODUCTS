"use client";

import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import type { Locale } from "@/i18n/request";

const LOCALE_COOKIE = "locale";

export default function LanguageSwitcher() {
  const locale = useLocale() as Locale;
  const router = useRouter();

  function setLocale(newLocale: Locale) {
    document.cookie = `${LOCALE_COOKIE}=${newLocale};path=/;max-age=${60 * 60 * 24 * 365}`;
    router.refresh();
  }

  return (
    <div className="flex items-center rounded-lg border border-slate-200 bg-white overflow-hidden">
      <button
        type="button"
        onClick={() => setLocale("en")}
        className={`px-3 py-1.5 text-xs font-medium transition ${
          locale === "en" ? "bg-teal-600 text-white" : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
        }`}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLocale("fr")}
        className={`px-3 py-1.5 text-xs font-medium transition ${
          locale === "fr" ? "bg-teal-600 text-white" : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
        }`}
      >
        FR
      </button>
    </div>
  );
}
