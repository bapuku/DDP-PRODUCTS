"use client";

import { NextIntlClientProvider } from "next-intl";
import Sidebar from "@/components/Sidebar";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import SystemAssistant from "@/components/SystemAssistant";
import { useTranslations } from "next-intl";
import Link from "next/link";

function Header() {
  const t = useTranslations("layout");
  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-4 shadow-sm">
      <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition">
        <div className="w-8 h-8 bg-gradient-to-br from-teal-600 to-cyan-500 rounded-lg flex items-center justify-center">
          <span className="text-white text-sm font-bold">EU</span>
        </div>
        <h1 className="text-base font-semibold text-slate-800">{t("title")}</h1>
      </Link>
      <div className="ml-auto flex items-center gap-4">
        <span className="text-xs text-slate-400 hidden md:block">{t("regulatoryRef")}</span>
        <LanguageSwitcher />
      </div>
    </header>
  );
}

export default function LayoutClient({
  locale,
  messages,
  children,
}: {
  locale: string;
  messages: Record<string, unknown>;
  children: React.ReactNode;
}) {
  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Header />
          <main className="flex-1 p-6 overflow-auto">{children}</main>
        </div>
      </div>
      <SystemAssistant />
    </NextIntlClientProvider>
  );
}
