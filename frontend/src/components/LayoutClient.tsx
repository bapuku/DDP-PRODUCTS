"use client";

import { NextIntlClientProvider } from "next-intl";
import Sidebar from "@/components/Sidebar";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import { useTranslations } from "next-intl";

function Header() {
  const t = useTranslations("layout");
  return (
    <header className="border-b border-slate-700 px-6 py-3 flex items-center gap-4">
      <h1 className="text-lg font-semibold">{t("title")}</h1>
      <span className="ml-auto text-xs text-slate-500">{t("regulatoryRef")}</span>
      <LanguageSwitcher />
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
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 p-6 overflow-auto">{children}</main>
        </div>
      </div>
    </NextIntlClientProvider>
  );
}
