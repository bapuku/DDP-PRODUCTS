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
    <div className="flex items-center gap-1">
      <button
        type="button"
        onClick={() => setLocale("en")}
        className={`px-2 py-1 text-xs font-medium rounded transition ${
          locale === "en" ? "bg-sky-600 text-white" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
        }`}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLocale("fr")}
        className={`px-2 py-1 text-xs font-medium rounded transition ${
          locale === "fr" ? "bg-sky-600 text-white" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
        }`}
      >
        FR
      </button>
    </div>
  );
}
