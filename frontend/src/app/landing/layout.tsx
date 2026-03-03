"use client";

import { NextIntlClientProvider } from "next-intl";
import { useEffect, useState } from "react";

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [messages, setMessages] = useState<Record<string, unknown> | null>(null);
  const [locale, setLocale] = useState("en");

  useEffect(() => {
    const cookieLocale = document.cookie.match(/locale=([^;]+)/)?.[1]?.trim() || "en";
    const loc = cookieLocale === "fr" ? "fr" : "en";
    setLocale(loc);
    import(`../../../messages/${loc}.json`).then((m) => setMessages(m.default));
  }, []);

  if (!messages) return null;

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      {children}
    </NextIntlClientProvider>
  );
}
