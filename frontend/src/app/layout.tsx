import type { Metadata } from "next";
import "./globals.css";
import { getLocale } from "@/i18n/request";
import LayoutClient from "@/components/LayoutClient";

export const metadata: Metadata = {
  title: "EU DPP Platform",
  description: "Digital Product Passport - EU compliance dashboard",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const messages = (await import(`../../messages/${locale}.json`)).default;
  return (
    <html lang={locale}>
      <body className="min-h-screen font-sans antialiased">
        <LayoutClient locale={locale} messages={messages}>
          {children}
        </LayoutClient>
      </body>
    </html>
  );
}
